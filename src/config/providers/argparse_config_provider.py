from typing import TypeVar

from config.providers.dict_config_provider import DictConfigProvider

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class ArgparseConfigProvider(DictConfigProvider):
    """
    Loads configuration data from processed argparse args.
    """

    def __init__(self, model: type[T], argparse_args: dict):
        super().__init__(model, argparse_args)
