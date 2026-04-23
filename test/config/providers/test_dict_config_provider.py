from pydantic import BaseModel

from config.providers.argparse_config_provider import ArgparseConfigProvider
from config.providers.dict_config_provider import DictConfigProvider
from config.providers.kwarg_config_provider import KwargConfigProvider


class SampleModel(BaseModel):
    name: str = "default"
    value: int = 0


def test_dict_provider_returns_data():
    provider = DictConfigProvider(SampleModel, {"name": "x"})
    assert provider.get_config() == {"name": "x"}


def test_kwarg_provider_wraps_kwargs():
    provider = KwargConfigProvider(SampleModel, name="x")
    assert provider.get_config() == {"name": "x"}


def test_argparse_provider_wraps_dict():
    provider = ArgparseConfigProvider(SampleModel, {"name": "x"})
    assert provider.get_config() == {"name": "x"}
