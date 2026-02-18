"""
Content CRUD: save photo/video/text, set active, list history, delete (soft).
"""
import logging
from datetime import datetime
from typing import List, Optional

from bot.database.connection import get_db
from bot.database.models import Content, ContentType, ContentStatus

logger = logging.getLogger(__name__)


def _row_to_content(row) -> Content:
    return Content(
        id=row["id"],
        content_type=row["content_type"],
        file_id=row["file_id"],
        text=row["text"],
        caption=row["caption"],
        status=row["status"],
        publishing_enabled=bool(row["publishing_enabled"]) if "publishing_enabled" in row.keys() else True,
        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
        created_by=row["created_by"],
    )


async def add_content(
    content_type: ContentType,
    created_by: int,
    file_id: Optional[str] = None,
    text: Optional[str] = None,
    caption: Optional[str] = None,
) -> Content:
    """Insert new content and set as only active (deactivate others)."""
    conn = get_db()
    # Deactivate all current active so only one is active
    await conn.execute("UPDATE content SET status = 'deleted' WHERE status = 'active'")
    cur = await conn.execute(
        """INSERT INTO content (content_type, file_id, text, caption, status, publishing_enabled, created_by)
           VALUES (?, ?, ?, ?, 'active', 1, ?)""",
        (content_type, file_id or "", text or "", caption or "", created_by),
    )
    rid = cur.lastrowid
    await conn.commit()
    async with conn.execute("SELECT * FROM content WHERE id = ?", (rid,)) as c2:
        row = await c2.fetchone()
    return _row_to_content(row)


async def get_active_content() -> Optional[Content]:
    """Get the single active content for reposting. None if none or all deleted."""
    conn = get_db()
    async with conn.execute(
        "SELECT * FROM content WHERE status = 'active' ORDER BY id DESC LIMIT 1"
    ) as cur:
        row = await cur.fetchone()
    return _row_to_content(row) if row else None


async def get_content_by_id(content_id: int) -> Optional[Content]:
    conn = get_db()
    async with conn.execute("SELECT * FROM content WHERE id = ?", (content_id,)) as cur:
        row = await cur.fetchone()
    return _row_to_content(row) if row else None


async def list_content(limit: int = 50, include_deleted: bool = False) -> List[Content]:
    """List content by created_at DESC."""
    conn = get_db()
    if include_deleted:
        async with conn.execute(
            "SELECT * FROM content ORDER BY created_at DESC LIMIT ?", (limit,)
        ) as cur:
            rows = await cur.fetchall()
    else:
        async with conn.execute(
            "SELECT * FROM content WHERE status = 'active' ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ) as cur:
            rows = await cur.fetchall()
    return [_row_to_content(r) for r in rows]


async def list_all_posts_for_history(limit: int = 50) -> List[Content]:
    """List all content (active + deleted) for history view."""
    conn = get_db()
    async with conn.execute(
        "SELECT * FROM content ORDER BY created_at DESC LIMIT ?", (limit,)
    ) as cur:
        rows = await cur.fetchall()
    return [_row_to_content(r) for r in rows]


async def delete_content(content_id: int) -> bool:
    """Soft-delete: set status to deleted. Returns True if found and updated."""
    conn = get_db()
    cur = await conn.execute(
        "UPDATE content SET status = 'deleted' WHERE id = ? AND status = 'active'",
        (content_id,),
    )
    # Clean up schedule bindings so deleted posts are not scheduled
    await conn.execute("DELETE FROM content_schedule WHERE content_id = ?", (content_id,))
    await conn.commit()
    return cur.rowcount > 0


async def set_content_active(content_id: int) -> bool:
    """Set this content as active (and deactivate others). Returns True if content existed and was updated."""
    conn = get_db()
    async with conn.execute("SELECT id FROM content WHERE id = ?", (content_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        return False
    await conn.execute("UPDATE content SET status = 'deleted' WHERE status = 'active'")
    cur = await conn.execute(
        "UPDATE content SET status = 'active' WHERE id = ?",
        (content_id,),
    )
    await conn.commit()
    return cur.rowcount > 0


async def set_content_publishing_enabled(content_id: int, enabled: bool) -> bool:
    """Turn publishing on/off for this post (at its scheduled times). Returns True if updated."""
    conn = get_db()
    cur = await conn.execute(
        "UPDATE content SET publishing_enabled = ? WHERE id = ?",
        (1 if enabled else 0, content_id),
    )
    await conn.commit()
    return cur.rowcount > 0


async def get_last_posted_at_map(content_ids: List[int]) -> dict:
    """Return {content_id: posted_at} for each content that has at least one post in posts_log."""
    if not content_ids:
        return {}
    conn = get_db()
    placeholders = ",".join("?" * len(content_ids))
    async with conn.execute(
        f"""SELECT content_id, MAX(posted_at) AS last_posted
            FROM posts_log WHERE content_id IN ({placeholders}) GROUP BY content_id""",
        content_ids,
    ) as cur:
        rows = await cur.fetchall()
    result = {}
    for row in rows:
        raw = row["last_posted"]
        if isinstance(raw, str):
            try:
                result[row["content_id"]] = datetime.fromisoformat(raw.replace(" ", "T", 1))
            except ValueError:
                try:
                    result[row["content_id"]] = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    result[row["content_id"]] = raw
        else:
            result[row["content_id"]] = raw
    return result


async def log_post(content_id: int, group_id: int, message_id: int) -> None:
    """Append to posts_log."""
    conn = get_db()
    await conn.execute(
        "INSERT INTO posts_log (content_id, group_id, message_id) VALUES (?, ?, ?)",
        (content_id, group_id, message_id),
    )
    await conn.commit()
