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
    Loads configuration data from a JSON file
    """

    def __init__(
        self,
        model: type[T],
        config: JsonProviderConfig,
    ):
        super().__init__(model)

        environment = config.environment
        if environment is None:
            filename = config.filename_template.replace(f".{ENVIRONMENT_PLACEHOLDER}", "").replace(
                f"{ENVIRONMENT_PLACEHOLDER}.", ""
            )
        else:
            filename = config.filename_template.format(environment=environment.value)

        file_path = config.directory_path / filename
        if not file_path.exists():
            if environment is not None:
                # env-specific file is optional, act as a no-op provider
                self.file_path = None
            else:
                raise FileNotFoundError(f"JSON config file '{file_path}' does not exist")
        else:
            self.file_path = file_path

    def _get_raw_config(self) -> dict:
        if self.file_path is None:
            return {}

        return JsonLoader.load_json(self.file_path)
