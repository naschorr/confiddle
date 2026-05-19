import os
from typing import Annotated, Literal, Union

import pytest
from pydantic import BaseModel, Field

from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.models.providers.env_var_provider_config import EnvVarProviderConfig
from confiddle.config.providers.env_var_provider import EnvVarProvider

## ── Setup ─────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    """Replace os.environ with an empty dict so tests only see vars they explicitly set."""
    monkeypatch.setattr(os, "environ", {})


class FlatModel(BaseModel):
    name: str = "default"
    db: dict = {}


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    credentials: dict = {}


class ServiceConfig(BaseModel):
    timeout: int = 30
    retries: int = 3


class NestedModel(BaseModel):
    app_name: str = "app"
    database: DatabaseConfig = DatabaseConfig()
    service: ServiceConfig = ServiceConfig()


## ── Prefix and filtering ──────────────────────────────────────────────────────


class TestPrefixFiltering:
    def test_reads_prefixed_var(self, monkeypatch):
        monkeypatch.setenv("MYAPP:NAME", "foo")
        result = EnvVarProvider(FlatModel, EnvVarProviderConfig(prefix="MYAPP", delimiter=":")).get_config()
        assert result == {"name": "foo"}

    def test_ignores_non_prefixed_vars(self, monkeypatch):
        monkeypatch.setenv("OTHER:NAME", "ignored")
        monkeypatch.setenv("MYAPP:NAME", "correct")
        result = EnvVarProvider(FlatModel, EnvVarProviderConfig(prefix="MYAPP", delimiter=":")).get_config()
        assert result == {"name": "correct"}

    def test_no_prefix_includes_all_vars(self, monkeypatch):
        monkeypatch.setenv("NAME", "noprefix")
        result = EnvVarProvider(FlatModel, EnvVarProviderConfig(prefix=None, delimiter=":")).get_config()
        assert result == {"name": "noprefix"}

    def test_empty_result_when_no_matching_vars(self, monkeypatch):
        for key in list(__import__("os").environ.keys()):
            if key.startswith("MYAPP"):
                monkeypatch.delenv(key, raising=False)
        result = EnvVarProvider(FlatModel, EnvVarProviderConfig(prefix="MYAPP", delimiter=":")).get_config()
        assert result == {}

    def test_prefix_consumed_from_key(self, monkeypatch):
        monkeypatch.setenv("APP:NAME", "bar")
        result = EnvVarProvider(FlatModel, EnvVarProviderConfig(prefix="APP", delimiter=":")).get_config()
        assert result == {"name": "bar"}
        assert "app" not in result

    def test_ignores_vars_with_longer_prefix_match(self, monkeypatch):
        # "APP" prefix must not match "APPSETTINGS", "APPLICATIONINSIGHTS", etc.
        monkeypatch.setenv("APPSETTINGS_DB", "should_be_ignored")
        monkeypatch.setenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "should_be_ignored")
        monkeypatch.setenv("APP:NAME", "correct")
        result = EnvVarProvider(FlatModel, EnvVarProviderConfig(prefix="APP", delimiter=":")).get_config()
        assert result == {"name": "correct"}


## ── Key normalisation ─────────────────────────────────────────────────────────


class TestKeyNormalisation:
    def test_keys_lowercased(self, monkeypatch):
        monkeypatch.setenv("MYAPP:NAME", "x")
        result = EnvVarProvider(FlatModel, EnvVarProviderConfig(prefix="MYAPP", delimiter=":")).get_config()
        assert "name" in result
        assert "NAME" not in result

    def test_leading_delimiter_stripped(self, monkeypatch):
        # env var is PREFIX:KEY - after removing prefix ":KEY" has a leading delimiter
        monkeypatch.setenv("MYAPP:NAME", "stripped")
        result = EnvVarProvider(FlatModel, EnvVarProviderConfig(prefix="MYAPP", delimiter=":")).get_config()
        assert result == {"name": "stripped"}


## ── Nesting ───────────────────────────────────────────────────────────────────


