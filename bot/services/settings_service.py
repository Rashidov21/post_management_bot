"""
Settings key-value storage: target_group_id, posting_enabled, banner_file_id.
"""
import logging
from typing import Optional

from bot.database.connection import get_db
from bot.database.models import Setting

logger = logging.getLogger(__name__)

KEYS = {
    "target_group_id": "0",
    "admin_group_id": "0",  # group where leads are forwarded
    "posting_enabled": "0",
    "banner_file_id": "",
}


def _row_to_setting(row) -> Setting:
    from datetime import datetime
    return Setting(
        id=row["id"],
        key=row["key"],
        value=row["value"],
        updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else row["updated_at"],
    )


async def get_setting(key: str) -> str:
    """Get setting value; return default if not set."""
    conn = get_db()
    async with conn.execute("SELECT key, value FROM settings WHERE key = ?", (key,)) as cur:
        row = await cur.fetchone()
    default = KEYS.get(key, "")
    return row["value"] if row else default


async def set_setting(key: str, value: str) -> None:
    """Set or update a setting."""
    conn = get_db()
    await conn.execute(
        """INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP""",
        (key, value, value),
    )
    await conn.commit()


async def get_target_group_id() -> Optional[int]:
    """Target group ID for reposts. None if not set or 0."""
    raw = await get_setting("target_group_id")
    try:
        n = int(raw)
        return n if n != 0 else None
    except (TypeError, ValueError):
        return None


async def get_admin_group_id() -> Optional[int]:
    """Admin group ID for lead forwarding. None if not set or 0."""
    raw = await get_setting("admin_group_id")
    try:
        n = int(raw)
        return n if n != 0 else None
    except (TypeError, ValueError):
        return None


async def set_target_group_id(group_id: int) -> None:
    await set_setting("target_group_id", str(group_id))


async def set_admin_group_id(group_id: int) -> None:
    await set_setting("admin_group_id", str(group_id))


async def is_posting_enabled() -> bool:
    raw = await get_setting("posting_enabled")
    return raw == "1" or str(raw).lower() == "true"


async def set_posting_enabled(enabled: bool) -> None:
    await set_setting("posting_enabled", "1" if enabled else "0")


async def get_banner_file_id() -> Optional[str]:
    raw = await get_setting("banner_file_id")
    return raw if raw else None


async def set_banner_file_id(file_id: str) -> None:
    await set_setting("banner_file_id", file_id)
