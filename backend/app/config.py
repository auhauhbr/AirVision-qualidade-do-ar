from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    openaq_api_key: str | None = Field(default=None, alias="OPENAQ_API_KEY")
    db_path: Path = Field(default=Path("backend/airvision.db"), alias="AIRVISION_DB_PATH")
    cache_ttl_minutes: int = Field(default=360, alias="AIRVISION_CACHE_TTL_MINUTES")
    openaq_base_url: str = "https://api.openaq.org/v3"

    model_config = SettingsConfigDict(populate_by_name=True, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
