import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from confiddle.config.models.confiddle_config_model import ConfiddleConfigModel
from confiddle.config.models.providers.json_config_provider_config_model import JsonConfigProviderConfigModel
from confiddle.config.config_manager import ConfigManager


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
    path = config_dir / "config.json"
    path.write_text(json.dumps({"name": "from_file"}))
    return path


@pytest.fixture
def bootstrapped_manager(config_dir: Path) -> ConfigManager:
    (config_dir / "config.json").write_text("{}")
    (config_dir / "config.dev.json").write_text("{}")
    config_manager = ConfigManager()
    config_manager.confiddle_config = ConfiddleConfigModel(
        json_file=JsonConfigProviderConfigModel(directory_path=config_dir)
    )
    return config_manager
