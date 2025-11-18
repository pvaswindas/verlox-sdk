import os
from enum import Enum

config = os.getenv


class EnvironmentOption(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class AppSettings:
    APP_NAME: str = "verlox"
    ENDPOINT: str | None = None
    API_KEY: str | None = None
    API_SECRET: str | None = None
    SERVICE_NAME: str | None = None
    ENVIRONMENT: str = EnvironmentOption.DEVELOPMENT


class Settings(
    AppSettings,
):
    pass


settings = Settings()
