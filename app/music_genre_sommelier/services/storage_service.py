from enum import Enum
from pathlib import Path
from typing import BinaryIO


class StorageDirectory(str, Enum):
    AUDIOS = "audios"
    SPECTROGRAMS = "spectrograms"


class StorageService:
    def __init__(self, base_path: str | Path = "storage"):
        self.base_path = Path(base_path)
        self._ensure_directories_exist()

    def _ensure_directories_exist(self) -> None:
        for directory in StorageDirectory:
            dir_path = self.base_path / directory.value
            dir_path.mkdir(parents=True, exist_ok=True)

    def get_directory_path(self, directory: StorageDirectory) -> Path:
        return self.base_path / directory.value

    def store(
        self,
        file: bytes | BinaryIO,
        target_directory: StorageDirectory,
        filename: str,
    ) -> Path:
        target_dir = self.get_directory_path(target_directory)
        target_path = target_dir / filename

        if isinstance(file, bytes):
            target_path.write_bytes(file)
        else:
            target_path.write_bytes(file.read())

        return target_path
