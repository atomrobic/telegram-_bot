"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    bot_token: str
    database_path: str = "attendance.db"
    monthly_leave_limit: int = 4
    admin_telegram_ids: tuple[int, ...] = ()


def _parse_admin_ids(raw_value: str) -> tuple[int, ...]:
    """Parse a comma-separated list of Telegram user IDs."""
    if not raw_value.strip():
        return ()
    admin_ids: list[int] = []
    for part in raw_value.split(","):
        cleaned = part.strip()
        if cleaned:
            admin_ids.append(int(cleaned))
    return tuple(admin_ids)


def load_settings() -> Settings:
    """Load and validate application settings from environment variables."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required.")

    database_path = os.getenv("DATABASE_PATH", "attendance.db").strip() or "attendance.db"
    monthly_leave_limit = int(os.getenv("MONTHLY_LEAVE_LIMIT", "4"))
    admin_telegram_ids = _parse_admin_ids(os.getenv("ADMIN_TELEGRAM_IDS", ""))

    return Settings(
        bot_token=bot_token,
        database_path=database_path,
        monthly_leave_limit=monthly_leave_limit,
        admin_telegram_ids=admin_telegram_ids,
    )
