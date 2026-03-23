"""
Routes: /state
  GET  /state          — current step + project + energy_mode
  PATCH /state/energy  — switch energy mode (triggers step regeneration)
  POST /state/session  — call on app open; handles interruption detection
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from database import get_db_dep
from models.domain import StepDetail, ProjectSummary, EnergyMode
from models.requests import EnergyModeRequest
from repositories import state_repo, project_repo, block_repo, step_repo
from services import session_service, step_service

router = APIRouter(prefix="/state", tags=["state"])


@router.get("")
async def get_state(db: aiosqlite.Connection = Depends(get_db_dep)):
    state = await state_repo.get_state(db)
    project_id = state["active_project_id"]

    if not project_id:
        return {
            "step": None,
            "project": None,
            "energy_mode": state["energy_mode"],
            "onboarding_complete": state["onboarding_complete"],
        }

    project = await project_repo.get(db, project_id)
    if project is None:
        return {
            "step": None,
            "project": None,
            "energy_mode": state["energy_mode"],
            "onboarding_complete": state["onboarding_complete"],
        }

    progress = await project_repo.compute_progress(db, project_id)
    step_row = await step_repo.get_current(db, project_id)

    if step_row is None:
        # Auto-generate so home page is never empty
        response = await step_service.generate_next(db, project_id, "auto")
        return {
            "step": response.step,
            "project": response.project,
            "energy_mode": state["energy_mode"],
            "onboarding_complete": state["onboarding_complete"],
        }

    block = await block_repo.get(db, step_row["block_id"]) if step_row["block_id"] else None
    step_detail = StepDetail(
        id=step_row["id"],
        description=step_row["description"],
        estimated_min=step_row["estimated_min"],
        pattern=step_row["pattern"],
        step_type=step_row["step_type"],
        block_title=block["title"] if block else "",
        energy_level=step_row["energy_level"],
    )
    project_summary = ProjectSummary(
        id=project["id"],
        title=project["title"],
        progress_pct=progress,
    )
    return {
        "step": step_detail,
        "project": project_summary,
        "energy_mode": state["energy_mode"],
        "onboarding_complete": state["onboarding_complete"],
    }


@router.patch("/energy")
async def set_energy_mode(
    body: EnergyModeRequest,
    db: aiosqlite.Connection = Depends(get_db_dep),
):
    """
    Switch energy mode. Skips the current pending step and generates a new one
    using the updated mode (Light pattern for low, auto for normal).
    """
    await state_repo.set_energy_mode(db, body.mode.value)

    state = await state_repo.get_state(db)
    project_id = state["active_project_id"]
    if not project_id:
        return {"energy_mode": body.mode.value, "step": None, "project": None}

    # Skip the current pending step so a fresh one is generated
    await step_repo.skip_all_pending(db, project_id)
    await db.commit()

    trigger = "low_energy" if body.mode == EnergyMode.low else "auto"
    response = await step_service.generate_next(db, project_id, trigger)

    return {
        "energy_mode": body.mode.value,
        "step": response.step,
        "project": response.project,
    }


@router.post("/session")
async def start_session(db: aiosqlite.Connection = Depends(get_db_dep)):
    """
    Call when the app opens.
    Creates a new session (ending the previous one) and detects interruptions.
    If trigger=resume, replaces the current step with a Recovery-pattern step.
    """
    trigger = await session_service.start_session(db)

    state = await state_repo.get_state(db)
    project_id = state["active_project_id"]

    if not project_id:
        return {"trigger": trigger, "step": None, "project": None}

    if trigger == "resume":
        # Replace any stale pending step with a fresh recovery step
        await step_repo.skip_all_pending(db, project_id)
        await db.commit()
        response = await step_service.generate_next(db, project_id, "resume")
        return {"trigger": trigger, "step": response.step, "project": response.project}

    # trigger=auto: ensure there is a current step (generate if missing)
    step_row = await step_repo.get_current(db, project_id)
    if step_row is None:
        response = await step_service.generate_next(db, project_id, "auto")
        return {"trigger": trigger, "step": response.step, "project": response.project}

    block = await block_repo.get(db, step_row["block_id"]) if step_row["block_id"] else None
    project = await project_repo.get(db, project_id)
    progress = await project_repo.compute_progress(db, project_id)

    step_detail = StepDetail(
        id=step_row["id"],
        description=step_row["description"],
        estimated_min=step_row["estimated_min"],
        pattern=step_row["pattern"],
        step_type=step_row["step_type"],
        block_title=block["title"] if block else "",
        energy_level=step_row["energy_level"],
    )
    project_summary = ProjectSummary(
        id=project["id"],
        title=project["title"],
        progress_pct=progress,
    )
    return {"trigger": trigger, "step": step_detail, "project": project_summary}
