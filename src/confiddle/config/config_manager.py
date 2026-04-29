from typing import Optional, TypeVar, cast

from pydantic import BaseModel

from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.enums.merge_strategy import MergeStrategy
from confiddle.config.factories.config_provider_factory import ConfigProviderFactory
from confiddle.config.models.confiddle_config_model import ConfiddleConfigModel
from confiddle.config.models.providers.argparse_config_provider_config_model import ArgparseProviderConfig
from confiddle.config.models.providers.dict_config_provider_config_model import DictProviderConfig
from confiddle.config.models.providers.kwarg_config_provider_config_model import KwargProviderConfig
from confiddle.config.models.providers.provider_config_model import BaseProviderConfigModel
from confiddle.config.providers.base_config_provider import BaseConfigProvider
from confiddle.utilities.dict_merger import DictMerger

T = TypeVar("T", bound=BaseModel)


class ConfigManager:

    ## Lifecycle

    def __init__(self):
        self._confiddle_config: Optional[ConfiddleConfigModel] = None
        self._factory = ConfigProviderFactory()

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
        is_bootstrap = model is ConfiddleConfigModel

        by_flavor: dict[ConfigFlavor, list[BaseProviderConfigModel]] = {}
        for provider_config in provider_configs:
            if isinstance(provider_config, ArgparseProviderConfig):
                by_flavor.setdefault(ConfigFlavor.ARGPARSE, []).append(provider_config)
            elif isinstance(provider_config, KwargProviderConfig):
                by_flavor.setdefault(ConfigFlavor.KWARG, []).append(provider_config)
            elif isinstance(provider_config, DictProviderConfig):
                by_flavor.setdefault(ConfigFlavor.DICT, []).append(provider_config)

        result: list[BaseConfigProvider] = []
        json_config = confiddle_config.bootstrap.json_file if is_bootstrap else confiddle_config.json_file
        env_config = confiddle_config.bootstrap.env_var if is_bootstrap else confiddle_config.env_var

        for item in confiddle_config.hierarchy:
            if item is ConfigFlavor.JSON:
                if json_config.directory_path is not None:
                    provider = self._factory.build_provider(model, json_config, environment=None)
                    if provider.file_path.exists():
                        result.append(provider)
            elif isinstance(item, ConfigEnvironment):
                if item is confiddle_config.environment and json_config.directory_path is not None:
                    provider = self._factory.build_provider(model, json_config, environment=item)
                    if provider.file_path.exists():
                        result.append(provider)
            elif item is ConfigFlavor.ENV_VAR:
                result.append(self._factory.build_provider(model, env_config))
            elif item is ConfigFlavor.ARGPARSE:
                result.extend(
                    self._factory.build_provider(model, pc) for pc in by_flavor.get(ConfigFlavor.ARGPARSE, [])
                )
            elif item is ConfigFlavor.KWARG:
                result.extend(self._factory.build_provider(model, pc) for pc in by_flavor.get(ConfigFlavor.KWARG, []))
            elif item is ConfigFlavor.DICT:
                result.extend(self._factory.build_provider(model, pc) for pc in by_flavor.get(ConfigFlavor.DICT, []))

        return result
