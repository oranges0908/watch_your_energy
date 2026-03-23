"""
FastAPI request / response schema models.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from models.domain import EnergyMode


class CreateProjectRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=50)
    # 0-based position indices of blocks already completed by the user
    completed_block_positions: List[int] = []


class EnergyModeRequest(BaseModel):
    mode: EnergyMode


class StepActionRequest(BaseModel):
    step_id: str
