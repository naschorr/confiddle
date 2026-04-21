import pytest
from pydantic import BaseModel, ValidationError

from config.providers.env_var_config_provider import EnvVarConfigProvider


class SampleModel(BaseModel):
    name: str = "default"
    db: dict = {}


def test_reads_prefixed_vars(monkeypatch):
    monkeypatch.setenv("MYAPP:NAME", "foo")
    provider = EnvVarConfigProvider(SampleModel, env_var_prefix="MYAPP", env_var_delimiter=":")
    assert provider.get_config() == {"name": "foo"}


def test_lowercase_keys(monkeypatch):
    monkeypatch.setenv("MYAPP:NAME", "foo")
    provider = EnvVarConfigProvider(SampleModel, env_var_prefix="MYAPP", env_var_delimiter=":")
    result = provider.get_config()
    assert "name" in result
    assert "NAME" not in result


def test_nested_keys(monkeypatch):
    monkeypatch.setenv("MYAPP:DB:HOST", "localhost")
    provider = EnvVarConfigProvider(SampleModel, env_var_prefix="MYAPP", env_var_delimiter=":")
    result = provider.get_config()
    assert result == {"db": {"host": "localhost"}}


def test_ignores_non_prefixed(monkeypatch):
    monkeypatch.setenv("OTHER:NAME", "should_be_ignored")
    monkeypatch.setenv("MYAPP:NAME", "correct")
    provider = EnvVarConfigProvider(SampleModel, env_var_prefix="MYAPP", env_var_delimiter=":")
    result = provider.get_config()
    assert result == {"name": "correct"}


def test_no_prefix_includes_all(monkeypatch):
    monkeypatch.setenv("NAME", "noprefix")
    provider = EnvVarConfigProvider(SampleModel, env_var_prefix=None, env_var_delimiter=":")
    result = provider.get_config()
    assert "name" in result


def test_empty_result_when_no_matching_vars(monkeypatch):
    # Clear any MYAPP-prefixed vars that might exist
    for key in list(__import__("os").environ.keys()):
        if key.startswith("MYAPP"):
            monkeypatch.delenv(key, raising=False)
    provider = EnvVarConfigProvider(SampleModel, env_var_prefix="MYAPP", env_var_delimiter=":")
    assert provider.get_config() == {}
