from pydantic import BaseModel, Field

from confiddle.config.models.providers.env_var_provider_config import EnvVarProviderConfig
from confiddle.config.models.providers.json_provider_config import JsonProviderConfig


class BootstrapConfigModel(BaseModel):
    """
    Model for configuring configuration providers.
    """

    env_var: EnvVarProviderConfig = Field(
        description="Configuration for the environment variable configuration provider.",
        default_factory=EnvVarProviderConfig,
    )

    json_file: JsonProviderConfig = Field(
        description="Configuration for the JSON file configuration provider.",
        default_factory=JsonProviderConfig,
    )
