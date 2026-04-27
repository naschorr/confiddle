from typing import TypeVar

from confiddle.config.providers.dict_config_provider import DictConfigProvider

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class KwargConfigProvider(DictConfigProvider):
    """
    Loads configuration data from arbitrary kwargs
    """

    def __init__(self, model: type[T], **kwargs):
        super().__init__(model, kwargs)
