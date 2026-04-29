import json
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from confiddle.config.config_manager import ConfigManager
from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.models.confiddle_config_model import ConfiddleConfigModel
from confiddle.config.models.providers.argparse_config_provider_config_model import ArgparseProviderConfig
from confiddle.config.models.providers.dict_config_provider_config_model import DictProviderConfig
from confiddle.config.models.providers.json_config_provider_config_model import JsonConfigProviderConfigModel
from confiddle.config.models.providers.kwarg_config_provider_config_model import KwargProviderConfig


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

    def test_allows_user_model_after_bootstrap(self, bootstrapped_manager: ConfigManager):
        result = bootstrapped_manager.get_config(SampleModel)
        assert isinstance(result, SampleModel)


class TestBaseData:
    def test_base_data_seeds_result(self, bootstrapped_manager: ConfigManager):
        result = bootstrapped_manager.get_config(SampleModel, base_data={"name": "seeded"})
        assert result.name == "seeded"

    def test_provider_overwrites_base_data(self, bootstrapped_manager: ConfigManager):
        result = bootstrapped_manager.get_config(
            SampleModel,
            base_data={"name": "seeded"},
            provider_configs=[KwargProviderConfig(name="overwritten")],
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
        config_manager.confiddle_config = ConfiddleConfigModel()  # json_file.directory_path=None
        result = config_manager.get_config(SampleModel)
        assert result.name == "default"

    def test_skips_json_when_file_not_present(self, bootstrapped_manager: ConfigManager):
        # config_dir has no JSON files placed - no config_file fixture used
        result = bootstrapped_manager.get_config(SampleModel)
        assert result.name == "default"

    def test_skips_json_when_environment_mismatch(self, config_dir: Path):
        # hierarchy default includes DEV env; we set environment=PROD so DEV file is skipped
        from confiddle.config.enums.config_environment import ConfigEnvironment

        dev_file = config_dir / "config.dev.json"
        dev_file.write_text(json.dumps({"name": "from_dev"}))

        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel(
            json_file=JsonConfigProviderConfigModel(directory_path=config_dir),
            environment=ConfigEnvironment.PROD,
        )
        result = config_manager.get_config(SampleModel)
        assert result.name == "default"


class TestProviderData:
    def test_kwarg_provider_data_applied(self, bootstrapped_manager: ConfigManager):
        result = bootstrapped_manager.get_config(
            SampleModel,
            provider_configs=[KwargProviderConfig(name="from_kwarg")],
        )
        assert result.name == "from_kwarg"

    def test_argparse_provider_data_applied(self, bootstrapped_manager: ConfigManager):
        result = bootstrapped_manager.get_config(
            SampleModel,
            provider_configs=[ArgparseProviderConfig(args={"value": 99})],
        )
        assert result.value == 99

    def test_kwarg_overrides_json(self, bootstrapped_manager: ConfigManager, config_file: Path):
        result = bootstrapped_manager.get_config(
            SampleModel,
            provider_configs=[KwargProviderConfig(name="kwarg_wins")],
        )
        assert result.name == "kwarg_wins"


class TestHierarchyOrder:
    def test_later_provider_overwrites_earlier(self, config_dir: Path):
        # BASE json sets name="from_base"; KWARG (later in hierarchy) should win
        (config_dir / "config.json").write_text(json.dumps({"name": "from_base"}))

        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel(
            json_file=JsonConfigProviderConfigModel(directory_path=config_dir),
            hierarchy=[ConfigFlavor.JSON, ConfigFlavor.KWARG],
        )
        result = config_manager.get_config(SampleModel, provider_configs=[KwargProviderConfig(name="from_kwarg")])
        assert result.name == "from_kwarg"

    def test_env_json_overwrites_base_json(self, config_dir: Path):
        # BASE loads first, then DEV env file - DEV should win
        (config_dir / "config.json").write_text(json.dumps({"name": "from_base"}))
        (config_dir / "config.dev.json").write_text(json.dumps({"name": "from_dev"}))

        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel(
            json_file=JsonConfigProviderConfigModel(directory_path=config_dir),
            environment=ConfigEnvironment.DEV,
            hierarchy=[ConfigFlavor.JSON, ConfigEnvironment.DEV],
        )
        result = config_manager.get_config(SampleModel)
        assert result.name == "from_dev"

    def test_argparse_overwrites_env_json(self, config_dir: Path):
        (config_dir / "config.json").write_text(json.dumps({"name": "from_base"}))

        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel(
            json_file=JsonConfigProviderConfigModel(directory_path=config_dir),
            hierarchy=[ConfigFlavor.JSON, ConfigFlavor.ARGPARSE],
        )
        result = config_manager.get_config(
            SampleModel, provider_configs=[ArgparseProviderConfig(args={"name": "from_argparse"})]
        )
        assert result.name == "from_argparse"

    def test_kwarg_overwrites_argparse(self, bootstrapped_manager: ConfigManager):
        bootstrapped_manager.confiddle_config = ConfiddleConfigModel(
            json_file=JsonConfigProviderConfigModel(
                directory_path=bootstrapped_manager.confiddle_config.json_file.directory_path
            ),
            hierarchy=[ConfigFlavor.ARGPARSE, ConfigFlavor.KWARG],
        )
        result = bootstrapped_manager.get_config(
            SampleModel,
            provider_configs=[
                ArgparseProviderConfig(args={"name": "from_argparse"}),
                KwargProviderConfig(name="from_kwarg"),
            ],
        )
        assert result.name == "from_kwarg"

    def test_custom_hierarchy_order_respected(self, config_dir: Path):
        # Reversed: KWARG first, BASE last - BASE json should win
        (config_dir / "config.json").write_text(json.dumps({"name": "from_base"}))

        config_manager = ConfigManager()
        config_manager.confiddle_config = ConfiddleConfigModel(
            json_file=JsonConfigProviderConfigModel(directory_path=config_dir),
            hierarchy=[ConfigFlavor.KWARG, ConfigFlavor.JSON],
        )
        result = config_manager.get_config(SampleModel, provider_configs=[KwargProviderConfig(name="from_kwarg")])
        assert result.name == "from_base"


class TestBuildProviderCoverage:
    def test_all_config_flavors_handled(self, bootstrapped_manager: ConfigManager):
        # Every ConfigFlavor member should result in a call to _build_provider without raising
        for flavor in ConfigFlavor:
            config_manager = ConfigManager()
            config_manager.confiddle_config = ConfiddleConfigModel(
                hierarchy=[flavor],
            )
            # Provide data for dict-based flavors so they aren't skipped as None
            providers = [
                KwargProviderConfig(name="x"),
                ArgparseProviderConfig(args={"name": "x"}),
                DictProviderConfig(data={"name": "x"}),
            ]
            config_manager.get_config(SampleModel, provider_configs=providers)  # should not raise

    def test_all_config_environments_handled(self, config_dir: Path):
        # Every ConfigEnvironment member should be accepted in the hierarchy without raising
        for env in ConfigEnvironment:
            (config_dir / f"config.{env.value}.json").write_text(json.dumps({"name": env.value}))

            config_manager = ConfigManager()
            config_manager.confiddle_config = ConfiddleConfigModel(
                json_file=JsonConfigProviderConfigModel(directory_path=config_dir),
                environment=env,
                hierarchy=[env],
            )
            result = config_manager.get_config(SampleModel)
            assert result.name == env.value


class TestOverlays:
    def test_overlay_applied_after_hierarchy(self, bootstrapped_manager: ConfigManager):
        result = bootstrapped_manager.get_config(
            SampleModel, provider_configs=[DictProviderConfig(data={"name": "from_overlay"})]
        )
        assert result.name == "from_overlay"

    def test_overlay_overrides_provider_data(self, bootstrapped_manager: ConfigManager):
        result = bootstrapped_manager.get_config(
            SampleModel,
            provider_configs=[
                KwargProviderConfig(name="kwarg_loses"),
                DictProviderConfig(data={"name": "overlay_wins"}),
            ],
        )
        assert result.name == "overlay_wins"

    def test_multiple_overlays_applied_in_order(self, bootstrapped_manager: ConfigManager):
        result = bootstrapped_manager.get_config(
            SampleModel,
            provider_configs=[DictProviderConfig(data={"name": "first"}), DictProviderConfig(data={"name": "second"})],
        )
        assert result.name == "second"

    def test_no_overlays_behaves_normally(self, bootstrapped_manager: ConfigManager):
        result = bootstrapped_manager.get_config(SampleModel, provider_configs=[])
        assert result.name == "default"


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
