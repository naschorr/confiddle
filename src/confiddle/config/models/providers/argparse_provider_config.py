from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BeforeValidator, Field

from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.models.providers.base_provider_config import BaseProviderConfig
from confiddle.helpers.field_validator import FieldValidator


class ArgparseProviderConfig(BaseProviderConfig):
    """
    Supplies configuration values from argparse-parsed arguments.

    Usage:

        ArgparseProviderConfig(args=namespace_or_dict)
    """

    args: Annotated[dict, BeforeValidator(FieldValidator.coerce(dict, transform=vars))] = Field(
        description="Parsed argparse Namespace or equivalent dict to load configuration values from.",
        default_factory=dict,
    )

    scope: Optional[str] = Field(
        description='Optional dot-separated path at which to nest the data before merging (e.g. "database.credentials"). When set, the provider deep-merges so sibling keys are preserved.',
        default=None,
    )

    @property
    def config_flavor(self) -> ConfigFlavor:
        return ConfigFlavor.ARGPARSE
