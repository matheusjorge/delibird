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
