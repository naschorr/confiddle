import os
from typing import Optional, TypeVar

from confiddle.config.providers.base_config_provider import BaseConfigProvider
from confiddle.helpers.field_annotation_helper import get_field_annotation, is_container_annotation, unwrap_annotation

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class EnvVarConfigProvider(BaseConfigProvider):
    """
    Loads configuration data from environment variables into a dictionary structure that matches the provided model.
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

            # Split into parts, lowercased to match Pydantic field names
            parts = [part.lower() for part in env_var.split(self._delimiter)]

            self._set_nested(config_dict, parts, value, self._model)

        return config_dict

    def _set_nested(self, target: dict, parts: list[str], value: str, model) -> None:
        key = parts[0]
        annotation = get_field_annotation(model, key)

        # For unknown fields (annotation is None), be permissive: allow both flat and nested paths.
        # For known fields, use the schema to decide whether to assign a flat value or descend.
        known_container = annotation is not None and is_container_annotation(annotation)
        known_primitive = annotation is not None and not is_container_annotation(annotation)

        if len(parts) == 1:
            # Leaf: only assign if the field is not a known container type
            if not known_container:
                target[key] = value
            return

        # Multi-part path: skip descent if the field is a known primitive
        if known_primitive:
            return

        if key not in target or not isinstance(target[key], dict):
            target[key] = {}

        # Determine the child model for schema lookups at the next level
        unwrapped = unwrap_annotation(annotation) if annotation is not None else None
        child_model = (
            unwrapped
            if unwrapped is not None and isinstance(unwrapped, type) and issubclass(unwrapped, BaseModel)
            else None
        )
        self._set_nested(target[key], parts[1:], value, child_model)
