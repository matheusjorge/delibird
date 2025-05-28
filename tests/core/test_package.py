import shutil
from pathlib import Path

import pytest

from delibird import File, Folder, Package


def test_create_package_ok():
    package = Package(name="test")
    assert package.name == "test"
    assert package.root == Path(".")
    assert len(package.folders) == 0


def test_add_folder(test_content):
    package = Package(name="test")
    folder = Folder(name="test")
    folder.add_file(File(filename="test.json", content=test_content))
    package.add_folder(folder)
    assert len(package.folders) == 1
    assert package.folders[0] == folder
    assert len(package.folders[0].files) == 1
    assert package.folders[0].files[0].filename == "test.json"
    assert package.folders[0].files[0].content == test_content


def test_add_complex_folder_structure(test_content):
    package = Package(name="test")
    files = [
        File(filename="test.json", content=test_content),
        File(filename="test2.json", content=test_content),
        File(filename="test3.json", content=test_content),
        File(filename="test4.json", content=test_content),
    ]
    folders = [
        Folder(name="test"),
        Folder(name="test2"),
    ]
    folders[0].add_file(files[0])
    folders[0].add_file(files[1])
    folders[1].add_file(files[2])
    folders[1].add_file(files[3])
    package.add_folder(folders[0])
    package.add_folder(folders[1])

    package.folders[0].add_folder(folders[1])


def test_dump(test_content):
    package = Package(name="test")
    files = [
        File(filename="test.json", content=test_content),
        File(filename="test2.json", content=test_content),
        File(filename="test3.json", content=test_content),
        File(filename="test4.json", content=test_content),
    ]
    folders = [
        Folder(name="test"),
        Folder(name="test2"),
    ]
    folders[0].add_file(files[0])
    folders[0].add_file(files[1])
    folders[1].add_file(files[2])
    folders[1].add_file(files[3])
    package.add_folder(folders[0])
    package.add_folder(folders[1])

    package.folders[0].add_folder(folders[1])
    package.dump()

    assert (Path(".") / "test").exists()
    assert (Path(".") / "test" / "test").exists()
    assert (Path(".") / "test" / "test" / "test.json").exists()
    assert (Path(".") / "test" / "test" / "test2.json").exists()
    assert (Path(".") / "test" / "test" / "test2" / "test3.json").exists()
    assert (Path(".") / "test" / "test" / "test2" / "test4.json").exists()
    assert (Path(".") / "test" / "test2").exists()
    assert (Path(".") / "test" / "test2" / "test3.json").exists()
    assert (Path(".") / "test" / "test2" / "test4.json").exists()

    # clean up
    shutil.rmtree(Path(".") / "test")


def test_load(test_content):
    package = Package(name="test")
    files = [
        File(filename="test.json", content=test_content),
        File(filename="test2.json", content=test_content),
        File(filename="test3.json", content=test_content),
        File(filename="test4.json", content=test_content),
    ]
    folders = [
        Folder(name="test"),
        Folder(name="test2"),
    ]
    folders[0].add_file(files[0])
    folders[0].add_file(files[1])
    folders[1].add_file(files[2])
    folders[1].add_file(files[3])
    package.add_folder(folders[0])
    package.add_folder(folders[1])

    package.folders[0].add_folder(folders[1])
    package.dump()

    loaded_package = Package.load(Path(".") / "test")
    assert loaded_package.name == "test"
    assert len(loaded_package.folders) == 2
    assert loaded_package.folders[0] == folders[0]
    assert loaded_package.folders[1] == folders[1]
    assert len(loaded_package.folders[0].files) == 2
    assert loaded_package.folders[0].files[0] == files[0]
    assert loaded_package.folders[0].files[1] == files[1]
    assert len(loaded_package.folders[1].files) == 2
    assert loaded_package.folders[1].files[0] == files[2]

    # clean up
    shutil.rmtree(Path(".") / "test")


def test_chaining():
    package = Package(name="test")
    package.add_folder(Folder(name="test")).add_folder(Folder(name="test2"))
    assert len(package.folders) == 2


def test_getitem(test_content):
    package = Package(name="test")
    folder = Folder(name="test").add_file(
        File(filename="test.json", content=test_content)
    )
    package.add_folder(folder)
    assert package["test"] == folder
    assert package["test"]["test.json"] == test_content


def test_getitem_not_found():
    package = Package(name="test")
    with pytest.raises(KeyError):
        _ = package["test"]
