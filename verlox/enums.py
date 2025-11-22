from enum import StrEnum


class Environment(StrEnum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    SANDBOX = "sandbox"
    PRODUCTION = "production"
