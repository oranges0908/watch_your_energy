"""
Unit tests for agent/validators.py

Run:  cd backend && pytest tests/test_validators.py -v
"""
import pytest
import sys
import os

# Allow importing from backend root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agent.validators import validate_step, get_fallback, FALLBACK_STEPS


# ── Blacklist tests ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("desc", [
    "优化简历的措辞",
    "学习新的项目管理方法",
    "思考项目经历如何呈现",
    "修改项目1的描述",
    "了解行业背景",
    "研究竞争对手案例",
    "考虑更好的表达方式",
    "整理文档结构",
])
def test_blacklist_rejected(desc):
    valid, error, verb, obj = validate_step(desc)
    assert not valid
    assert error is not None
    assert verb is None
    assert obj is None


# ── Valid step tests ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("desc,expected_verb", [
    ("写项目2的第一句话（描述你做了什么）", "写"),
    ("把项目1的标题改成一行以内", "把"),
    ("在总结块中填入你的核心收获", "在总结块中填入"),
    ("列出项目3中还没解决的两个问题", "列出"),
    ("检查项目中一个已完成段落的措辞", "检查"),
    ("填写当前结构块中最后一个空白字段", "填写"),
])
def test_valid_steps(desc, expected_verb):
    valid, error, verb, obj = validate_step(desc)
    assert valid, f"Expected valid but got error: {error}"
    assert error is None
    assert verb is not None
    assert obj is not None


# ── Length boundary tests ─────────────────────────────────────────────────────

def test_too_short():
    valid, error, _, _ = validate_step("写文")
    assert not valid
    assert "太短" in error or "格式" in error


def test_too_long():
    long_desc = "写" + "项目1中关于具体工作内容的详细描述，包括所有背景信息和上下文" * 2
    valid, error, _, _ = validate_step(long_desc)
    assert not valid
    assert "太长" in error or "格式" in error


# ── Structure tests ───────────────────────────────────────────────────────────

def test_verb_only_fails():
    valid, error, _, _ = validate_step("写一下")
    assert not valid


def test_returns_verb_and_object_on_success():
    valid, error, verb, obj = validate_step("写项目2的第一句话")
    assert valid
    # Regex greedily matches up to 4 CJK chars as verb; "写项目" is a valid 3-char verb
    assert verb is not None and len(verb) >= 1
    assert obj is not None and len(obj) >= 4


# ── Fallback tests ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("pattern", [
    "Light", "Continuation", "Completion", "Decomposition", "Recovery", "Refinement"
])
def test_fallback_is_valid(pattern):
    fb = get_fallback(pattern)
    assert "description" in fb
    assert "estimated_min" in fb
    # Fallback steps must themselves pass validation
    valid, error, _, _ = validate_step(fb["description"])
    assert valid, f"Fallback for {pattern} failed validation: {error} — '{fb['description']}'"


def test_fallback_unknown_pattern_returns_refinement():
    fb = get_fallback("NonExistentPattern")
    assert fb == FALLBACK_STEPS["Refinement"]
