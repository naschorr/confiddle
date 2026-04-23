from pathlib import Path
from typing import TypeVar

from config.enums.config_environment import ConfigEnvironment
from config.enums.config_flavor import ConfigFlavor
from config.providers.base_config_provider import BaseConfigProvider
from utilities.json_loader import JsonLoader

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class JsonConfigProvider(BaseConfigProvider):
    """
    Loads configuration data from a JSON file
    """

    def __init__(
        self,
        model: type[T],
        *,
        directory_path: Path,
        filename_template: str,
        environment: ConfigFlavor | ConfigEnvironment,
    ):
        super().__init__(model)

        ## TODO: If config_key == ConfigFlavor.BASE, we should also handle the config.json case in addition to config.base.json
        self._file_path = directory_path / filename_template.format(environment=environment.value)

    @property
    def file_path(self) -> Path:
        return self._file_path

    def _get_raw_config(self) -> dict:
        if not self._file_path.exists():
            raise FileNotFoundError(f"Config file path '{self._file_path}' does not exist")

        return JsonLoader.load_json(self._file_path)
