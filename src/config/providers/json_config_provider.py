from pathlib import Path
from typing import TypeVar

from config.enums.config_environment import ConfigEnvironment
from config.providers.base_config_provider import BaseConfigProvider
from helpers.model_validator import ModelValidator
from utilities.json_loader import JsonLoader

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class JsonConfigProvider(BaseConfigProvider):
    """
    Loads configuration data from JSON files
    """

    def __init__(
        self,
        model: type[T],
        environment: ConfigEnvironment,
        config_directory_path: Path,
        config_filename_template: str,
    ):
        self._model = model
        self._environment = environment
        self._config_directory_path = config_directory_path
        self._config_filename_template = config_filename_template

    def get_config(self) -> dict:
        ## Build the path to the config file
        assert (
            self._config_directory_path.exists()
        ), f"Config directory path '{self._config_directory_path}' does not exist"

        config_file_name = self._config_filename_template.format(environment=self._environment.value)
        config_file_path = self._config_directory_path / config_file_name

        assert config_file_path.exists(), f"Config file path '{config_file_path}' does not exist"

        ## Load and validate the JSON from the config file
        data = JsonLoader.load_json(config_file_path)
        ModelValidator.validate_partial_model(self._model, data)

        return data
