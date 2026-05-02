"""
Integration tests for Confiddle end-to-end configuration loading.

These tests exercise the full pipeline: Confiddle -> ConfigManager -> providers -> model.
Each test controls the hierarchy explicitly so only the intended providers participate.
"""

import json
import os
from pathlib import Path

import pytest
from pydantic import BaseModel

from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.models.confiddle_config_model import ConfiddleConfigModel
from confiddle.config.models.provider_config_model import ProviderConfigModel
from confiddle.config.models.providers.env_var_provider_config import EnvVarProviderConfig
from confiddle.config.models.providers.json_provider_config import JsonProviderConfig
from confiddle import Confiddle, ArgparseProviderConfig, DictProviderConfig


## ── Models ─────────────────────────────────────────────────────────────────────


class AppConfig(BaseModel):
    host: str = "localhost"
    port: int = 8080
    debug: bool = False


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "db"


class ServiceConfig(BaseModel):
    timeout: int = 30
    retries: int = 3


class FullConfig(BaseModel):
    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    service: ServiceConfig = ServiceConfig()


## ── Helpers ────────────────────────────────────────────────────────────────────


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def _confiddle(
    *, tmp_path: Path = None, hierarchy: list, env_prefix: str = "APP", env_delimiter: str = ":"
) -> Confiddle:
    """Build a Confiddle instance with an explicit hierarchy and no bootstrap side-effects."""
    return Confiddle(
        confiddle_config=ConfiddleConfigModel(
            app=ProviderConfigModel(
                json_file_provider=(
                    [
                        JsonProviderConfig(
                            directory_path=tmp_path,
                            filename_template="config.{environment}.json",
                        )
                    ]
                    if tmp_path
                    else []
                ),
                env_var_provider=[EnvVarProviderConfig(prefix=env_prefix, delimiter=env_delimiter)],
            ),
            hierarchy=hierarchy,
        )
    )


## ── Single provider ────────────────────────────────────────────────────────────


class TestSingleProvider:
    """Confiddle with one provider in the hierarchy loads only from that source."""

    def test_json_base_only_loads_from_file(self, tmp_path: Path):
        _write_json(tmp_path / "config.json", {"host": "file-host", "port": 9000})
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.JSON])
        result = confiddle.load_config(AppConfig)
        assert result.host == "file-host"
        assert result.port == 9000

    def test_env_only_loads_from_env_vars(self, monkeypatch):
        monkeypatch.setenv("APP:HOST", "env-host")
        monkeypatch.setenv("APP:PORT", "7000")
        confiddle = _confiddle(hierarchy=[ConfigFlavor.ENV_VAR])
        result = confiddle.load_config(AppConfig)
        assert result.host == "env-host"
        assert result.port == 7000

    def test_dict_only_loads_from_dict(self, tmp_path: Path):
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.DICT])
        result = confiddle.load_config(AppConfig, provider_configs=[DictProviderConfig(data={"host": "dict-host"})])
        assert result.host == "dict-host"

    def test_argparse_only_loads_from_argparse_data(self):
        confiddle = _confiddle(hierarchy=[ConfigFlavor.ARGPARSE])
        result = confiddle.load_config(AppConfig, provider_configs=[ArgparseProviderConfig(args={"port": 1234})])
        assert result.port == 1234
        assert result.host == "localhost"  # default - no other source

    def test_single_provider_falls_back_to_model_defaults_when_no_data(self, tmp_path: Path):
        # File does not contain all fields - missing fields use model defaults
        _write_json(tmp_path / "config.json", {"host": "only-host"})
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.JSON])
        result = confiddle.load_config(AppConfig)
        assert result.host == "only-host"
        assert result.port == 8080  # default
        assert result.debug is False  # default


## ── Argparse ───────────────────────────────────────────────────────────────────


