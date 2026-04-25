import pytest
from pydantic import BaseModel, ValidationError

from confit.helpers.model_validator import ModelValidator


class SampleModel(BaseModel):
    name: str
    value: int = 0


def test_valid_partial_passes():
    ModelValidator.validate_partial_model(SampleModel, {"name": "x"})


def test_empty_dict_passes():
    ModelValidator.validate_partial_model(SampleModel, {})


def test_unknown_field_ignored():
    ModelValidator.validate_partial_model(SampleModel, {"unknown": "field"})


def test_wrong_type_raises():
    with pytest.raises(ValidationError):
        ModelValidator.validate_partial_model(SampleModel, {"value": "not_an_int"})


def test_subset_of_fields_passes():
    ModelValidator.validate_partial_model(SampleModel, {"value": 42})
