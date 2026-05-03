from abc import ABC, abstractmethod
from typing import Optional, TypeVar

from pydantic import BaseModel

from confiddle.config.enums.merge_strategy import MergeStrategy
from confiddle.config.models.providers.base_provider_config import BaseProviderConfig
from confiddle.helpers.model_validator import ModelValidator

T = TypeVar("T", bound=BaseModel)


class BaseProvider(ABC):

    def __init__(self, model: type[T], config: Optional[BaseProviderConfig] = None):
        self._model = model
        self._provider_config = config

    @classmethod
    def provider_family(cls) -> type:
        """Returns the root concrete provider type for this class.
        Used to group related providers (e.g. JsonProvider and JsonEnvironmentProvider)
        for warning purposes. Walks the MRO to find the nearest ancestor that is a
        direct subclass of BaseProvider."""
        for parent in cls.__mro__[1:]:
            if issubclass(parent, BaseProvider) and parent is not BaseProvider:
                return parent
        return cls

    @property
    def merge_strategy(self) -> MergeStrategy:
        return MergeStrategy.SHALLOW

    @abstractmethod
    def _get_raw_config(self) -> dict:
        """
        Subclasses implement this to return raw, unfiltered configuration data.
        """
        raise NotImplementedError("Subclasses of BaseProvider must implement the _get_raw_config method.")

    def get_config(self) -> dict:
        """
        Returns configuration data filtered to model fields and validated. Not overrideable.
        """
        return self._build_result(self._get_raw_config())

    def _build_result(self, data: dict) -> dict:
        """
        Filter to model fields then validate. Called automatically, subclasses should not call this directly.
        """
        filtered = {k: v for k, v in data.items() if k in self._model.model_fields}
        ModelValidator.validate_partial_model(self._model, filtered)
        return filtered
