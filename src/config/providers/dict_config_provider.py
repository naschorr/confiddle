from typing import TypeVar

from config.providers.base_config_provider import BaseConfigProvider

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class DictConfigProvider(BaseConfigProvider):
    """
    Loads configuration data from a dictionary.
    """

    def __init__(self, model: type[T], config_dict: dict):
        super().__init__(model)
        self._config_dict = config_dict

    def _get_raw_config(self) -> dict:
        return self._config_dict
