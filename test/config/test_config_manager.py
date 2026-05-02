import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from confiddle.config.config_manager import ConfigManager
from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.models.confiddle_config_model import ConfiddleConfigModel
from confiddle.config.models.provider_config_model import ProviderConfigModel
from confiddle.config.models.providers.argparse_provider_config import ArgparseProviderConfig
from confiddle.config.models.providers.dict_provider_config import DictProviderConfig
from confiddle.config.models.providers.env_var_provider_config import EnvVarProviderConfig
from confiddle.config.models.providers.json_provider_config import JsonProviderConfig


class SampleModel(BaseModel):
    name: str = "default"
    value: int = 0


class TestGetConfigGuard:
    def test_raises_before_bootstrap(self):
        config_manager = ConfigManager()
        with pytest.raises(RuntimeError, match="bootstrap"):
            config_manager.get_config(SampleModel)

    def test_allows_confiddle_config_model_before_bootstrap(self):
        config_manager = ConfigManager()
        result = config_manager.get_config(ConfiddleConfigModel)
        assert isinstance(result, ConfiddleConfigModel)


class TestBaseData:
    def test_base_data_seeds_result(self, bootstrapped_manager: ConfigManager):
        result = bootstrapped_manager.get_config(SampleModel, base_data={"name": "seeded"})
        assert result.name == "seeded"

    def test_provider_overwrites_base_data(self, bootstrapped_manager: ConfigManager):
        result = bootstrapped_manager.get_config(
            SampleModel,
            base_data={"name": "seeded"},
            provider_configs=[DictProviderConfig(data={"name": "overwritten"})],
        )
        assert result.name == "overwritten"

    def test_no_base_data_uses_model_defaults(self, bootstrapped_manager: ConfigManager):
        result = bootstrapped_manager.get_config(SampleModel)
        assert result.name == "default"
        assert result.value == 0


class TestJsonProvider:
    def test_loads_base_json_file(self, bootstrapped_manager: ConfigManager, config_file: Path):
        result = bootstrapped_manager.get_config(SampleModel)
        assert result.name == "from_file"

    def test_skips_json_when_no_config_directory(self):
        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel()  # app.json_file_provider is empty
        result = config_manager.get_config(SampleModel)
        assert result.name == "default"

    def test_raises_when_json_file_not_present(self, config_dir: Path):
        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel(
            app=ProviderConfigModel(json_file_provider=[JsonProviderConfig(directory_path=config_dir)])
        )
        with pytest.raises(FileNotFoundError):
            config_manager.get_config(SampleModel)

    def test_skips_json_when_environment_mismatch(self, config_dir: Path):
        # hierarchy default includes JSON_ENV; we set environment=PROD so DEV file is skipped
        (config_dir / "config.json").write_text(json.dumps({}))
        (config_dir / "config.dev.json").write_text(json.dumps({"name": "from_dev"}))

        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel(
            app=ProviderConfigModel(json_file_provider=[JsonProviderConfig(directory_path=config_dir)]),
            environment=ConfigEnvironment.PROD,
        )
        result = config_manager.get_config(SampleModel)
        assert result.name == "default"


class TestProviderData:
    def test_dict_provider_data_applied(self, bootstrapped_manager: ConfigManager):
        result = bootstrapped_manager.get_config(
            SampleModel,
            provider_configs=[DictProviderConfig(data={"name": "from_dict"})],
        )
        assert result.name == "from_dict"

    def test_argparse_provider_data_applied(self, bootstrapped_manager: ConfigManager):
        result = bootstrapped_manager.get_config(
            SampleModel,
            provider_configs=[ArgparseProviderConfig(args={"value": 99})],
        )
        assert result.value == 99


