from pydantic import ConfigDict

from confiddle.config.models.providers.provider_config_model import BaseProviderConfigModel


class KwargProviderConfig(BaseProviderConfigModel):
    """
    Supplies configuration values as keyword arguments.

    Any extra fields passed at construction time are treated as configuration values.

    Usage::

        KwargProviderConfig(host="localhost", port=8080)
    """

    model_config = ConfigDict(extra="allow")

    @property
    def data(self) -> dict:
        return self.model_extra or {}
