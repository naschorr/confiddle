import os
from typing import Optional, TypeVar

from config.providers.base_config_provider import BaseConfigProvider

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class EnvVarConfigProvider(BaseConfigProvider):
    """
    Loads configuration data from environment variables
    """

    def __init__(self, model: type[T], *, prefix: Optional[str], delimiter: str):
        super().__init__(model)

        self._prefix = prefix
        self._delimiter = delimiter

    def _get_raw_config(self) -> dict:
        ## Filter environment variables by prefix if a prefix is specified
        env_vars = dict(os.environ)
        if self._prefix:
            env_vars = {
                k: v for k, v in env_vars.items() if k == self._prefix or k.startswith(self._prefix + self._delimiter)
            }

        ## Parse the environment variables into a nested config dict
        config_dict = {}
        for env_var, value in env_vars.items():
            # Remove the prefix from the environment variable name if a prefix is specified
            if self._prefix:
                env_var = env_var[len(self._prefix) :]

            # Remove any leading delimiter from the environment variable name
            if env_var.startswith(self._delimiter):
                env_var = env_var[len(self._delimiter) :]

            # Split the environment variable name into parts using the delimiter, lowercased to match Pydantic field names
            parts = [part.lower() for part in env_var.split(self._delimiter)]

            # Insert the value into the config dict at the appropriate nested level
            current_level = config_dict
            for part in parts[:-1]:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
            current_level[parts[-1]] = value

        return config_dict