class TestHierarchyOrder:
    def test_later_provider_overwrites_earlier(self, config_dir: Path):
        # BASE json sets name="from_base"; DICT (later in hierarchy) should win
        (config_dir / "config.json").write_text(json.dumps({"name": "from_base"}))

        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel(
            app=ProviderConfigModel(json_file_provider=[JsonProviderConfig(directory_path=config_dir)]),
            hierarchy=[ConfigFlavor.JSON, ConfigFlavor.DICT],
        )
        result = config_manager.get_config(
            SampleModel, provider_configs=[DictProviderConfig(data={"name": "from_dict"})]
        )
        assert result.name == "from_dict"

    def test_env_json_overwrites_base_json(self, config_dir: Path):
        # BASE loads first, then DEV env file - DEV should win
        (config_dir / "config.json").write_text(json.dumps({"name": "from_base"}))
        (config_dir / "config.dev.json").write_text(json.dumps({"name": "from_dev"}))

        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel(
            app=ProviderConfigModel(json_file_provider=[JsonProviderConfig(directory_path=config_dir)]),
            environment=ConfigEnvironment.DEV,
            hierarchy=[ConfigFlavor.JSON, ConfigFlavor.JSON_ENV],
        )
        result = config_manager.get_config(SampleModel)
        assert result.name == "from_dev"

    def test_argparse_overwrites_env_json(self, config_dir: Path):
        (config_dir / "config.json").write_text(json.dumps({"name": "from_base"}))

        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel(
            app=ProviderConfigModel(json_file_provider=[JsonProviderConfig(directory_path=config_dir)]),
            hierarchy=[ConfigFlavor.JSON, ConfigFlavor.ARGPARSE],
        )
        result = config_manager.get_config(
            SampleModel, provider_configs=[ArgparseProviderConfig(args={"name": "from_argparse"})]
        )
        assert result.name == "from_argparse"

    def test_dict_overwrites_argparse(self, bootstrapped_manager: ConfigManager):
        bootstrapped_manager.confiddle_config = ConfiddleConfigModel(
            hierarchy=[ConfigFlavor.ARGPARSE, ConfigFlavor.DICT],
        )
        result = bootstrapped_manager.get_config(
            SampleModel,
            provider_configs=[
                ArgparseProviderConfig(args={"name": "from_argparse"}),
                DictProviderConfig(data={"name": "from_dict"}),
            ],
        )
        assert result.name == "from_dict"

    def test_custom_hierarchy_order_respected(self, config_dir: Path):
        # Reversed: DICT first, BASE last - BASE json should win
        (config_dir / "config.json").write_text(json.dumps({"name": "from_base"}))

        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel(
            app=ProviderConfigModel(json_file_provider=[JsonProviderConfig(directory_path=config_dir)]),
            hierarchy=[ConfigFlavor.DICT, ConfigFlavor.JSON],
        )
        result = config_manager.get_config(
            SampleModel, provider_configs=[DictProviderConfig(data={"name": "from_dict"})]
        )
        assert result.name == "from_base"


class TestBuildProviderCoverage:
    def test_all_config_flavors_handled(self, config_dir: Path):
        # Every ConfigFlavor member should result in a call to _build_provider without raising.
        # Write base and env-specific files so JSON/JSON_ENV flavors can resolve their providers.
        (config_dir / "config.json").write_text(json.dumps({"name": "x"}))
        (config_dir / "config.dev.json").write_text(json.dumps({}))
        for flavor in ConfigFlavor:
            config_manager = ConfigManager()
            config_manager.confiddle_config = ConfiddleConfigModel(
                app=ProviderConfigModel(json_file_provider=[JsonProviderConfig(directory_path=config_dir)]),
                environment=ConfigEnvironment.DEV,
                hierarchy=[flavor],
            )
            providers = [
                ArgparseProviderConfig(args={"name": "x"}),
                DictProviderConfig(data={"name": "x"}),
            ]
            config_manager.get_config(SampleModel, provider_configs=providers)  # should not raise

    def test_all_config_environments_handled(self, config_dir: Path):
        # Every ConfigEnvironment member should load its env-specific file via JSON_ENV
        for env in ConfigEnvironment:
            (config_dir / f"config.{env.value}.json").write_text(json.dumps({"name": env.value}))

            config_manager = ConfigManager()
            config_manager.confiddle_config = ConfiddleConfigModel(
                app=ProviderConfigModel(json_file_provider=[JsonProviderConfig(directory_path=config_dir)]),
                environment=env,
                hierarchy=[ConfigFlavor.JSON_ENV],
            )
            result = config_manager.get_config(SampleModel)
            assert result.name == env.value


