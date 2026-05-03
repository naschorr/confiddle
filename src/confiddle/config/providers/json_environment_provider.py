from pathlib import Path
from typing import Optional, TypeVar

from pydantic import BaseModel

from confiddle.config.models.providers.json_provider_config import JsonProviderConfig
from confiddle.config.providers.json_provider import JsonProvider

T = TypeVar("T", bound=BaseModel)


class JsonEnvironmentProvider(JsonProvider):
    """
    Loads configuration from the environment-specific JSON file.

    The environment value is substituted into the filename template
    (e.g. ``config.{environment}.json`` + ``DEV`` → ``config.dev.json``).
    The file is optional - missing silently returns {}.

    ``provider_family()`` resolves to ``JsonProvider`` via MRO, so this provider
    is grouped with its base counterpart for unresolved-data warnings.
    """

    def __init__(
        self,
        model: type[T],
        config: JsonProviderConfig,
    ):
        super().__init__(model, config)

        if config.environment is None:
            raise ValueError("JsonEnvironmentProvider requires an environment to be specified in the config.")

        filename = config.filename_template.format(environment=config.environment.value)
        path = config.directory_path / filename

        self.file_path: Optional[Path] = path if path.exists() else None
