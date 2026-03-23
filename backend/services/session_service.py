"""
Session lifecycle management and interruption detection.
"""
from __future__ import annotations

import time

import aiosqlite

from config import SESSION_GAP_HOURS
from repositories import state_repo


async def start_session(db: aiosqlite.Connection) -> str:
    """
    Start a new session (or continue an active one if the gap is small).

    Ends the previously active session if it exists.
    Returns the trigger to use for step generation:
      'resume'  — gap since last session > SESSION_GAP_HOURS
      'auto'    — first session or gap is within threshold
    """
    state = await state_repo.get_state(db)

    # End the currently active session if any
    if state["active_session_id"]:
        await state_repo.end_session(db, state["active_session_id"])

    # Check the most-recently ended session for interruption gap
    last = await state_repo.get_last_ended_session(db)
    trigger = "auto"
    if last and last["ended_at"]:
        gap_ms = time.time() * 1000 - last["ended_at"]
        gap_hours = gap_ms / (1000 * 3600)
        if gap_hours > SESSION_GAP_HOURS:
            trigger = "resume"

    # Create the new session
    await state_repo.create_session(db, state["energy_mode"])
    return trigger
