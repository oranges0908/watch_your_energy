"""
Repository for the blocks table.
"""
from __future__ import annotations

import time
import uuid

import aiosqlite

# Fixed block titles for every project
BLOCK_TITLES = ["项目1", "项目2", "项目3", "总结"]


def _progress_to_status(pct: int) -> str:
    if pct == 0:
        return "not_started"
    elif pct < 75:
        return "in_progress"
    elif pct < 100:
        return "near_complete"
    else:
        return "completed"


async def create_bulk(
    db: aiosqlite.Connection,
    project_id: str,
    titles: list[str] | None = None,
) -> list[dict]:
    """
    Create the 4 structure blocks for a project.
    Uses `titles` when provided (must be exactly 4); falls back to BLOCK_TITLES.
    Returns list of created block dicts.
    """
    effective_titles = (
        titles if titles and len(titles) == 4 else BLOCK_TITLES
    )
    now = int(time.time() * 1000)
    blocks = []
    for position, title in enumerate(effective_titles):
        block_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO blocks "
            "(id, project_id, title, position, status, progress_pct, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 'not_started', 0, ?, ?)",
            (block_id, project_id, title, position, now, now),
        )
        blocks.append({
            "id": block_id,
            "project_id": project_id,
            "title": title,
            "position": position,
            "status": "not_started",
            "progress_pct": 0,
            "created_at": now,
            "updated_at": now,
        })
    await db.commit()
    return blocks


async def get(db: aiosqlite.Connection, block_id: str) -> dict | None:
    async with db.execute(
        "SELECT id, project_id, title, position, status, progress_pct, created_at, updated_at "
        "FROM blocks WHERE id = ?",
        (block_id,),
    ) as cur:
        row = await cur.fetchone()
    return dict(row) if row else None


async def get_by_project(
    db: aiosqlite.Connection, project_id: str
) -> list[dict]:
    async with db.execute(
        "SELECT id, project_id, title, position, status, progress_pct, created_at, updated_at "
        "FROM blocks WHERE project_id = ? ORDER BY position",
        (project_id,),
    ) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def advance_progress(
    db: aiosqlite.Connection, block_id: str, delta: int
) -> int:
    """
    Add delta to block's progress_pct (capped at 100).
    Updates status automatically from the new progress.
    Returns the new progress_pct.
    """
    async with db.execute(
        "SELECT progress_pct FROM blocks WHERE id = ?", (block_id,)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        return 0

    new_pct = min(100, int(row[0]) + delta)
    new_status = _progress_to_status(new_pct)
    now = int(time.time() * 1000)

    await db.execute(
        "UPDATE blocks SET progress_pct = ?, status = ?, updated_at = ? WHERE id = ?",
        (new_pct, new_status, now, block_id),
    )
    return new_pct


async def set_completed(db: aiosqlite.Connection, block_id: str) -> None:
    """Force a block to 100% completed (used when user marks it done in create flow)."""
    now = int(time.time() * 1000)
    await db.execute(
        "UPDATE blocks SET progress_pct = 100, status = 'completed', updated_at = ? "
        "WHERE id = ?",
        (now, block_id),
    )
