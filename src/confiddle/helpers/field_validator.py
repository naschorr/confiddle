from pathlib import Path
from typing import TypeVar

T = TypeVar("T")


class FieldValidator:
    """
    Utility class for providing common validation functions for Pydantic model fields.
    """

    @staticmethod
    def create_directory_validator(path: Path) -> Path:
        """Ensure the directory exists, creating it if necessary."""
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        elif not path.is_dir():
            raise ValueError(f"Path {path} exists but is not a directory")
        return path

    @staticmethod
    def directory_exists_validator(path: Path) -> Path:
        """Ensure the directory exists."""
        if not path.exists():
            raise ValueError(f"Directory {path} does not exist")
        elif not path.is_dir():
            raise ValueError(f"Path {path} exists but is not a directory")
        return path

    @staticmethod
    def file_exists_validator(path: Path) -> Path:
        """Ensure the file exists."""
        if not path.exists() or not path.is_file():
            raise ValueError(f"File {path} does not exist or is not a file")
        return path

    @staticmethod
    def coerce_to_list(v: T | list[T]) -> list[T]:
        """Coerce a single instance of T or a list of T into a list of T."""
        return v if isinstance(v, list) else [v]
