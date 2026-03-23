"""
Tracks recently-rejected step verb+object pairs per project to enforce diversity.
Only the most-recent REJECTION_HISTORY_SIZE entries are kept per project.
"""
from __future__ import annotations

import time
import uuid

import aiosqlite

from config import REJECTION_HISTORY_SIZE


async def record_rejection(
    db: aiosqlite.Connection,
    project_id: str,
    step_id: str,
    verb: str,
    object_text: str,
    pattern: str,
) -> None:
    """Insert a rejection record and prune old ones beyond the history limit."""
    rejection_id = str(uuid.uuid4())
    now = int(time.time() * 1000)

    await db.execute(
        "INSERT INTO step_rejections (id, project_id, step_id, verb, object_text, pattern, rejected_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (rejection_id, project_id, step_id, verb, object_text, pattern, now),
    )

    # Keep only the most-recent REJECTION_HISTORY_SIZE per project
    await db.execute(
        """
        DELETE FROM step_rejections
        WHERE project_id = ? AND id NOT IN (
            SELECT id FROM step_rejections
            WHERE project_id = ?
            ORDER BY rejected_at DESC
            LIMIT ?
        )
        """,
        (project_id, project_id, REJECTION_HISTORY_SIZE),
    )
    await db.commit()


async def get_recent(
    db: aiosqlite.Connection, project_id: str
) -> list[dict]:
    """Return the recent rejection records for diversity enforcement."""
    async with db.execute(
        "SELECT verb, object_text, pattern FROM step_rejections "
        "WHERE project_id = ? ORDER BY rejected_at DESC LIMIT ?",
        (project_id, REJECTION_HISTORY_SIZE),
    ) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]
