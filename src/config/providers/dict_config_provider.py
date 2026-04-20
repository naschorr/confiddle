from typing import TypeVar

from config.providers.base_config_provider import BaseConfigProvider
from helpers.model_validator import ModelValidator

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class DictConfigProvider(BaseConfigProvider):
    """
    Loads configuration data from a dictionary.
    """

    def __init__(self, model: type[T], config_dict: dict):
        self._model = model
        self._config_dict = config_dict

    def get_config(self) -> dict:
        ## Validate the config dict against the partial model
        ModelValidator.validate_partial_model(self._model, self._config_dict)

        return self._config_dict
