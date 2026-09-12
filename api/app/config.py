from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(API_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # sqlite:///./data/lead_feed.db  → later postgresql://... (Supabase)
    database_url: str = f"sqlite:///{API_ROOT / 'data' / 'lead_feed.db'}"

    # Telethon
    tg_api_id: int | None = None
    tg_api_hash: str | None = None
    tg_session: str = "tg_session"

    # First sync for a channel pulls at most this many recent messages
    sync_backfill_limit: int = 5
    # Pause between channels to reduce flood risk
    sync_channel_pause_seconds: float = 1.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


def session_path() -> Path:
    """Telethon session path without .session extension."""
    settings = get_settings()
    return API_ROOT / settings.tg_session
