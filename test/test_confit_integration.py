"""
Integration tests for Confit end-to-end configuration loading.

These tests exercise the full pipeline: Confit -> ConfigManager -> providers -> model.
Each test controls the hierarchy explicitly so only the intended providers participate.
"""

import json
import os
from pathlib import Path

import pytest
from pydantic import BaseModel

from config.enums.config_environment import ConfigEnvironment
from config.enums.config_flavor import ConfigFlavor
from config.models.confit_config_model import ConfitConfigModel
from config.models.providers.env_var_config_provider_config_model import EnvVarConfigProviderConfigModel
from config.models.providers.json_config_provider_config_model import JsonConfigProviderConfigModel
from confit import Confit


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


def _confit(*, tmp_path: Path = None, hierarchy: list, env_prefix: str = "APP", env_delimiter: str = ":") -> Confit:
    """Build a Confit instance with an explicit hierarchy and no bootstrap side-effects."""
    return Confit(
        confit_config=ConfitConfigModel(
            json_file=(
                JsonConfigProviderConfigModel(
                    directory_path=tmp_path,
                    filename_template="config.{environment}.json",
                )
                if tmp_path
                else JsonConfigProviderConfigModel()
            ),
            env_var=EnvVarConfigProviderConfigModel(prefix=env_prefix, delimiter=env_delimiter),
            hierarchy=hierarchy,
        )
    )


## ── Single provider ────────────────────────────────────────────────────────────


class TestSingleProvider:
    """Confit with one provider in the hierarchy loads only from that source."""

    def test_json_base_only_loads_from_file(self, tmp_path: Path):
        _write_json(tmp_path / "config.base.json", {"host": "file-host", "port": 9000})
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.BASE])
        result = confit.load_config(AppConfig)
        assert result.host == "file-host"
        assert result.port == 9000

    def test_json_base_falls_back_to_plain_config_json(self, tmp_path: Path):
        # No config.base.json — should fall back to config.json end-to-end
        _write_json(tmp_path / "config.json", {"host": "fallback-host", "port": 7070})
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.BASE])
        result = confit.load_config(AppConfig)
        assert result.host == "fallback-host"
        assert result.port == 7070

    def test_env_only_loads_from_env_vars(self, monkeypatch):
        monkeypatch.setenv("APP:HOST", "env-host")
        monkeypatch.setenv("APP:PORT", "7000")
        confit = _confit(hierarchy=[ConfigFlavor.ENV])
        result = confit.load_config(AppConfig)
        assert result.host == "env-host"
        assert result.port == 7000

    def test_kwarg_only_loads_from_kwargs(self, tmp_path: Path):
        # JSON file exists but should be ignored
        _write_json(tmp_path / "config.base.json", {"host": "should-be-ignored"})
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.KWARG])
        result = confit.load_config(AppConfig, provider_data={ConfigFlavor.KWARG: {"host": "kwarg-host"}})
        assert result.host == "kwarg-host"

    def test_argparse_only_loads_from_argparse_data(self):
        confit = _confit(hierarchy=[ConfigFlavor.ARGPARSE])
        result = confit.load_config(AppConfig, provider_data={ConfigFlavor.ARGPARSE: {"port": 1234}})
        assert result.port == 1234
        assert result.host == "localhost"  # default - no other source

    def test_single_provider_falls_back_to_model_defaults_when_no_data(self, tmp_path: Path):
        # File does not contain all fields - missing fields use model defaults
        _write_json(tmp_path / "config.base.json", {"host": "only-host"})
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.BASE])
        result = confit.load_config(AppConfig)
        assert result.host == "only-host"
        assert result.port == 8080  # default
        assert result.debug is False  # default


## ── Disabled providers ─────────────────────────────────────────────────────────


