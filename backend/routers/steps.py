"""
Routes: /steps
  GET  /steps/current  — current pending/active step for the active project
  POST /steps/start    — mark step as active (user tapped 开始)
  POST /steps/complete — complete step + generate next
  POST /steps/skip     — skip step (换一个) + generate next
  POST /steps/stuck    — mark stuck + generate Decomposition step
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from database import get_db_dep
from models.domain import StepDetail, ProjectSummary
from models.requests import StepActionRequest
from repositories import state_repo, project_repo, block_repo, step_repo
from services import step_service

router = APIRouter(prefix="/steps", tags=["steps"])


@router.get("/current")
async def get_current_step(db: aiosqlite.Connection = Depends(get_db_dep)):
    state = await state_repo.get_state(db)
    project_id = state["active_project_id"]
    if not project_id:
        raise HTTPException(status_code=404, detail="No active project")

    step_row = await step_repo.get_current(db, project_id)
    if step_row is None:
        raise HTTPException(status_code=404, detail="No current step")

    block = await block_repo.get(db, step_row["block_id"]) if step_row["block_id"] else None
    project = await project_repo.get(db, project_id)
    progress = await project_repo.compute_progress(db, project_id)

    return {
        "step": StepDetail(
            id=step_row["id"],
            description=step_row["description"],
            estimated_min=step_row["estimated_min"],
            pattern=step_row["pattern"],
            step_type=step_row["step_type"],
            block_title=block["title"] if block else "",
            energy_level=step_row["energy_level"],
        ),
        "project": ProjectSummary(
            id=project["id"],
            title=project["title"],
            progress_pct=progress,
        ),
    }


@router.post("/start")
async def start_step(
    body: StepActionRequest,
    db: aiosqlite.Connection = Depends(get_db_dep),
):
    try:
        response = await step_service.start_step(db, body.step_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"step": response.step, "project": response.project}


@router.post("/complete")
async def complete_step(
    body: StepActionRequest,
    db: aiosqlite.Connection = Depends(get_db_dep),
):
    try:
        response = await step_service.complete_step(db, body.step_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "step": response.step,
        "project": response.project,
        "feedback_message": response.feedback_message,
    }


@router.post("/skip")
async def skip_step(
    body: StepActionRequest,
    db: aiosqlite.Connection = Depends(get_db_dep),
):
    try:
        response = await step_service.skip_step(db, body.step_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"step": response.step, "project": response.project}


@router.post("/stuck")
async def stuck_step(
    body: StepActionRequest,
    db: aiosqlite.Connection = Depends(get_db_dep),
):
    try:
        response = await step_service.stuck_on_step(db, body.step_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"step": response.step, "project": response.project}
