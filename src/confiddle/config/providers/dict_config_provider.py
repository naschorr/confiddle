from __future__ import annotations

from typing import TypeVar

from confiddle.config.enums.merge_strategy import MergeStrategy
from confiddle.config.providers.base_config_provider import BaseConfigProvider

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class DictConfigProvider(BaseConfigProvider):
    """
    Loads configuration data from a dictionary, optionally nested at a dot-separated scope path.

    When ``scope`` is provided (e.g. ``"database.credentials"``), the data is wrapped at that
    location in the config tree and merged deeply so that sibling keys at the same level are
    preserved. Without a scope the merge is shallow.
    """

    def __init__(self, model: type[T], config_dict: dict, *, scope: str | None = None):
        super().__init__(model)
        if scope:
            wrapped = config_dict
            for key in reversed(scope.split(".")):
                wrapped = {key: wrapped}

            self._config_dict = wrapped
            self._merge_strategy = MergeStrategy.DEEP
        else:
            self._config_dict = config_dict
            self._merge_strategy = MergeStrategy.SHALLOW

    @property
    def merge_strategy(self) -> MergeStrategy:
        return self._merge_strategy

    def _get_raw_config(self) -> dict:
        return self._config_dict
