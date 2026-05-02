from typing import Optional

from pydantic import Field

from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.models.providers.base_provider_config import BaseProviderConfig

_DEFAULT_ENV_VAR_DELIMITER = ":"
_EXAMPLE_ENV_VAR_DELIMITERS = [":", "__"]


class EnvVarProviderConfig(BaseProviderConfig):
    """
    Model for configuring the environment variable configuration provider.
    """

    prefix: Optional[str] = Field(
        description="The prefix to use for that all environment variables must have in order to be loaded into the configuration model. Note that this prefix is consumed, so the rest of the environment variable after the prefix is what will be attempted to be loaded into the configuration model.",
        default=None,
    )

    delimiter: str = Field(
        description="The delimiter to use when parsing environment variables into nested configuration values. For example, with a delimiter of ':', an environment variable of 'MY_APP:DATABASE:HOST=localhost' would be parsed into {'database': {'host': 'localhost'}} (assuming a prefix of 'MY_APP').",
        default=_DEFAULT_ENV_VAR_DELIMITER,
        examples=_EXAMPLE_ENV_VAR_DELIMITERS,
    )

    @property
    def config_flavor(self) -> ConfigFlavor:
        return ConfigFlavor.ENV_VAR