class TestNesting:
    def test_single_level_nesting(self, monkeypatch):
        monkeypatch.setenv("MYAPP:DB:HOST", "db.local")
        result = EnvVarProvider(FlatModel, EnvVarProviderConfig(prefix="MYAPP", delimiter=":")).get_config()
        assert result == {"db": {"host": "db.local"}}

    def test_two_sibling_nested_keys(self, monkeypatch):
        monkeypatch.setenv("MYAPP:DATABASE:HOST", "db.local")
        monkeypatch.setenv("MYAPP:DATABASE:PORT", "5433")
        result = EnvVarProvider(NestedModel, EnvVarProviderConfig(prefix="MYAPP", delimiter=":")).get_config()
        assert result["database"] == {"host": "db.local", "port": "5433"}

    def test_multiple_top_level_nested_sections(self, monkeypatch):
        monkeypatch.setenv("APP:DATABASE:HOST", "prod-db")
        monkeypatch.setenv("APP:DATABASE:PORT", "3306")
        monkeypatch.setenv("APP:SERVICE:TIMEOUT", "60")
        monkeypatch.setenv("APP:SERVICE:RETRIES", "5")
        result = EnvVarProvider(NestedModel, EnvVarProviderConfig(prefix="APP", delimiter=":")).get_config()
        assert result["database"]["host"] == "prod-db"
        assert result["database"]["port"] == "3306"
        assert result["service"]["timeout"] == "60"
        assert result["service"]["retries"] == "5"

    def test_three_level_deep_nesting(self, monkeypatch):
        monkeypatch.setenv("APP:DATABASE:CREDENTIALS:PASSWORD", "secret")
        result = EnvVarProvider(NestedModel, EnvVarProviderConfig(prefix="APP", delimiter=":")).get_config()
        assert result["database"]["credentials"]["password"] == "secret"

    def test_double_underscore_delimiter(self, monkeypatch):
        monkeypatch.setenv("APP__DATABASE__HOST", "dunder-host")
        result = EnvVarProvider(NestedModel, EnvVarProviderConfig(prefix="APP", delimiter="__")).get_config()
        assert result["database"]["host"] == "dunder-host"

    def test_double_underscore_three_levels(self, monkeypatch):
        monkeypatch.setenv("APP__DATABASE__CREDENTIALS__PASSWORD", "pw")
        result = EnvVarProvider(NestedModel, EnvVarProviderConfig(prefix="APP", delimiter="__")).get_config()
        assert result["database"]["credentials"]["password"] == "pw"

    def test_mixed_flat_and_nested(self, monkeypatch):
        monkeypatch.setenv("APP:APP_NAME", "myservice")
        monkeypatch.setenv("APP:DATABASE:HOST", "db.io")
        result = EnvVarProvider(NestedModel, EnvVarProviderConfig(prefix="APP", delimiter=":")).get_config()
        assert result["app_name"] == "myservice"
        assert result["database"]["host"] == "db.io"


## ── Full ingest round-trip ────────────────────────────────────────────────────


class TestIngestRoundTrip:
    def test_flat_values_round_trip(self, monkeypatch):
        monkeypatch.setenv("APP:APP_NAME", "roundtrip")
        monkeypatch.setenv("APP:DATABASE__HOST", "db")  # wrong delimiter - should not parse
        result = EnvVarProvider(NestedModel, EnvVarProviderConfig(prefix="APP", delimiter=":")).get_config()
        model = NestedModel(**result)
        assert model.app_name == "roundtrip"

    def test_nested_values_round_trip_into_model(self, monkeypatch):
        monkeypatch.setenv("APP:DATABASE:HOST", "db.prod")
        monkeypatch.setenv("APP:DATABASE:PORT", "5433")
        monkeypatch.setenv("APP:SERVICE:TIMEOUT", "90")
        result = EnvVarProvider(NestedModel, EnvVarProviderConfig(prefix="APP", delimiter=":")).get_config()
        model = NestedModel(**result)
        assert model.database.host == "db.prod"
        assert model.database.port == 5433  # Pydantic coerces "5433" str -> int
        assert model.service.timeout == 90


