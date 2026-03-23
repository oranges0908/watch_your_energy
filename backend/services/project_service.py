"""
Project creation, archival, and onboarding flow.
"""
from __future__ import annotations

import aiosqlite

from config import MAX_ACTIVE_PROJECTS
from repositories import project_repo, block_repo, state_repo
from services import step_service


async def create_project(
    db: aiosqlite.Connection,
    title: str,
    completed_block_ids_positions: list[int],
) -> dict:
    """
    Create a project with 4 fixed structure blocks.

    completed_block_ids_positions: 0-based position indices of blocks the
    user has already completed (selected in the creation flow).

    Returns: {"project": {...}, "block_ids": [...], "step_response": StepResponse}
    """
    # Enforce hard limit
    count = await project_repo.count_active(db)
    if count >= MAX_ACTIVE_PROJECTS:
        raise ValueError(f"最多{MAX_ACTIVE_PROJECTS}个活跃项目")

    # Create project row
    project = await project_repo.create(db, title)
    project_id = project["id"]

    # Create 4 fixed blocks
    blocks = await block_repo.create_bulk(db, project_id)

    # Mark user-selected blocks as already completed
    for pos in completed_block_ids_positions:
        if 0 <= pos < len(blocks):
            await block_repo.set_completed(db, blocks[pos]["id"])
    if completed_block_ids_positions:
        await db.commit()

    # Set as active project
    await state_repo.set_active_project(db, project_id)
    await state_repo.set_onboarding_complete(db)

    # Generate first step
    step_response = await step_service.generate_next(db, project_id, "auto")

    return {
        "project": project,
        "blocks": blocks,
        "step_response": step_response,
    }


async def archive_project(db: aiosqlite.Connection, project_id: str) -> None:
    """Soft-delete: set project status to 'archived'."""
    await project_repo.archive(db, project_id)

    # If this was the active project, clear app_state
    state = await state_repo.get_state(db)
    if state["active_project_id"] == project_id:
        # Try to switch to another active project
        others = await project_repo.list_active(db)
        next_id = others[0]["id"] if others else None
        await state_repo.set_active_project(db, next_id)


async def set_active_project(
    db: aiosqlite.Connection, project_id: str
) -> dict:
    """
    Switch the active project. Generates a new step for the newly-active project.
    Returns StepResponse.
    """
    await state_repo.set_active_project(db, project_id)
    await db.commit()
    return await step_service.generate_next(db, project_id, "auto")
