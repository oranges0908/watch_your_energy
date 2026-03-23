"""
Orchestration hub for all step-mutating operations.

Connects routers → Agent → repositories and enforces business invariants.
All public functions accept an open aiosqlite.Connection and return StepResponse.
"""
from __future__ import annotations

import logging
from typing import Optional

import aiosqlite

from config import PROGRESS_DELTA, MAX_ACTIVE_PROJECTS
from agent.agent import generate_step
from agent.validators import validate_step
from models.domain import StepDetail, ProjectSummary, StepResponse
from repositories import project_repo, block_repo, step_repo, state_repo
from services import diversity_service

logger = logging.getLogger(__name__)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _progress_delta(step_type: str, energy_level: str) -> int:
    if energy_level == "low":
        return PROGRESS_DELTA["Low"]
    return PROGRESS_DELTA.get(step_type, 0)


async def _ensure_session(db: aiosqlite.Connection) -> str:
    """Return active_session_id, creating a new session if one doesn't exist."""
    state = await state_repo.get_state(db)
    if state["active_session_id"]:
        return state["active_session_id"]
    session_id = await state_repo.create_session(db, state["energy_mode"])
    return session_id


async def _build_response(
    db: aiosqlite.Connection,
    step_out: dict,
    feedback_message: Optional[str] = None,
) -> StepResponse:
    """Convert agent StepOutput + optional message into a StepResponse."""
    project = await project_repo.get(db, step_out["project_id"] if "project_id" in step_out else "")
    # step_out from agent doesn't carry project_id; we look it up from the saved step
    step_row = await step_repo.get_by_id(db, step_out["step_id"])
    project_id = step_row["project_id"] if step_row else None

    if project_id:
        project = await project_repo.get(db, project_id)
        progress = await project_repo.compute_progress(db, project_id)
    else:
        project = None
        progress = 0

    return StepResponse(
        step=StepDetail(
            id=step_out["step_id"],
            description=step_out["description"],
            estimated_min=step_out["estimated_min"],
            pattern=step_out["pattern"],
            step_type=step_out["step_type"],
            block_title=step_out["block_title"],
            energy_level=step_out["energy_level"],
        ),
        project=ProjectSummary(
            id=project["id"] if project else "",
            title=project["title"] if project else "",
            progress_pct=progress,
        ),
        feedback_message=feedback_message,
    )


# ── Public API ────────────────────────────────────────────────────────────────

async def generate_next(
    db: aiosqlite.Connection,
    project_id: str,
    trigger: str,
    current_block_id: Optional[str] = None,
) -> StepResponse:
    """
    Call the agent to generate the next step for a project.
    Ensures a session exists before calling the agent.
    """
    state = await state_repo.get_state(db)
    session_id = await _ensure_session(db)
    energy_mode = state["energy_mode"]

    step_out = await generate_step(
        trigger=trigger,
        project_id=project_id,
        energy_mode=energy_mode,
        session_id=session_id,
        db=db,
        current_block_id=current_block_id,
    )
    return await _build_response(db, step_out)


async def start_step(db: aiosqlite.Connection, step_id: str) -> StepResponse:
    """Mark a step as active (user tapped 开始)."""
    step = await step_repo.get_by_id(db, step_id)
    if step is None:
        raise ValueError(f"Step not found: {step_id}")

    await step_repo.mark_status(db, step_id, "active")
    await db.commit()

    # Return current state without generating a new step
    block = await block_repo.get(db, step["block_id"])
    project = await project_repo.get(db, step["project_id"])
    progress = await project_repo.compute_progress(db, step["project_id"])

    return StepResponse(
        step=StepDetail(
            id=step["id"],
            description=step["description"],
            estimated_min=step["estimated_min"],
            pattern=step["pattern"],
            step_type=step["step_type"],
            block_title=block["title"] if block else "",
            energy_level=step["energy_level"],
        ),
        project=ProjectSummary(
            id=project["id"],
            title=project["title"],
            progress_pct=progress,
        ),
    )


async def complete_step(db: aiosqlite.Connection, step_id: str) -> StepResponse:
    """
    Complete a step, advance block progress, then generate the next step.
    Returns StepResponse with feedback_message set.
    """
    step = await step_repo.get_by_id(db, step_id)
    if step is None:
        raise ValueError(f"Step not found: {step_id}")

    project_id = step["project_id"]
    block_id = step["block_id"]

    # Mark the current step done
    await step_repo.mark_completed(db, step_id)

    # Advance block progress
    delta = _progress_delta(step["step_type"], step["energy_level"])
    if block_id and delta > 0:
        await block_repo.advance_progress(db, block_id, delta)

    # Touch the project's updated_at
    await project_repo.touch(db, project_id)
    await db.commit()

    # Get block title for feedback
    block = await block_repo.get(db, block_id) if block_id else None
    feedback_message = f"{block['title']}已推进" if block else None

    # Generate next step
    response = await generate_next(db, project_id, "complete")
    response.feedback_message = feedback_message
    return response


async def skip_step(db: aiosqlite.Connection, step_id: str) -> StepResponse:
    """
    Skip a step (换一个). Records a rejection for diversity tracking,
    then generates a new step with the same trigger context.
    """
    step = await step_repo.get_by_id(db, step_id)
    if step is None:
        raise ValueError(f"Step not found: {step_id}")

    project_id = step["project_id"]

    await step_repo.mark_status(db, step_id, "skipped")

    # Record for diversity tracking if verb/object can be extracted
    _, _, verb, object_text = validate_step(step["description"])
    if verb and object_text:
        await diversity_service.record_rejection(
            db, project_id, step_id, verb, object_text, step["pattern"]
        )
    else:
        await db.commit()

    return await generate_next(db, project_id, "skip")


async def stuck_on_step(db: aiosqlite.Connection, step_id: str) -> StepResponse:
    """
    User is stuck. Marks step as stuck and generates a Decomposition step
    targeting the same block (simpler, same scope).
    """
    step = await step_repo.get_by_id(db, step_id)
    if step is None:
        raise ValueError(f"Step not found: {step_id}")

    project_id = step["project_id"]
    block_id = step["block_id"]

    await step_repo.mark_status(db, step_id, "stuck")
    await db.commit()

    return await generate_next(db, project_id, "stuck", current_block_id=block_id)
