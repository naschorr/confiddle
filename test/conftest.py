import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from config.models.confit_config_model import ConfitConfigModel
from config.config_manager import ConfigManager


class SampleModel(BaseModel):
    name: str = "default"
    value: int = 0


@pytest.fixture
def sample_model():
    return SampleModel


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def config_file(config_dir: Path) -> Path:
    path = config_dir / "config.base.json"
    path.write_text(json.dumps({"name": "from_file"}))
    return path


@pytest.fixture
def bootstrapped_manager(config_dir: Path) -> ConfigManager:
    config_manager = ConfigManager()
    config_manager.confit_config = ConfitConfigModel(config_directory=config_dir)
    return config_manager
