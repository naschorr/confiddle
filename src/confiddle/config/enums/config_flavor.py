from enum import Enum


class ConfigFlavor(str, Enum):
    """
    Enum to represent different flavors of configuration that Config can handle.
    """

    ARGPARSE = "argparse"
    CLICK = "click"
    DICT = "dict"
    ENV_VAR = "env_var"
    JSON = "json"
    JSON_ENV = "json_env"
