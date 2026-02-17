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

# Owner Telegram user ID (super admin, required)
OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))

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


def validate_config() -> None:
    """Validate required config. Raises ValueError if invalid."""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required")
    if not OWNER_ID:
        raise ValueError("OWNER_ID is required (Telegram user ID of owner)")
