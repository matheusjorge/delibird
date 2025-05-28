import importlib
import inspect
import json
from copy import deepcopy
from pathlib import Path
from typing import Annotated, Any, Mapping, Sequence, Type

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    computed_field,
    field_serializer,
    model_validator,
)

from ..encoders.pydantic_encoder import PydanticEncoder
from .protocols import ContentEncoderProtocol


def _ensure_path(p: str | Path) -> Path:
    if isinstance(p, Path):
        return p
    if isinstance(p, str):
        return Path(p)
    raise TypeError(f"Expected str or Path, got {type(p)}")


class FileMetadata(BaseModel):
    filename: str
    file_content_encoder_class: Type[ContentEncoderProtocol]
    file_content_class: Type[Any]
    file_dump_kwargs: Mapping[str, Any] = {}

    @field_serializer("file_content_encoder_class")
    def serialize_file_content_encoder_class(
        self, v: Type[ContentEncoderProtocol]
    ) -> str:
        return self._module_dumping(v)

    @field_serializer("file_content_class")
    def serialize_file_content_class(self, v: Type[Any]) -> str:
        return self._module_dumping(v)

    @staticmethod
    def _module_dumping(v: Type[Any]) -> str:
        return json.dumps({"name": v.__name__, "module": inspect.getmodule(v).__name__})

    @staticmethod
    def _module_loading(metadata: Mapping[str, str], field_name: str) -> Type[Any]:
        data = json.loads(metadata[field_name])
        return getattr(
            importlib.import_module(data["module"]),
            data["name"],
        )

    @classmethod
    def load(cls, data: dict) -> "FileMetadata":
        data["file_content_class"] = cls._module_loading(data, "file_content_class")
        data["file_content_encoder_class"] = cls._module_loading(
            data, "file_content_encoder_class"
        )
        return cls.model_validate(data)


class FolderMetadata(BaseModel):
    files_metadata: Annotated[
        Sequence[FileMetadata],
        Field(..., description="The metadata of the files in the folder"),
    ] = []
    folders: Annotated[
        Sequence[str], Field(..., description="The names of the folders in the package")
    ] = []

    def append(self, file_metadata: FileMetadata):
        self.files_metadata.append(file_metadata)

    def dump(self, path: Path) -> None:
        with open(path / "__metadata__", "w") as f:
            f.write(self.model_dump_json())

    @classmethod
    def load(cls, path: Path) -> "FolderMetadata":
        with open(path / "__metadata__", "r") as f:
            data = json.loads(f.read())
            data["files_metadata"] = [
                FileMetadata.load(file_metadata)
                for file_metadata in data["files_metadata"]
            ]
            return cls.model_validate(data)

    def __len__(self):
        return len(self.files_metadata)

    def __getitem__(self, idx: int) -> FileMetadata:
        return self.files_metadata[idx]


class File(BaseModel):
    filename: Annotated[str, Field(..., description="The name of the file")]
    content: Annotated[
        Any,
        Field(
            ...,
            description="The content of the file. Can be any object that matches the encoder",
        ),
    ]
    content_encoder: Annotated[
        ContentEncoderProtocol,
        Field(
            default=PydanticEncoder,
            description="The encoder used to dump and load the content",
        ),
    ]
    dump_kwargs: Annotated[
        Mapping[str, Any],
        Field(
            ...,
            description="The kwargs used to dump the file. Will be passed to the content encoder",
        ),
    ] = {}

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def validate_content_encoder(self):
        if not self.content_encoder.validate_content(self.content):
            raise ValueError(f"Invalid content: {self.content}")
        return self

    def dump(self, path: Path, **kwargs) -> None:
        _kwargs = deepcopy(self.dump_kwargs)
        _kwargs.update(kwargs)
        self.content_encoder.disk_dump(self.content, path / self.filename, **_kwargs)

    @classmethod
    def load(
        cls,
        folder_path: Path,
        filename: str,
        content_class: Type[Any],
        dump_kwargs: Mapping[str, Any] | None = None,
        content_encoder_class: Type[ContentEncoderProtocol] = PydanticEncoder,
        **kwargs,
    ) -> "File":
        content = content_encoder_class.disk_load(
            folder_path / filename,
            content_class,
            **kwargs,
        )
        if dump_kwargs is None:
            dump_kwargs = {}
        return cls(
            filename=filename,
            content=content,
            content_encoder=content_encoder_class,
            dump_kwargs=dump_kwargs,
        )

    @computed_field
    @property
    def metadata(self) -> FileMetadata:
        return FileMetadata(
            filename=self.filename,
            file_content_class=self.content_encoder.base_dump_class(self.content),
            file_content_encoder_class=self.content_encoder,
            file_dump_kwargs=self.dump_kwargs,
        )


