from typing import Optional, TypeVar

from pydantic import BaseModel

from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.models.providers.argparse_config_provider_config_model import ArgparseProviderConfig
from confiddle.config.models.providers.dict_config_provider_config_model import DictProviderConfig
from confiddle.config.models.providers.env_var_config_provider_config_model import EnvVarConfigProviderConfigModel
from confiddle.config.models.providers.json_config_provider_config_model import JsonConfigProviderConfigModel
from confiddle.config.models.providers.kwarg_config_provider_config_model import KwargProviderConfig
from confiddle.config.models.providers.base_provider_config_model import BaseProviderConfigModel
from confiddle.config.providers.argparse_config_provider import ArgparseConfigProvider
from confiddle.config.providers.base_config_provider import BaseConfigProvider
from confiddle.config.providers.dict_config_provider import DictConfigProvider
from confiddle.config.providers.env_var_config_provider import EnvVarConfigProvider
from confiddle.config.providers.json_config_provider import JsonConfigProvider
from confiddle.config.providers.kwarg_config_provider import KwargConfigProvider

T = TypeVar("T", bound=BaseModel)


class ConfigProviderFactory:
    """
    Factory class to create config providers based on the provided configuration.
    """

    def build_provider(
        self,
        model: type[T],
        provider_config: BaseProviderConfigModel,
        *,
        environment: Optional[ConfigEnvironment] = None,
    ) -> BaseConfigProvider:
        if isinstance(provider_config, ArgparseProviderConfig):
            return ArgparseConfigProvider(model, provider_config)
        elif isinstance(provider_config, EnvVarConfigProviderConfigModel):
            return EnvVarConfigProvider(model, provider_config)
        elif isinstance(provider_config, DictProviderConfig):
            return DictConfigProvider(model, provider_config)
        elif isinstance(provider_config, JsonConfigProviderConfigModel):
            return JsonConfigProvider(model, provider_config, environment=environment)
        elif isinstance(provider_config, KwargProviderConfig):
            return KwargConfigProvider(model, provider_config)
        else:
            raise ValueError(f"Unsupported provider config type: {type(provider_config)}")
