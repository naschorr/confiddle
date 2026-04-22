import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from config.enums.config_flavor import ConfigFlavor
from config.providers.json_config_provider import JsonConfigProvider


class SampleModel(BaseModel):
    name: str = "default"
    value: int = 0


def test_loads_valid_json(tmp_path: Path):
    f = tmp_path / "config.json"
    f.write_text(json.dumps({"name": "from_file"}))
    provider = JsonConfigProvider(
        SampleModel, directory_path=tmp_path, filename_template="config.json", environment=ConfigFlavor.BASE
    )
    assert provider.get_config() == {"name": "from_file"}


def test_raises_if_file_missing(tmp_path: Path):
    provider = JsonConfigProvider(
        SampleModel, directory_path=tmp_path, filename_template="nonexistent.json", environment=ConfigFlavor.BASE
    )
    with pytest.raises(AssertionError):
        provider.get_config()


def test_passes_through_unknown_field(tmp_path: Path):
    f = tmp_path / "config.json"
    f.write_text(json.dumps({"unknown_key": "extra"}))
    provider = JsonConfigProvider(
        SampleModel, directory_path=tmp_path, filename_template="config.json", environment=ConfigFlavor.BASE
    )
    result = provider.get_config()
    assert result == {"unknown_key": "extra"}


def test_loads_partial_fields(tmp_path: Path):
    f = tmp_path / "config.json"
    f.write_text(json.dumps({"name": "partial"}))
    provider = JsonConfigProvider(
        SampleModel, directory_path=tmp_path, filename_template="config.json", environment=ConfigFlavor.BASE
    )
    result = provider.get_config()
    assert result["name"] == "partial"
    assert "value" not in result
