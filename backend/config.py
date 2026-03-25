import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "watch_your_energy.db")))

# Server
PORT: int = int(os.getenv("PORT", "8000"))

# LLM provider — "gemini" (default) or "anthropic"
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")

# Gemini
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Anthropic (fallback / alternative)
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

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
