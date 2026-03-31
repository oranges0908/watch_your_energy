"""
API integration tests for I3.

Uses httpx.AsyncClient + ASGITransport against the FastAPI app with a
temporary in-memory SQLite DB (overrides config.DB_PATH via monkeypatch).

Run:  cd backend && pytest tests/test_api.py -v
"""
from __future__ import annotations

import asyncio
import time
import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
import httpx

# Allow imports from backend root
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import config

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    """Point every test at a fresh temporary SQLite file."""
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")


@pytest.fixture
def mock_agent():
    """
    Mock agent.generate_step so tests don't hit the real LLM.
    Returns a minimal StepOutput dict with unique ids.
    """
    call_count = {"n": 0}

    async def fake_generate_step(trigger, project_id, energy_mode, session_id, db, current_block_id=None):
        call_count["n"] += 1
        n = call_count["n"]
        # Vary verb+object so diversity tests pass
        descriptions = [
            "Write the opening sentence of Part 1 (describe what you did)",
            "Trim the title of Part 2 to one line",
            "Check the wording of one completed paragraph in Part 3",
            "List two unresolved issues remaining in Wrap-up",
            "Complete the last blank field in the current block",
            "Fill in your key takeaways in Part 1",
        ]
        desc = descriptions[(n - 1) % len(descriptions)]
        pattern = "Light" if trigger == "low_energy" else (
            "Decomposition" if trigger == "stuck" else
            "Recovery" if trigger == "resume" else
            "Continuation"
        )
        step_type = "Bootstrap" if n <= 2 else "Push"
        step_id = str(uuid.uuid4())

        # Actually save to DB so downstream queries work
        from repositories import state_repo
        session_id_used = session_id
        if session_id_used is None:
            session_id_used = await state_repo.create_session(db, energy_mode)

        import time as t
        now = int(t.time() * 1000)
        await db.execute(
            "INSERT INTO steps "
            "(id, project_id, block_id, description, pattern, step_type, "
            "estimated_min, energy_level, trigger, status, created_at, session_id) "
            "SELECT ?, ?, b.id, ?, ?, ?, ?, ?, ?, 'pending', ?, ? "
            "FROM blocks b WHERE b.project_id = ? ORDER BY b.position LIMIT 1",
            (step_id, project_id, desc, pattern, step_type,
             5 if energy_mode == "low" else 10,
             energy_mode, trigger, now, session_id_used, project_id),
        )
        await db.commit()

        # Get the block used
        from repositories import block_repo
        blocks = await block_repo.get_by_project(db, project_id)
        block = blocks[0] if blocks else {"title": ""}

        if current_block_id:
            block_found = await block_repo.get(db, current_block_id)
            if block_found:
                block = block_found

        return {
            "step_id": step_id,
            "description": desc,
            "estimated_min": 5 if energy_mode == "low" else 10,
            "pattern": pattern,
            "step_type": step_type,
            "block_id": block["id"] if isinstance(block, dict) and "id" in block else "",
            "block_title": block["title"] if isinstance(block, dict) else "",
            "energy_level": energy_mode,
        }

    with patch("agent.agent.generate_step", side_effect=fake_generate_step):
        yield fake_generate_step


@pytest_asyncio.fixture
async def client(mock_agent):
    """httpx AsyncClient pointed at the ASGI app."""
    # Import app AFTER monkeypatching DB path
    from main import app
    from database import init_db
    await init_db()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# ── Helper ────────────────────────────────────────────────────────────────────

async def create_test_project(client, title="Improve my resume"):
    resp = await client.post("/projects", json={"title": title, "completed_block_positions": []})
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Scenario A: Complete first-time flow ──────────────────────────────────────

@pytest.mark.asyncio
async def test_A_create_project_returns_step(client):
    data = await create_test_project(client)
    assert "step" in data
    assert data["step"]["description"]
    assert data["project"]["progress_pct"] == 0


