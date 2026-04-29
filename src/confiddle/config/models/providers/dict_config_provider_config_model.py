from __future__ import annotations

from typing import Optional

from pydantic import Field

from confiddle.config.models.providers.provider_config_model import BaseProviderConfigModel


class DictProviderConfig(BaseProviderConfigModel):
    """
    Supplies configuration values from a dictionary, optionally nested at a dot-separated scope path.

    When ``scope`` is provided (e.g. ``"database.credentials"``),
    the data is wrapped at that location in the config tree and merged deeply so that sibling keys
    at the same level are preserved. Without a scope the merge is shallow.
    """

    data: dict = Field(description="Configuration values to merge into the configuration.")

    scope: Optional[str] = Field(
        description='Optional dot-separated path at which to nest the data before merging (e.g. "database.credentials"). When set, the provider deep-merges so sibling keys are preserved.',
        default=None,
    )
