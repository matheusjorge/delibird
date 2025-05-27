<div align="center">
  <img src="assets/delibird_icon2.png" alt="Delibird Logo" width="200"/>
</div>

# Delibird

Delibird (Data Exchange LIB) is a Python package for managing and exporting Python objects to persistent storage, with a flexible structure. It provides a simple way to organize files and folders, and supports exporting to various storage backends like S3.

## Features

- Create and manage data packages with nested folder structures
- Support for Pydantic models as file content
- Export packages to S3 with optional compression
- Load packages from storage
- Enforce package uniqueness during export

## Installation

Clone the repository and install using uv:
```sh
git clone https://github.com/matheusjorge/delibird.git
````

```sh
cd delibird
uv sync
```

## Usage

Here's a basic example of how to use Delibird:

```python
from pydantic import BaseModel

from delibird import File, Folder, Package
from delibird.exporters.s3 import S3Exporter


# Define your data model
class UserData(BaseModel):
    name: str
    age: int
    email: str


# Manipulate the data all you want
user_obj = UserData(name="John Doe", age=30, email="john@example.com")

# Create a file from it
# By default, pydantic objects will be converted to json
file = File(filename="john.json", content=user_obj)

# Add the file to a folder
folder = Folder(name="users")
folder.add_file(file)

# Add the folder to the package
package = Package(name="demo")
package.add_folder(folder)


# Export the package to S3
exporter = S3Exporter(bucket_name="delibird-test", endpoint_url="http://localhost:9000")
exporter.export(package)

# Or dump the package to a folder
package.dump()

```

## Documentation

To be implemented

## Contributing

We welcome contributions! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For any questions or suggestions, please open an issue in the GitHub repository.









