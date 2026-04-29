from enum import Enum


class MergeStrategy(str, Enum):
    """
    Controls how a configuration provider's output is merged into the accumulated configuration.
    """

    SHALLOW = "shallow"
    DEEP = "deep"
