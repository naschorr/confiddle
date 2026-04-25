import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from confit.config.enums.config_flavor import ConfigFlavor
from confit.config.models.confit_config_model import ConfitConfigModel
from confit.config.models.providers.json_config_provider_config_model import JsonConfigProviderConfigModel
from confit import Confit


class SampleModel(BaseModel):
    name: str = "default"
    value: int = 0


class TestBootstrap:
    def test_default_bootstrap_produces_confit_config(self):
        confit = Confit()
        assert isinstance(confit._config_manager.confit_config, ConfitConfigModel)

    def test_bootstrap_from_confit_config(self, config_dir: Path):
        confit_config = ConfitConfigModel(json_file=JsonConfigProviderConfigModel(directory_path=config_dir))
        confit = Confit(confit_config=confit_config)
        assert confit._config_manager.confit_config.json_file.directory_path == config_dir

    def test_bootstrap_with_no_args_uses_defaults(self):
        confit = Confit()
        assert confit._config_manager.confit_config.env_var.prefix is None

    def test_bootstrap_env_var_overrides_default(self, monkeypatch):
        monkeypatch.setenv("CONFIT:ENV_VAR:PREFIX", "MYAPP")
        confit = Confit()
        assert confit._config_manager.confit_config.env_var.prefix == "MYAPP"


class TestLoadConfig:
    def test_returns_instance_of_model(self, config_dir: Path):
        confit = Confit(
            confit_config=ConfitConfigModel(json_file=JsonConfigProviderConfigModel(directory_path=config_dir))
        )
        result = confit.load_config(SampleModel)
        assert isinstance(result, SampleModel)

    def test_loads_from_json_file(self, config_dir: Path):
        (config_dir / "config.base.json").write_text(json.dumps({"name": "from_file"}))
        confit = Confit(
            confit_config=ConfitConfigModel(
                json_file=JsonConfigProviderConfigModel(directory_path=config_dir),
                hierarchy=[ConfigFlavor.BASE],
            )
        )
        result = confit.load_config(SampleModel)
        assert result.name == "from_file"

    def test_provider_data_applied(self, config_dir: Path):
        confit = Confit(
            confit_config=ConfitConfigModel(json_file=JsonConfigProviderConfigModel(directory_path=config_dir))
        )
        result = confit.load_config(SampleModel, provider_data={ConfigFlavor.KWARG: {"name": "from_kwarg"}})
        assert result.name == "from_kwarg"

    def test_base_data_seeded(self, config_dir: Path):
        confit = Confit(
            confit_config=ConfitConfigModel(json_file=JsonConfigProviderConfigModel(directory_path=config_dir))
        )
        result = confit.load_config(SampleModel, base_data={"value": 42})
        assert result.value == 42
