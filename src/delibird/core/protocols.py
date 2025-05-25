from pathlib import Path
from typing import Any, Protocol, Type, runtime_checkable

from pydantic import BaseModel


@runtime_checkable
class ContentEncoderProtocol(Protocol):
    @staticmethod
    def disk_dump(content: Any, path: Path, **kwargs) -> None: ...

    @staticmethod
    def disk_load(path: Path, klass: Type[BaseModel], **kwargs) -> BaseModel: ...

    @staticmethod
    def validate_content(content: Any, **kwargs) -> bool: ...
