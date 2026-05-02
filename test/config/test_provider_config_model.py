from pathlib import Path

import pytest

from confiddle.config.models.provider_config_model import ProviderConfigModel
from confiddle.config.models.providers.argparse_provider_config import ArgparseProviderConfig
from confiddle.config.models.providers.dict_provider_config import DictProviderConfig
from confiddle.config.models.providers.env_var_provider_config import EnvVarProviderConfig
from confiddle.config.models.providers.json_provider_config import JsonProviderConfig


## ── Helpers ───────────────────────────────────────────────────────────────────


def _json(tmp_path: Path) -> JsonProviderConfig:
    (tmp_path / "config.json").write_text("{}")
    return JsonProviderConfig(directory_path=tmp_path)


## ── Single instance coercion ──────────────────────────────────────────────────


class TestSingleInstanceCoercion:
    """A single provider instance (not wrapped in a list) is accepted and stored as a one-element list."""

    def test_argparse_single_instance(self):
        argparse_config = ArgparseProviderConfig()
        model = ProviderConfigModel(argparse_provider=argparse_config)
        assert model.argparse_provider == [argparse_config]

    def test_dict_single_instance(self):
        dict_config = DictProviderConfig(data={"key": "value"})
        model = ProviderConfigModel(dict_provider=dict_config)
        assert model.dict_provider == [dict_config]

    def test_env_var_single_instance(self):
        env_var_config = EnvVarProviderConfig(prefix="APP")
        model = ProviderConfigModel(env_var_provider=env_var_config)
        assert model.env_var_provider == [env_var_config]

    def test_json_file_single_instance(self, tmp_path: Path):
        json_config = _json(tmp_path)
        model = ProviderConfigModel(json_file_provider=json_config)
        assert model.json_file_provider == [json_config]


## ── List form unchanged ───────────────────────────────────────────────────────


class TestListFormUnchanged:
    """Passing a list works exactly as before."""

    def test_argparse_list(self):
        argparse_config = ArgparseProviderConfig()
        model = ProviderConfigModel(argparse_provider=[argparse_config])
        assert model.argparse_provider == [argparse_config]

    def test_dict_list(self):
        dict_config = DictProviderConfig()
        model = ProviderConfigModel(dict_provider=[dict_config])
        assert model.dict_provider == [dict_config]

    def test_env_var_list(self):
        env_var_config = EnvVarProviderConfig()
        model = ProviderConfigModel(env_var_provider=[env_var_config])
        assert model.env_var_provider == [env_var_config]

    def test_json_file_list(self, tmp_path: Path):
        json_config = _json(tmp_path)
        model = ProviderConfigModel(json_file_provider=[json_config])
        assert model.json_file_provider == [json_config]

    def test_multiple_items_in_list_preserved(self, tmp_path: Path):
        first_dict_config = DictProviderConfig(data={"a": 1})
        second_dict_config = DictProviderConfig(data={"b": 2})
        model = ProviderConfigModel(dict_provider=[first_dict_config, second_dict_config])
        assert model.dict_provider == [first_dict_config, second_dict_config]


## ── Empty / default ───────────────────────────────────────────────────────────


class TestDefaults:
    def test_all_providers_default_to_empty_list(self):
        model = ProviderConfigModel()
        assert model.argparse_provider == []
        assert model.dict_provider == []
        assert model.env_var_provider == []
        assert model.json_file_provider == []
