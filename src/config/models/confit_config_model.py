from pathlib import Path
from typing import Annotated, Optional

from pydantic import AfterValidator, BaseModel, Field, field_validator

from config.enums.config_environment import ConfigEnvironment
from config.enums.config_flavor import ConfigFlavor
from helpers.field_validator import FieldValidator


_DEFAULT_CONFIG_ENVIRONMENT = ConfigEnvironment.DEV
_DEFAULT_CONFIG_HIERARCHY = [
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

    confit_env_var_prefix: str = Field(
        description="The prefix to use for environment variables when loading Confit's configuration from the environment.",
        default="CONFIT",
        examples=["CONFIT"],
    )

    config_env_var_prefix: Optional[str] = Field(
        description="The prefix to use for environment variables when loading the application's configuration from the environment. All environment variables that aren't prefixed by this will be ignored.",
        default=None,
        examples=["MY_APP"],
    )

    env_var_delimiter: str = Field(
        description="The delimiter to use when parsing environment variables into nested configuration values. For example, with a delimiter of ':', the environment variable 'DATABASE:HOST' would be parsed into the configuration value 'database.host'.",
        default=":",
        examples=[":", "__"],
    )

    environment: ConfigEnvironment = Field(
        description="The environment in which the application to be configured is running.",
        default=_DEFAULT_CONFIG_ENVIRONMENT,
        examples=[_DEFAULT_CONFIG_ENVIRONMENT],
    )

    config_hierarchy: list[ConfigFlavor | ConfigEnvironment] = Field(
        description="The order in which to apply configurations. Configurations will be applied in the order they are listed, with later configurations overwriting earlier ones.",
        default_factory=lambda: list(_DEFAULT_CONFIG_HIERARCHY),
        examples=[_DEFAULT_CONFIG_HIERARCHY],
    )

    @field_validator("config_hierarchy", mode="before")
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

    ## TODO: Validator to warn of mixed environments in the config_hierarchy? It could be unsafe to mix test/dev/prod environments together

    config_directory: Optional[Annotated[Path, AfterValidator(FieldValidator.directory_exists_validator)]] = Field(
        description="The directory to search for configuration files. If not provided, configuration files will be ignored.",
        default=None,
    )

    config_filename_template: str = Field(
        description="The template for configuration file names. Optionally includes {environment} as a placeholder for the environment name.",
        default="config.{environment}.json",
    )

    ## TODO: Validate shape of filename template
