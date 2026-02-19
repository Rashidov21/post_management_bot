"""
Schedule times: add/remove/list posting times (HH:MM), enable/disable.
Post–time binding: which content_id posts at which schedule_id (content_schedule table).
"""
import logging
import re
from datetime import datetime
from typing import List, Optional

from bot.database.connection import get_db
from bot.database.models import Schedule

logger = logging.getLogger(__name__)

TIME_PATTERN = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def _row_to_schedule(row) -> Schedule:
    return Schedule(
        id=row["id"],
        time_str=row["time_str"],
        enabled=bool(row["enabled"]),
        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
    )


def parse_time(s: str) -> str | None:
    """Validate and return 'HH:MM' or None."""
    s = s.strip()
    if TIME_PATTERN.match(s):
        parts = s.split(":")
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    return None


async def add_schedule(time_str: str) -> Optional[int]:
    """Add a posting time. Returns new schedule id, or None if invalid or duplicate."""
    normalized = parse_time(time_str)
    if not normalized:
        return None
    conn = get_db()
    async with conn.execute(
        "SELECT 1 FROM schedules WHERE time_str = ?", (normalized,)
    ) as cur:
        row = await cur.fetchone()
    if row:
        return None  # duplicate
    try:
        cur = await conn.execute(
            "INSERT INTO schedules (time_str, enabled) VALUES (?, 1)",
            (normalized,),
        )
        new_id = cur.lastrowid
        await conn.commit()
        return new_id
    except Exception:
        await conn.rollback()
        return None


async def get_schedule_id_by_time_str(time_str: str) -> Optional[int]:
    """Get schedule id by time string (e.g. 09:00). None if not found."""
    normalized = parse_time(time_str)
    if not normalized:
        return None
    conn = get_db()
    async with conn.execute(
        "SELECT id FROM schedules WHERE time_str = ?", (normalized,)
    ) as cur:
        row = await cur.fetchone()
    return row["id"] if row else None


async def remove_schedule(time_str: str) -> bool:
    """Remove a schedule by time string."""
    normalized = parse_time(time_str)
    if not normalized:
        return False
    conn = get_db()
    cur = await conn.execute("DELETE FROM schedules WHERE time_str = ?", (normalized,))
    await conn.commit()
    return cur.rowcount > 0


async def list_schedules() -> List[Schedule]:
    conn = get_db()
    async with conn.execute(
        "SELECT * FROM schedules ORDER BY time_str"
    ) as cur:
        rows = await cur.fetchall()
    return [_row_to_schedule(r) for r in rows]


async def get_schedule_by_id(schedule_id: int) -> Optional[Schedule]:
    conn = get_db()
    async with conn.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,)) as cur:
        row = await cur.fetchone()
    return _row_to_schedule(row) if row else None


async def set_schedule_enabled(time_str: str, enabled: bool) -> bool:
    normalized = parse_time(time_str)
    if not normalized:
        return False
    conn = get_db()
    cur = await conn.execute(
        "UPDATE schedules SET enabled = ? WHERE time_str = ?",
        (1 if enabled else 0, normalized),
    )
    await conn.commit()
    return cur.rowcount > 0


async def get_content_id_for_schedule(schedule_id: int) -> Optional[int]:
    """Which content_id is assigned to this schedule (time). None if none."""
    conn = get_db()
    async with conn.execute(
        "SELECT content_id FROM content_schedule WHERE schedule_id = ?",
        (schedule_id,),
    ) as cur:
        row = await cur.fetchone()
    return row["content_id"] if row else None


async def set_schedule_content(schedule_id: int, content_id: int) -> bool:
    """Assign a post to this schedule time (one post per time). INSERT OR REPLACE."""
    conn = get_db()
    try:
        await conn.execute(
            """INSERT INTO content_schedule (schedule_id, content_id) VALUES (?, ?)
               ON CONFLICT(schedule_id) DO UPDATE SET content_id = excluded.content_id""",
            (schedule_id, content_id),
        )
        await conn.commit()
        return True
    except Exception:
        await conn.rollback()
        return False


async def get_schedule_ids_for_content(content_id: int) -> List[int]:
    """List schedule_id(s) that are assigned to this content."""
    conn = get_db()
    async with conn.execute(
        "SELECT schedule_id FROM content_schedule WHERE content_id = ?",
        (content_id,),
    ) as cur:
        rows = await cur.fetchall()
    return [r["schedule_id"] for r in rows]
