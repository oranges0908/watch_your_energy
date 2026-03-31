"""
Project creation, archival, and onboarding flow.
"""
from __future__ import annotations

import json
import logging
import re

import aiosqlite

from config import MAX_ACTIVE_PROJECTS
from repositories import project_repo, block_repo, state_repo
from services import step_service

logger = logging.getLogger(__name__)


async def suggest_block_titles(project_title: str) -> list[str]:
    """
    Ask the LLM to suggest 4 structure-block names for the given project goal.
    Falls back to generic titles on any error.
    """
    from agent.llm_client import generate_text  # avoid circular import at module load

    system = "You are a project structure planner. Help users break down their goal into 4 clear structure blocks."
    user = (
        f"Project goal: {project_title}\n"
        "Suggest 4 structure block names for this project:\n"
        "- Each name should be 2–5 words, directly reflecting specific project content\n"
        "- The first 3 are parallel main work areas; the last 1 is a wrap-up/summary\n"
        'Return only a JSON array, e.g.: ["Work Experience", "Project Experience", "Skills", "Final Polish"]'
    )
    try:
        text = await generate_text(system, user, max_tokens=20480)
        # Strip markdown code fences if present
        text = re.sub(r"^```[a-z]*\n?", "", text.strip())
        text = re.sub(r"\n?```$", "", text)
        data = json.loads(text)
        if isinstance(data, list) and len(data) == 4:
            return [str(s)[:20] for s in data]
    except Exception as exc:
        logger.warning("suggest_block_titles failed: %s", exc)
    return ["Part 1", "Part 2", "Part 3", "Wrap-up"]


async def create_project(
    db: aiosqlite.Connection,
    title: str,
    completed_block_ids_positions: list[int],
    block_titles: list[str] | None = None,
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
        raise ValueError(f"Maximum {MAX_ACTIVE_PROJECTS} active projects allowed")

    # Create project row
    project = await project_repo.create(db, title)
    project_id = project["id"]

    # Create 4 blocks — use LLM-suggested titles when provided
    blocks = await block_repo.create_bulk(db, project_id, titles=block_titles)

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
