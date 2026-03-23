"""
Routes: /projects/{id}/blocks
  GET /projects/{project_id}/blocks — return all blocks for a project (progress page)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from database import get_db_dep
from repositories import project_repo, block_repo

router = APIRouter(tags=["blocks"])


@router.get("/projects/{project_id}/blocks")
async def get_blocks(
    project_id: str,
    db: aiosqlite.Connection = Depends(get_db_dep),
):
    project = await project_repo.get(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    blocks = await block_repo.get_by_project(db, project_id)
    return blocks
