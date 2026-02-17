"""
User (lead) registration and lookup.
"""
import logging
from datetime import datetime
from typing import Optional

from bot.database.connection import get_db
from bot.database.models import User

logger = logging.getLogger(__name__)


def _row_to_user(row) -> User:
    return User(
        id=row["id"],
        telegram_id=row["telegram_id"],
        username=row["username"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
    )


async def get_or_create_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> User:
    """Get user by telegram_id or create."""
    conn = get_db()
    async with conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
        row = await cur.fetchone()
    if row:
        return _row_to_user(row)
    cur = await conn.execute(
        """INSERT INTO users (telegram_id, username, first_name, last_name)
           VALUES (?, ?, ?, ?)""",
        (telegram_id, username or "", first_name or "", last_name or ""),
    )
    rid = cur.lastrowid
    await conn.commit()
    async with conn.execute("SELECT * FROM users WHERE id = ?", (rid,)) as c2:
        row = await c2.fetchone()
    return _row_to_user(row)


async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    conn = get_db()
    async with conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
        row = await cur.fetchone()
    return _row_to_user(row) if row else None
