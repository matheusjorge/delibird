from pathlib import Path

from pydantic import BaseModel

from delibird import File, Folder, Package
from delibird.exporters.s3 import S3Exporter


class TestContent(BaseModel):
    name: str
    age: int


def build_package(package_name: str) -> Package:
    files = [
        File(filename="test.json", content=TestContent(name="test", age=10)),
        File(filename="test2.json", content=TestContent(name="test2", age=20)),
        File(filename="test3.json", content=TestContent(name="test3", age=30)),
        File(filename="test4.json", content=TestContent(name="test4", age=40)),
    ]
    folders = [
        Folder(name="test"),
        Folder(name="test2"),
    ]

    folders[0].add_file(files[0])
    folders[0].add_file(files[1])
    folders[1].add_file(files[2])
    folders[1].add_file(files[3])
    folders[1].add_folder(folders[0])

    root = Path(".")
    package = Package(name=package_name, root=root)
    package.add_folder(folders[0])
    package.add_folder(folders[1])

    return package


def main():
    exporter = S3Exporter(
        bucket_name="delibird-test", endpoint_url="http://localhost:9000"
    )
    package = build_package("test")
    exporter.export(package, enforce_uniqueness=False)
    loaded_package = exporter.load(package.name)
    assert loaded_package.name == package.name
    assert loaded_package.folders == package.folders
    assert loaded_package.folders[0].files == package.folders[0].files
    assert loaded_package.folders[1].files == package.folders[1].files
    assert loaded_package.folders[1].folders == package.folders[1].folders

    package = build_package("test_compressed")
    exporter.export(package, enforce_uniqueness=False, compress=True)
    loaded_compressed_package = exporter.load(package.name, compressed=True)
    assert loaded_compressed_package.name == package.name
    assert loaded_compressed_package.folders == package.folders
    assert loaded_compressed_package.folders[0].files == package.folders[0].files
    assert loaded_compressed_package.folders[1].files == package.folders[1].files
    assert loaded_compressed_package.folders[1].folders == package.folders[1].folders


if __name__ == "__main__":
    main()
