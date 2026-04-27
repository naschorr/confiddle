from typing import Optional, TypeVar, cast

from pydantic import BaseModel

from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.models.confiddle_config_model import ConfiddleConfigModel
from confiddle.config.models.providers.json_config_provider_config_model import JsonConfigProviderConfigModel
from confiddle.config.providers.argparse_config_provider import ArgparseConfigProvider
from confiddle.config.providers.base_config_provider import BaseConfigProvider
from confiddle.config.providers.env_var_config_provider import EnvVarConfigProvider
from confiddle.config.providers.json_config_provider import JsonConfigProvider
from confiddle.config.providers.kwarg_config_provider import KwargConfigProvider

T = TypeVar("T", bound=BaseModel)


class ConfigManager:

    ## Lifecycle

    def __init__(self):
        self._confiddle_config: Optional[ConfiddleConfigModel] = None

    ## Properties

    @property
    def confiddle_config(self) -> Optional[ConfiddleConfigModel]:
        return self._confiddle_config

    @confiddle_config.setter
    def confiddle_config(self, value: ConfiddleConfigModel) -> None:
        self._confiddle_config = value

    ## Methods

    def get_config(
        self,
        model: type[T],
        *,
        provider_data: Optional[dict[ConfigFlavor, dict]] = None,
        base_data: Optional[dict] = None,
    ) -> T:
        if self._confiddle_config is None and model is not ConfiddleConfigModel:
            raise RuntimeError(
                "ConfigManager must be bootstrapped before building a user config model. "
                "Call get_config(ConfiddleConfigModel, ...) first and assign the result to confiddle_config."
            )

        merged = dict(base_data) if base_data else {}
        for provider in self._build_providers(model, provider_data or {}):
            merged |= provider.get_config()

        return cast(T, model(**merged))

    ## Private

    def _build_providers(self, model: type[T], provider_data: dict[ConfigFlavor, dict]) -> list[BaseConfigProvider]:
        confiddle_config = self._confiddle_config or ConfiddleConfigModel()
        providers = []
        for item in confiddle_config.hierarchy:
            provider = self._build_provider(item, model, confiddle_config, provider_data)
            if provider is not None:
                providers.append(provider)

        return providers

    def _build_provider(
        self,
        item: ConfigFlavor | ConfigEnvironment,
        model: type[T],
        confiddle_config: ConfiddleConfigModel,
        provider_data: dict[ConfigFlavor, dict],
    ) -> Optional[BaseConfigProvider]:
        if item is ConfigFlavor.BASE:
            json_config = (
                confiddle_config.bootstrap.json_file if model is ConfiddleConfigModel else confiddle_config.json_file
            )
            return self._build_json_provider(model, ConfigFlavor.BASE, json_config)
        elif isinstance(item, ConfigEnvironment):
            if item is not confiddle_config.environment:
                return None
            json_config = (
                confiddle_config.bootstrap.json_file if model is ConfiddleConfigModel else confiddle_config.json_file
            )
            return self._build_json_provider(model, item, json_config)
        elif item is ConfigFlavor.ENV:
            return self._build_env_provider(model, confiddle_config)
        elif item is ConfigFlavor.ARGPARSE:
            return self._build_argparse_provider(model, provider_data.get(ConfigFlavor.ARGPARSE))
        elif item is ConfigFlavor.KWARG:
            return self._build_kwarg_provider(model, provider_data.get(ConfigFlavor.KWARG))

        return None

    def _build_json_provider(
        self,
        model: type[T],
        config_key: ConfigFlavor | ConfigEnvironment,
        json_config: JsonConfigProviderConfigModel,
    ) -> Optional[JsonConfigProvider]:
        if json_config.directory_path is None:
            return None

        provider = JsonConfigProvider(
            model,
            directory_path=json_config.directory_path,
            filename_template=json_config.filename_template,
            environment=config_key,
        )

        if not provider.file_path.exists():
            return None

        return provider

    def _build_env_provider(
        self,
        model: type[T],
        confiddle_config: ConfiddleConfigModel,
    ) -> EnvVarConfigProvider:
        env_config = confiddle_config.bootstrap.env_var if model is ConfiddleConfigModel else confiddle_config.env_var

        return EnvVarConfigProvider(model, prefix=env_config.prefix, delimiter=env_config.delimiter)

    def _build_argparse_provider(
        self,
        model: type[T],
        data: Optional[dict],
    ) -> Optional[ArgparseConfigProvider]:
        if not data:
            return None

        return ArgparseConfigProvider(model, data)

    def _build_kwarg_provider(
        self,
        model: type[T],
        data: Optional[dict],
    ) -> Optional[KwargConfigProvider]:
        if not data:
            return None

        return KwargConfigProvider(model, **data)
