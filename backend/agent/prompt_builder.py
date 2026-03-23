"""
Builds system and user prompts for the step-generation LLM call.
"""
from __future__ import annotations
from typing import Optional

SYSTEM_PROMPT = """\
你是一个行动引导助手，专门帮助用户在任意精力状态下推进项目进展。

## 你的任务
根据提供的上下文，生成**一条**下一步行动描述和预计所需时间。

## 步骤格式规则
格式：[动词1-4字] + [具体对象≥4字] + [可选范围限定]
总长度：8-30字

**合法示例：**
- 写项目2的第一句话（描述你做了什么）
- 把项目1的标题改成一行以内
- 在总结块中填入你的核心收获
- 列出项目3中还没解决的两个问题

**非法示例（拒绝这类表达）：**
- 优化简历（动词太模糊）
- 思考项目经历（动词禁用）
- 学习新技能（动词禁用，且对象不具体）
- 写（太短，缺少对象）

**禁用动词（不得以这些词开头）：**
优化、学习、思考、修改、了解、研究、考虑、整理

## 低能量模式规则
当 energy_mode = low 时：
- 步骤必须在5分钟内可完成
- 仅限这些类型：回顾型 / 微调型 / 确认型 / 整理型
- 仍必须推动结构性进展（不能是纯观察）

## 输出格式（严格JSON）
{
  "description": "步骤描述文字",
  "estimated_min": 数字（5到20之间的整数）
}
不要输出JSON之外的任何内容。\
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
        project_title: e.g. "优化简历"
        block_title: e.g. "项目1"
        block_status: e.g. "in_progress"
        pattern: one of Light|Continuation|Completion|Decomposition|Recovery|Refinement
        energy_mode: "normal" or "low"
        recent_steps: list of {"description": ..., "status": ...} (last 5 completed)
        rejections: list of {"verb": ..., "object_text": ...} (last 3 rejected)
        step_type: Bootstrap|Push|Wrap|Transfer
        extra_hint: optional extra instruction (e.g. for Decomposition: task to decompose)
    """
    lines: list[str] = []

    lines.append(f"## 当前项目\n项目名称：{project_title}")
    lines.append(f"当前结构块：{block_title}（状态：{block_status}）")
    lines.append(f"生成模式：{pattern}（步骤类型：{step_type}）")
    lines.append(f"能量模式：{energy_mode}")

    if recent_steps:
        lines.append("\n## 最近完成的步骤（最多5条，供参考上下文）")
        for s in recent_steps[-5:]:
            status_label = "✓" if s.get("status") == "completed" else "~"
            lines.append(f"  {status_label} {s['description']}")

    if rejections:
        lines.append("\n## 用户已拒绝的步骤（必须回避相似的动词+对象组合）")
        for r in rejections:
            lines.append(f"  - 动词「{r['verb']}」+ 对象「{r['object_text']}」")

    if extra_hint:
        lines.append(f"\n## 额外提示\n{extra_hint}")

    # Pattern-specific instructions
    pattern_hints = {
        "Light": "请生成一个极轻量的步骤，5分钟内可完成，类型限回顾/微调/确认/整理。",
        "Continuation": "请生成一个推进当前块进展的步骤，延续上一步的方向。",
        "Completion": "请生成一个帮助完成当前结构块剩余内容的步骤。",
        "Decomposition": "用户遇到了障碍。请把当前任务拆解成一个更小、更具体的步骤。",
        "Recovery": "用户刚刚回来，可能已中断一段时间。请生成一个低门槛的再入口步骤，不要引用上次未完成的内容。",
        "Refinement": "请生成一个打磨/细化已有内容的步骤。",
    }
    if pattern in pattern_hints:
        lines.append(f"\n## 模式说明\n{pattern_hints[pattern]}")

    lines.append("\n请严格按照JSON格式输出，不要包含任何其他文字。")

    return "\n".join(lines)
