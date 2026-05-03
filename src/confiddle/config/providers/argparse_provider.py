from typing import TypeVar

from confiddle.config.models.providers.argparse_provider_config import ArgparseProviderConfig
from confiddle.config.models.providers.dict_provider_config import DictProviderConfig
from confiddle.config.providers.dict_provider import DictProvider

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ArgparseProvider(DictProvider):
    """
    Loads configuration data from processed argparse args.
    """

    def __init__(self, model: type[T], config: ArgparseProviderConfig):
        ## Strip None values - argparse uses None as the sentinel for "not provided"
        args = {k: v for k, v in config.args.items() if v is not None}
        super().__init__(model, DictProviderConfig(data=args, scope=config.scope))
