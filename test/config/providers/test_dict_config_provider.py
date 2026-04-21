from pydantic import BaseModel

from config.providers.argparse_config_provider import ArgparseConfigProvider
from config.providers.dict_config_provider import DictConfigProvider
from config.providers.kwarg_config_provider import KwargConfigProvider


class SampleModel(BaseModel):
    name: str = "default"
    value: int = 0


def test_returns_dict():
    provider = DictConfigProvider(SampleModel, {"name": "x"})
    assert provider.get_config() == {"name": "x"}


def test_passes_through_unknown_field():
    result = DictConfigProvider(SampleModel, {"unknown": "field"}).get_config()
    assert result == {"unknown": "field"}


def test_kwarg_provider_wraps_kwargs():
    provider = KwargConfigProvider(SampleModel, name="x")
    assert provider.get_config() == {"name": "x"}


def test_argparse_provider_wraps_dict():
    provider = ArgparseConfigProvider(SampleModel, {"name": "x"})
    assert provider.get_config() == {"name": "x"}


def test_empty_dict_returns_empty():
    provider = DictConfigProvider(SampleModel, {})
    assert provider.get_config() == {}
