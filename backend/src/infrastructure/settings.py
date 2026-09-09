from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/src/infrastructure/settings.py -> parents[2] is backend/
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        # backend/.env is the project's env file; a cwd .env is picked up too if present.
        env_file=(BACKEND_DIR / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
