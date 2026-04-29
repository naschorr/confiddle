from pathlib import Path
from typing import TypeVar

from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.models.providers.json_config_provider_config_model import (
    ENVIRONMENT_PLACEHOLDER,
    JsonConfigProviderConfigModel,
)
from confiddle.config.providers.base_config_provider import BaseConfigProvider
from confiddle.utilities.json_loader import JsonLoader

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class JsonConfigProvider(BaseConfigProvider):
    """
    Loads configuration data from a JSON file
    """

    def __init__(
        self,
        model: type[T],
        config: JsonConfigProviderConfigModel,
        *,
        environment: ConfigFlavor | ConfigEnvironment,
    ):
        if config.directory_path is None:
            raise ValueError("JsonConfigProvider requires a directory_path in its config")

        super().__init__(model)

        primary = config.directory_path / config.filename_template.format(environment=environment.value)

        ## For ConfigFlavor.JSON with a template that contains {environment}, also resolve a plain fallback (e.g.
        ## "config.json") so a bare config file works without renaming.
        if environment is ConfigFlavor.JSON and ENVIRONMENT_PLACEHOLDER in config.filename_template:
            fallback = config.directory_path / config.filename_template.replace(ENVIRONMENT_PLACEHOLDER, "").replace(
                "..", "."
            )
            self._file_path = primary
            self._fallback_path: Path | None = fallback
        else:
            self._file_path = primary
            self._fallback_path = None

    @property
    def file_path(self) -> Path:
        if self._fallback_path is not None and not self._file_path.exists() and self._fallback_path.exists():
            return self._fallback_path
        return self._file_path

    def _get_raw_config(self) -> dict:
        if not self.file_path.exists():
            raise FileNotFoundError(f"Config file path '{self.file_path}' does not exist")

        return JsonLoader.load_json(self.file_path)