## ── Schema-aware ingest ───────────────────────────────────────────────────────


class TestSchemaAwareIngest:
    def test_flat_string_for_nested_model_field_is_ignored(self, monkeypatch):
        # DATABASE is a DatabaseConfig (BaseModel) field - a raw string can't populate it
        monkeypatch.setenv("APP:DATABASE", "flat-string")
        result = EnvVarProvider(NestedModel, EnvVarProviderConfig(prefix="APP", delimiter=":")).get_config()
        assert "database" not in result

    def test_nested_path_for_nested_model_field_still_works(self, monkeypatch):
        monkeypatch.setenv("APP:DATABASE:HOST", "db.io")
        result = EnvVarProvider(NestedModel, EnvVarProviderConfig(prefix="APP", delimiter=":")).get_config()
        assert result["database"]["host"] == "db.io"

    def test_collision_flat_and_nested_same_key_does_not_crash(self, monkeypatch):
        # The flat var must be silently discarded; the nested var must survive
        monkeypatch.setenv("APP:DATABASE", "flat-string")
        monkeypatch.setenv("APP:DATABASE:HOST", "db.io")
        result = EnvVarProvider(NestedModel, EnvVarProviderConfig(prefix="APP", delimiter=":")).get_config()
        assert result["database"]["host"] == "db.io"

    def test_nested_path_for_primitive_field_is_ignored(self, monkeypatch):
        # app_name is a str - a deeper path like APP:APP_NAME:EXTRA should be silently dropped
        monkeypatch.setenv("APP:APP_NAME:EXTRA", "value")
        result = EnvVarProvider(NestedModel, EnvVarProviderConfig(prefix="APP", delimiter=":")).get_config()
        assert "app_name" not in result

    def test_flat_value_for_primitive_field_still_works(self, monkeypatch):
        monkeypatch.setenv("APP:APP_NAME", "myapp")
        result = EnvVarProvider(NestedModel, EnvVarProviderConfig(prefix="APP", delimiter=":")).get_config()
        assert result["app_name"] == "myapp"

    def test_dict_field_still_builds_nested_dict_from_env_vars(self, monkeypatch):
        # db: dict - env vars should build a nested dict as before
        monkeypatch.setenv("MYAPP:DB:HOST", "db.local")
        result = EnvVarProvider(FlatModel, EnvVarProviderConfig(prefix="MYAPP", delimiter=":")).get_config()
        assert result["db"] == {"host": "db.local"}


class TestConfigFlavor:
    def test_env_var_provider_config_flavor_is_env_var(self):
        config = EnvVarProviderConfig(prefix="APP")
        assert config.config_flavor is ConfigFlavor.ENV_VAR


## ── List of objects ───────────────────────────────────────────────────────────


class ItemConfig(BaseModel):
    id: str
    name: str = "default"


class TagsConfig(BaseModel):
    label: str


class ItemWithListConfig(BaseModel):
    id: str
    tags: list[TagsConfig] = []


class ListContainerModel(BaseModel):
    items: list[ItemConfig] = []


class NestedListModel(BaseModel):
    items: list[ItemWithListConfig] = []


