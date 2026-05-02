from typing import Optional, TypeVar, cast

from pydantic import BaseModel, ValidationError

from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.enums.merge_strategy import MergeStrategy
from confiddle.config.factories.provider_factory import ProviderFactory
from confiddle.config.models.confiddle_config_model import ConfiddleConfigModel
from confiddle.config.models.provider_config_model import ProviderConfigModel
from confiddle.config.models.providers.base_provider_config import BaseProviderConfig
from confiddle.config.providers.base_provider import BaseProvider
from confiddle.utilities.dict_merger import DictMerger

T = TypeVar("T", bound=BaseModel)


class ConfigManager:

    ## Lifecycle

    def __init__(self):
        self._confiddle_config: Optional[ConfiddleConfigModel] = None
        self._factory = ProviderFactory()

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
        provider_configs: list[BaseProviderConfig] = [],
        base_data: Optional[dict] = None,
    ) -> T:
        if self._confiddle_config is None and model is not ConfiddleConfigModel:
            raise RuntimeError(
                "ConfigManager must be bootstrapped before building a user config model. "
                "Call get_config(ConfiddleConfigModel, ...) first and assign the result to confiddle_config."
            )

        confiddle_config = self._confiddle_config or ConfiddleConfigModel()
        is_bootstrap = model is ConfiddleConfigModel
        environment = None
        if self._confiddle_config is not None and not is_bootstrap:
            environment = self._confiddle_config.environment

        providers: list[BaseProvider] = []
        if is_bootstrap:
            configured_provider_configs = self._build_provider_configs_from_provider_config_model(
                confiddle_config.bootstrap
            )
            provider_config = configured_provider_configs + provider_configs
        else:
            configured_provider_configs = self._build_provider_configs_from_provider_config_model(confiddle_config.app)
            provider_config = configured_provider_configs + provider_configs
        providers = self._build_providers(model, is_bootstrap, environment, provider_config)

        merged = dict(base_data) if base_data else {}
        for provider in providers:
            provider_config = provider.get_config()

            if provider.merge_strategy is MergeStrategy.DEEP:
                merged = DictMerger.deep_merge(merged, provider_config)
            else:
                merged |= provider_config

        return cast(T, model(**merged))

    ## Private

    def _build_provider_configs_from_provider_config_model(
        self, provider_config_model: ProviderConfigModel
    ) -> list[BaseProviderConfig]:
        provider_configs: list[BaseProviderConfig] = []

        provider_configs.extend(provider_config_model.argparse_provider)
        provider_configs.extend(provider_config_model.env_var_provider)
        provider_configs.extend(provider_config_model.dict_provider)
        provider_configs.extend(provider_config_model.json_file_provider)

        return provider_configs

    def _inject_context(
        self, provider_configs: list[BaseProviderConfig], environment: Optional[ConfigEnvironment]
    ) -> list[BaseProviderConfig]:
        """For each provider config that supports environment substitution, emit a base copy and an
        environment-bound copy. Configs without an ``environment`` attribute are passed through as-is."""
        result: list[BaseProviderConfig] = []
        for provider_config in provider_configs:
            result.append(provider_config)
            if hasattr(provider_config, "environment") and environment is not None:
                result.append(provider_config.model_copy(update={"environment": environment}))
        return result

    def _map_config_flavor_to_provider_configs(
        self, provider_configs: list[BaseProviderConfig]
    ) -> dict[ConfigFlavor, list[BaseProviderConfig]]:
        result: dict[ConfigFlavor, list[BaseProviderConfig]] = {}
        for provider_config in provider_configs:
            result.setdefault(provider_config.config_flavor, []).append(provider_config)

        return result

    def _build_providers(
        self,
        model: type[T],
        is_bootstrap: bool,
        environment: Optional[ConfigEnvironment],
        provider_configs: list[BaseProviderConfig],
    ) -> list[BaseProvider]:
        confiddle_config = self._confiddle_config or ConfiddleConfigModel()
        config_flavor_to_provider_config = self._map_config_flavor_to_provider_configs(
            self._inject_context(provider_configs, environment)
        )

        result: list[BaseProvider] = []
        for hierarchy_element in confiddle_config.hierarchy:
            for provider_config in config_flavor_to_provider_config.get(hierarchy_element, []):
                try:
                    provider = self._factory.build_provider(model, provider_config)
                except Exception:
                    if is_bootstrap:
                        continue
                    raise

                result.append(provider)

        return result
