"""
Step format validator.

Two-pass validation:
  Pass 1 — blacklist: reject steps starting with vague verbs
  Pass 2 — structure: [verb] + [specific object], total 15-100 chars

Returns (is_valid: bool, error: str | None, verb: str | None, object_text: str | None)
"""
from __future__ import annotations
import re
from typing import Optional

# Verbs that indicate vague/non-actionable steps
BLACKLIST_VERBS = {"optimize", "learn", "think", "modify", "understand", "research", "consider", "organize"}

# Regex: first word (verb) + space + remaining content (object, ≥10 chars total after verb)
_VERB_RE = re.compile(r"^([A-Za-z\u4e00-\u9fff]{1,15})\s+(.{5,})$", re.DOTALL)

# Hardcoded fallback steps — guaranteed non-empty, one per pattern
FALLBACK_STEPS: dict[str, dict] = {
    "Light": {
        "description": "Review the most recently completed step in your current project",
        "estimated_min": 5,
    },
    "Continuation": {
        "description": "Write the first sentence of the next part of your project",
        "estimated_min": 10,
    },
    "Completion": {
        "description": "Fill in the last remaining blank field in the current block",
        "estimated_min": 10,
    },
    "Decomposition": {
        "description": "Break the current stuck task into two smaller steps and write them down",
        "estimated_min": 5,
    },
    "Recovery": {
        "description": "Skim through the content left from your last work session",
        "estimated_min": 5,
    },
    "Refinement": {
        "description": "Check the wording of one completed paragraph in your project",
        "estimated_min": 10,
    },
}


def validate_step(description: str) -> tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Validate a step description.

    Returns:
        (is_valid, error_message, verb, object_text)
        verb and object_text are None when is_valid is False.
    """
    description = description.strip()

    # Pass 1: blacklist
    first_word = description.split()[0].lower() if description.split() else ""
    if first_word in BLACKLIST_VERBS:
        return False, f"Step cannot start with \"{first_word}\" — use a more specific action verb", None, None

    # Pass 2: structure check
    total_len = len(description)
    if total_len < 15:
        return False, f"Step description too short ({total_len} chars), minimum 15 chars required", None, None
    if total_len > 100:
        return False, f"Step description too long ({total_len} chars), maximum 100 chars allowed", None, None

    m = _VERB_RE.match(description)
    if not m:
        return False, "Step format should be: [verb] + [specific object]", None, None

    verb = m.group(1)
    object_text = m.group(2).strip()

    return True, None, verb, object_text


def get_fallback(pattern: str) -> dict:
    """Return a guaranteed-valid fallback step for the given pattern."""
    return FALLBACK_STEPS.get(pattern, FALLBACK_STEPS["Refinement"])
