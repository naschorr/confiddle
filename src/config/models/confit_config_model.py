from pydantic import BaseModel, Field, field_validator

from config.enums.config_environment import ConfigEnvironment
from config.enums.config_flavor import ConfigFlavor
from config.models.provider_config_model import ProviderConfigModel
from config.models.providers.env_var_config_provider_config_model import EnvVarConfigProviderConfigModel
from config.models.providers.json_config_provider_config_model import JsonConfigProviderConfigModel


_DEFAULT_CONFIG_ENVIRONMENT = ConfigEnvironment.DEV
_DEFAULT_HIERARCHY = [
    ConfigFlavor.BASE,
    _DEFAULT_CONFIG_ENVIRONMENT,
    ConfigFlavor.ENV,
    ConfigFlavor.ARGPARSE,
    ConfigFlavor.KWARG,
]


class ConfitConfigModel(BaseModel):
    """
    Base model for configuring Confit
    """

    bootstrap: ProviderConfigModel = Field(
        description="Configuration for the Confit bootstrapper, which sets up the configuration providers and their settings so that Confit can run.",
        default_factory=lambda: ProviderConfigModel(
            json_file=JsonConfigProviderConfigModel(filename_template="confit.json"),
            env_var=EnvVarConfigProviderConfigModel(prefix="CONFIT"),
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
