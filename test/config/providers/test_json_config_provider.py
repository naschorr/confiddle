import json
from pathlib import Path
from typing import Optional

import pytest
from pydantic import BaseModel, ValidationError

from confit.config.enums.config_environment import ConfigEnvironment
from confit.config.enums.config_flavor import ConfigFlavor
from confit.config.providers.json_config_provider import JsonConfigProvider

## ── Setup ─────────────────────────────────────────────────────────


class FlatModel(BaseModel):
    name: str = "default"
    value: int = 0


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432


class ServiceConfig(BaseModel):
    timeout: int = 30
    retries: int = 3


class NestedModel(BaseModel):
    app_name: str = "app"
    database: DatabaseConfig = DatabaseConfig()
    service: ServiceConfig = ServiceConfig()


class DeepModel(BaseModel):
    class Level2(BaseModel):
        class Level3(BaseModel):
            value: str = "deep"

        level3: Level3 = Level3()

    level2: Level2 = Level2()


class StrictModel(BaseModel):
    count: int
    label: str


def _provider(
    tmp_path: Path,
    data: dict,
    *,
    filename: str = "config.json",
    environment: ConfigFlavor | ConfigEnvironment = ConfigFlavor.BASE
) -> JsonConfigProvider:
    f = tmp_path / filename
    f.write_text(json.dumps(data))
    return JsonConfigProvider(tmp_path / filename)


def _make(
    tmp_path: Path,
    data: dict,
    *,
    filename_template: str = "config.json",
    environment: ConfigFlavor | ConfigEnvironment = ConfigFlavor.BASE
) -> JsonConfigProvider:
    name = filename_template.format(environment=environment.value)
    (tmp_path / name).write_text(json.dumps(data))
    return JsonConfigProvider(
        FlatModel, directory_path=tmp_path, filename_template=filename_template, environment=environment
    )


## ── Flat field loading ────────────────────────────────────────────────────────


class TestFlatFields:
    def test_loads_single_field(self, tmp_path):
        p = JsonConfigProvider(
            FlatModel, directory_path=tmp_path, filename_template="config.json", environment=ConfigFlavor.BASE
        )
        (tmp_path / "config.json").write_text(json.dumps({"name": "hello"}))
        assert p.get_config()["name"] == "hello"

    def test_loads_multiple_fields(self, tmp_path):
        (tmp_path / "config.json").write_text(json.dumps({"name": "hi", "value": 42}))
        p = JsonConfigProvider(
            FlatModel, directory_path=tmp_path, filename_template="config.json", environment=ConfigFlavor.BASE
        )
        result = p.get_config()
        assert result == {"name": "hi", "value": 42}

    def test_empty_file_returns_empty_dict(self, tmp_path):
        (tmp_path / "config.json").write_text(json.dumps({}))
        p = JsonConfigProvider(
            FlatModel, directory_path=tmp_path, filename_template="config.json", environment=ConfigFlavor.BASE
        )
        assert p.get_config() == {}

    def test_raises_if_file_missing(self, tmp_path):
        p = JsonConfigProvider(
            FlatModel, directory_path=tmp_path, filename_template="missing.json", environment=ConfigFlavor.BASE
        )
        with pytest.raises(FileNotFoundError, match="does not exist"):
            p.get_config()


## ── Nested model ingest ───────────────────────────────────────────────────────


