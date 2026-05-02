from pydantic import BaseModel, Field

from confiddle.config.models.providers.argparse_provider_config import ArgparseProviderConfig
from confiddle.config.models.providers.dict_provider_config import DictProviderConfig
from confiddle.config.models.providers.env_var_provider_config import EnvVarProviderConfig
from confiddle.config.models.providers.json_provider_config import JsonProviderConfig


class ProviderConfigModel(BaseModel):
    """
    Model for configuring configuration providers.
    """

    argparse_provider: list[ArgparseProviderConfig] = Field(
        description="Configuration for the argparse provider.",
        default_factory=list,
    )

    dict_provider: list[DictProviderConfig] = Field(
        description="Configuration for the dict provider.",
        default_factory=list,
    )

    env_var_provider: list[EnvVarProviderConfig] = Field(
        description="Configuration for the environment variable provider.",
        default_factory=list,
    )

    json_file_provider: list[JsonProviderConfig] = Field(
        description="Configuration for the JSON file provider.",
        default_factory=list,
    )