class TestArgparse:
    """End-to-end tests for the argparse provider using stdlib argparse -> ArgparseProviderConfig."""

    def _parse(self, argv: list[str]):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--host", default=None)
        parser.add_argument("--port", type=int, default=None)
        parser.add_argument("--debug", action="store_true", default=None)
        return parser.parse_args(argv)

    def test_argparse_values_loaded_into_model(self):
        confiddle = _confiddle(hierarchy=[ConfigFlavor.ARGPARSE])
        result = confiddle.load_config(
            AppConfig,
            provider_configs=[ArgparseProviderConfig(args=self._parse(["--host", "cli-host", "--port", "1234"]))],
        )
        assert result.host == "cli-host"
        assert result.port == 1234

    def test_argparse_overrides_json(self, tmp_path: Path):
        _write_json(tmp_path / "config.json", {"host": "file-host", "port": 9000})
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.JSON, ConfigFlavor.ARGPARSE])
        result = confiddle.load_config(
            AppConfig, provider_configs=[ArgparseProviderConfig(args=self._parse(["--host", "cli-host"]))]
        )
        assert result.host == "cli-host"
        assert result.port == 9000  # from JSON - argparse did not supply it

    def test_argparse_and_dict_both_present_dict_wins(self, tmp_path: Path):
        # ARGPARSE before DICT in hierarchy - dict should win
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.ARGPARSE, ConfigFlavor.DICT])
        result = confiddle.load_config(
            AppConfig,
            provider_configs=[
                ArgparseProviderConfig(args=self._parse(["--host", "cli-host"])),
                DictProviderConfig(data={"host": "dict-host"}),
            ],
        )
        assert result.host == "dict-host"

    def test_missing_argparse_data_silently_skipped(self, tmp_path: Path):
        # ARGPARSE in hierarchy but no providers supplied - should not error
        _write_json(tmp_path / "config.json", {"host": "file-host"})
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.JSON, ConfigFlavor.ARGPARSE])
        result = confiddle.load_config(AppConfig)
        assert result.host == "file-host"

    def test_unknown_argparse_keys_filtered_out(self):
        confiddle = _confiddle(hierarchy=[ConfigFlavor.ARGPARSE])
        result = confiddle.load_config(
            AppConfig, provider_configs=[ArgparseProviderConfig(args={"host": "h", "unrecognised": "x"})]
        )
        assert result.host == "h"
        assert not hasattr(result, "unrecognised")


## ── Disabled providers ─────────────────────────────────────────────────────────


class TestDisabledProviders:
    """Data that could be loaded by a provider is ignored when that provider is not in the hierarchy."""

    def test_env_vars_ignored_when_env_not_in_hierarchy(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("APP:HOST", "env-host")
        _write_json(tmp_path / "config.json", {"host": "file-host"})
        # ENV not in hierarchy - env var must not reach the model
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.JSON])
        result = confiddle.load_config(AppConfig)
        assert result.host == "file-host"

    def test_json_file_ignored_when_base_not_in_hierarchy(self, tmp_path: Path, monkeypatch):
        _write_json(tmp_path / "config.json", {"host": "file-host"})
        monkeypatch.setenv("APP:HOST", "env-host")
        # BASE not in hierarchy - the JSON file must not be read
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.ENV_VAR])
        result = confiddle.load_config(AppConfig)
        assert result.host == "env-host"

    def test_dict_data_ignored_when_dict_not_in_hierarchy(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("APP:HOST", "env-host")
        # DICT not in hierarchy - dict data passed to load_config must be ignored
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.ENV_VAR])
        result = confiddle.load_config(AppConfig, provider_configs=[DictProviderConfig(data={"host": "dict-host"})])
        assert result.host == "env-host"

    def test_missing_dict_data_does_not_error_when_dict_in_hierarchy(self, tmp_path: Path):
        # DICT is in hierarchy but no providers supplied - should be silently skipped
        _write_json(tmp_path / "config.json", {"host": "file-host"})
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.JSON, ConfigFlavor.DICT])
        result = confiddle.load_config(AppConfig)
        assert result.host == "file-host"

    def test_raises_when_json_file_missing(self, tmp_path: Path):
        # directory_path set but no file written - FileNotFoundError raised
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.JSON])
        with pytest.raises(FileNotFoundError):
            confiddle.load_config(AppConfig)

    def test_env_specific_file_ignored_when_environment_differs(self, tmp_path: Path):
        # File for PROD exists but environment is DEV -> skip
        _write_json(tmp_path / "config.prod.json", {"host": "prod-host"})
        confiddle = Confiddle(
            confiddle_config=ConfiddleConfigModel(
                app=ProviderConfigModel(
                    json_file_provider=[
                        JsonProviderConfig(
                            directory_path=tmp_path,
                            filename_template="config.{environment}.json",
                        )
                    ],
                ),
                environment=ConfigEnvironment.DEV,
                hierarchy=[ConfigFlavor.JSON_ENV],
            )
        )
        result = confiddle.load_config(AppConfig)
        assert result.host == "localhost"  # default - PROD file not loaded