class TestNestedIngest:
    def test_nested_dict_ingested_by_model(self, tmp_path):
        data = {"database": {"host": "db.example.com", "port": 5433}}
        (tmp_path / "config.json").write_text(json.dumps(data))
        p = JsonConfigProvider(
            NestedModel, directory_path=tmp_path, filename_template="config.json", environment=ConfigFlavor.BASE
        )
        result = p.get_config()
        model = NestedModel(**result)
        assert model.database.host == "db.example.com"
        assert model.database.port == 5433

    def test_partial_nested_dict_leaves_defaults(self, tmp_path):
        data = {"database": {"host": "other-host"}}
        (tmp_path / "config.json").write_text(json.dumps(data))
        p = JsonConfigProvider(
            NestedModel, directory_path=tmp_path, filename_template="config.json", environment=ConfigFlavor.BASE
        )
        result = p.get_config()
        model = NestedModel(**result)
        assert model.database.host == "other-host"
        assert model.database.port == 5432  # default preserved

    def test_multiple_nested_sections(self, tmp_path):
        data = {
            "database": {"host": "db.prod", "port": 3306},
            "service": {"timeout": 60, "retries": 5},
        }
        (tmp_path / "config.json").write_text(json.dumps(data))
        p = JsonConfigProvider(
            NestedModel, directory_path=tmp_path, filename_template="config.json", environment=ConfigFlavor.BASE
        )
        result = p.get_config()
        model = NestedModel(**result)
        assert model.database.host == "db.prod"
        assert model.service.timeout == 60
        assert model.service.retries == 5

    def test_deeply_nested_structure(self, tmp_path):
        data = {"level2": {"level3": {"value": "found"}}}
        (tmp_path / "config.json").write_text(json.dumps(data))
        p = JsonConfigProvider(
            DeepModel, directory_path=tmp_path, filename_template="config.json", environment=ConfigFlavor.BASE
        )
        result = p.get_config()
        model = DeepModel(**result)
        assert model.level2.level3.value == "found"


## ── Environment-substituted filenames ────────────────────────────────────────


class TestFilenameTemplates:
    def test_environment_substituted_into_filename(self, tmp_path):
        (tmp_path / "config.dev.json").write_text(json.dumps({"name": "from_dev"}))
        p = JsonConfigProvider(
            FlatModel,
            directory_path=tmp_path,
            filename_template="config.{environment}.json",
            environment=ConfigEnvironment.DEV,
        )
        assert p.get_config()["name"] == "from_dev"

    def test_prod_environment_loads_prod_file(self, tmp_path):
        (tmp_path / "config.prod.json").write_text(json.dumps({"name": "from_prod"}))
        p = JsonConfigProvider(
            FlatModel,
            directory_path=tmp_path,
            filename_template="config.{environment}.json",
            environment=ConfigEnvironment.PROD,
        )
        assert p.get_config()["name"] == "from_prod"

    def test_no_placeholder_uses_same_file_for_all_envs(self, tmp_path):
        (tmp_path / "config.json").write_text(json.dumps({"name": "shared"}))
        for env in (ConfigEnvironment.DEV, ConfigEnvironment.PROD, ConfigFlavor.BASE):
            p = JsonConfigProvider(FlatModel, directory_path=tmp_path, filename_template="config.json", environment=env)
            assert p.get_config()["name"] == "shared"

    def test_file_path_resolves_correctly(self, tmp_path):
        (tmp_path / "config.base.json").write_text(json.dumps({}))
        p = JsonConfigProvider(
            FlatModel,
            directory_path=tmp_path,
            filename_template="config.{environment}.json",
            environment=ConfigFlavor.BASE,
        )
        assert p.file_path == tmp_path / "config.base.json"

    def test_file_path_for_non_base_environment_is_direct_substitution(self, tmp_path):
        # For non-BASE envs, file_path is just the substituted template - no fallback involved
        (tmp_path / "config.dev.json").write_text(json.dumps({}))
        p = JsonConfigProvider(
            FlatModel,
            directory_path=tmp_path,
            filename_template="config.{environment}.json",
            environment=ConfigEnvironment.DEV,
        )
        assert p.file_path == tmp_path / "config.dev.json"


## ── Type coercion and validation ─────────────────────────────────────────────


