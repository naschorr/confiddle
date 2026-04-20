from typing import TypeVar
from pathlib import Path

from pydantic import BaseModel

from config.models.confit_config_model import ConfitConfigModel

T = TypeVar("T", bound=BaseModel)


class ConfigManager:

    ## Lifecycle

    def __init__(self, config_model: type[T]):
        self._config_model = config_model

    ## Methods
