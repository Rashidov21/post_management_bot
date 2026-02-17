"""
Schedule times: add/remove/list posting times (HH:MM), enable/disable.
"""
import logging
import re
from datetime import datetime
from typing import List

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


async def add_schedule(time_str: str) -> bool:
    """Add a posting time. Returns False if duplicate."""
    normalized = parse_time(time_str)
    if not normalized:
        return False
    conn = get_db()
    try:
        await conn.execute(
            "INSERT INTO schedules (time_str, enabled) VALUES (?, 1)",
            (normalized,),
        )
        await conn.commit()
        return True
    except Exception:
        await conn.rollback()
        return False


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
