from pathlib import Path
from typing import TypeVar

from config.providers.base_config_provider import BaseConfigProvider
from helpers.model_validator import ModelValidator
from utilities.json_loader import JsonLoader

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class JsonConfigProvider(BaseConfigProvider):
    """
    Loads configuration data from a JSON file
    """

    def __init__(self, model: type[T], config_file_path: Path):
        self._model = model
        self._config_file_path = config_file_path

    def get_config(self) -> dict:
        assert self._config_file_path.exists(), f"Config file path '{self._config_file_path}' does not exist"

        data = JsonLoader.load_json(self._config_file_path)
        ModelValidator.validate_partial_model(self._model, data)

        return data
