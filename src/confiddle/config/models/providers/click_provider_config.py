from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BeforeValidator, Field

from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.models.providers.base_provider_config import BaseProviderConfig
from confiddle.helpers.field_validator import FieldValidator


class ClickProviderConfig(BaseProviderConfig):
    """
    Supplies configuration values from Click-parsed arguments.

    Accepts either a plain dict (e.g. the ``**kwargs`` received by a Click command function)
    or a ``click.Context`` object - confiddle duck-types ``.params`` off the context so
    that Click is not a required dependency.

    Usage::

        # From a command function's kwargs:
        @click.command()
        @click.option("--host", default="localhost")
        def cli(**kwargs):
            confiddle.load_config(MyModel, provider_configs=[ClickProviderConfig(args=kwargs)])

        # From a context object:
        @click.command()
        @click.pass_context
        def cli(ctx):
            confiddle.load_config(MyModel, provider_configs=[ClickProviderConfig(args=ctx)])
    """

    args: Annotated[dict, BeforeValidator(FieldValidator.coerce(dict, transform=lambda v: v.params))] = Field(
        description="Parsed Click kwargs dict, or a click.Context whose .params will be used.",
        default_factory=dict,
    )

    scope: Optional[str] = Field(
        description='Optional dot-separated path at which to nest the data before merging (e.g. "database.credentials"). When set, the provider deep-merges so sibling keys are preserved.',
        default=None,
    )

    @property
    def config_flavor(self) -> ConfigFlavor:
        return ConfigFlavor.CLICK
