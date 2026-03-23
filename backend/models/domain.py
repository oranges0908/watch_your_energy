from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class ProjectStatus(str, Enum):
    active = "active"
    completed = "completed"
    archived = "archived"


class BlockStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    near_complete = "near_complete"
    completed = "completed"


class StepPattern(str, Enum):
    Light = "Light"
    Continuation = "Continuation"
    Completion = "Completion"
    Decomposition = "Decomposition"
    Recovery = "Recovery"
    Refinement = "Refinement"


class StepType(str, Enum):
    Bootstrap = "Bootstrap"
    Push = "Push"
    Wrap = "Wrap"
    Transfer = "Transfer"


class EnergyMode(str, Enum):
    normal = "normal"
    low = "low"


class Trigger(str, Enum):
    auto = "auto"
    skip = "skip"
    stuck = "stuck"
    low_energy = "low_energy"
    resume = "resume"
    complete = "complete"


class StepStatus(str, Enum):
    pending = "pending"
    active = "active"
    completed = "completed"
    skipped = "skipped"
    stuck = "stuck"


# ── Domain Models ─────────────────────────────────────────────────────────────

class Project(BaseModel):
    id: str
    title: str
    status: ProjectStatus = ProjectStatus.active
    sort_order: int = 0
    progress_pct: int = Field(default=0, ge=0, le=100)
    created_at: int
    updated_at: int


class Block(BaseModel):
    id: str
    project_id: str
    title: str
    position: int
    status: BlockStatus = BlockStatus.not_started
    progress_pct: int = Field(default=0, ge=0, le=100)
    created_at: int
    updated_at: int


class Step(BaseModel):
    id: str
    project_id: str
    block_id: Optional[str] = None
    description: str
    pattern: StepPattern
    step_type: StepType
    estimated_min: int = Field(ge=5, le=20)
    energy_level: EnergyMode = EnergyMode.normal
    trigger: Trigger
    status: StepStatus = StepStatus.pending
    created_at: int
    completed_at: Optional[int] = None
    session_id: str


class StepRejection(BaseModel):
    id: str
    project_id: str
    step_id: str
    verb: str
    object_text: str
    pattern: StepPattern
    rejected_at: int


class Session(BaseModel):
    id: str
    started_at: int
    ended_at: Optional[int] = None
    energy_mode: EnergyMode = EnergyMode.normal


class AppState(BaseModel):
    id: int = 1
    active_project_id: Optional[str] = None
    active_session_id: Optional[str] = None
    energy_mode: EnergyMode = EnergyMode.normal
    onboarding_complete: bool = False


# ── Response Models ───────────────────────────────────────────────────────────

class StepDetail(BaseModel):
    """Step data returned to Flutter."""
    id: str
    description: str
    estimated_min: int
    pattern: StepPattern
    step_type: StepType
    block_title: str
    energy_level: EnergyMode


class ProjectSummary(BaseModel):
    """Project data returned to Flutter."""
    id: str
    title: str
    progress_pct: int


class StepResponse(BaseModel):
    """Unified response body for all step-mutating operations."""
    step: StepDetail
    project: ProjectSummary
    feedback_message: Optional[str] = None  # non-null only after 'complete'
