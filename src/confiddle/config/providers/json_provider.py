from pathlib import Path
from typing import Optional, TypeVar

from confiddle.config.models.providers.json_provider_config import (
    ENVIRONMENT_PLACEHOLDER,
    JsonProviderConfig,
)
from confiddle.config.providers.base_provider import BaseProvider
from confiddle.utilities.json_loader import JsonLoader

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class JsonProvider(BaseProvider):
    """
    Loads configuration from the base JSON file.

    The environment placeholder is stripped from the filename template, collapsing
    any double period that results (e.g. ``config.{environment}.json`` → ``config.json``).
    The file is optional - missing silently returns {}.
    """

    def __init__(
        self,
        model: type[T],
        config: JsonProviderConfig,
    ):
        super().__init__(model, config)
        filename = config.filename_template.replace(ENVIRONMENT_PLACEHOLDER, "").replace("..", ".")
        path = config.directory_path / filename
        self.file_path: Optional[Path] = path if path.exists() else None

    def _get_raw_config(self) -> dict:
        if self.file_path is None:
            return {}
        return JsonLoader.load_json(self.file_path)
