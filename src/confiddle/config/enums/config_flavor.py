from enum import Enum


class ConfigFlavor(str, Enum):
    """
    Enum to represent different flavors of configuration that Config can handle.
    """

    JSON = "base"
    ENV_VAR = "env_var"
    ARGPARSE = "argparse"
    KWARG = "kwarg"
    DICT = "dict"
