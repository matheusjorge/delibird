import shutil
from pathlib import Path

import pytest
from pydantic import BaseModel

from delibird import File, Folder, Package
from delibird.encoders.paginated_pydantic_encoder import PaginatedPydanticEncoder


class SimpleModel(BaseModel):
    name: str
    age: int


def test_paginated_pydantic_encoder_dump_one_page():
    content = [SimpleModel(name=f"test_{i}", age=i) for i in range(10)]
    directory = Path(".") / "paginated"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "test.json"
    PaginatedPydanticEncoder.disk_dump(content, path)

    print(list(directory.glob("*.json")))
    assert (directory / "test_0.json").exists()
    assert not (directory / "test_1.json").exists()

    shutil.rmtree(directory)


def test_paginated_pydantic_encoder_dump_multiple_pages():
    content = [SimpleModel(name=f"test_{i}", age=i) for i in range(10)]
    directory = Path(".") / "paginated"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "test.json"
    PaginatedPydanticEncoder.disk_dump(content, path, page_size=3)

    assert (directory / "test_0.json").exists()
    assert (directory / "test_1.json").exists()
    assert (directory / "test_2.json").exists()
    assert (directory / "test_3.json").exists()
    assert not (directory / "test_4.json").exists()

    shutil.rmtree(directory)


def test_paginated_pydantic_encoder_load_one_page():
    content = [SimpleModel(name=f"test_{i}", age=i) for i in range(10)]
    directory = Path(".") / "paginated"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "test.json"
    PaginatedPydanticEncoder.disk_dump(content, path)

    loaded = PaginatedPydanticEncoder.disk_load(path, SimpleModel)
    assert loaded == content

    shutil.rmtree(directory)


def test_paginated_pydantic_encoder_load_multiple_pages():
    content = [SimpleModel(name=f"test_{i}", age=i) for i in range(10)]
    directory = Path(".") / "paginated"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "test.json"
    PaginatedPydanticEncoder.disk_dump(content, path, page_size=3)

    loaded = PaginatedPydanticEncoder.disk_load(path, SimpleModel)
    assert loaded == content

    shutil.rmtree(directory)


def test_paginated_with_file():
    content = [SimpleModel(name=f"test_{i}", age=i) for i in range(10)]
    directory = Path(".") / "paginated"
    directory.mkdir(parents=True, exist_ok=True)
    file = File(
        filename="test.json", content=content, content_encoder=PaginatedPydanticEncoder
    )

    file.dump(directory, page_size=3)

    assert (directory / "test_0.json").exists()
    assert (directory / "test_1.json").exists()
    assert (directory / "test_2.json").exists()
    assert (directory / "test_3.json").exists()
    assert not (directory / "test_4.json").exists()

    loaded_file = File.load(
        directory,
        "test.json",
        SimpleModel,
        content_encoder_class=PaginatedPydanticEncoder,
    )
    assert loaded_file == file
    shutil.rmtree(directory)


def test_paginated_with_file_error():
    content = [SimpleModel(name=f"test_{i}", age=i) for i in range(10)]
    with pytest.raises(ValueError):
        File(filename="test.json", content=content)


def test_paginated_with_folder():
    content = [SimpleModel(name=f"test_{i}", age=i) for i in range(10)]
    directory = Path(".")
    directory.mkdir(parents=True, exist_ok=True)
    file = File(
        filename="test.json", content=content, content_encoder=PaginatedPydanticEncoder
    )
    folder = Folder(name="paginated")
    folder.add_file(file, dump_kwargs={"page_size": 3})

    folder.dump(directory)

    assert (directory / "paginated" / "test_0.json").exists()
    assert (directory / "paginated" / "test_1.json").exists()
    assert (directory / "paginated" / "test_2.json").exists()
    assert (directory / "paginated" / "test_3.json").exists()
    assert not (directory / "paginated" / "test_4.json").exists()

    shutil.rmtree(directory / "paginated")
