from abc import ABC

from pydantic import BaseModel


class BaseProviderConfigModel(BaseModel, ABC):
    """
    Base class for all provider configuration objects. Used for type hinting
    when provider configs are passed to ``load_config``.
    """
