"""
Lead collection: create lead, assign to admin, rate limit.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from bot.database.connection import get_db
from bot.database.models import Lead, LeadStatus

logger = logging.getLogger(__name__)


def _row_to_lead(row) -> Lead:
    phone = None
    try:
        if hasattr(row, "keys") and "phone_number" in row.keys():
            phone = row["phone_number"]
    except Exception:
        pass
    return Lead(
        id=row["id"],
        user_id=row["user_id"],
        telegram_user_id=row["telegram_user_id"],
        message_text=row["message_text"],
        source_content_id=row["source_content_id"],
        status=row["status"],
        taken_by_telegram_id=row["taken_by_telegram_id"],
        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
        phone_number=phone,
    )


async def create_lead(
    user_id: int,
    telegram_user_id: int,
    message_text: str,
    source_content_id: Optional[int] = None,
    phone_number: Optional[str] = None,
) -> Lead:
    conn = get_db()
    cur = await conn.execute(
        """INSERT INTO leads (user_id, telegram_user_id, message_text, source_content_id, status, phone_number)
           VALUES (?, ?, ?, ?, 'pending', ?)""",
        (user_id, telegram_user_id, message_text, source_content_id, phone_number),
    )
    rid = cur.lastrowid
    await conn.commit()
    async with conn.execute("SELECT * FROM leads WHERE id = ?", (rid,)) as c2:
        row = await c2.fetchone()
    return _row_to_lead(row)


async def get_lead(lead_id: int) -> Optional[Lead]:
    conn = get_db()
    async with conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)) as cur:
        row = await cur.fetchone()
    return _row_to_lead(row) if row else None


async def take_lead(lead_id: int, by_telegram_id: int) -> bool:
    """Assign lead to admin. Returns False if already taken."""
    conn = get_db()
    cur = await conn.execute(
        "UPDATE leads SET status = 'taken', taken_by_telegram_id = ? WHERE id = ? AND status = 'pending'",
        (by_telegram_id, lead_id),
    )
    await conn.commit()
    return cur.rowcount > 0


async def count_leads_from_user_since(telegram_user_id: int, since: datetime) -> int:
    """For rate limiting: count leads from this user since `since`."""
    conn = get_db()
    # SQLite stores "YYYY-MM-DD HH:MM:SS"; use same format for reliable comparison
    since_str = since.strftime("%Y-%m-%d %H:%M:%S") if hasattr(since, "strftime") else str(since)
    async with conn.execute(
        "SELECT COUNT(*) AS c FROM leads WHERE telegram_user_id = ? AND created_at >= ?",
        (telegram_user_id, since_str),
    ) as cur:
        row = await cur.fetchone()
    return row["c"] if row else 0


async def list_recent_leads(limit: int = 50) -> List[Lead]:
    conn = get_db()
    async with conn.execute(
        "SELECT * FROM leads ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ) as cur:
        rows = await cur.fetchall()
    return [_row_to_lead(r) for r in rows]