## ── Multi-provider with override ordering ──────────────────────────────────────


class TestMultiProviderOrdering:
    """Later providers in the hierarchy win when the same key is present in multiple sources."""

    def test_dict_overrides_json(self, tmp_path: Path):
        _write_json(tmp_path / "config.json", {"host": "file-host", "port": 9000})
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.JSON, ConfigFlavor.DICT])
        result = confiddle.load_config(AppConfig, provider_configs=[DictProviderConfig(data={"host": "dict-host"})])
        assert result.host == "dict-host"
        assert result.port == 9000  # from JSON - dict did not supply it

    def test_env_overrides_json(self, tmp_path: Path, monkeypatch):
        _write_json(tmp_path / "config.json", {"host": "file-host", "port": 9000})
        monkeypatch.setenv("APP:HOST", "env-host")
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.JSON, ConfigFlavor.ENV_VAR])
        result = confiddle.load_config(AppConfig)
        assert result.host == "env-host"
        assert result.port == 9000  # from JSON - env did not supply it

    def test_dict_overrides_env_overrides_json(self, tmp_path: Path, monkeypatch):
        _write_json(tmp_path / "config.json", {"host": "file-host", "port": 9000, "debug": False})
        monkeypatch.setenv("APP:HOST", "env-host")
        monkeypatch.setenv("APP:PORT", "7777")
        confiddle = _confiddle(
            tmp_path=tmp_path, hierarchy=[ConfigFlavor.JSON, ConfigFlavor.ENV_VAR, ConfigFlavor.DICT]
        )
        result = confiddle.load_config(
            AppConfig, provider_configs=[DictProviderConfig(data={"host": "dict-host", "debug": True})]
        )
        assert result.host == "dict-host"  # dict wins
        assert result.port == 7777  # env wins over json
        assert result.debug is True  # dict wins

    def test_json_base_then_env_environment_file(self, tmp_path: Path, monkeypatch):
        _write_json(tmp_path / "config.json", {"host": "base-host", "port": 8080})
        _write_json(tmp_path / "config.dev.json", {"port": 9999})
        confiddle = Confiddle(
            confiddle_config=ConfiddleConfigModel(
                app=ProviderConfigModel(
                    json_file_provider=[
                        JsonProviderConfig(
                            directory_path=tmp_path,
                            filename_template="config.{environment}.json",
                        )
                    ],
                ),
                environment=ConfigEnvironment.DEV,
                hierarchy=[ConfigFlavor.JSON, ConfigFlavor.JSON_ENV],
            )
        )
        result = confiddle.load_config(AppConfig)
        assert result.host == "base-host"  # from base file
        assert result.port == 9999  # dev file overrides


## ── Nested model configuration ─────────────────────────────────────────────────


