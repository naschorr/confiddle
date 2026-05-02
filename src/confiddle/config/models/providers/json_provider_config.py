from pathlib import Path
from typing import Annotated, Optional

from pydantic import Field, AfterValidator

from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.models.providers.base_provider_config import BaseProviderConfig
from confiddle.helpers.field_validator import FieldValidator

ENVIRONMENT_PLACEHOLDER = "{environment}"
_DEFAULT_FILENAME_TEMPLATE = f"config.{ENVIRONMENT_PLACEHOLDER}.json"


class JsonProviderConfig(BaseProviderConfig):
    """
    Model for configuring the JSON configuration provider.
    """

    directory_path: Annotated[
        Path,
        AfterValidator(FieldValidator.directory_exists_validator),
    ] = Field(
        description="The directory to search for configuration files (relative to the current working directory). If not provided, configuration files will be ignored.",
    )

    filename_template: str = Field(
        description=f"The template for configuration file names. Optionally includes {ENVIRONMENT_PLACEHOLDER} as a placeholder for the environment name. If no {ENVIRONMENT_PLACEHOLDER} placeholder is included, the same file will be used for all environments.",
        default=_DEFAULT_FILENAME_TEMPLATE,
    )

    ## TODO: Validate shape of filename template?

    environment: Optional[ConfigEnvironment] = Field(
        description="The environment to substitute into the filename template. If None, the environment placeholder is stripped from the template.",
        default=None,
    )

    @property
    def config_flavor(self) -> ConfigFlavor:
        return ConfigFlavor.JSON_ENV if self.environment is not None else ConfigFlavor.JSON
