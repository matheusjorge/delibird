import shutil
from pathlib import Path

import boto3

from .. import Package


class S3Exporter:
    def __init__(self, bucket_name: str, endpoint_url: str | None = None):
        if endpoint_url:
            self.s3 = boto3.client("s3", endpoint_url=endpoint_url)
        else:
            self.s3 = boto3.client("s3")
        self.bucket_name = bucket_name
        if self.bucket_name not in [
            bucket["Name"] for bucket in self.s3.list_buckets()["Buckets"]
        ]:
            self.s3.create_bucket(Bucket=self.bucket_name)

    def _package_exists(self, package_name: str, compressed: bool = False) -> bool:
        response = self.s3.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=f"{package_name}.zip" if compressed else f"{package_name}/",
            MaxKeys=1,
        )
        return "Contents" in response

    def export(
        self,
        package: Package,
        enforce_uniqueness: bool = False,
        compress: bool = False,
    ):

        if enforce_uniqueness:
            if self._package_exists(package.name):
                raise ValueError(f"Package {package.name} already exists")

        package.dump()

        if compress:
            self._export_compressed(package)
        else:
            self._export_uncompressed(package)

    def _export_compressed(self, package: Package):
        shutil.make_archive(
            package.root / package.name, "zip", package.root / package.name
        )
        try:
            self.s3.upload_file(
                package.root / f"{package.name}.zip",
                self.bucket_name,
                f"{package.name}.zip",
            )
        finally:
            (package.root / f"{package.name}.zip").unlink()
            shutil.rmtree(package.root / package.name)

    def _export_uncompressed(self, package: Package):
        def _upload_folder(folder_path: Path):
            for file_path in folder_path.rglob("*"):
                if file_path.is_file():
                    key = str(file_path.relative_to(folder_path.parent.parent))
                    self.s3.upload_file(str(file_path), self.bucket_name, key)

        try:
            for folder in package.folders:
                _upload_folder(package.root / package.name / folder.name)
        finally:
            shutil.rmtree(package.root / package.name)

    def load(
        self,
        package_name: str,
        temp_dir: Path = Path(".") / "tmp",
        compressed: bool = False,
    ) -> Package:
        if not self._package_exists(package_name, compressed=compressed):
            raise ValueError(f"Package {package_name} does not exist")

        # Create temp directory to store downloaded files
        temp_dir = temp_dir
        temp_dir.mkdir(exist_ok=True)

        if compressed:
            self._download_compressed_package(package_name, temp_dir)
        else:
            files = self._get_package_files(package_name)
            self._download_uncompressed_package(files, temp_dir)

        # Load package from downloaded files
        package = Package.load(temp_dir / package_name)

        if compressed:
            (temp_dir / f"{package_name}.zip").unlink()

        shutil.rmtree(temp_dir / package_name)

        return package

    def _get_package_files(self, package_name: str) -> list[str]:
        response = self.s3.list_objects_v2(
            Bucket=self.bucket_name, Prefix=f"{package_name}/"
        )
        return [file["Key"] for file in response["Contents"]]

    def _download_compressed_package(
        self, package_name: str, temp_dir: Path = Path(".") / "tmp"
    ) -> Package:
        self.s3.download_file(
            self.bucket_name,
            f"{package_name}.zip",
            str(temp_dir / f"{package_name}.zip"),
        )
        shutil.unpack_archive(temp_dir / f"{package_name}.zip", temp_dir / package_name)

    def _download_uncompressed_package(
        self, files: list[str], temp_dir: Path = Path(".") / "tmp"
    ) -> Package:
        # Download all files
        for file in files:
            file_path = Path(file)
            (temp_dir / file_path.parent).mkdir(parents=True, exist_ok=True)
            self.s3.download_file(self.bucket_name, file, str(temp_dir / file_path))
