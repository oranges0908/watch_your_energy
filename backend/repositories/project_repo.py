"""
Repository for the projects table.
"""
from __future__ import annotations

import time
import uuid

import aiosqlite


async def create(db: aiosqlite.Connection, title: str) -> dict:
    """Insert a new active project and return its row dict."""
    project_id = str(uuid.uuid4())
    now = int(time.time() * 1000)
    await db.execute(
        "INSERT INTO projects (id, title, status, sort_order, created_at, updated_at) "
        "VALUES (?, ?, 'active', 0, ?, ?)",
        (project_id, title, now, now),
    )
    await db.commit()
    return {
        "id": project_id,
        "title": title,
        "status": "active",
        "sort_order": 0,
        "created_at": now,
        "updated_at": now,
    }


async def get(db: aiosqlite.Connection, project_id: str) -> dict | None:
    async with db.execute(
        "SELECT id, title, status, sort_order, created_at, updated_at "
        "FROM projects WHERE id = ?",
        (project_id,),
    ) as cur:
        row = await cur.fetchone()
    return dict(row) if row else None


async def list_active(db: aiosqlite.Connection) -> list[dict]:
    async with db.execute(
        "SELECT id, title, status, sort_order, created_at, updated_at "
        "FROM projects WHERE status = 'active' ORDER BY updated_at DESC",
    ) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def compute_progress(db: aiosqlite.Connection, project_id: str) -> int:
    """Return the average progress_pct across all blocks for the project (0 if no blocks)."""
    async with db.execute(
        "SELECT COALESCE(AVG(progress_pct), 0) FROM blocks WHERE project_id = ?",
        (project_id,),
    ) as cur:
        row = await cur.fetchone()
    return int(row[0])


async def touch(db: aiosqlite.Connection, project_id: str) -> None:
    """Update updated_at to now (call after a step is completed on this project)."""
    now = int(time.time() * 1000)
    await db.execute(
        "UPDATE projects SET updated_at = ? WHERE id = ?",
        (now, project_id),
    )


async def archive(db: aiosqlite.Connection, project_id: str) -> None:
    now = int(time.time() * 1000)
    await db.execute(
        "UPDATE projects SET status = 'archived', updated_at = ? WHERE id = ?",
        (now, project_id),
    )
    await db.commit()


async def count_active(db: aiosqlite.Connection) -> int:
    async with db.execute(
        "SELECT COUNT(*) FROM projects WHERE status = 'active'",
    ) as cur:
        row = await cur.fetchone()
    return int(row[0])