class Folder(BaseModel):
    name: Annotated[Path, BeforeValidator(_ensure_path)]
    files: Annotated[Sequence[File], Field(default_factory=list)]
    folders: Annotated[Sequence["Folder"], Field(default_factory=list)]
    folder_metadata: Annotated[FolderMetadata, Field(default_factory=FolderMetadata)]
    _index: Mapping[str, Any]

    def model_post_init(self, context: Any):
        self._index = {str(file.filename): file.content for file in self.files}
        self._index.update({str(folder.name): folder for folder in self.folders})

    def add_file(self, file: File):
        if file.filename in [f.filename for f in self.files]:
            raise ValueError(f"File {file.filename} already exists")
        self.files.append(file)
        self.folder_metadata.append(file.metadata)
        self._index[str(file.filename)] = file.content
        return self

    def remove_file(self, file: File):
        idx = self.files.index(file)
        self.files.remove(file)
        self.folder_metadata.files_metadata.pop(idx)
        self._index.pop(str(file.filename))
        return self

    def add_folder(self, folder: "Folder"):
        if folder.name in [f.name for f in self.folders]:
            raise ValueError(f"Folder {folder.name} already exists")
        self.folders.append(folder)
        self.folder_metadata.folders.append(str(folder.name))
        self._index[str(folder.name)] = folder
        return self

    def dump(self, path: Path, **kwargs) -> None:
        full_path = path / self.name
        full_path.mkdir(parents=True, exist_ok=True)
        for file in self.files:
            file.dump(full_path, **kwargs)
        for folder in self.folders:
            folder.dump(full_path, **kwargs)
        self.folder_metadata.dump(full_path)

    @classmethod
    def load(cls, path: Path, level: int = 0) -> "Folder":
        folder_metadata = FolderMetadata.load(path)
        files = []
        for file_metadata in folder_metadata.files_metadata:
            file = File.load(
                folder_path=path,
                filename=file_metadata.filename,
                content_encoder_class=file_metadata.file_content_encoder_class,
                content_class=file_metadata.file_content_class,
                dump_kwargs=file_metadata.file_dump_kwargs,
            )
            files.append(file)

        folders = [
            cls.load(path / folder_name, level=level + 1)
            for folder_name in folder_metadata.folders
        ]

        if level != 0:
            _path = path.relative_to(path.parent)
        else:
            _path = path

        return cls(
            name=_path, files=files, folders=folders, folder_metadata=folder_metadata
        )

    def __getitem__(self, key: str) -> Any:
        return self._index[key]


class Package(BaseModel):
    name: str
    root: Annotated[Path, BeforeValidator(_ensure_path)] = Path(".")
    folders: Annotated[
        Sequence[Folder],
        Field(default_factory=list, description="The folders in the package"),
    ]
    _index: Mapping[str, Any]

    def model_post_init(self, context: Any):
        self._index = {str(folder.name): folder for folder in self.folders}

    def add_folder(self, folder: Folder):
        if folder.name in [f.name for f in self.folders]:
            raise ValueError(f"Folder {folder.name} already exists")
        self.folders.append(folder)
        self._index[str(folder.name)] = folder

        return self

    def dump(self, **kwargs) -> None:
        for folder in self.folders:
            folder.dump(self.root / self.name, **kwargs)

    @classmethod
    def load(cls, path: Path) -> "Package":
        folders = [
            Folder.load(folder_name, level=1)
            for folder_name in path.iterdir()
            if folder_name.is_dir()
        ]
        return cls(name=path.name, root=path.parent, folders=folders)

    def __getitem__(self, key: str) -> Any:
        return self._index[key]
