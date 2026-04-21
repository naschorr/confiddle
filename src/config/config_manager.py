from typing import Optional, TypeVar, cast

from pydantic import BaseModel

from config.enums.config_environment import ConfigEnvironment
from config.enums.config_flavor import ConfigFlavor
from config.models.confit_config_model import ConfitConfigModel
from config.providers.argparse_config_provider import ArgparseConfigProvider
from config.providers.base_config_provider import BaseConfigProvider
from config.providers.dict_config_provider import DictConfigProvider
from config.providers.env_var_config_provider import EnvVarConfigProvider
from config.providers.json_config_provider import JsonConfigProvider
from config.providers.kwarg_config_provider import KwargConfigProvider

T = TypeVar("T", bound=BaseModel)


class ConfigManager:

    ## Lifecycle

    def __init__(self):
        self._confit_config: Optional[ConfitConfigModel] = None

    ## Properties

    @property
    def confit_config(self) -> Optional[ConfitConfigModel]:
        return self._confit_config

    @confit_config.setter
    def confit_config(self, value: ConfitConfigModel) -> None:
        self._confit_config = value

    ## Methods

    def get_config(
        self,
        model: type[T],
        *,
        provider_data: Optional[dict[ConfigFlavor, dict]] = None,
        base_data: Optional[dict] = None,
    ) -> T:
        if self._confit_config is None and model is not ConfitConfigModel:
            raise RuntimeError(
                "ConfigManager must be bootstrapped before building a user config model. "
                "Call get_config(ConfitConfigModel, ...) first and assign the result to confit_config."
            )

        merged = dict(base_data) if base_data else {}
        for provider in self._build_providers(model, provider_data or {}):
            merged |= provider.get_config()

        return cast(T, model(**merged))

    ## Private

    def _build_providers(self, model: type[T], provider_data: dict[ConfigFlavor, dict]) -> list[BaseConfigProvider]:
        confit_config = self._confit_config or ConfitConfigModel()
        providers = []
        for item in confit_config.config_hierarchy:
            provider = self._build_provider(item, model, confit_config, provider_data)
            if provider is not None:
                providers.append(provider)

        return providers

    def _build_provider(
        self,
        item: ConfigFlavor | ConfigEnvironment,
        model: type[T],
        confit_config: ConfitConfigModel,
        provider_data: dict[ConfigFlavor, dict],
    ) -> Optional[BaseConfigProvider]:
        if item is ConfigFlavor.BASE:
            return self._build_json_provider(model, ConfigFlavor.BASE, confit_config)
        elif isinstance(item, ConfigEnvironment):
            if item is not confit_config.environment:
                return None
            return self._build_json_provider(model, item, confit_config)
        elif item is ConfigFlavor.ENV:
            return self._build_env_provider(model, confit_config)
        elif item is ConfigFlavor.ARGPARSE:
            return self._build_dict_provider(model, ArgparseConfigProvider, provider_data.get(ConfigFlavor.ARGPARSE))
        elif item is ConfigFlavor.KWARG:
            return self._build_dict_provider(model, KwargConfigProvider, provider_data.get(ConfigFlavor.KWARG))

        return None

    def _build_json_provider(
        self,
        model: type[T],
        config_key: ConfigFlavor | ConfigEnvironment,
        confit_config: ConfitConfigModel,
    ) -> Optional[JsonConfigProvider]:
        if confit_config.config_directory is None:
            return None

        config_file_name = confit_config.config_filename_template.format(environment=config_key.value)
        config_file_path = confit_config.config_directory / config_file_name

        if not config_file_path.exists():
            return None

        return JsonConfigProvider(model, config_file_path)

    def _build_env_provider(
        self,
        model: type[T],
        confit_config: ConfitConfigModel,
    ) -> EnvVarConfigProvider:
        prefix = confit_config.config_env_var_prefix
        if model is ConfitConfigModel:
            prefix = confit_config.confit_env_var_prefix

        return EnvVarConfigProvider(model, env_var_prefix=prefix, env_var_delimiter=confit_config.env_var_delimiter)

    def _build_dict_provider(
        self,
        model: type[T],
        provider_cls: type[DictConfigProvider],
        data: Optional[dict],
    ) -> Optional[DictConfigProvider]:
        if not data:
            return None

        return provider_cls(model, data)