class TestNestedConfig:
    """Complex nested models loaded across multiple providers."""

    def test_nested_config_from_json_only(self, tmp_path: Path):
        _write_json(
            tmp_path / "config.json",
            {
                "app": {"host": "app-host", "port": 443},
                "database": {"host": "db-host", "port": 5433, "name": "prod"},
            },
        )
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.JSON])
        result = confiddle.load_config(FullConfig)
        assert result.app.host == "app-host"
        assert result.app.port == 443
        assert result.database.host == "db-host"
        assert result.database.name == "prod"
        assert result.service.timeout == 30  # default

    def test_nested_config_from_env_only(self, monkeypatch):
        monkeypatch.setenv("APP:APP:HOST", "env-app-host")
        monkeypatch.setenv("APP:APP:PORT", "5000")
        monkeypatch.setenv("APP:DATABASE:HOST", "env-db-host")
        monkeypatch.setenv("APP:SERVICE:TIMEOUT", "90")
        confiddle = _confiddle(hierarchy=[ConfigFlavor.ENV_VAR])
        result = confiddle.load_config(FullConfig)
        assert result.app.host == "env-app-host"
        assert result.app.port == 5000
        assert result.database.host == "env-db-host"
        assert result.service.timeout == 90

    def test_nested_json_base_overridden_by_dict(self, tmp_path: Path):
        _write_json(
            tmp_path / "config.json",
            {
                "app": {"host": "base-host", "port": 8080},
                "database": {"host": "base-db", "port": 5432, "name": "base_db"},
                "service": {"timeout": 30, "retries": 3},
            },
        )
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.JSON, ConfigFlavor.DICT])
        # dict replaces the entire `app` top-level key (shallow merge)
        result = confiddle.load_config(
            FullConfig,
            provider_configs=[DictProviderConfig(data={"app": {"host": "override-host", "port": 9090, "debug": True}})],
        )
        assert result.app.host == "override-host"
        assert result.app.port == 9090
        assert result.app.debug is True
        # database and service untouched by dict
        assert result.database.host == "base-db"
        assert result.service.retries == 3

    def test_shallow_merge_replaces_entire_nested_section(self, tmp_path: Path):
        """
        Merging is shallow: if two providers both supply the same top-level key,
        the later provider's value replaces the earlier one entirely - sub-keys
        from the earlier provider that the later one omits are lost.
        """
        _write_json(
            tmp_path / "config.json",
            {"database": {"host": "base-host", "port": 5432, "name": "important-db"}},
        )
        # dict only supplies `host` - `port` and `name` from the JSON are discarded
        confiddle = _confiddle(tmp_path=tmp_path, hierarchy=[ConfigFlavor.JSON, ConfigFlavor.DICT])
        result = confiddle.load_config(
            FullConfig,
            provider_configs=[DictProviderConfig(data={"database": {"host": "dict-host"}})],
        )
        assert result.database.host == "dict-host"
        assert result.database.port == 5432  # DatabaseConfig model default - NOT the JSON value
        assert result.database.name == "db"  # DatabaseConfig model default - NOT "important-db"

    def test_three_providers_build_complete_nested_config(self, tmp_path: Path, monkeypatch):
        # JSON sets the database section
        _write_json(tmp_path / "config.json", {"database": {"host": "db-host", "port": 5432, "name": "mydb"}})
        # Env vars set the service section
        monkeypatch.setenv("APP:SERVICE:TIMEOUT", "120")
        monkeypatch.setenv("APP:SERVICE:RETRIES", "5")
        # Dict sets the app section
        confiddle = _confiddle(
            tmp_path=tmp_path, hierarchy=[ConfigFlavor.JSON, ConfigFlavor.ENV_VAR, ConfigFlavor.DICT]
        )
        result = confiddle.load_config(
            FullConfig,
            provider_configs=[DictProviderConfig(data={"app": {"host": "dict-host", "port": 443, "debug": True}})],
        )
        assert result.database.host == "db-host"  # from JSON
        assert result.database.name == "mydb"
        assert result.service.timeout == 120  # from env
        assert result.service.retries == 5
        assert result.app.host == "dict-host"  # from dict
        assert result.app.debug is True
