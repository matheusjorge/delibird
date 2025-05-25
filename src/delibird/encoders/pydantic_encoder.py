from pathlib import Path
from typing import Any, Type

from pydantic import BaseModel


class PydanticEncoder:
    @staticmethod
    def disk_dump(content: BaseModel, path: Path, **kwargs) -> None:
        with open(path, "w") as f:
            f.write(content.model_dump_json(**kwargs))

    @staticmethod
    def disk_load(path: Path, klass: Type[BaseModel], **kwargs) -> BaseModel:
        with open(path, "r") as f:
            return klass.model_validate_json(f.read(), **kwargs)

    @staticmethod
    def validate_content(content: Any, **kwargs) -> bool:
        return isinstance(content, BaseModel)
