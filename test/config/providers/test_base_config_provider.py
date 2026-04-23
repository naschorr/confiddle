import pytest
from pydantic import BaseModel, ValidationError

from config.providers.base_config_provider import BaseConfigProvider


## ── Stub ───────────────────────────────────────────────────────────────────────


class _StubProvider(BaseConfigProvider):
    """Minimal concrete subclass that returns a pre-set dict from _get_raw_config."""

    def __init__(self, model, raw_data: dict):
        super().__init__(model)
        self._raw_data = raw_data

    def _get_raw_config(self) -> dict:
        return self._raw_data


## ── Models ─────────────────────────────────────────────────────────────────────


class SampleModel(BaseModel):
    name: str = "default"
    value: int = 0


class StrictModel(BaseModel):
    count: int
    label: str


## ── Template method ────────────────────────────────────────────────────────────


class TestTemplateMethod:
    def test_get_config_returns_raw_config_data(self):
        result = _StubProvider(SampleModel, {"name": "hello"}).get_config()
        assert result["name"] == "hello"

    def test_get_config_chains_through_build_result(self):
        # Unknown keys from _get_raw_config must be stripped by the time get_config returns
        result = _StubProvider(SampleModel, {"name": "x", "unknown": "y"}).get_config()
        assert "unknown" not in result
        assert result["name"] == "x"

    def test_get_config_empty_raw_returns_empty(self):
        assert _StubProvider(SampleModel, {}).get_config() == {}


## ── Field filtering ────────────────────────────────────────────────────────────


class TestFieldFiltering:
    def test_unknown_keys_are_filtered_out(self):
        result = _StubProvider(SampleModel, {"extra": "ignored"}).get_config()
        assert result == {}

    def test_known_keys_are_kept(self):
        result = _StubProvider(SampleModel, {"name": "kept", "value": 1}).get_config()
        assert result == {"name": "kept", "value": 1}

    def test_mix_of_known_and_unknown_keys(self):
        result = _StubProvider(SampleModel, {"name": "kept", "unknown": "gone"}).get_config()
        assert result == {"name": "kept"}
        assert "unknown" not in result

    def test_only_unknown_keys_returns_empty_dict(self):
        result = _StubProvider(SampleModel, {"foo": "bar", "baz": 99}).get_config()
        assert result == {}


## ── Validation ─────────────────────────────────────────────────────────────────


class TestValidation:
    def test_invalid_type_raises_validation_error(self):
        with pytest.raises(ValidationError):
            _StubProvider(StrictModel, {"count": "not-a-number", "label": "ok"}).get_config()

    def test_valid_data_does_not_raise(self):
        result = _StubProvider(StrictModel, {"count": 1, "label": "ok"}).get_config()
        assert result == {"count": 1, "label": "ok"}

    def test_partial_data_does_not_raise_when_fields_have_defaults(self):
        result = _StubProvider(SampleModel, {"name": "partial"}).get_config()
        assert result == {"name": "partial"}
