"""
Bot configuration loaded from environment variables.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent / ".env")

# Bot token (required)
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# Owner Telegram user ID(s). One ID or comma-separated: OWNER_ID=123 or OWNER_IDS=123,456
_owner_ids_str: str = os.getenv("OWNER_IDS", "").strip()
if _owner_ids_str:
    OWNER_IDS: tuple[int, ...] = tuple(
        int(x.strip()) for x in _owner_ids_str.split(",") if x.strip()
    )
else:
    _single: int = int(os.getenv("OWNER_ID", "0"))
    OWNER_IDS = (_single,) if _single else ()

# Backward compatibility: first owner as OWNER_ID
OWNER_ID: int = OWNER_IDS[0] if OWNER_IDS else 0


def is_owner(user_id: int) -> bool:
    """True if user_id is one of the configured owners."""
    return user_id in OWNER_IDS

# SQLite database path
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/bot.db")

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: str = os.getenv(
    "LOG_FORMAT",
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# Optional: rate limit leads per user per hour
LEAD_RATE_LIMIT_PER_HOUR: int = int(os.getenv("LEAD_RATE_LIMIT_PER_HOUR", "10"))

# Domain for docs (optional)
BOT_DOMAIN: str = os.getenv("BOT_DOMAIN", "postbot.rashidevs.uz")

# Scheduler timezone (e.g. Asia/Tashkent for Uzbekistan)
SCHEDULER_TIMEZONE: str = os.getenv("SCHEDULER_TIMEZONE", "Asia/Tashkent")


def validate_config() -> None:
    """Validate required config. Raises ValueError if invalid."""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required")
    if not OWNER_IDS:
        raise ValueError(
            "OWNER_ID or OWNER_IDS is required (Telegram user ID of owner(s), comma-separated for multiple)"
        )
