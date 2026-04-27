from pydantic import BaseModel, Field

from confiddle.config.models.providers.env_var_config_provider_config_model import EnvVarConfigProviderConfigModel
from confiddle.config.models.providers.json_config_provider_config_model import JsonConfigProviderConfigModel


class BootstrapConfigModel(BaseModel):
    """
    Model for configuring configuration providers.
    """

    env_var: EnvVarConfigProviderConfigModel = Field(
        description="Configuration for the environment variable configuration provider.",
        default_factory=EnvVarConfigProviderConfigModel,
    )

    json_file: JsonConfigProviderConfigModel = Field(
        description="Configuration for the JSON file configuration provider.",
        default_factory=JsonConfigProviderConfigModel,
    )
