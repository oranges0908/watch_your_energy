"""
Step format validator.

Two-pass validation:
  Pass 1 — blacklist: reject steps starting with vague verbs
  Pass 2 — structure: [verb 1-4 chars] + [specific object ≥4 chars], total 8-30 chars

Returns (is_valid: bool, error: str | None, verb: str | None, object_text: str | None)
"""
from __future__ import annotations
import re
from typing import Optional

# Verbs that indicate vague/non-actionable steps
BLACKLIST_VERBS = {"优化", "学习", "思考", "修改", "了解", "研究", "考虑", "整理"}

# Regex: verb (1-4 CJK or ASCII chars) followed by space or directly by object
# Object must be ≥4 chars; total description 8-30 chars
_VERB_RE = re.compile(r"^([\u4e00-\u9fffA-Za-z]{1,4})([\u4e00-\u9fffA-Za-z0-9（）()，,、\-·\s]{4,})$")

# Hardcoded fallback steps — guaranteed non-empty, one per pattern
FALLBACK_STEPS: dict[str, dict] = {
    "Light": {
        "description": "回顾当前项目的最近一个完成步骤",
        "estimated_min": 5,
    },
    "Continuation": {
        "description": "写下项目下一部分的第一句话",
        "estimated_min": 10,
    },
    "Completion": {
        "description": "填写当前结构块中最后一个空白字段",
        "estimated_min": 10,
    },
    "Decomposition": {
        "description": "把当前卡住的任务拆成两个更小的步骤并写下来",
        "estimated_min": 5,
    },
    "Recovery": {
        "description": "浏览一遍上次工作留下的内容",
        "estimated_min": 5,
    },
    "Refinement": {
        "description": "检查项目中一个已完成段落的措辞",
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
    for bad_verb in BLACKLIST_VERBS:
        if description.startswith(bad_verb):
            return False, f"步骤不能以「{bad_verb}」开头，请用更具体的动作动词", None, None

    # Pass 2: structure check
    total_len = len(description)
    if total_len < 8:
        return False, f"步骤描述太短（{total_len}字），至少需要8字", None, None
    if total_len > 30:
        return False, f"步骤描述太长（{total_len}字），不能超过30字", None, None

    m = _VERB_RE.match(description)
    if not m:
        return False, "步骤格式应为：[动词1-4字] + [具体对象≥4字]", None, None

    verb = m.group(1)
    object_text = m.group(2).strip()

    return True, None, verb, object_text


def get_fallback(pattern: str) -> dict:
    """Return a guaranteed-valid fallback step for the given pattern."""
    return FALLBACK_STEPS.get(pattern, FALLBACK_STEPS["Refinement"])
