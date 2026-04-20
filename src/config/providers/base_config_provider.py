from abc import ABC, abstractmethod


class BaseConfigProvider(ABC):

    @abstractmethod
    def get_config(self) -> dict:
        """Method to retrieve the config as a dictionary."""
        pass