class TestValidation:
    def test_invalid_type_raises_on_ingest(self, tmp_path):
        # "count" must be int; passing a non-numeric string should fail model validation
        (tmp_path / "config.json").write_text(json.dumps({"count": "not-a-number", "label": "x"}))
        p = JsonConfigProvider(
            StrictModel, directory_path=tmp_path, filename_template="config.json", environment=ConfigFlavor.BASE
        )
        with pytest.raises(ValidationError):
            p.get_config()

    def test_numeric_string_coerced_to_int(self, tmp_path):
        # Pydantic v2 coerces "42" -> 42 for int fields
        (tmp_path / "config.json").write_text(json.dumps({"count": 99, "label": "y"}))
        p = JsonConfigProvider(
            StrictModel, directory_path=tmp_path, filename_template="config.json", environment=ConfigFlavor.BASE
        )
        result = p.get_config()
        model = StrictModel(**result)
        assert model.count == 99


## ── BASE fallback to plain config.json ───────────────────────────────────────


class TestBaseFallback:
    def test_loads_config_base_json_when_present(self, tmp_path):
        (tmp_path / "config.base.json").write_text(json.dumps({"name": "from_base"}))
        p = JsonConfigProvider(
            FlatModel,
            directory_path=tmp_path,
            filename_template="config.{environment}.json",
            environment=ConfigFlavor.BASE,
        )
        assert p.get_config()["name"] == "from_base"

    def test_falls_back_to_config_json_when_base_file_missing(self, tmp_path):
        (tmp_path / "config.json").write_text(json.dumps({"name": "from_fallback"}))
        p = JsonConfigProvider(
            FlatModel,
            directory_path=tmp_path,
            filename_template="config.{environment}.json",
            environment=ConfigFlavor.BASE,
        )
        assert p.get_config()["name"] == "from_fallback"

    def test_prefers_config_base_json_over_config_json(self, tmp_path):
        (tmp_path / "config.base.json").write_text(json.dumps({"name": "primary"}))
        (tmp_path / "config.json").write_text(json.dumps({"name": "fallback"}))
        p = JsonConfigProvider(
            FlatModel,
            directory_path=tmp_path,
            filename_template="config.{environment}.json",
            environment=ConfigFlavor.BASE,
        )
        assert p.get_config()["name"] == "primary"

    def test_file_path_reflects_primary_when_present(self, tmp_path):
        (tmp_path / "config.base.json").write_text(json.dumps({}))
        p = JsonConfigProvider(
            FlatModel,
            directory_path=tmp_path,
            filename_template="config.{environment}.json",
            environment=ConfigFlavor.BASE,
        )
        assert p.file_path == tmp_path / "config.base.json"

    def test_file_path_reflects_fallback_when_primary_missing(self, tmp_path):
        (tmp_path / "config.json").write_text(json.dumps({}))
        p = JsonConfigProvider(
            FlatModel,
            directory_path=tmp_path,
            filename_template="config.{environment}.json",
            environment=ConfigFlavor.BASE,
        )
        assert p.file_path == tmp_path / "config.json"

    def test_raises_when_neither_file_exists(self, tmp_path):
        p = JsonConfigProvider(
            FlatModel,
            directory_path=tmp_path,
            filename_template="config.{environment}.json",
            environment=ConfigFlavor.BASE,
        )
        with pytest.raises(FileNotFoundError):
            p.get_config()

    def test_fallback_only_applies_to_base_not_other_environments(self, tmp_path):
        # config.json exists but we're loading DEV - should not fall back to it
        (tmp_path / "config.json").write_text(json.dumps({"name": "should_not_load"}))
        p = JsonConfigProvider(
            FlatModel,
            directory_path=tmp_path,
            filename_template="config.{environment}.json",
            environment=ConfigEnvironment.DEV,
        )
        with pytest.raises(FileNotFoundError):
            p.get_config()

    def test_no_fallback_when_template_has_no_placeholder(self, tmp_path):
        # Template without {environment} resolves to the same name regardless of flavor - no special fallback logic needed or triggered
        (tmp_path / "config.json").write_text(json.dumps({"name": "static"}))
        p = JsonConfigProvider(
            FlatModel,
            directory_path=tmp_path,
            filename_template="config.json",
            environment=ConfigFlavor.BASE,
        )
        assert p.get_config()["name"] == "static"
