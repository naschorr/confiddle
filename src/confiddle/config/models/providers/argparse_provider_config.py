from __future__ import annotations

import argparse

from pydantic import ConfigDict, Field

from confiddle.config.models.providers.base_provider_config import BaseProviderConfig


class ArgparseProviderConfig(BaseProviderConfig):
    """
    Supplies configuration values from argparse-parsed arguments.

    Usage::

        ArgparseProviderConfig(args=namespace_or_dict)
    """

    ## Allow arbitrary types for maximum flexibility in accepting both Namespace and dict
    model_config = ConfigDict(arbitrary_types_allowed=True)

    args: argparse.Namespace | dict = Field(
        description="Parsed argparse Namespace or equivalent dict to load configuration values from.", default={}
    )
