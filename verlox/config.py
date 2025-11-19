from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)


class VerloxSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="VERLOX_",
    )

    APP_NAME: str
    ENDPOINT: str
    API_KEY: str
    API_SECRET: str
    SERVICE_NAME: str
    ENVIRONMENT: str


settings = VerloxSettings()
