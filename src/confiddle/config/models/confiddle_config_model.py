from pydantic import BaseModel, Field, field_validator

from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.models.bootstrap_config_model import BootstrapConfigModel
from confiddle.config.models.providers.env_var_config_provider_config_model import EnvVarConfigProviderConfigModel
from confiddle.config.models.providers.json_config_provider_config_model import JsonConfigProviderConfigModel


_DEFAULT_CONFIG_ENVIRONMENT = ConfigEnvironment.DEV
_DEFAULT_HIERARCHY = [
    ConfigFlavor.JSON,
    _DEFAULT_CONFIG_ENVIRONMENT,
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
            json_file=JsonConfigProviderConfigModel(filename_template="confiddle.json"),
            env_var=EnvVarConfigProviderConfigModel(prefix="CONFIDDLE"),
        ),
    )

    env_var: EnvVarConfigProviderConfigModel = Field(
        description="Configuration for the environment variable provider for the application being configured.",
        default_factory=EnvVarConfigProviderConfigModel,
    )

    json_file: JsonConfigProviderConfigModel = Field(
        description="Configuration for the JSON file provider for the application being configured.",
        default_factory=JsonConfigProviderConfigModel,
    )

    environment: ConfigEnvironment = Field(
        description="The environment in which the application to be configured is running.",
        default=_DEFAULT_CONFIG_ENVIRONMENT,
        examples=[_DEFAULT_CONFIG_ENVIRONMENT],
    )

    hierarchy: list[ConfigFlavor | ConfigEnvironment] = Field(
        description="The order in which to apply configurations. Configurations will be applied in the order they are listed, with later configurations overwriting earlier ones.",
        default_factory=lambda: list(_DEFAULT_HIERARCHY),
        examples=[_DEFAULT_HIERARCHY],
    )

    @field_validator("hierarchy", mode="before")
    @classmethod
    def _coerce_hierarchy_values(cls, values: list) -> list:
        result = []
        for value in values:
            if isinstance(value, (ConfigFlavor, ConfigEnvironment)):
                result.append(value)
                continue
            for enum_cls in (ConfigFlavor, ConfigEnvironment):
                try:
                    result.append(enum_cls(value))
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"'{value}' is not a valid ConfigFlavor or ConfigEnvironment value")
        return result

    ## TODO: Validator to warn of mixed environments in the hierarchy? It could be unsafe to mix test/dev/prod environments together
