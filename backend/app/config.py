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
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000,https://auhauhbr.github.io",
        alias="CORS_ORIGINS",
    )
    openaq_base_url: str = "https://api.openaq.org/v3"

    model_config = SettingsConfigDict(populate_by_name=True, extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
