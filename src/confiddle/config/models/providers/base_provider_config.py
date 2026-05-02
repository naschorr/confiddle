from abc import ABC, abstractmethod

from pydantic import BaseModel

from confiddle.config.enums.config_flavor import ConfigFlavor


class BaseProviderConfig(BaseModel, ABC):
    """
    Base class for all provider configuration objects.
    """

    @property
    @abstractmethod
    def config_flavor(self) -> ConfigFlavor:
        pass
