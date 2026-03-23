import aiosqlite
from contextlib import asynccontextmanager
from config import DB_PATH

DDL = """
CREATE TABLE IF NOT EXISTS projects (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active',   -- active | completed | archived
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  INTEGER NOT NULL,
    updated_at  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS blocks (
    id           TEXT PRIMARY KEY,
    project_id   TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    position     INTEGER NOT NULL,
    status       TEXT NOT NULL DEFAULT 'not_started',  -- not_started | in_progress | near_complete | completed
    progress_pct INTEGER NOT NULL DEFAULT 0,
    created_at   INTEGER NOT NULL,
    updated_at   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    started_at  INTEGER NOT NULL,
    ended_at    INTEGER,          -- NULL = current session
    energy_mode TEXT NOT NULL DEFAULT 'normal'
);

CREATE TABLE IF NOT EXISTS steps (
    id            TEXT PRIMARY KEY,
    project_id    TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    block_id      TEXT REFERENCES blocks(id),
    description   TEXT NOT NULL,
    pattern       TEXT NOT NULL,    -- Light | Continuation | Completion | Decomposition | Recovery | Refinement
    step_type     TEXT NOT NULL,    -- Bootstrap | Push | Wrap | Transfer
    estimated_min INTEGER NOT NULL,
    energy_level  TEXT NOT NULL DEFAULT 'normal',  -- normal | low
    trigger       TEXT NOT NULL,    -- auto | skip | stuck | low_energy | resume | complete
    status        TEXT NOT NULL DEFAULT 'pending',  -- pending | active | completed | skipped | stuck
    created_at    INTEGER NOT NULL,
    completed_at  INTEGER,
    session_id    TEXT NOT NULL REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS step_rejections (
    id           TEXT PRIMARY KEY,
    project_id   TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    step_id      TEXT NOT NULL REFERENCES steps(id),
    verb         TEXT NOT NULL,
    object_text  TEXT NOT NULL,
    pattern      TEXT NOT NULL,
    rejected_at  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS app_state (
    id                  INTEGER PRIMARY KEY DEFAULT 1,
    active_project_id   TEXT REFERENCES projects(id),
    active_session_id   TEXT REFERENCES sessions(id),
    energy_mode         TEXT NOT NULL DEFAULT 'normal',
    onboarding_complete INTEGER NOT NULL DEFAULT 0
);
"""

INSERT_APP_STATE = """
INSERT OR IGNORE INTO app_state (id) VALUES (1);
"""


async def init_db() -> None:
    """Create all tables and seed the single app_state row. Idempotent."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(DDL)
        await db.execute(INSERT_APP_STATE)
        await db.commit()


@asynccontextmanager
async def get_db():
    """Async context manager yielding an aiosqlite connection with row_factory set."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
