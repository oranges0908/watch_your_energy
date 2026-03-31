"""
Builds system and user prompts for the step-generation LLM call.
"""
from __future__ import annotations
from typing import Optional

SYSTEM_PROMPT = """\
You are an action-guidance assistant that helps users make progress on their projects at any energy level.

## Your task
Based on the provided context, generate **one** next-action description and estimated time.

## Step format rules
Format: [verb] + [specific object] + [optional scope]
Length: 15–100 characters

**Valid examples:**
- Write the opening sentence of Part 2 (describe what you did)
- Trim the title of Part 1 to one line
- Fill in your key takeaway in the Wrap-up block
- List two unresolved issues remaining in Part 3

**Invalid examples (reject these):**
- Improve resume (verb too vague)
- Think about project experience (forbidden verb)
- Learn a new skill (forbidden verb, object not specific)
- Write (too short, missing object)

**Forbidden verbs (do not start with these):**
optimize, learn, think, modify, understand, research, consider, organize

## Low-energy mode rules
When energy_mode = low:
- Step must be completable within 5 minutes
- Restricted to these types: review / micro-edit / confirm / tidy
- Must still drive structural progress (not pure observation)

## Output format (strict JSON)
{
  "description": "step description text",
  "estimated_min": number (integer between 5 and 20)
}
Do not output anything outside the JSON.\
"""


def build_user_prompt(
    project_title: str,
    block_title: str,
    block_status: str,
    pattern: str,
    energy_mode: str,
    recent_steps: list[dict],
    rejections: list[dict],
    step_type: str,
    extra_hint: Optional[str] = None,
) -> str:
    """
    Construct the user-turn prompt for generate_step_candidate.

    Args:
        project_title: e.g. "Improve my resume"
        block_title: e.g. "Part 1"
        block_status: e.g. "in_progress"
        pattern: one of Light|Continuation|Completion|Decomposition|Recovery|Refinement
        energy_mode: "normal" or "low"
        recent_steps: list of {"description": ..., "status": ...} (last 5 completed)
        rejections: list of {"verb": ..., "object_text": ...} (last 3 rejected)
        step_type: Bootstrap|Push|Wrap|Transfer
        extra_hint: optional extra instruction (e.g. for Decomposition: task to decompose)
    """
    lines: list[str] = []

    lines.append(f"## Current project\nProject: {project_title}")
    lines.append(f"Current block: {block_title} (status: {block_status})")
    lines.append(f"Generation pattern: {pattern} (step type: {step_type})")
    lines.append(f"Energy mode: {energy_mode}")

    if recent_steps:
        lines.append("\n## Recently completed steps (up to 5, for context)")
        for s in recent_steps[-5:]:
            status_label = "✓" if s.get("status") == "completed" else "~"
            lines.append(f"  {status_label} {s['description']}")

    if rejections:
        lines.append("\n## Steps already rejected by user (avoid similar verb+object combinations)")
        for r in rejections:
            lines.append(f"  - verb \"{r['verb']}\" + object \"{r['object_text']}\"")

    if extra_hint:
        lines.append(f"\n## Extra hint\n{extra_hint}")

    # Pattern-specific instructions
    pattern_hints = {
        "Light": "Generate a very lightweight step, completable within 5 minutes, restricted to review/micro-edit/confirm/tidy types.",
        "Continuation": "Generate a step that advances the current block's progress, continuing in the direction of the previous step.",
        "Completion": "Generate a step that helps finish the remaining content of the current structure block.",
        "Decomposition": "The user is stuck. Break the current task down into a smaller, more concrete step.",
        "Recovery": "The user just returned, possibly after a break. Generate a low-barrier re-entry step — do not reference any previously unfinished content.",
        "Refinement": "Generate a step that polishes or refines existing content.",
    }
    if pattern in pattern_hints:
        lines.append(f"\n## Pattern guidance\n{pattern_hints[pattern]}")

    lines.append("\nOutput strictly in JSON format, no other text.")

    return "\n".join(lines)
