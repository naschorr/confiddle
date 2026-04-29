from pydantic import BaseModel

from confiddle.config.enums.merge_strategy import MergeStrategy
from confiddle.config.models.providers.argparse_config_provider_config_model import ArgparseProviderConfig
from confiddle.config.models.providers.dict_config_provider_config_model import DictProviderConfig
from confiddle.config.providers.argparse_config_provider import ArgparseConfigProvider
from confiddle.config.providers.dict_config_provider import DictConfigProvider


class SampleModel(BaseModel):
    name: str = "default"
    value: int = 0


def test_dict_provider_returns_data():
    provider = DictConfigProvider(SampleModel, DictProviderConfig(data={"name": "x"}))
    assert provider.get_config() == {"name": "x"}


def test_dict_provider_no_scope_is_shallow():
    provider = DictConfigProvider(SampleModel, DictProviderConfig(data={"name": "x"}))
    assert provider.merge_strategy is MergeStrategy.SHALLOW


def test_dict_provider_scope_wraps_data():
    class DbModel(BaseModel):
        database: dict = {}

    provider = DictConfigProvider(
        DbModel, DictProviderConfig(data={"password": "secret"}, scope="database.credentials")
    )
    assert provider.get_config() == {"database": {"credentials": {"password": "secret"}}}


def test_dict_provider_scope_is_deep():
    provider = DictConfigProvider(
        SampleModel, DictProviderConfig(data={"password": "secret"}, scope="database.credentials")
    )
    assert provider.merge_strategy is MergeStrategy.DEEP


def test_argparse_provider_wraps_dict():
    provider = ArgparseConfigProvider(SampleModel, ArgparseProviderConfig(args={"name": "x"}))
    assert provider.get_config() == {"name": "x"}


def test_argparse_provider_wraps_namespace():
    import argparse

    ns = argparse.Namespace(name="x")
    provider = ArgparseConfigProvider(SampleModel, ArgparseProviderConfig(args=ns))
    assert provider.get_config() == {"name": "x"}


def test_argparse_provider_is_shallow():
    provider = ArgparseConfigProvider(SampleModel, ArgparseProviderConfig(args={"name": "x"}))
    assert provider.merge_strategy is MergeStrategy.SHALLOW
