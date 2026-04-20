from enum import Enum


class ConfigEnvironment(str, Enum):
    """
    Enum to represent different environments that the application can run in.
    """

    DEV = "dev"
    PROD = "prod"
    TEST = "test"
