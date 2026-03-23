"""
Repository for the steps table.
"""
from __future__ import annotations

import time

import aiosqlite


async def get_current(
    db: aiosqlite.Connection, project_id: str
) -> dict | None:
    """Return the most-recent pending or active step for the project."""
    async with db.execute(
        "SELECT id, project_id, block_id, description, pattern, step_type, "
        "estimated_min, energy_level, trigger, status, created_at, completed_at, session_id "
        "FROM steps "
        "WHERE project_id = ? AND status IN ('pending', 'active') "
        "ORDER BY created_at DESC LIMIT 1",
        (project_id,),
    ) as cur:
        row = await cur.fetchone()
    return dict(row) if row else None


async def get_by_id(db: aiosqlite.Connection, step_id: str) -> dict | None:
    async with db.execute(
        "SELECT id, project_id, block_id, description, pattern, step_type, "
        "estimated_min, energy_level, trigger, status, created_at, completed_at, session_id "
        "FROM steps WHERE id = ?",
        (step_id,),
    ) as cur:
        row = await cur.fetchone()
    return dict(row) if row else None


async def mark_completed(db: aiosqlite.Connection, step_id: str) -> None:
    now = int(time.time() * 1000)
    await db.execute(
        "UPDATE steps SET status = 'completed', completed_at = ? WHERE id = ?",
        (now, step_id),
    )


async def mark_status(
    db: aiosqlite.Connection, step_id: str, status: str
) -> None:
    """Set step status to one of: active | skipped | stuck."""
    await db.execute(
        "UPDATE steps SET status = ? WHERE id = ?",
        (status, step_id),
    )


async def skip_all_pending(
    db: aiosqlite.Connection, project_id: str
) -> None:
    """Mark every pending/active step for a project as skipped (used on energy switch or resume)."""
    await db.execute(
        "UPDATE steps SET status = 'skipped' "
        "WHERE project_id = ? AND status IN ('pending', 'active')",
        (project_id,),
    )
