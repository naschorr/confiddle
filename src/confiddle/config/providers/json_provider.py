from pathlib import Path
from typing import Optional, TypeVar

from confiddle.config.enums.config_environment import ConfigEnvironment
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
        *,
        environment: Optional[ConfigEnvironment] = None,
    ):
        if config.directory_path is None:
            raise ValueError("JsonProvider requires a directory_path in its config")

        super().__init__(model)

        if environment is None:
            filename = config.filename_template.replace(f".{ENVIRONMENT_PLACEHOLDER}", "").replace(
                f"{ENVIRONMENT_PLACEHOLDER}.", ""
            )
        else:
            filename = config.filename_template.format(environment=environment.value)

        file_path = config.directory_path / filename
        if not file_path.exists():
            raise FileNotFoundError(f"JSON config file '{file_path}' does not exist")

        self.file_path = file_path

    def _get_raw_config(self) -> dict:
        return JsonLoader.load_json(self.file_path)
