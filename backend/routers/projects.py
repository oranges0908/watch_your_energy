"""
Routes: /projects
  GET    /projects            — list active projects
  POST   /projects            — create project
  GET    /projects/{id}       — project detail + blocks
  PATCH  /projects/{id}/active — switch active project
  DELETE /projects/{id}       — soft archive
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
import aiosqlite

from database import get_db_dep
from models.requests import CreateProjectRequest
from repositories import project_repo, block_repo, state_repo
from services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
async def list_projects(db: aiosqlite.Connection = Depends(get_db_dep)):
    projects = await project_repo.list_active(db)
    result = []
    for p in projects:
        progress = await project_repo.compute_progress(db, p["id"])
        result.append({**p, "progress_pct": progress})
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    body: CreateProjectRequest,
    db: aiosqlite.Connection = Depends(get_db_dep),
):
    try:
        result = await project_service.create_project(
            db,
            title=body.title,
            completed_block_ids_positions=body.completed_block_positions,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    resp = result["step_response"]
    return {
        "project": {**result["project"], "progress_pct": 0},
        "step": resp.step,
        "feedback_message": resp.feedback_message,
    }


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    db: aiosqlite.Connection = Depends(get_db_dep),
):
    project = await project_repo.get(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    blocks = await block_repo.get_by_project(db, project_id)
    progress = await project_repo.compute_progress(db, project_id)

    return {**project, "progress_pct": progress, "blocks": blocks}


@router.patch("/{project_id}/active")
async def set_active_project(
    project_id: str,
    db: aiosqlite.Connection = Depends(get_db_dep),
):
    project = await project_repo.get(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project["status"] != "active":
        raise HTTPException(status_code=400, detail="Project is not active")

    response = await project_service.set_active_project(db, project_id)
    return {"step": response.step, "project": response.project}


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_project(
    project_id: str,
    db: aiosqlite.Connection = Depends(get_db_dep),
):
    project = await project_repo.get(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    await project_service.archive_project(db, project_id)