class TestListOfObjects:
    def test_single_item_in_list(self, monkeypatch):
        monkeypatch.setenv("APP__ITEMS__0__ID", "item1")
        result = EnvVarProvider(ListContainerModel, EnvVarProviderConfig(prefix="APP", delimiter="__")).get_config()
        assert result == {"items": [{"id": "item1"}]}

    def test_single_item_with_multiple_fields(self, monkeypatch):
        monkeypatch.setenv("APP__ITEMS__0__ID", "item1")
        monkeypatch.setenv("APP__ITEMS__0__NAME", "Item One")
        result = EnvVarProvider(ListContainerModel, EnvVarProviderConfig(prefix="APP", delimiter="__")).get_config()
        assert result == {"items": [{"id": "item1", "name": "Item One"}]}

    def test_multiple_items_in_list(self, monkeypatch):
        monkeypatch.setenv("APP__ITEMS__0__ID", "first")
        monkeypatch.setenv("APP__ITEMS__1__ID", "second")
        result = EnvVarProvider(ListContainerModel, EnvVarProviderConfig(prefix="APP", delimiter="__")).get_config()
        assert result["items"] == [{"id": "first"}, {"id": "second"}]

    def test_list_items_ordered_by_index(self, monkeypatch):
        monkeypatch.setenv("APP__ITEMS__1__ID", "second")
        monkeypatch.setenv("APP__ITEMS__0__ID", "first")
        result = EnvVarProvider(ListContainerModel, EnvVarProviderConfig(prefix="APP", delimiter="__")).get_config()
        assert result["items"][0] == {"id": "first"}
        assert result["items"][1] == {"id": "second"}

    def test_nested_list_inside_list_item(self, monkeypatch):
        monkeypatch.setenv("APP__ITEMS__0__ID", "item1")
        monkeypatch.setenv("APP__ITEMS__0__TAGS__0__LABEL", "urgent")
        result = EnvVarProvider(NestedListModel, EnvVarProviderConfig(prefix="APP", delimiter="__")).get_config()
        assert result == {"items": [{"id": "item1", "tags": [{"label": "urgent"}]}]}

    def test_list_result_is_python_list_not_dict(self, monkeypatch):
        monkeypatch.setenv("APP__ITEMS__0__ID", "item1")
        result = EnvVarProvider(ListContainerModel, EnvVarProviderConfig(prefix="APP", delimiter="__")).get_config()
        assert isinstance(result["items"], list)

    def test_dict_field_with_digit_keys_is_not_converted_to_list(self, monkeypatch):
        # FlatModel.db is typed as dict, not list - digit keys must not trigger list conversion
        monkeypatch.setenv("MYAPP__DB__0", "first")
        monkeypatch.setenv("MYAPP__DB__1", "second")
        result = EnvVarProvider(FlatModel, EnvVarProviderConfig(prefix="MYAPP", delimiter="__")).get_config()
        assert isinstance(result["db"], dict)
        assert result["db"] == {"0": "first", "1": "second"}


## ── List with Annotated/discriminated-union element type ─────────────────────


class CpuVariant(BaseModel):
    flavor: Literal["cpu"] = "cpu"
    id: str
    fans: list[str] = []


# Mirrors a Pydantic discriminated union: Annotated[Union[CpuVariant], Field(discriminator="flavor")]
AnnotatedSensorConfig = Annotated[Union[CpuVariant], Field(discriminator="flavor")]


class SensorContainerModel(BaseModel):
    sensors: list[AnnotatedSensorConfig] = []


class TestAnnotatedListElement:
    def test_primitive_list_inside_annotated_element_is_converted(self, monkeypatch):
        # sensors[0].fans is list[str]; fans__0 must become ["primary"], not {"0": "primary"}
        monkeypatch.setenv("APP__SENSORS__0__ID", "cpu")
        monkeypatch.setenv("APP__SENSORS__0__FLAVOR", "cpu")
        monkeypatch.setenv("APP__SENSORS__0__FANS__0", "primary")
        result = EnvVarProvider(
            SensorContainerModel, EnvVarProviderConfig(prefix="APP", delimiter="__")
        ).get_config()
        assert result["sensors"][0]["fans"] == ["primary"]

    def test_annotated_element_fields_survive_conversion(self, monkeypatch):
        monkeypatch.setenv("APP__SENSORS__0__ID", "cpu")
        monkeypatch.setenv("APP__SENSORS__0__FLAVOR", "cpu")
        result = EnvVarProvider(
            SensorContainerModel, EnvVarProviderConfig(prefix="APP", delimiter="__")
        ).get_config()
        assert result["sensors"][0]["id"] == "cpu"
        assert result["sensors"][0]["flavor"] == "cpu"
