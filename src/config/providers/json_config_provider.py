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

        primary = directory_path / filename_template.format(environment=environment.value)

        ## For ConfigFlavor.BASE with a template that contains {environment}, also resolve a plain fallback (e.g.
        ## "config.json") so a bare config file works without renaming.
        if environment is ConfigFlavor.BASE and "{environment}" in filename_template:
            fallback = directory_path / filename_template.replace("{environment}", "").replace("..", ".")
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