class TestDisabledProviders:
    """Data that could be loaded by a provider is ignored when that provider is not in the hierarchy."""

    def test_env_vars_ignored_when_env_not_in_hierarchy(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("APP:HOST", "env-host")
        _write_json(tmp_path / "config.base.json", {"host": "file-host"})
        # ENV not in hierarchy - env var must not reach the model
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.BASE])
        result = confit.load_config(AppConfig)
        assert result.host == "file-host"

    def test_json_file_ignored_when_base_not_in_hierarchy(self, tmp_path: Path, monkeypatch):
        _write_json(tmp_path / "config.base.json", {"host": "file-host"})
        monkeypatch.setenv("APP:HOST", "env-host")
        # BASE not in hierarchy - the JSON file must not be read
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.ENV])
        result = confit.load_config(AppConfig)
        assert result.host == "env-host"

    def test_kwarg_data_ignored_when_kwarg_not_in_hierarchy(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("APP:HOST", "env-host")
        # KWARG not in hierarchy - kwarg data passed to load_config must be ignored
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.ENV])
        result = confit.load_config(AppConfig, provider_data={ConfigFlavor.KWARG: {"host": "kwarg-host"}})
        assert result.host == "env-host"

    def test_missing_kwarg_data_does_not_error_when_kwarg_in_hierarchy(self, tmp_path: Path):
        # KWARG is in hierarchy but no provider_data supplied - should be silently skipped
        _write_json(tmp_path / "config.base.json", {"host": "file-host"})
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.BASE, ConfigFlavor.KWARG])
        result = confit.load_config(AppConfig)
        assert result.host == "file-host"

    def test_missing_json_file_silently_skipped(self, tmp_path: Path, monkeypatch):
        # directory_path set but no file written - JSON provider silently skipped
        monkeypatch.setenv("APP:HOST", "env-host")
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.BASE, ConfigFlavor.ENV])
        result = confit.load_config(AppConfig)
        assert result.host == "env-host"

    def test_env_specific_file_ignored_when_environment_differs(self, tmp_path: Path):
        # File for PROD exists but environment is DEV -> skip
        _write_json(tmp_path / "config.prod.json", {"host": "prod-host"})
        confit = Confit(
            confit_config=ConfitConfigModel(
                json_file=JsonConfigProviderConfigModel(
                    directory_path=tmp_path,
                    filename_template="config.{environment}.json",
                ),
                environment=ConfigEnvironment.DEV,
                hierarchy=[ConfigEnvironment.PROD],
            )
        )
        result = confit.load_config(AppConfig)
        assert result.host == "localhost"  # default - PROD file not loaded


## ── Multi-provider with override ordering ──────────────────────────────────────


class TestMultiProviderOrdering:
    """Later providers in the hierarchy win when the same key is present in multiple sources."""

    def test_kwarg_overrides_json(self, tmp_path: Path):
        _write_json(tmp_path / "config.base.json", {"host": "file-host", "port": 9000})
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.BASE, ConfigFlavor.KWARG])
        result = confit.load_config(AppConfig, provider_data={ConfigFlavor.KWARG: {"host": "kwarg-host"}})
        assert result.host == "kwarg-host"
        assert result.port == 9000  # from JSON - kwarg did not supply it

    def test_env_overrides_json(self, tmp_path: Path, monkeypatch):
        _write_json(tmp_path / "config.base.json", {"host": "file-host", "port": 9000})
        monkeypatch.setenv("APP:HOST", "env-host")
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.BASE, ConfigFlavor.ENV])
        result = confit.load_config(AppConfig)
        assert result.host == "env-host"
        assert result.port == 9000  # from JSON - env did not supply it

    def test_kwarg_overrides_env_overrides_json(self, tmp_path: Path, monkeypatch):
        _write_json(tmp_path / "config.base.json", {"host": "file-host", "port": 9000, "debug": False})
        monkeypatch.setenv("APP:HOST", "env-host")
        monkeypatch.setenv("APP:PORT", "7777")
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.BASE, ConfigFlavor.ENV, ConfigFlavor.KWARG])
        result = confit.load_config(
            AppConfig, provider_data={ConfigFlavor.KWARG: {"host": "kwarg-host", "debug": True}}
        )
        assert result.host == "kwarg-host"  # kwarg wins
        assert result.port == 7777  # env wins over json
        assert result.debug is True  # kwarg wins

    def test_json_base_then_env_environment_file(self, tmp_path: Path, monkeypatch):
        _write_json(tmp_path / "config.base.json", {"host": "base-host", "port": 8080})
        _write_json(tmp_path / "config.dev.json", {"port": 9999})
        confit = Confit(
            confit_config=ConfitConfigModel(
                json_file=JsonConfigProviderConfigModel(
                    directory_path=tmp_path,
                    filename_template="config.{environment}.json",
                ),
                environment=ConfigEnvironment.DEV,
                hierarchy=[ConfigFlavor.BASE, ConfigEnvironment.DEV],
            )
        )
        result = confit.load_config(AppConfig)
        assert result.host == "base-host"  # from base file
        assert result.port == 9999  # dev file overrides


