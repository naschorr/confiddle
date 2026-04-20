from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class Confit:

    ## Lifecycle

    def __init__(self, config_model: type[T]):
        self._config_model = config_model

    ## Properties

    @property
    def config_model(self) -> T:
        return self._config_model
