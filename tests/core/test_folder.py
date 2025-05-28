import shutil
from pathlib import Path

import pytest

from delibird import File, Folder


def test_create_folder_ok():
    folder = Folder(name="test")
    assert folder.name == Path("test")
    assert len(folder.files) == 0
    assert len(folder.folders) == 0
    assert len(folder.folder_metadata) == 0


def test_create_folder_not_ok():
    with pytest.raises(TypeError):
        _ = Folder(name=1)


def test_add_file_ok(test_content):
    folder = Folder(name="test")
    folder.add_file(File(filename="test.json", content=test_content))
    assert len(folder.files) == 1
    assert folder.files[0].filename == "test.json"
    assert folder.files[0].content == test_content


def test_add_multiple_files_ok(test_content):
    folder = Folder(name="test")
    folder.add_file(File(filename="test.json", content=test_content))
    folder.add_file(File(filename="test2.json", content=test_content))
    assert len(folder.files) == 2
    assert folder.files[0].filename == "test.json"
    assert folder.files[0].content == test_content
    assert folder.files[1].filename == "test2.json"
    assert folder.files[1].content == test_content


def test_remove_file_ok(test_content):
    folder = Folder(name="test")
    file = File(filename="test.json", content=test_content)
    folder.add_file(file)
    assert len(folder.files) == 1
    folder.remove_file(file)
    assert len(folder.files) == 0


def test_add_duplicate_file_not_ok(test_content):
    folder = Folder(name="test")
    file = File(filename="test.json", content=test_content)
    folder.add_file(file)
    with pytest.raises(ValueError):
        folder.add_file(file)


def test_dump(test_content):
    folder_name = "test"
    directory = Path(".")
    folder = Folder(name=folder_name)
    folder.add_file(File(filename="test.json", content=test_content))
    folder.dump(directory)
    assert directory.joinpath(folder_name).exists()
    assert directory.joinpath(folder_name).joinpath("test.json").exists()
    assert (
        directory.joinpath(folder_name).joinpath("test.json").read_text()
        == test_content.model_dump_json()
    )
    assert directory.joinpath(folder_name).joinpath("__metadata__").exists()

    # clean up
    shutil.rmtree(directory / folder_name)


def test_nested_folder_dump(test_content):
    folder_name = "test"
    directory = Path(".")
    folder = Folder(name=folder_name)
    folder.add_file(File(filename="test.json", content=test_content))

    folder_name2 = "test2"
    folder.add_folder(Folder(name=folder_name2))
    folder.folders[0].add_file(File(filename="test2.json", content=test_content))
    folder.dump(directory)
    assert directory.joinpath(folder_name).exists()
    assert directory.joinpath(folder_name).joinpath("test.json").exists()
    assert (
        directory.joinpath(folder_name).joinpath("test.json").read_text()
        == test_content.model_dump_json()
    )
    assert directory.joinpath(folder_name).joinpath("__metadata__").exists()
    assert directory.joinpath(folder_name).joinpath(folder_name2).exists()
    assert (
        directory.joinpath(folder_name)
        .joinpath(folder_name2)
        .joinpath("test2.json")
        .exists()
    )
    assert (
        directory.joinpath(folder_name)
        .joinpath(folder_name2)
        .joinpath("test2.json")
        .read_text()
        == test_content.model_dump_json()
    )
    assert (
        directory.joinpath(folder_name)
        .joinpath(folder_name2)
        .joinpath("__metadata__")
        .exists()
    )

    # clean up
    shutil.rmtree(directory / folder_name)


def test_load(test_content):
    folder_name = "test"
    directory = Path(".")
    folder = Folder(name=folder_name)
    folder.add_file(File(filename="test.json", content=test_content))
    folder.dump(directory)
    loaded_folder = Folder.load(directory / folder_name)
    assert loaded_folder.name == Path(folder_name)
    assert len(loaded_folder.files) == 1
    assert loaded_folder.files[0].filename == "test.json"
    assert loaded_folder.files[0].content == test_content

    # clean up
    shutil.rmtree(directory / folder_name)


def test_load_nested_folder(test_content):
    folder_name = "test"
    directory = Path(".")
    folder = Folder(name=folder_name)
    folder.add_file(File(filename="test.json", content=test_content))
    folder.add_folder(Folder(name="test2"))
    folder.folders[0].add_file(File(filename="test2.json", content=test_content))
    folder.dump(directory)
    loaded_folder = Folder.load(directory / folder_name)
    assert loaded_folder.name == Path(folder_name)
    assert len(loaded_folder.files) == 1
    assert loaded_folder.files[0].filename == "test.json"
    assert loaded_folder.files[0].content == test_content

    # clean up
    shutil.rmtree(directory / folder_name)


def test_chaining(test_content):
    folder = Folder(name="test")
    (
        folder.add_file(File(filename="test.json", content=test_content))
        .add_folder(Folder(name="test2"))
        .folders[0]
        .add_file(File(filename="test2.json", content=test_content))
    )
    assert len(folder.files) == 1
    assert len(folder.folders) == 1
    assert len(folder.folders[0].files) == 1


def test_getitem(test_content):
    folder = Folder(name="test")
    folder.add_file(File(filename="test.json", content=test_content))
    assert folder["test.json"] == test_content


def test_getitem_not_found():
    folder = Folder(name="test")
    with pytest.raises(KeyError):
        _ = folder["test.json"]


def test_getitem_nested(test_content):
    folder = Folder(name="test")
    folder.add_folder(Folder(name="test2"))
    folder["test2"].add_file(File(filename="test2.json", content=test_content))
    assert folder["test2"]["test2.json"] == test_content
