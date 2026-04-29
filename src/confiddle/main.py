from typing import Optional, TypeVar

from pydantic import BaseModel

from confiddle.config.config_manager import ConfigManager
from confiddle.config.models.confiddle_config_model import ConfiddleConfigModel
from confiddle.config.models.providers.base_provider_config_model import BaseProviderConfigModel

T = TypeVar("T", bound=BaseModel)


class Confiddle:

    ## Lifecycle

    def __init__(self, confiddle_config: Optional[ConfiddleConfigModel] = None):
        config_manager = ConfigManager()

        ## Two pass generation of ConfiddleConfigModel
        ## 1: Load available configuration from low context providers (ex: env vars and kwargs) to bootstrap
        ##    ConfiddleConfigModel with basic configuration data
        ## 2: Load available configuration again, but now with all possible providers available (assuming configuration
        ##    data was found in the first pass).

        ## TODO: Skip second pass if we're in a bad state after the first pass.
        partial = config_manager.get_config(
            ConfiddleConfigModel, base_data=dict(confiddle_config) if confiddle_config else None
        )
        config_manager.confiddle_config = partial

        final = config_manager.get_config(ConfiddleConfigModel, base_data=dict(partial))
        config_manager.confiddle_config = final

        self._config_manager = config_manager

    ## Methods

    def load_config(self, config_model: type[T], *, provider_configs: list[BaseProviderConfigModel] = []) -> T:
        return self._config_manager.get_config(config_model, provider_configs=provider_configs)
