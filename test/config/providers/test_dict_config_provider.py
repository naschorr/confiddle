from pydantic import BaseModel

from confiddle.config.enums.merge_strategy import MergeStrategy
from confiddle.config.models.providers.argparse_provider_config import ArgparseProviderConfig
from confiddle.config.models.providers.dict_provider_config import DictProviderConfig
from confiddle.config.providers.argparse_provider import ArgparseProvider
from confiddle.config.providers.dict_provider import DictProvider


class SampleModel(BaseModel):
    name: str = "default"
    value: int = 0


def test_dict_provider_returns_data():
    provider = DictProvider(SampleModel, DictProviderConfig(data={"name": "x"}))
    assert provider.get_config() == {"name": "x"}


def test_dict_provider_no_scope_is_shallow():
    provider = DictProvider(SampleModel, DictProviderConfig(data={"name": "x"}))
    assert provider.merge_strategy is MergeStrategy.SHALLOW


def test_dict_provider_scope_wraps_data():
    class DbModel(BaseModel):
        database: dict = {}

    provider = DictProvider(DbModel, DictProviderConfig(data={"password": "secret"}, scope="database.credentials"))
    assert provider.get_config() == {"database": {"credentials": {"password": "secret"}}}


def test_dict_provider_scope_is_deep():
    provider = DictProvider(SampleModel, DictProviderConfig(data={"password": "secret"}, scope="database.credentials"))
    assert provider.merge_strategy is MergeStrategy.DEEP


def test_argparse_provider_wraps_dict():
    provider = ArgparseProvider(SampleModel, ArgparseProviderConfig(args={"name": "x"}))
    assert provider.get_config() == {"name": "x"}


def test_argparse_provider_wraps_namespace():
    import argparse

    ns = argparse.Namespace(name="x")
    provider = ArgparseProvider(SampleModel, ArgparseProviderConfig(args=ns))
    assert provider.get_config() == {"name": "x"}


def test_argparse_provider_is_shallow():
    provider = ArgparseProvider(SampleModel, ArgparseProviderConfig(args={"name": "x"}))
    assert provider.merge_strategy is MergeStrategy.SHALLOW
