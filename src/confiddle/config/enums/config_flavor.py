from enum import Enum


class ConfigFlavor(str, Enum):
    """
    Enum to represent different flavors of configuration that Config can handle.
    """

    JSON = "base"
    ENV = "env"
    ARGPARSE = "argparse"
    KWARG = "kwarg"
    DICT = "dict"
