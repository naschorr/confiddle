from typing import TypeVar

from confiddle.config.models.providers.dict_config_provider_config_model import DictProviderConfig
from confiddle.config.models.providers.kwarg_config_provider_config_model import KwargProviderConfig
from confiddle.config.providers.dict_config_provider import DictConfigProvider

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class KwargConfigProvider(DictConfigProvider):
    """
    Loads configuration data from arbitrary kwargs
    """

    def __init__(self, model: type[T], config: KwargProviderConfig):
        super().__init__(model, DictProviderConfig(data=config.data))
