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

    def export(self, package: Package, enforce_uniqueness: bool = False):
        def _upload_folder(folder_path: Path):
            for file_path in folder_path.rglob("*"):
                if file_path.is_file():
                    key = str(file_path.relative_to(folder_path.parent.parent))
                    self.s3.upload_file(str(file_path), self.bucket_name, key)

        # checks if the package already exists
        if enforce_uniqueness:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name, Prefix=f"{package.name}/", MaxKeys=1
            )
            if "Contents" in response:
                raise ValueError(f"Package {package.name} already exists")

        package.dump()
        for folder in package.folders:
            _upload_folder(package.root / package.name / folder.name)

        # remove temp structure
        shutil.rmtree(package.root / package.name)

    def load(self, package_name: str, temp_dir: Path = Path(".") / "tmp") -> Package:
        response = self.s3.list_objects_v2(
            Bucket=self.bucket_name, Prefix=f"{package_name}/", MaxKeys=1
        )
        if "Contents" not in response:
            raise ValueError(f"Package {package_name} does not exist")

        response = self.s3.list_objects_v2(
            Bucket=self.bucket_name, Prefix=f"{package_name}/"
        )
        if "Contents" not in response:
            raise ValueError(f"Package {package_name} does not exist")

        # Create temp directory to store downloaded files
        temp_dir = temp_dir
        temp_dir.mkdir(exist_ok=True)

        # Download all files
        for file in response["Contents"]:
            file_path = Path(file["Key"])
            (temp_dir / file_path.parent).mkdir(parents=True, exist_ok=True)
            self.s3.download_file(
                self.bucket_name, file["Key"], str(temp_dir / file_path)
            )

        # Load package from downloaded files
        package = Package.load(temp_dir / package_name)

        # Clean up temp directory
        shutil.rmtree(temp_dir / package_name)

        return package
