from __future__ import annotations

from typing import TypeVar

from confiddle.config.enums.merge_strategy import MergeStrategy
from confiddle.config.models.providers.dict_provider_config import DictProviderConfig
from confiddle.config.providers.base_provider import BaseProvider

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class DictProvider(BaseProvider):
    """
    Loads configuration data from a dictionary, optionally nested at a dot-separated scope path.

    When ``scope`` is provided (e.g. ``"database.credentials"``), the data is wrapped at that
    location in the config tree and merged deeply so that sibling keys at the same level are
    preserved. Without a scope the merge is shallow.
    """

    def __init__(self, model: type[T], config: DictProviderConfig):
        super().__init__(model, config)
        if config.scope:
            wrapped = config.data
            for key in reversed(config.scope.split(".")):
                wrapped = {key: wrapped}

            self._config_dict = wrapped
            self._merge_strategy = MergeStrategy.DEEP
        else:
            self._config_dict = config.data
            self._merge_strategy = MergeStrategy.SHALLOW

    @property
    def merge_strategy(self) -> MergeStrategy:
        return self._merge_strategy

    def _get_raw_config(self) -> dict:
        return self._config_dict
