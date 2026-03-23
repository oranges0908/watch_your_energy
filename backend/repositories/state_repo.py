"""
Repository for the app_state singleton and sessions table.
"""
from __future__ import annotations

import time
import uuid
from typing import Optional

import aiosqlite


# ── app_state ─────────────────────────────────────────────────────────────────

async def get_state(db: aiosqlite.Connection) -> dict:
    async with db.execute(
        "SELECT id, active_project_id, active_session_id, energy_mode, onboarding_complete "
        "FROM app_state WHERE id = 1"
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        # Should never happen after init_db(), but guard anyway
        return {
            "active_project_id": None,
            "active_session_id": None,
            "energy_mode": "normal",
            "onboarding_complete": False,
        }
    return {
        "active_project_id": row["active_project_id"],
        "active_session_id": row["active_session_id"],
        "energy_mode": row["energy_mode"],
        "onboarding_complete": bool(row["onboarding_complete"]),
    }


async def set_active_project(
    db: aiosqlite.Connection, project_id: Optional[str]
) -> None:
    await db.execute(
        "UPDATE app_state SET active_project_id = ? WHERE id = 1",
        (project_id,),
    )
    await db.commit()


async def set_energy_mode(db: aiosqlite.Connection, mode: str) -> None:
    await db.execute(
        "UPDATE app_state SET energy_mode = ? WHERE id = 1",
        (mode,),
    )
    await db.commit()


async def set_onboarding_complete(db: aiosqlite.Connection) -> None:
    await db.execute(
        "UPDATE app_state SET onboarding_complete = 1 WHERE id = 1"
    )
    await db.commit()


# ── sessions ──────────────────────────────────────────────────────────────────

async def create_session(
    db: aiosqlite.Connection, energy_mode: str = "normal"
) -> str:
    """Create a new session, link it in app_state, and return the session id."""
    session_id = str(uuid.uuid4())
    now = int(time.time() * 1000)
    await db.execute(
        "INSERT INTO sessions (id, started_at, energy_mode) VALUES (?, ?, ?)",
        (session_id, now, energy_mode),
    )
    await db.execute(
        "UPDATE app_state SET active_session_id = ? WHERE id = 1",
        (session_id,),
    )
    await db.commit()
    return session_id


async def end_session(db: aiosqlite.Connection, session_id: str) -> None:
    now = int(time.time() * 1000)
    await db.execute(
        "UPDATE sessions SET ended_at = ? WHERE id = ?",
        (now, session_id),
    )
    await db.commit()


async def get_last_ended_session(db: aiosqlite.Connection) -> dict | None:
    """Return the most-recently ended session, or None."""
    async with db.execute(
        "SELECT id, started_at, ended_at, energy_mode "
        "FROM sessions WHERE ended_at IS NOT NULL "
        "ORDER BY ended_at DESC LIMIT 1"
    ) as cur:
        row = await cur.fetchone()
    return dict(row) if row else None
