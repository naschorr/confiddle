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
