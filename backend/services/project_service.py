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

    system = "你是项目结构规划助手，帮用户将目标拆解为4个清晰的结构块。"
    user = (
        f"项目目标：{project_title}\n"
        "请为该项目推荐4个结构块名称，要求：\n"
        "- 每个名称2-8字，直接体现项目具体内容\n"
        "- 前3个是并列的主要工作内容，最后1个是收尾/总结类\n"
        '只返回JSON数组，例：["工作经历", "项目经历", "技能介绍", "整体润色"]'
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
    return ["项目1", "项目2", "项目3", "总结"]


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
        raise ValueError(f"最多{MAX_ACTIVE_PROJECTS}个活跃项目")

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
