from pathlib import Path
from typing import Optional, Annotated

from pydantic import BaseModel, Field, AfterValidator

from helpers.field_validator import FieldValidator


class JsonConfigProviderConfigModel(BaseModel):
    """
    Model for configuring the JSON configuration provider.
    """

    directory_path: Optional[Annotated[Path, AfterValidator(FieldValidator.directory_exists_validator)]] = Field(
        description="The directory to search for configuration files (relative to the current working directory). If not provided, configuration files will be ignored.",
        default=None,
    )

    filename_template: str = Field(
        description="The template for configuration file names. Optionally includes {environment} as a placeholder for the environment name. If no {environment} placeholder is included, the same file will be used for all environments.",
        default="config.{environment}.json",
    )

    ## TODO: Validate shape of filename template?
