import argparse
from typing import TypeVar, Union

from confiddle.config.providers.dict_config_provider import DictConfigProvider

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class ArgparseConfigProvider(DictConfigProvider):
    """
    Loads configuration data from processed argparse args.
    """

    def __init__(self, model: type[T], argparse_args: Union[argparse.Namespace, dict]):
        ## Convert Namespace to dict if needed for maximum flexibility
        if isinstance(argparse_args, argparse.Namespace):
            argparse_args = vars(argparse_args)

        ## Strip None values, argparse uses None as the sentinel for "not provided"
        argparse_args = {k: v for k, v in argparse_args.items() if v is not None}

        super().__init__(model, argparse_args)
