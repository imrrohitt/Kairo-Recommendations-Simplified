from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Kairo"
    database_url: str = f"sqlite:///{ROOT_DIR / 'data' / 'kairo.db'}"
    redis_url: str | None = None
    model_path: str = str(ROOT_DIR / "ml_models" / "xgb_classifier.pkl")
    api_cors_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
