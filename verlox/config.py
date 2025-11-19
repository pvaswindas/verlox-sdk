from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env from the application, not SDK
load_dotenv()

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