## ── Nested model configuration ─────────────────────────────────────────────────


class TestNestedConfig:
    """Complex nested models loaded across multiple providers."""

    def test_nested_config_from_json_only(self, tmp_path: Path):
        _write_json(
            tmp_path / "config.base.json",
            {
                "app": {"host": "app-host", "port": 443},
                "database": {"host": "db-host", "port": 5433, "name": "prod"},
            },
        )
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.BASE])
        result = confit.load_config(FullConfig)
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
        confit = _confit(hierarchy=[ConfigFlavor.ENV])
        result = confit.load_config(FullConfig)
        assert result.app.host == "env-app-host"
        assert result.app.port == 5000
        assert result.database.host == "env-db-host"
        assert result.service.timeout == 90

    def test_nested_json_base_overridden_by_kwargs(self, tmp_path: Path):
        _write_json(
            tmp_path / "config.base.json",
            {
                "app": {"host": "base-host", "port": 8080},
                "database": {"host": "base-db", "port": 5432, "name": "base_db"},
                "service": {"timeout": 30, "retries": 3},
            },
        )
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.BASE, ConfigFlavor.KWARG])
        # kwarg replaces the entire `app` top-level key (shallow merge)
        result = confit.load_config(
            FullConfig,
            provider_data={ConfigFlavor.KWARG: {"app": {"host": "override-host", "port": 9090, "debug": True}}},
        )
        assert result.app.host == "override-host"
        assert result.app.port == 9090
        assert result.app.debug is True
        # database and service untouched by kwarg
        assert result.database.host == "base-db"
        assert result.service.retries == 3

    def test_shallow_merge_replaces_entire_nested_section(self, tmp_path: Path):
        """
        Merging is shallow: if two providers both supply the same top-level key,
        the later provider's value replaces the earlier one entirely - sub-keys
        from the earlier provider that the later one omits are lost.
        """
        _write_json(
            tmp_path / "config.base.json",
            {"database": {"host": "base-host", "port": 5432, "name": "important-db"}},
        )
        # kwarg only supplies `host` - `port` and `name` from the JSON are discarded
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.BASE, ConfigFlavor.KWARG])
        result = confit.load_config(
            FullConfig,
            provider_data={ConfigFlavor.KWARG: {"database": {"host": "kwarg-host"}}},
        )
        assert result.database.host == "kwarg-host"
        assert result.database.port == 5432  # DatabaseConfig model default - NOT the JSON value
        assert result.database.name == "db"  # DatabaseConfig model default - NOT "important-db"

    def test_three_providers_build_complete_nested_config(self, tmp_path: Path, monkeypatch):
        # JSON sets the database section
        _write_json(tmp_path / "config.base.json", {"database": {"host": "db-host", "port": 5432, "name": "mydb"}})
        # Env vars set the service section
        monkeypatch.setenv("APP:SERVICE:TIMEOUT", "120")
        monkeypatch.setenv("APP:SERVICE:RETRIES", "5")
        # Kwargs set the app section
        confit = _confit(tmp_path=tmp_path, hierarchy=[ConfigFlavor.BASE, ConfigFlavor.ENV, ConfigFlavor.KWARG])
        result = confit.load_config(
            FullConfig,
            provider_data={ConfigFlavor.KWARG: {"app": {"host": "kwarg-host", "port": 443, "debug": True}}},
        )
        assert result.database.host == "db-host"  # from JSON
        assert result.database.name == "mydb"
        assert result.service.timeout == 120  # from env
        assert result.service.retries == 5
        assert result.app.host == "kwarg-host"  # from kwargs
        assert result.app.debug is True
