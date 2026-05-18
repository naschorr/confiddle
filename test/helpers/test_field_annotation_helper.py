from typing import Optional

import pytest
from pydantic import BaseModel

from confiddle.helpers.field_annotation_helper import get_list_element_annotation, is_container_annotation


class Inner(BaseModel):
    id: str
    value: int = 0


## ── is_container_annotation ──────────────────────────────────────────────────


class TestIsContainerAnnotationExistingBehavior:
    def test_base_model_subclass_is_container(self):
        assert is_container_annotation(Inner) is True

    def test_dict_is_container(self):
        assert is_container_annotation(dict) is True

    def test_str_is_not_container(self):
        assert is_container_annotation(str) is False

    def test_int_is_not_container(self):
        assert is_container_annotation(int) is False

    def test_float_is_not_container(self):
        assert is_container_annotation(float) is False


class TestIsContainerAnnotationListSupport:
    def test_list_of_base_model_is_container(self):
        assert is_container_annotation(list[Inner]) is True

    def test_list_of_str_is_not_container(self):
        assert is_container_annotation(list[str]) is False

    def test_list_of_int_is_not_container(self):
        assert is_container_annotation(list[int]) is False

    def test_optional_list_of_base_model_is_container(self):
        assert is_container_annotation(Optional[list[Inner]]) is True

    def test_optional_list_of_str_is_not_container(self):
        assert is_container_annotation(Optional[list[str]]) is False


## ── get_list_element_annotation ──────────────────────────────────────────────


class TestGetListElementAnnotation:
    def test_returns_element_type_for_list_of_base_model(self):
        assert get_list_element_annotation(list[Inner]) is Inner

    def test_returns_element_type_for_list_of_str(self):
        assert get_list_element_annotation(list[str]) is str

    def test_returns_none_for_plain_base_model(self):
        assert get_list_element_annotation(Inner) is None

    def test_returns_none_for_str(self):
        assert get_list_element_annotation(str) is None

    def test_unwraps_optional_list(self):
        assert get_list_element_annotation(Optional[list[Inner]]) is Inner
