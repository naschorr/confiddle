from typing import Optional, TypeVar, cast

from pydantic import BaseModel

from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.enums.merge_strategy import MergeStrategy
from confiddle.config.models.confiddle_config_model import ConfiddleConfigModel
from confiddle.config.models.providers.argparse_config_provider_config_model import ArgparseProviderConfig
from confiddle.config.models.providers.dict_config_provider_config_model import DictProviderConfig
from confiddle.config.models.providers.json_config_provider_config_model import JsonConfigProviderConfigModel
from confiddle.config.models.providers.kwarg_config_provider_config_model import KwargProviderConfig
from confiddle.config.models.providers.provider_config_model import BaseProviderConfigModel
from confiddle.config.providers.argparse_config_provider import ArgparseConfigProvider
from confiddle.config.providers.base_config_provider import BaseConfigProvider
from confiddle.config.providers.dict_config_provider import DictConfigProvider
from confiddle.config.providers.env_var_config_provider import EnvVarConfigProvider
from confiddle.config.providers.json_config_provider import JsonConfigProvider
from confiddle.config.providers.kwarg_config_provider import KwargConfigProvider
from confiddle.utilities.dict_merger import DictMerger

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
        provider_configs: list[BaseProviderConfigModel] = [],
        base_data: Optional[dict] = None,
    ) -> T:
        if self._confiddle_config is None and model is not ConfiddleConfigModel:
            raise RuntimeError(
                "ConfigManager must be bootstrapped before building a user config model. "
                "Call get_config(ConfiddleConfigModel, ...) first and assign the result to confiddle_config."
            )

        merged = dict(base_data) if base_data else {}
        for provider in self._build_providers(model, provider_configs):
            provider_config = provider.get_config()
            if provider.merge_strategy is MergeStrategy.DEEP:
                merged = DictMerger.deep_merge(merged, provider_config)
            else:
                merged |= provider_config

        return cast(T, model(**merged))

    ## Private

    def _build_providers(
        self, model: type[T], provider_configs: list[BaseProviderConfigModel]
    ) -> list[BaseConfigProvider]:
        confiddle_config = self._confiddle_config or ConfiddleConfigModel()
        by_flavor: dict[ConfigFlavor, list[BaseProviderConfigModel]] = {}

        for pc in provider_configs:
            if isinstance(pc, ArgparseProviderConfig):
                by_flavor.setdefault(ConfigFlavor.ARGPARSE, []).append(pc)
            elif isinstance(pc, KwargProviderConfig):
                by_flavor.setdefault(ConfigFlavor.KWARG, []).append(pc)
            elif isinstance(pc, DictProviderConfig):
                by_flavor.setdefault(ConfigFlavor.DICT, []).append(pc)

        result = []

        for item in confiddle_config.hierarchy:
            result.extend(self._build_provider(item, model, confiddle_config, by_flavor))

        return result

    def _build_provider(
        self,
        item: ConfigFlavor | ConfigEnvironment,
        model: type[T],
        confiddle_config: ConfiddleConfigModel,
        by_flavor: dict[ConfigFlavor, list[BaseProviderConfigModel]],
    ) -> list[BaseConfigProvider]:
        if item is ConfigFlavor.JSON:
            json_config = (
                confiddle_config.bootstrap.json_file if model is ConfiddleConfigModel else confiddle_config.json_file
            )
            return self._build_json_provider(model, ConfigFlavor.JSON, json_config)
        elif isinstance(item, ConfigEnvironment):
            if item is not confiddle_config.environment:
                return []
            json_config = (
                confiddle_config.bootstrap.json_file if model is ConfiddleConfigModel else confiddle_config.json_file
            )
            return self._build_json_provider(model, item, json_config)
        elif item is ConfigFlavor.ENV:
            return [self._build_env_provider(model, confiddle_config)]
        elif item is ConfigFlavor.ARGPARSE:
            return self._build_argparse_providers(model, by_flavor.get(ConfigFlavor.ARGPARSE, []))
        elif item is ConfigFlavor.KWARG:
            return self._build_kwarg_providers(model, by_flavor.get(ConfigFlavor.KWARG, []))
        elif item is ConfigFlavor.DICT:
            return self._build_dict_providers(model, by_flavor.get(ConfigFlavor.DICT, []))

        return []

    def _build_json_provider(
        self,
        model: type[T],
        config_key: ConfigFlavor | ConfigEnvironment,
        json_config: JsonConfigProviderConfigModel,
    ) -> list[BaseConfigProvider]:
        if json_config.directory_path is None:
            return []

        provider = JsonConfigProvider(model, json_config, environment=config_key)

        if not provider.file_path.exists():
            return []

        return [provider]

    def _build_env_provider(
        self,
        model: type[T],
        confiddle_config: ConfiddleConfigModel,
    ) -> EnvVarConfigProvider:
        env_config = confiddle_config.bootstrap.env_var if model is ConfiddleConfigModel else confiddle_config.env_var

        return EnvVarConfigProvider(model, env_config)

    def _build_argparse_providers(
        self,
        model: type[T],
        configs: list[ArgparseProviderConfig],
    ) -> list[BaseConfigProvider]:
        return [ArgparseConfigProvider(model, apc) for apc in configs]

    def _build_kwarg_providers(
        self,
        model: type[T],
        configs: list[KwargProviderConfig],
    ) -> list[BaseConfigProvider]:
        return [KwargConfigProvider(model, kpc) for kpc in configs]

    def _build_dict_providers(
        self,
        model: type[T],
        configs: Optional[list[DictProviderConfig]],
    ) -> list[BaseConfigProvider]:
        if not configs:
            return []
        return [DictConfigProvider(model, cfg) for cfg in configs]

