from pathlib import Path

import pytest

from delibird import File
from delibird.encoders.pydantic_encoder import PydanticEncoder


def test_create_file_ok(test_content):
    file = File(
        filename="test.json",
        content=test_content,
    )
    assert file.filename == "test.json"
    assert file.content == test_content


def test_create_file_invalid_content(test_content):
    with pytest.raises(ValueError):
        File(
            filename="test.json",
            content="test",
        )


def test_file_dump(test_content):
    file = File(
        filename="test.json",
        content=test_content,
    )
    file.dump(Path("."))
    assert Path(".").joinpath("test.json").exists()
    assert Path(".").joinpath("test.json").read_text() == test_content.model_dump_json()

    # clean up
    (Path(".") / "test.json").unlink()


def test_file_load(test_content, test_content_class):
    file = File(
        filename="test.json",
        content=test_content,
    )
    file.dump(Path("."))

    loaded_file = File.load(
        Path("."),
        "test.json",
        content_encoder_class=PydanticEncoder,
        content_class=test_content_class,
    )
    assert loaded_file.content == test_content

    # clean up
    (Path(".") / "test.json").unlink()
