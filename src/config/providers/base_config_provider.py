from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from helpers.model_validator import ModelValidator

T = TypeVar("T", bound=BaseModel)


class BaseConfigProvider(ABC):

    def __init__(self, model: type[T]):
        self._model = model

    @abstractmethod
    def _get_raw_config(self) -> dict:
        """
        Subclasses implement this to return raw, unfiltered configuration data.
        """
        raise NotImplementedError("Subclasses of BaseConfigProvider must implement the _get_raw_config method.")

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
