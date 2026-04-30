from enum import Enum


class ConfigEnvironment(str, Enum):
    """
    Enum to represent different environments that the application can run in.
    """

    DEV = "dev"
    TEST = "test"
    PROD = "prod"
