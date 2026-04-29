from typing import Optional, TypeVar

from pydantic import BaseModel

from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.models.providers.argparse_provider_config import ArgparseProviderConfig
from confiddle.config.models.providers.dict_provider_config import DictProviderConfig
from confiddle.config.models.providers.env_var_provider_config import EnvVarProviderConfig
from confiddle.config.models.providers.json_provider_config import JsonProviderConfig
from confiddle.config.models.providers.base_provider_config import BaseProviderConfig
from confiddle.config.providers.argparse_provider import ArgparseProvider
from confiddle.config.providers.base_provider import BaseProvider
from confiddle.config.providers.dict_provider import DictProvider
from confiddle.config.providers.env_var_provider import EnvVarProvider
from confiddle.config.providers.json_provider import JsonProvider

T = TypeVar("T", bound=BaseModel)


class ProviderFactory:
    """
    Factory class to create config providers based on the provided configuration.
    """

    def build_provider(
        self,
        model: type[T],
        provider_config: BaseProviderConfig,
        *,
        environment: Optional[ConfigEnvironment] = None,
    ) -> BaseProvider:
        if isinstance(provider_config, ArgparseProviderConfig):
            return ArgparseProvider(model, provider_config)
        elif isinstance(provider_config, EnvVarProviderConfig):
            return EnvVarProvider(model, provider_config)
        elif isinstance(provider_config, DictProviderConfig):
            return DictProvider(model, provider_config)
        elif isinstance(provider_config, JsonProviderConfig):
            return JsonProvider(model, provider_config, environment=environment)
        else:
            raise ValueError(f"Unsupported provider config type: {type(provider_config)}")
