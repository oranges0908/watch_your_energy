"""
Tool implementations and Anthropic tool-schema definitions for the Step-generation Agent.

Tools:
  get_project_context      — loads blocks + recent completed steps + last session
  select_target_block      — deterministic block selection by status
  get_recent_rejections    — last N rejected steps for diversity enforcement
  generate_step_candidate  — the only LLM call; returns description + estimated_min
  validate_step_format     — format check; returns pass/fail + extracted verb/object
  save_generated_step      — persists the validated step to DB
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, Optional

import anthropic
import aiosqlite

from config import LLM_API_KEY, LLM_MODEL, REJECTION_HISTORY_SIZE
from agent.validators import validate_step, get_fallback
from agent.prompt_builder import SYSTEM_PROMPT, build_user_prompt


# ── Tool JSON Schemas (used by Anthropic tool-calling API) ────────────────────

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "get_project_context",
        "description": "Load project blocks state and recent completed steps to build generation context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "UUID of the project"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "select_target_block",
        "description": (
            "Deterministically select which block to target for the next step. "
            "Rules: not_started→Bootstrap, in_progress→Push, near_complete→Wrap, "
            "all_completed→Transfer (next project). "
            "When trigger=stuck, always return the currently active block."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "trigger": {"type": "string", "description": "auto|skip|stuck|low_energy|resume|complete"},
                "current_block_id": {
                    "type": "string",
                    "description": "Required when trigger=stuck; must return this block.",
                },
            },
            "required": ["project_id", "trigger"],
        },
    },
    {
        "name": "get_recent_rejections",
        "description": "Return the most recent rejected step verb+object pairs for a project (diversity enforcement).",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "generate_step_candidate",
        "description": "Call the LLM to generate a step description and estimated_min. This is the only tool that calls the LLM.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_title": {"type": "string"},
                "block_title": {"type": "string"},
                "block_status": {"type": "string"},
                "pattern": {"type": "string"},
                "step_type": {"type": "string"},
                "energy_mode": {"type": "string"},
                "recent_steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "status": {"type": "string"},
                        },
                    },
                },
                "rejections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "verb": {"type": "string"},
                            "object_text": {"type": "string"},
                        },
                    },
                },
                "extra_hint": {"type": "string"},
            },
            "required": [
                "project_title", "block_title", "block_status",
                "pattern", "step_type", "energy_mode",
                "recent_steps", "rejections",
            ],
        },
    },
    {
        "name": "validate_step_format",
        "description": "Validate a generated step description for format compliance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
            },
            "required": ["description"],
        },
    },
    {
        "name": "save_generated_step",
        "description": "Persist the validated step to the database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "block_id": {"type": "string"},
                "description": {"type": "string"},
                "pattern": {"type": "string"},
                "step_type": {"type": "string"},
                "estimated_min": {"type": "integer"},
                "energy_level": {"type": "string"},
                "trigger": {"type": "string"},
                "session_id": {"type": "string"},
            },
            "required": [
                "project_id", "block_id", "description", "pattern",
                "step_type", "estimated_min", "energy_level", "trigger", "session_id",
            ],
        },
    },
]


# ── Tool implementations ──────────────────────────────────────────────────────

async def tool_get_project_context(db: aiosqlite.Connection, project_id: str) -> dict:
    """Return blocks list + last 5 completed steps for a project."""
    async with db.execute(
        "SELECT id, title, position, status, progress_pct FROM blocks "
        "WHERE project_id = ? ORDER BY position",
        (project_id,),
    ) as cur:
        rows = await cur.fetchall()
    blocks = [dict(r) for r in rows]

    async with db.execute(
        "SELECT description, status FROM steps "
        "WHERE project_id = ? AND status = 'completed' "
        "ORDER BY completed_at DESC LIMIT 5",
        (project_id,),
    ) as cur:
        rows = await cur.fetchall()
    recent_steps = [dict(r) for r in rows]

    async with db.execute(
        "SELECT s.started_at, s.ended_at FROM sessions s "
        "JOIN app_state a ON a.active_session_id = s.id LIMIT 1"
    ) as cur:
        session_row = await cur.fetchone()
    last_session = dict(session_row) if session_row else None

    return {"blocks": blocks, "recent_steps": recent_steps, "last_session": last_session}


async def tool_select_target_block(
    db: aiosqlite.Connection,
    project_id: str,
    trigger: str,
    current_block_id: Optional[str] = None,
) -> dict:
    """Deterministically select the target block based on trigger and block states."""
    # When stuck, always stay on the same block
    if trigger == "stuck" and current_block_id:
        async with db.execute(
            "SELECT id, title, status, position FROM blocks WHERE id = ?",
            (current_block_id,),
        ) as cur:
            row = await cur.fetchone()
        if row:
            return {"block_id": row["id"], "block_title": row["title"],
                    "block_status": row["status"], "step_type": "Push"}

    async with db.execute(
        "SELECT id, title, position, status FROM blocks "
        "WHERE project_id = ? ORDER BY position",
        (project_id,),
    ) as cur:
        rows = await cur.fetchall()
    blocks = [dict(r) for r in rows]

    if not blocks:
        return {"error": "no_blocks"}

    # Status → step_type mapping
    status_to_type = {
        "not_started": "Bootstrap",
        "in_progress": "Push",
        "near_complete": "Wrap",
    }

    for block in blocks:
        st = block["status"]
        if st in status_to_type:
            return {
                "block_id": block["id"],
                "block_title": block["title"],
                "block_status": st,
                "step_type": status_to_type[st],
            }

    # All blocks completed → Transfer
    last = blocks[-1]
    return {
        "block_id": last["id"],
        "block_title": last["title"],
        "block_status": last["status"],
        "step_type": "Transfer",
    }


async def tool_get_recent_rejections(
    db: aiosqlite.Connection, project_id: str
) -> list[dict]:
    """Return last REJECTION_HISTORY_SIZE rejected step verb+object pairs."""
    async with db.execute(
        "SELECT verb, object_text FROM step_rejections "
        "WHERE project_id = ? ORDER BY rejected_at DESC LIMIT ?",
        (project_id, REJECTION_HISTORY_SIZE),
    ) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def tool_generate_step_candidate(
    project_title: str,
    block_title: str,
    block_status: str,
    pattern: str,
    step_type: str,
    energy_mode: str,
    recent_steps: list[dict],
    rejections: list[dict],
    extra_hint: Optional[str] = None,
) -> dict:
    """Call the Claude API to generate a step candidate. Returns {description, estimated_min}."""
    user_prompt = build_user_prompt(
        project_title=project_title,
        block_title=block_title,
        block_status=block_status,
        pattern=pattern,
        energy_mode=energy_mode,
        recent_steps=recent_steps,
        rejections=rejections,
        step_type=step_type,
        extra_hint=extra_hint,
    )

    client = anthropic.Anthropic(api_key=LLM_API_KEY)
    message = client.messages.create(
        model=LLM_MODEL,
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text = message.content[0].text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    data = json.loads(text)
    return {
        "description": str(data["description"]).strip(),
        "estimated_min": int(data["estimated_min"]),
    }


def tool_validate_step_format(description: str) -> dict:
    """Run the two-pass validator. Returns {valid, error, verb, object_text}."""
    is_valid, error, verb, object_text = validate_step(description)
    return {
        "valid": is_valid,
        "error": error,
        "verb": verb,
        "object_text": object_text,
    }


async def tool_save_generated_step(
    db: aiosqlite.Connection,
    project_id: str,
    block_id: str,
    description: str,
    pattern: str,
    step_type: str,
    estimated_min: int,
    energy_level: str,
    trigger: str,
    session_id: str,
) -> dict:
    """Insert the validated step into the DB and return its id."""
    step_id = str(uuid.uuid4())
    now = int(time.time() * 1000)

    await db.execute(
        """
        INSERT INTO steps
            (id, project_id, block_id, description, pattern, step_type,
             estimated_min, energy_level, trigger, status, created_at, session_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        """,
        (step_id, project_id, block_id, description, pattern, step_type,
         estimated_min, energy_level, trigger, now, session_id),
    )
    await db.commit()

    return {"step_id": step_id, "created_at": now}
