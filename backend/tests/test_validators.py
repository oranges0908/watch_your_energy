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
    "Optimize the wording of my resume",
    "Learn a new project management method",
    "Think about how to present project experience",
    "Modify the description of Part 1",
    "Understand the industry background",
    "Research competitor case studies",
    "Consider a better way to phrase this",
    "Organize the document structure",
])
def test_blacklist_rejected(desc):
    valid, error, verb, obj = validate_step(desc)
    assert not valid
    assert error is not None
    assert verb is None
    assert obj is None


# ── Valid step tests ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("desc,expected_verb", [
    ("Write the opening sentence of Part 2 (describe what you did)", "Write"),
    ("Trim the title of Part 1 to one line", "Trim"),
    ("Fill in your key takeaway in the Wrap-up block", "Fill"),
    ("List two unresolved issues remaining in Part 3", "List"),
    ("Check the wording of one completed paragraph in your project", "Check"),
    ("Complete the last blank field in the current block", "Complete"),
])
def test_valid_steps(desc, expected_verb):
    valid, error, verb, obj = validate_step(desc)
    assert valid, f"Expected valid but got error: {error}"
    assert error is None
    assert verb is not None
    assert obj is not None


# ── Length boundary tests ─────────────────────────────────────────────────────

def test_too_short():
    valid, error, _, _ = validate_step("Write it")
    assert not valid
    assert "short" in error or "format" in error.lower()


def test_too_long():
    long_desc = "Write " + "a very detailed description of the project content including all background context and additional notes " * 2
    valid, error, _, _ = validate_step(long_desc)
    assert not valid
    assert "long" in error or "format" in error.lower()


# ── Structure tests ───────────────────────────────────────────────────────────

def test_verb_only_fails():
    valid, error, _, _ = validate_step("Write a bit")
    # "Write a bit" is 11 chars — too short
    assert not valid


def test_returns_verb_and_object_on_success():
    valid, error, verb, obj = validate_step("Write the opening sentence of Part 2")
    assert valid
    assert verb is not None and len(verb) >= 1
    assert obj is not None and len(obj) >= 5


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
