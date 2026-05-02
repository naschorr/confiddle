import pytest
from pathlib import Path

from confiddle.helpers.field_validator import FieldValidator


class TestCreateDirectoryValidator:
    def test_creates_missing_directory(self, tmp_path: Path):
        new_dir = tmp_path / "new"
        result = FieldValidator.create_directory_validator(new_dir)
        assert result == new_dir
        assert new_dir.is_dir()

    def test_creates_nested_directories(self, tmp_path: Path):
        nested = tmp_path / "a" / "b" / "c"
        FieldValidator.create_directory_validator(nested)
        assert nested.is_dir()

    def test_returns_path_when_dir_exists(self, tmp_path: Path):
        result = FieldValidator.create_directory_validator(tmp_path)
        assert result == tmp_path

    def test_raises_when_path_is_file(self, tmp_path: Path):
        f = tmp_path / "file.txt"
        f.write_text("x")
        with pytest.raises(ValueError, match="not a directory"):
            FieldValidator.create_directory_validator(f)


class TestDirectoryExistsValidator:
    def test_returns_path_when_dir_exists(self, tmp_path: Path):
        result = FieldValidator.directory_exists_validator(tmp_path)
        assert result == tmp_path

    def test_raises_when_missing(self, tmp_path: Path):
        missing = tmp_path / "missing"
        with pytest.raises(ValueError, match="does not exist"):
            FieldValidator.directory_exists_validator(missing)

    def test_raises_when_path_is_file(self, tmp_path: Path):
        f = tmp_path / "file.txt"
        f.write_text("x")
        with pytest.raises(ValueError, match="not a directory"):
            FieldValidator.directory_exists_validator(f)


class TestFileExistsValidator:
    def test_returns_path_when_file_exists(self, tmp_path: Path):
        f = tmp_path / "file.txt"
        f.write_text("x")
        result = FieldValidator.file_exists_validator(f)
        assert result == f

    def test_raises_when_missing(self, tmp_path: Path):
        missing = tmp_path / "missing.txt"
        with pytest.raises(ValueError, match="does not exist or is not a file"):
            FieldValidator.file_exists_validator(missing)

    def test_raises_when_path_is_directory(self, tmp_path: Path):
        with pytest.raises(ValueError, match="does not exist or is not a file"):
            FieldValidator.file_exists_validator(tmp_path)


class TestCoerceList:
    def test_list_is_returned_unchanged(self):
        items = [1, 2, 3]
        assert FieldValidator.coerce(list, transform=lambda v: [v])(items) is items

    def test_single_item_is_wrapped_in_list(self):
        assert FieldValidator.coerce(list, transform=lambda v: [v])(42) == [42]

    def test_single_string_is_wrapped_in_list(self):
        assert FieldValidator.coerce(list, transform=lambda v: [v])("hello") == ["hello"]

    def test_empty_list_is_returned_unchanged(self):
        assert FieldValidator.coerce(list, transform=lambda v: [v])([]) == []


class TestCoercePath:
    def test_string_is_converted_to_path(self, tmp_path: Path):
        result = FieldValidator.coerce(Path)(str(tmp_path))
        assert isinstance(result, Path)
        assert result == tmp_path

    def test_path_is_returned_as_path(self, tmp_path: Path):
        result = FieldValidator.coerce(Path)(tmp_path)
        assert isinstance(result, Path)
        assert result == tmp_path

    def test_relative_string_produces_path(self):
        result = FieldValidator.coerce(Path)(".")
        assert isinstance(result, Path)
        assert result == Path(".")


class TestCoerceDict:
    def test_dict_is_returned_unchanged(self):
        d = {"a": 1}
        assert FieldValidator.coerce(dict, transform=vars)(d) is d

    def test_transform_applied_to_non_dict(self):
        class Ns:
            def __init__(self):
                self.x = 1

        assert FieldValidator.coerce(dict, transform=vars)(Ns()) == {"x": 1}

    def test_lambda_transform_extracts_attribute(self):
        class Ctx:
            params = {"host": "localhost"}

        assert FieldValidator.coerce(dict, transform=lambda v: v.params)(Ctx()) == {"host": "localhost"}

    def test_constructor_fallback_when_no_transform(self):
        assert FieldValidator.coerce(dict)({"a": 1}) == {"a": 1}
