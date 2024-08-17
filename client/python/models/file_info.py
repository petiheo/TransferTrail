import os
from datetime import datetime

class FileInfo:
    def __init__(self, name: str, size: int, last_modified: datetime):
        self.name = name
        self.size = size
        self.last_modified = last_modified

    def to_dict(self):
        return {
            "name": self.name,
            "size": self.size,
            "last_modified": self.last_modified.isoformat()
        }

    @staticmethod
    def from_dict(data: dict):
        return FileInfo(
            name=data["name"],
            size=data["size"],
            last_modified=datetime.fromisoformat(data["last_modified"])
        )

    @staticmethod
    def from_path(file_path: str):
        name = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        last_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
        return FileInfo(name, size, last_modified)

    @staticmethod
    def list_from_directory(directory: str):
        return [FileInfo.from_path(os.path.join(directory, f)) 
                for f in os.listdir(directory) 
                if os.path.isfile(os.path.join(directory, f))]
