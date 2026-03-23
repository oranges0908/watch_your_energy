import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "watch_your_energy.db"

# LLM
LLM_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL = "claude-sonnet-4-6"

# Session
SESSION_GAP_HOURS: float = 2.0

# Block progress deltas (percentage points)
PROGRESS_DELTA: dict[str, int] = {
    "Bootstrap": 20,
    "Push": 15,
    "Wrap": 10,
    "Transfer": 0,
    "Low": 5,  # applies to any step type when energy_mode == 'low'
}

# Step generation
MAX_LLM_RETRIES = 2
REJECTION_HISTORY_SIZE = 3  # per project

# Project limit
MAX_ACTIVE_PROJECTS = 3