class TestMultipleProvidersOfSameKind:
    def test_two_json_providers_second_wins_on_conflict(self, config_dir: Path):
        # Two separate JSON directories; the second one is later in the provider list so it wins
        first_dir = config_dir / "first"
        second_dir = config_dir / "second"
        first_dir.mkdir()
        second_dir.mkdir()
        (first_dir / "config.json").write_text(json.dumps({"name": "from_first", "value": 1}))
        (second_dir / "config.json").write_text(json.dumps({"name": "from_second"}))

        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel(
            app=ProviderConfigModel(
                json_file_provider=[
                    JsonProviderConfig(directory_path=first_dir),
                    JsonProviderConfig(directory_path=second_dir),
                ]
            ),
            hierarchy=[ConfigFlavor.JSON],
        )
        result = config_manager.get_config(SampleModel)
        assert result.name == "from_second"  # second provider wins
        assert result.value == 1  # only in first provider, preserved

    def test_two_json_providers_non_conflicting_keys_both_applied(self, config_dir: Path):
        first_dir = config_dir / "first"
        second_dir = config_dir / "second"
        first_dir.mkdir()
        second_dir.mkdir()
        (first_dir / "config.json").write_text(json.dumps({"name": "from_first"}))
        (second_dir / "config.json").write_text(json.dumps({"value": 99}))

        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel(
            app=ProviderConfigModel(
                json_file_provider=[
                    JsonProviderConfig(directory_path=first_dir),
                    JsonProviderConfig(directory_path=second_dir),
                ]
            ),
            hierarchy=[ConfigFlavor.JSON],
        )
        result = config_manager.get_config(SampleModel)
        assert result.name == "from_first"
        assert result.value == 99

    def test_two_env_var_providers_different_prefixes_both_applied(self, config_dir: Path, monkeypatch):
        monkeypatch.setenv("APP:NAME", "from_app")
        monkeypatch.setenv("SVC:VALUE", "42")

        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel(
            app=ProviderConfigModel(
                env_var_provider=[
                    EnvVarProviderConfig(prefix="APP"),
                    EnvVarProviderConfig(prefix="SVC"),
                ]
            ),
            hierarchy=[ConfigFlavor.ENV_VAR],
        )
        result = config_manager.get_config(SampleModel)
        assert result.name == "from_app"
        assert result.value == 42


class TestDeepMerge:
    def test_scoped_overlay_deep_merges_nested_dict(self, bootstrapped_manager: ConfigManager):
        class NestedModel(BaseModel):
            items: dict = {}

        bootstrapped_manager.confiddle_config = ConfiddleConfigModel(hierarchy=[ConfigFlavor.DICT])

        result = bootstrapped_manager.get_config(
            NestedModel,
            provider_configs=[
                DictProviderConfig(data={"a": 1, "b": 2}, scope="items"),
                DictProviderConfig(data={"b": 99, "c": 3}, scope="items"),
            ],
        )
        assert result.items == {"a": 1, "b": 99, "c": 3}

    def test_flat_overlay_shallow_replaces_nested_dict(self, bootstrapped_manager: ConfigManager):
        class NestedModel(BaseModel):
            items: dict = {}

        bootstrapped_manager.confiddle_config = ConfiddleConfigModel(hierarchy=[ConfigFlavor.DICT])

        result = bootstrapped_manager.get_config(
            NestedModel,
            provider_configs=[
                DictProviderConfig(data={"items": {"a": 1, "b": 2}}),
                DictProviderConfig(data={"items": {"b": 99, "c": 3}}),
            ],
        )
        assert result.items == {"b": 99, "c": 3}

    def test_scoped_overlay_does_not_affect_scalar_fields(self, bootstrapped_manager: ConfigManager):
        bootstrapped_manager.confiddle_config = ConfiddleConfigModel(hierarchy=[ConfigFlavor.DICT])

        result = bootstrapped_manager.get_config(
            SampleModel,
            provider_configs=[
                DictProviderConfig(data={"name": "base", "value": 1}),
                DictProviderConfig(data={"name": "overlay"}),
            ],
        )
        assert result.name == "overlay"
        assert result.value == 1
