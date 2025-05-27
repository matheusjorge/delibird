import json
from pathlib import Path
from typing import Any, Sequence, Type

from pydantic import BaseModel


class PaginatedPydanticEncoder:
    @staticmethod
    def disk_dump(content: Sequence[BaseModel], path: Path, **kwargs) -> None:
        page_size = kwargs.pop("page_size", 10)
        total_pages = len(content) // page_size
        if len(content) % page_size != 0:
            total_pages += 1
        for page_number in range(total_pages):
            page_content = content[
                page_number * page_size : (page_number + 1) * page_size
            ]
            with open(path.parent / f"{path.stem}_{page_number}.json", "w") as f:
                json.dump([page.model_dump(**kwargs) for page in page_content], f)

    @staticmethod
    def disk_load(path: Path, klass: Type[BaseModel], **kwargs) -> Sequence[BaseModel]:
        parent = path.parent
        files = list(parent.glob(f"{path.stem}_*.json"))
        files.sort(key=lambda x: int(x.stem.split("_")[-1]))
        content = []
        for file in files:
            with open(file, "r") as f:
                content.extend(json.load(f))
        return [klass.model_validate(item) for item in content]

    @staticmethod
    def validate_content(content: Any, **kwargs) -> bool:
        return isinstance(content, Sequence) and all(
            isinstance(item, BaseModel) for item in content
        )

    @staticmethod
    def base_dump_class(content: Sequence[BaseModel], **kwargs) -> Type[BaseModel]:
        return type(content[0])
