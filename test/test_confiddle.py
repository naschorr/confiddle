import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.models.confiddle_config_model import ConfiddleConfigModel
from confiddle.config.models.providers.json_provider_config import JsonProviderConfig
from confiddle import Confiddle, DictProviderConfig


class SampleModel(BaseModel):
    name: str = "default"
    value: int = 0


class TestBootstrap:
    def test_default_bootstrap_produces_confiddle_config(self):
        confiddle = Confiddle()
        assert isinstance(confiddle._config_manager.confiddle_config, ConfiddleConfigModel)

    def test_bootstrap_from_confiddle_config(self, config_dir: Path):
        confiddle_config = ConfiddleConfigModel(json_file=JsonProviderConfig(directory_path=config_dir))
        confiddle = Confiddle(confiddle_config=confiddle_config)
        assert confiddle._config_manager.confiddle_config.json_file.directory_path == config_dir

    def test_bootstrap_with_no_args_uses_defaults(self):
        confiddle = Confiddle()
        assert confiddle._config_manager.confiddle_config.env_var.prefix is None

    def test_bootstrap_env_var_overrides_default(self, monkeypatch):
        monkeypatch.setenv("CONFIDDLE:ENV_VAR:PREFIX", "MYAPP")
        confiddle = Confiddle()
        assert confiddle._config_manager.confiddle_config.env_var.prefix == "MYAPP"


class TestLoadConfig:
    def test_returns_instance_of_model(self, config_dir: Path):
        (config_dir / "config.json").write_text("{}")
        (config_dir / "config.dev.json").write_text("{}")
        confiddle = Confiddle(
            confiddle_config=ConfiddleConfigModel(json_file=JsonProviderConfig(directory_path=config_dir))
        )
        result = confiddle.load_config(SampleModel)
        assert isinstance(result, SampleModel)

    def test_loads_from_json_file(self, config_dir: Path):
        (config_dir / "config.json").write_text(json.dumps({"name": "from_file"}))
        confiddle = Confiddle(
            confiddle_config=ConfiddleConfigModel(
                json_file=JsonProviderConfig(directory_path=config_dir),
                hierarchy=[ConfigFlavor.JSON],
            )
        )
        result = confiddle.load_config(SampleModel)
        assert result.name == "from_file"

    def test_provider_data_applied(self, config_dir: Path):
        (config_dir / "config.json").write_text("{}")
        (config_dir / "config.dev.json").write_text("{}")
        confiddle = Confiddle(
            confiddle_config=ConfiddleConfigModel(json_file=JsonProviderConfig(directory_path=config_dir))
        )
        result = confiddle.load_config(SampleModel, provider_configs=[DictProviderConfig(data={"name": "from_dict"})])
        assert result.name == "from_dict"
