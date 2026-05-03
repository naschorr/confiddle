from typing import TypeVar

from pydantic import BaseModel

from confiddle.config.models.providers.click_provider_config import ClickProviderConfig
from confiddle.config.models.providers.dict_provider_config import DictProviderConfig
from confiddle.config.providers.dict_provider import DictProvider

T = TypeVar("T", bound=BaseModel)


class ClickProvider(DictProvider):
    """
    Loads configuration data from Click-parsed arguments.

    None values are stripped - Click uses None as the sentinel for options the user
    did not supply, mirroring the behaviour of ArgparseProvider.
    """

    def __init__(self, model: type[T], config: ClickProviderConfig):
        args = {k: v for k, v in config.args.items() if v is not None}
        super().__init__(model, DictProviderConfig(data=args, scope=config.scope))
