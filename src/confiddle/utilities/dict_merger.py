class DictMerger:
    """
    Utility class for merging dictionaries.
    """

    @staticmethod
    def deep_merge(base: dict, override: dict) -> dict:
        """
        Recursively merge ``override`` into ``base``. When both sides contain a dict at the same key, the dicts are
        merged. Otherwise the value from ``override`` wins.
        """
        result = dict(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DictMerger.deep_merge(result[key], value)
            else:
                result[key] = value
        return result
