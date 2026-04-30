from pydantic import BaseModel, Field, field_validator

from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.models.bootstrap_config_model import BootstrapConfigModel
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

    bootstrap: BootstrapConfigModel = Field(
        description="Configuration for the Confiddle bootstrapper, which sets up the configuration providers and their settings so that Confiddle can run.",
        default_factory=lambda: BootstrapConfigModel(
            json_file=JsonProviderConfig(filename_template="confiddle.json"),
            env_var=EnvVarProviderConfig(prefix="CONFIDDLE"),
        ),
    )

    env_var: EnvVarProviderConfig = Field(
        description="Configuration for the environment variable provider for the application being configured.",
        default_factory=EnvVarProviderConfig,
    )

    json_file: JsonProviderConfig = Field(
        description="Configuration for the JSON file provider for the application being configured.",
        default_factory=JsonProviderConfig,
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
