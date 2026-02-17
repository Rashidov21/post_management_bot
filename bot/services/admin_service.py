"""
Admin management: add/remove/list. Only owner can modify.
"""
import logging
from datetime import datetime
from typing import List, Optional

from bot.database.connection import get_db
from bot.database.models import Admin

logger = logging.getLogger(__name__)


def _row_to_admin(row) -> Admin:
    return Admin(
        id=row["id"],
        telegram_id=row["telegram_id"],
        username=row["username"],
        added_at=datetime.fromisoformat(row["added_at"]) if isinstance(row["added_at"], str) else row["added_at"],
    )


async def is_admin(telegram_id: int) -> bool:
    conn = get_db()
    async with conn.execute("SELECT 1 FROM admins WHERE telegram_id = ?", (telegram_id,)) as cur:
        row = await cur.fetchone()
    return row is not None


async def add_admin(telegram_id: int, username: Optional[str] = None) -> bool:
    """Add admin. False if already exists."""
    conn = get_db()
    try:
        await conn.execute(
            "INSERT INTO admins (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username or ""),
        )
        await conn.commit()
        return True
    except Exception:
        await conn.rollback()
        return False


async def remove_admin(telegram_id: int) -> bool:
    conn = get_db()
    cur = await conn.execute("DELETE FROM admins WHERE telegram_id = ?", (telegram_id,))
    await conn.commit()
    return cur.rowcount > 0


async def list_admins() -> List[Admin]:
    conn = get_db()
    async with conn.execute("SELECT * FROM admins ORDER BY added_at") as cur:
        rows = await cur.fetchall()
    return [_row_to_admin(r) for r in rows]
