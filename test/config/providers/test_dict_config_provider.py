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


def test_unknown_keys_filtered_out():
    result = DictConfigProvider(SampleModel, {"unknown": "field"}).get_config()
    assert result == {}


def test_kwarg_provider_wraps_kwargs():
    provider = KwargConfigProvider(SampleModel, name="x")
    assert provider.get_config() == {"name": "x"}


def test_kwarg_unknown_keys_filtered_out():
    result = KwargConfigProvider(SampleModel, unknown="field").get_config()
    assert result == {}


def test_argparse_provider_wraps_dict():
    provider = ArgparseConfigProvider(SampleModel, {"name": "x"})
    assert provider.get_config() == {"name": "x"}


def test_argparse_unknown_keys_filtered_out():
    result = ArgparseConfigProvider(SampleModel, {"unknown": "field"}).get_config()
    assert result == {}


def test_empty_dict_returns_empty():
    provider = DictConfigProvider(SampleModel, {})
    assert provider.get_config() == {}
