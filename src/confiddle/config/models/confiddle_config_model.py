from pathlib import Path

from pydantic import BaseModel, Field

from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.models.provider_config_model import ProviderConfigModel
from confiddle.config.models.providers.argparse_provider_config import ArgparseProviderConfig
from confiddle.config.models.providers.dict_provider_config import DictProviderConfig
from confiddle.config.models.providers.env_var_provider_config import EnvVarProviderConfig
from confiddle.config.models.providers.json_provider_config import JsonProviderConfig


_DEFAULT_CONFIG_ENVIRONMENT = ConfigEnvironment.DEV
_DEFAULT_HIERARCHY = [
    ConfigFlavor.JSON,
    ConfigFlavor.JSON_ENV,
    ConfigFlavor.ENV_VAR,
    ConfigFlavor.ARGPARSE,
    ConfigFlavor.DICT,
]


class ConfiddleConfigModel(BaseModel):
    """
    Base model for configuring Confiddle
    """

    bootstrap: ProviderConfigModel = Field(
        description="Configuration for the Confiddle bootstrapper, which sets up the configuration providers and their settings so that Confiddle can run.",
        default_factory=lambda: ProviderConfigModel(
            env_var_provider=[EnvVarProviderConfig(prefix="CONFIDDLE")],
            json_file_provider=[JsonProviderConfig(directory_path=Path("."), filename_template="confiddle.json")],
        ),
    )

    app: ProviderConfigModel = Field(
        description="Configuration for the application to be configured, which will be used to configure providers that load configuration for the application.",
        default_factory=ProviderConfigModel,
    )

    environment: ConfigEnvironment = Field(
        description="The environment in which the application to be configured is running.",
        default=_DEFAULT_CONFIG_ENVIRONMENT,
        examples=[_DEFAULT_CONFIG_ENVIRONMENT],
    )

    hierarchy: list[ConfigFlavor] = Field(
        description="The order in which to apply configurations. Configurations will be applied in the order they are listed, with later configurations overwriting earlier ones.",
        default_factory=lambda: list(_DEFAULT_HIERARCHY),
        examples=[_DEFAULT_HIERARCHY],
    )

    ## TODO: Validator to trim `hierarchy` to only include unique items (sets are unordered)
