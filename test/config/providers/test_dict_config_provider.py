from pydantic import BaseModel

from confiddle.config.enums.merge_strategy import MergeStrategy
from confiddle.config.providers.argparse_config_provider import ArgparseConfigProvider
from confiddle.config.providers.dict_config_provider import DictConfigProvider
from confiddle.config.providers.kwarg_config_provider import KwargConfigProvider


class SampleModel(BaseModel):
    name: str = "default"
    value: int = 0


def test_dict_provider_returns_data():
    provider = DictConfigProvider(SampleModel, {"name": "x"})
    assert provider.get_config() == {"name": "x"}


def test_dict_provider_no_scope_is_shallow():
    provider = DictConfigProvider(SampleModel, {"name": "x"})
    assert provider.merge_strategy is MergeStrategy.SHALLOW


def test_dict_provider_scope_wraps_data():
    class DbModel(BaseModel):
        database: dict = {}

    provider = DictConfigProvider(DbModel, {"password": "secret"}, scope="database.credentials")
    assert provider.get_config() == {"database": {"credentials": {"password": "secret"}}}


def test_dict_provider_scope_is_deep():
    provider = DictConfigProvider(SampleModel, {"password": "secret"}, scope="database.credentials")
    assert provider.merge_strategy is MergeStrategy.DEEP


def test_kwarg_provider_wraps_kwargs():
    provider = KwargConfigProvider(SampleModel, name="x")
    assert provider.get_config() == {"name": "x"}


def test_kwarg_provider_is_shallow():
    provider = KwargConfigProvider(SampleModel, name="x")
    assert provider.merge_strategy is MergeStrategy.SHALLOW


def test_argparse_provider_wraps_dict():
    provider = ArgparseConfigProvider(SampleModel, {"name": "x"})
    assert provider.get_config() == {"name": "x"}


def test_argparse_provider_wraps_namespace():
    import argparse

    ns = argparse.Namespace(name="x")
    provider = ArgparseConfigProvider(SampleModel, ns)
    assert provider.get_config() == {"name": "x"}


def test_argparse_provider_is_shallow():
    provider = ArgparseConfigProvider(SampleModel, {"name": "x"})
    assert provider.merge_strategy is MergeStrategy.SHALLOW
