"""
Step-generation Agent.

Entry point: generate_step(trigger, project_id, energy_mode, session_id, db, [block_id])

Flow:
  1. select_pattern()          — deterministic, no LLM
  2. get_project_context       — loads blocks + recent steps
  3. select_target_block       — deterministic block selection
  4. get_recent_rejections     — diversity tracking
  5. generate_step_candidate   — the only LLM call
  6. validate_step_format      — format gate; retry up to MAX_LLM_RETRIES times
  7. save_generated_step       — persist to DB
  Returns StepOutput (dict with step_id, description, estimated_min, pattern,
                       step_type, block_id, block_title, energy_level)
"""
from __future__ import annotations

import logging
from typing import Optional

import aiosqlite

from config import MAX_LLM_RETRIES
from agent.tools import (
    tool_get_project_context,
    tool_select_target_block,
    tool_get_recent_rejections,
    tool_generate_step_candidate,
    tool_validate_step_format,
    tool_save_generated_step,
)
from agent.validators import get_fallback

logger = logging.getLogger(__name__)


# ── Pattern selection (deterministic) ────────────────────────────────────────

_TRIGGER_TO_PATTERN = {
    "low_energy": "Light",
    "stuck": "Decomposition",
    "resume": "Recovery",
    "complete": "Continuation",
    "skip": None,   # resolved dynamically (rotation)
    "auto": None,   # resolved from block status
}

_BLOCK_STATUS_TO_PATTERN = {
    "not_started": "Continuation",
    "in_progress": "Continuation",
    "near_complete": "Completion",
    "completed": "Refinement",
}


def select_pattern(trigger: str, block_status: Optional[str] = None) -> str:
    """
    Return the generation pattern for a given trigger.
    low_energy has highest priority regardless of other state.
    """
    if trigger == "low_energy":
        return "Light"

    fixed = _TRIGGER_TO_PATTERN.get(trigger)
    if fixed:
        return fixed

    # skip / auto → derive from block_status
    if block_status and block_status in _BLOCK_STATUS_TO_PATTERN:
        return _BLOCK_STATUS_TO_PATTERN[block_status]

    return "Refinement"


# ── Main agent entry point ────────────────────────────────────────────────────

async def generate_step(
    trigger: str,
    project_id: str,
    energy_mode: str,
    session_id: str,
    db: aiosqlite.Connection,
    current_block_id: Optional[str] = None,
) -> dict:
    """
    Orchestrate the full step-generation pipeline.

    Returns a StepOutput dict:
      step_id, description, estimated_min, pattern, step_type,
      block_id, block_title, energy_level
    """
    # ── Step 1: load project context ─────────────────────────────────────────
    context = await tool_get_project_context(db, project_id)
    blocks = context["blocks"]
    recent_steps = context["recent_steps"]

    # ── Step 2: select target block ───────────────────────────────────────────
    block_info = await tool_select_target_block(
        db, project_id, trigger, current_block_id
    )
    if "error" in block_info:
        logger.error("select_target_block error: %s", block_info["error"])
        raise RuntimeError(f"Cannot select block: {block_info['error']}")

    block_id: str = block_info["block_id"]
    block_title: str = block_info["block_title"]
    block_status: str = block_info["block_status"]
    step_type: str = block_info["step_type"]

    # ── Step 3: determine pattern ─────────────────────────────────────────────
    pattern = select_pattern(trigger, block_status)

    # In low-energy mode, always use Light pattern and override step_type
    if energy_mode == "low":
        pattern = "Light"

    # ── Step 4: get rejections for diversity ──────────────────────────────────
    rejections = await tool_get_recent_rejections(db, project_id)

    # ── Step 5+6: generate + validate (up to MAX_LLM_RETRIES + 1 attempts) ───
    description: Optional[str] = None
    estimated_min: int = 10
    error_hint: Optional[str] = None

    for attempt in range(MAX_LLM_RETRIES + 1):
        try:
            candidate = await tool_generate_step_candidate(
                project_title=_get_project_title(blocks),
                block_title=block_title,
                block_status=block_status,
                pattern=pattern,
                step_type=step_type,
                energy_mode=energy_mode,
                recent_steps=recent_steps,
                rejections=rejections,
                extra_hint=error_hint,
            )
        except Exception as exc:
            logger.warning("LLM call failed (attempt %d): %s", attempt + 1, exc)
            if attempt == MAX_LLM_RETRIES:
                fallback = get_fallback(pattern)
                description = fallback["description"]
                estimated_min = fallback["estimated_min"]
                break
            continue

        result = tool_validate_step_format(candidate["description"])
        if result["valid"]:
            description = candidate["description"]
            estimated_min = candidate["estimated_min"]
            break

        logger.info(
            "Validation failed (attempt %d): %s — %s",
            attempt + 1,
            candidate["description"],
            result["error"],
        )
        error_hint = f"The previously generated step \"{candidate['description']}\" failed validation: {result['error']}. Please regenerate and ensure the format is correct."

        if attempt == MAX_LLM_RETRIES:
            fallback = get_fallback(pattern)
            description = fallback["description"]
            estimated_min = fallback["estimated_min"]

    assert description is not None  # guaranteed by fallback path

    # Clamp estimated_min to [5, 20]
    estimated_min = max(5, min(20, estimated_min))

    # ── Step 7: persist ───────────────────────────────────────────────────────
    save_result = await tool_save_generated_step(
        db=db,
        project_id=project_id,
        block_id=block_id,
        description=description,
        pattern=pattern,
        step_type=step_type,
        estimated_min=estimated_min,
        energy_level=energy_mode,
        trigger=trigger,
        session_id=session_id,
    )

    return {
        "step_id": save_result["step_id"],
        "description": description,
        "estimated_min": estimated_min,
        "pattern": pattern,
        "step_type": step_type,
        "block_id": block_id,
        "block_title": block_title,
        "energy_level": energy_mode,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_project_title(blocks: list[dict]) -> str:
    """
    blocks don't carry the project title; this is a placeholder.
    The caller (step_service) should pass the title separately.
    For now we return a generic label — step_service will override via context injection.
    """
    return "(project)"
