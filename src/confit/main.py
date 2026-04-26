from typing import Optional, TypeVar

from pydantic import BaseModel

from confit.config.config_manager import ConfigManager
from confit.config.enums.config_flavor import ConfigFlavor
from confit.config.models.confit_config_model import ConfitConfigModel

T = TypeVar("T", bound=BaseModel)


class Confit:

    ## Lifecycle

    def __init__(self, confit_config: Optional[ConfitConfigModel] = None):
        config_manager = ConfigManager()

        ## Two pass generation of ConfitConfigModel
        ## 1: Load available configuration from low context providers (ex: env vars and kwargs) to bootstrap
        ##    ConfitConfigModel with basic configuration data
        ## 2: Load available configuration again, but now with all possible providers available (assuming configuration
        ##    data was found in the first pass).

        ## TODO: Skip second pass if we're in a bad state after the first pass.
        partial = config_manager.get_config(ConfitConfigModel, base_data=dict(confit_config) if confit_config else None)
        config_manager.confit_config = partial

        final = config_manager.get_config(ConfitConfigModel, base_data=dict(partial))
        config_manager.confit_config = final

        self._config_manager = config_manager

    ## Methods

    def load_config(self, config_model: type[T], *, provider_data: dict[ConfigFlavor, dict] = {}) -> T:
        return self._config_manager.get_config(config_model, provider_data=provider_data)
