import json
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from confiddle.config.enums.config_environment import ConfigEnvironment
from confiddle.config.models.providers.json_provider_config import JsonProviderConfig
from confiddle.config.providers.json_provider import JsonProvider

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


## ── Flat field loading ────────────────────────────────────────────────────────


class TestFlatFields:
    def test_loads_single_field(self, tmp_path):
        (tmp_path / "config.json").write_text(json.dumps({"name": "hello"}))
        p = JsonProvider(
            FlatModel,
            JsonProviderConfig(directory_path=tmp_path, filename_template="config.json"),
        )
        assert p.get_config()["name"] == "hello"

    def test_loads_multiple_fields(self, tmp_path):
        (tmp_path / "config.json").write_text(json.dumps({"name": "hi", "value": 42}))
        p = JsonProvider(
            FlatModel,
            JsonProviderConfig(directory_path=tmp_path, filename_template="config.json"),
        )
        result = p.get_config()
        assert result == {"name": "hi", "value": 42}

    def test_empty_file_returns_empty_dict(self, tmp_path):
        (tmp_path / "config.json").write_text(json.dumps({}))
        p = JsonProvider(
            FlatModel,
            JsonProviderConfig(directory_path=tmp_path, filename_template="config.json"),
        )
        assert p.get_config() == {}

    def test_raises_if_file_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="does not exist"):
            JsonProvider(
                FlatModel,
                JsonProviderConfig(directory_path=tmp_path, filename_template="missing.json"),
            )


## ── Nested model ingest ───────────────────────────────────────────────────────


class TestNestedIngest:
    def test_nested_dict_ingested_by_model(self, tmp_path):
        data = {"database": {"host": "db.example.com", "port": 5433}}
        (tmp_path / "config.json").write_text(json.dumps(data))
        p = JsonProvider(
            NestedModel,
            JsonProviderConfig(directory_path=tmp_path, filename_template="config.json"),
        )
        result = p.get_config()
        model = NestedModel(**result)
        assert model.database.host == "db.example.com"
        assert model.database.port == 5433

    def test_partial_nested_dict_leaves_defaults(self, tmp_path):
        data = {"database": {"host": "other-host"}}
        (tmp_path / "config.json").write_text(json.dumps(data))
        p = JsonProvider(
            NestedModel,
            JsonProviderConfig(directory_path=tmp_path, filename_template="config.json"),
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
        p = JsonProvider(
            NestedModel,
            JsonProviderConfig(directory_path=tmp_path, filename_template="config.json"),
        )
        result = p.get_config()
        model = NestedModel(**result)
        assert model.database.host == "db.prod"
        assert model.service.timeout == 60
        assert model.service.retries == 5

    def test_deeply_nested_structure(self, tmp_path):
        data = {"level2": {"level3": {"value": "found"}}}
        (tmp_path / "config.json").write_text(json.dumps(data))
        p = JsonProvider(
            DeepModel,
            JsonProviderConfig(directory_path=tmp_path, filename_template="config.json"),
        )
        result = p.get_config()
        model = DeepModel(**result)
        assert model.level2.level3.value == "found"


## ── Environment-substituted filenames ────────────────────────────────────────


class TestFilenameTemplates:
    def test_environment_substituted_into_filename(self, tmp_path):
        (tmp_path / "config.dev.json").write_text(json.dumps({"name": "from_dev"}))
        p = JsonProvider(
            FlatModel,
            JsonProviderConfig(
                directory_path=tmp_path,
                filename_template="config.{environment}.json",
                environment=ConfigEnvironment.DEV,
            ),
        )
        assert p.get_config()["name"] == "from_dev"

    def test_prod_environment_loads_prod_file(self, tmp_path):
        (tmp_path / "config.prod.json").write_text(json.dumps({"name": "from_prod"}))
        p = JsonProvider(
            FlatModel,
            JsonProviderConfig(
                directory_path=tmp_path,
                filename_template="config.{environment}.json",
                environment=ConfigEnvironment.PROD,
            ),
        )
        assert p.get_config()["name"] == "from_prod"

    def test_no_placeholder_uses_same_file_for_all_envs(self, tmp_path):
        (tmp_path / "config.json").write_text(json.dumps({"name": "shared"}))
        for env in (None, ConfigEnvironment.DEV, ConfigEnvironment.PROD):
            p = JsonProvider(
                FlatModel,
                JsonProviderConfig(
                    directory_path=tmp_path,
                    filename_template="config.json",
                    environment=env,
                ),
            )
            assert p.get_config()["name"] == "shared"

    def test_file_path_resolves_correctly(self, tmp_path):
        (tmp_path / "config.json").write_text(json.dumps({}))
        p = JsonProvider(
            FlatModel,
            JsonProviderConfig(directory_path=tmp_path, filename_template="config.{environment}.json"),
        )
        assert p.file_path == tmp_path / "config.json"

    def test_file_path_for_non_base_environment_is_direct_substitution(self, tmp_path):
        # For non-BASE envs, file_path is just the substituted template - no fallback involved
        (tmp_path / "config.dev.json").write_text(json.dumps({}))
        p = JsonProvider(
            FlatModel,
            JsonProviderConfig(
                directory_path=tmp_path,
                filename_template="config.{environment}.json",
                environment=ConfigEnvironment.DEV,
            ),
        )
        assert p.file_path == tmp_path / "config.dev.json"

    def test_missing_env_file_returns_empty_dict(self, tmp_path):
        # env-specific file is optional — missing file is a no-op, not an error
        p = JsonProvider(
            FlatModel,
            JsonProviderConfig(
                directory_path=tmp_path,
                filename_template="config.{environment}.json",
                environment=ConfigEnvironment.DEV,
            ),
        )
        assert p.get_config() == {}


## ── Type coercion and validation ─────────────────────────────────────────────


class TestValidation:
    def test_invalid_type_raises_on_ingest(self, tmp_path):
        # "count" must be int; passing a non-numeric string should fail model validation
        (tmp_path / "config.json").write_text(json.dumps({"count": "not-a-number", "label": "x"}))
        p = JsonProvider(
            StrictModel,
            JsonProviderConfig(directory_path=tmp_path, filename_template="config.json"),
        )
        with pytest.raises(ValidationError):
            p.get_config()

    def test_numeric_string_coerced_to_int(self, tmp_path):
        # Pydantic v2 coerces "42" -> 42 for int fields
        (tmp_path / "config.json").write_text(json.dumps({"count": 99, "label": "y"}))
        p = JsonProvider(
            StrictModel,
            JsonProviderConfig(directory_path=tmp_path, filename_template="config.json"),
        )
        result = p.get_config()
        model = StrictModel(**result)
        assert model.count == 99
