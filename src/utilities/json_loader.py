import json
from pathlib import Path


class JsonLoader:
    """
    Utility class for loading JSON data from files with consistent error handling.
    """

    @staticmethod
    def load_json(file_path: Path) -> dict:
        """
        Load JSON data from a file with consistent error handling.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to load JSON from {file_path}: {e}")
