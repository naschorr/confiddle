from pathlib import Path
from typing import Any, Callable, TypeVar

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
    def coerce(target_type: type, *, transform: Callable[[Any], Any] | None = None) -> Callable[[Any], Any]:
        """Return a BeforeValidator-compatible coercion function.

        If *value* is already an instance of *target_type* it is returned unchanged.
        Otherwise *transform* is called if provided, else ``target_type(value)`` is tried.
        """

        def _coerce(value: Any) -> Any:
            if isinstance(value, target_type):
                return value
            try:
                if transform is not None:
                    return transform(value)
                return target_type(value)
            except (TypeError, AttributeError) as exc:
                raise ValueError(str(exc)) from exc

        return _coerce