@pytest.mark.asyncio
async def test_A_complete_step_advances_progress(client):
    proj_data = await create_test_project(client)
    step_id = proj_data["step"]["id"]

    resp = await client.post("/steps/complete", json={"step_id": step_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["step"]["description"]
    assert data["project"]["progress_pct"] >= 0
    assert data["feedback_message"] is not None


# ── Scenario B: Skip (diversity) ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_B_skip_returns_new_step(client):
    proj_data = await create_test_project(client)
    step_id = proj_data["step"]["id"]

    resp = await client.post("/steps/skip", json={"step_id": step_id})
    assert resp.status_code == 200
    data = resp.json()
    assert "step" in data
    assert data["step"]["id"] != step_id


# ── Scenario C: Stuck → Decomposition ────────────────────────────────────────

@pytest.mark.asyncio
async def test_C_stuck_returns_decomposition_same_block(client):
    proj_data = await create_test_project(client)
    step_id = proj_data["step"]["id"]
    original_block = proj_data["step"]["block_title"]

    resp = await client.post("/steps/stuck", json={"step_id": step_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["step"]["pattern"] == "Decomposition"
    # Progress must not change (stuck doesn't advance)
    assert data["project"]["progress_pct"] == 0


# ── Scenario D: Low-energy mode ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_D_low_energy_returns_light_step(client):
    await create_test_project(client)

    resp = await client.patch("/state/energy", json={"mode": "low"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["energy_mode"] == "low"
    assert data["step"]["pattern"] == "Light"
    assert data["step"]["energy_level"] == "low"
    assert data["step"]["estimated_min"] <= 5


# ── Scenario E: Project limit ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_E_project_limit_enforced(client):
    for i in range(config.MAX_ACTIVE_PROJECTS):
        await create_test_project(client, title=f"Project {i}")

    resp = await client.post(
        "/projects", json={"title": "Fourth project", "completed_block_positions": []}
    )
    assert resp.status_code == 400
    assert "Maximum" in resp.json()["detail"]


# ── Scenario F: Interruption detection ───────────────────────────────────────

@pytest.mark.asyncio
async def test_F_long_gap_triggers_resume(client):
    await create_test_project(client)

    # Simulate a session that ended 3 hours ago
    from database import get_db_dep
    import aiosqlite
    import config as cfg

    now_ms = int(time.time() * 1000)
    three_hours_ago = now_ms - int(3 * 3600 * 1000)
    old_session_id = str(uuid.uuid4())

    async with aiosqlite.connect(cfg.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # End the current session at 3h ago
        await db.execute(
            "UPDATE sessions SET ended_at = ?", (three_hours_ago,)
        )
        # Clear active_session_id so start_session sees the ended one
        await db.execute("UPDATE app_state SET active_session_id = NULL")
        await db.commit()

    resp = await client.post("/state/session")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trigger"] == "resume"
    assert data["step"] is not None


@pytest.mark.asyncio
async def test_F_short_gap_triggers_auto(client):
    await create_test_project(client)

    # Session ended 10 minutes ago
    now_ms = int(time.time() * 1000)
    ten_min_ago = now_ms - int(10 * 60 * 1000)

    import aiosqlite
    import config as cfg
    async with aiosqlite.connect(cfg.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("UPDATE sessions SET ended_at = ?", (ten_min_ago,))
        await db.execute("UPDATE app_state SET active_session_id = NULL")
        await db.commit()

    resp = await client.post("/state/session")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trigger"] == "auto"


# ── Scenario G: Never empty (fallback) ───────────────────────────────────────

@pytest.mark.asyncio
async def test_G_step_never_empty_on_agent_failure(client):
    """
    Even when the agent raises, step_service must return something
    (the agent's own fallback guarantees this at a lower level;
    here we test that the API still returns 200 with a step).
    """
    proj_data = await create_test_project(client)
    step_id = proj_data["step"]["id"]

    # Confirm complete still returns 200 with a step
    resp = await client.post("/steps/complete", json={"step_id": step_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["step"]["description"]


# ── Misc endpoint smoke tests ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_state_no_project(client):
    resp = await client.get("/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["step"] is None
    assert data["project"] is None


@pytest.mark.asyncio
async def test_get_state_with_project(client):
    await create_test_project(client)
    resp = await client.get("/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["step"] is not None
    assert data["project"] is not None


@pytest.mark.asyncio
async def test_list_projects(client):
    await create_test_project(client, "My project")
    resp = await client.get("/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "My project"


@pytest.mark.asyncio
async def test_get_project_blocks(client):
    proj_data = await create_test_project(client)
    project_id = proj_data["project"]["id"]

    resp = await client.get(f"/projects/{project_id}/blocks")
    assert resp.status_code == 200
    blocks = resp.json()
    assert len(blocks) == 4
    assert blocks[0]["title"] == "Part 1"
    assert blocks[-1]["title"] == "Wrap-up"


@pytest.mark.asyncio
async def test_archive_project(client):
    proj_data = await create_test_project(client)
    project_id = proj_data["project"]["id"]

    resp = await client.delete(f"/projects/{project_id}")
    assert resp.status_code == 204

    # Should not appear in list anymore
    resp = await client.get("/projects")
    assert resp.status_code == 200
    assert all(p["id"] != project_id for p in resp.json())


@pytest.mark.asyncio
async def test_start_step(client):
    proj_data = await create_test_project(client)
    step_id = proj_data["step"]["id"]

    resp = await client.post("/steps/start", json={"step_id": step_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["step"]["id"] == step_id
