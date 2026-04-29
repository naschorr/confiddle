from confiddle.utilities.dict_merger import DictMerger


def test_deep_merge_top_level_keys():
    result = DictMerger.deep_merge({"a": 1}, {"b": 2})
    assert result == {"a": 1, "b": 2}


def test_deep_merge_override_wins_for_scalar():
    result = DictMerger.deep_merge({"a": 1}, {"a": 2})
    assert result == {"a": 2}


def test_deep_merge_nested_dicts_combined():
    result = DictMerger.deep_merge({"a": {"x": 1, "y": 2}}, {"a": {"y": 99, "z": 3}})
    assert result == {"a": {"x": 1, "y": 99, "z": 3}}


def test_deep_merge_recursive():
    result = DictMerger.deep_merge({"a": {"b": {"c": 1}}}, {"a": {"b": {"d": 2}}})
    assert result == {"a": {"b": {"c": 1, "d": 2}}}


def test_deep_merge_does_not_mutate_base():
    base = {"a": {"x": 1}}
    DictMerger.deep_merge(base, {"a": {"y": 2}})
    assert base == {"a": {"x": 1}}


def test_deep_merge_empty_override():
    result = DictMerger.deep_merge({"a": 1}, {})
    assert result == {"a": 1}


def test_deep_merge_empty_base():
    result = DictMerger.deep_merge({}, {"a": 1})
    assert result == {"a": 1}
