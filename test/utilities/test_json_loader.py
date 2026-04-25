import json
from pathlib import Path

import pytest

from confit.utilities.json_loader import JsonLoader


def test_loads_valid_json(tmp_path: Path):
    f = tmp_path / "data.json"
    f.write_text(json.dumps({"key": "value", "num": 42}))
    result = JsonLoader.load_json(f)
    assert result == {"key": "value", "num": 42}


def test_raises_when_file_missing(tmp_path: Path):
    missing = tmp_path / "nonexistent.json"
    with pytest.raises(ValueError, match="Failed to load JSON"):
        JsonLoader.load_json(missing)


def test_raises_on_invalid_json(tmp_path: Path):
    f = tmp_path / "bad.json"
    f.write_text("not valid json {{{")
    with pytest.raises(ValueError, match="Failed to load JSON"):
        JsonLoader.load_json(f)
