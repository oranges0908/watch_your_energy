# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

Full MVP implementation complete (I1–I7). Docker + Railway deployment configured. All design documents are in `doc/`.

## Product Overview

**Energy-Based Progress App** — a behavior-guidance tool that gives users one immediately executable next step at all times, preventing progress from stalling across any energy state.

Core design philosophy: the app does not help users "manage tasks" — it keeps users in a state of "always advancing something."

## Key Design Documents

- `doc/产品需求.md` — Full product requirements (MVP): core objects, 7 use-case scenarios, Step generation rules, Project management
- `doc/UI.md` — UI design spec: 3 pages + 1 sidebar, interaction paths, layout structure
- `doc/系统架构.md` — Full system architecture: DB schema, API endpoints, Agent design, Flutter structure, key data flows

## Core Domain Model

```
Project (max 3, hard limit)
  └── Structure Blocks (e.g. 项目1 / 项目2 / 项目3 / 总结)
        └── Step (system-generated, 5–20 min, bound to a block)
              └── Pattern (generation rule)
```

**Step generation patterns (priority order):**

| Trigger | Pattern |
| --- | --- |
| User selected low-energy mode | Light |
| Just completed a step | Continuation |
| Incomplete structure block exists | Completion |
| User hit "stuck" | Decomposition |
| Returned after interruption | Recovery |
| Default | Refinement |

**Step format constraint:** `[verb] + [specific object] + [optional scope]`
- Valid: `写项目2的第一句话（描述你做了什么）`
- Invalid: `优化简历` / `思考项目经历`

## UI Architecture

3 pages + 1 sidebar (non-independent):

1. **Home (Current Step)** — sole entry point; shows one Step, three buttons: 开始 / 换一个 / 我卡住了
2. **Project Progress Page** — shows structure blocks and completion state; no task list, no Step history
3. **Project Creation Page** — 2-step flow: input goal (1 sentence) → select completed blocks
4. **Project Sidebar** — slides in from left (~40% width); lists up to 3 Projects with progress %; "＋ New" disabled when at limit

Home page layout (top → bottom):
- Project info bar: name + progress% + "切换" button (triggers sidebar)
- Energy mode toggle: `[⚡ 正常]` / `[🌙 低能量]`
- Step card: description (1–2 lines) + estimated time
- Action buttons: 开始 (primary) / 换一个 / 我卡住了

## Development Commands

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload          # dev server (port 8000)
pytest                             # all tests
pytest tests/test_validators.py    # single test file

# Frontend
cd frontend
flutter pub get
flutter run                        # run on connected device/emulator
flutter test                       # all widget/unit tests
flutter test test/providers/       # single directory

# Docker (local) — Gemini is default
GEMINI_API_KEY=<key> docker compose up --build      # start backend on :8000
LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=<key> docker compose up --build
docker compose down                                  # stop
docker compose down -v                               # stop + delete volume (wipes DB)
```

## Deployment

**Docker**: backend only (`backend/Dockerfile`). SQLite data is persisted via a named volume (`db_data`).

**Railway**:
- `railway.toml` at repo root — points to `backend/Dockerfile`, sets healthcheck on `/docs`
- Required env vars: `DB_PATH=/data/watch_your_energy.db` + LLM key (see below)
- Add a Railway Volume mounted at `/data` to persist the SQLite file across deploys
- Optional: `ALLOWED_ORIGINS` (comma-separated) for additional CORS origins

**LLM env vars** (`LLM_PROVIDER` defaults to `"gemini"`):

| Provider | Env vars required |
|---|---|
| Gemini (default) | `GEMINI_API_KEY`, optionally `GEMINI_MODEL` (default: `gemini-2.0-flash`) |
| Anthropic | `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, optionally `ANTHROPIC_MODEL` |

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11+ · FastAPI · aiosqlite |
| Frontend | Flutter · Riverpod 2.x · go_router · Dio |
| Database | SQLite (5 tables: projects, blocks, steps, step_rejections, sessions + app_state) |
| LLM | Anthropic Claude API · tool-calling Agent pattern |

## Backend Directory Layout

```
backend/
├── main.py / config.py / database.py
├── routers/      projects.py · steps.py · blocks.py · state.py
├── services/     project_service · step_service · session_service · diversity_service
├── repositories/ project_repo · block_repo · step_repo · state_repo
├── agent/        agent.py · tools.py · prompt_builder.py · validators.py
└── models/       domain.py · requests.py
```

## Flutter Directory Layout

```
lib/
├── main.dart / app.dart
├── models/    project · step · app_state
├── providers/ app_state_provider (core) · project_provider · feedback_provider
├── services/  api_service.dart (all HTTP calls)
├── pages/     home · progress · create_project
├── widgets/   step_card · project_header · energy_toggle · action_buttons
│              execution_overlay · completion_flash · project_sidebar · block_list_item
└── theme/     app_theme.dart
```

## Implementation Order

Build in this order — each layer depends on the previous:
1. `backend/database.py` — DDL schema
2. `backend/agent/validators.py` — Step format gate (unit-testable standalone)
3. `backend/models/domain.py` — Pydantic models shared by all layers
4. `backend/agent/agent.py` — Pattern selection + tool orchestration + retry + fallback
5. `backend/services/step_service.py` — Orchestration hub connecting HTTP → Agent → DB
6. `lib/providers/app_state_provider.dart` — Flutter's single source of truth

## Critical Constraints to Enforce in Code

- Home page must **never** show an empty Step state
- All Steps must be bound to a Project and a structure block
- Project count hard limit: **3**
- Low-energy mode is **user-initiated** (not inferred); system responds with lighter Step variants
- On return after interruption: do **not** restore the previous Step — generate a fresh, lower-barrier one
- Step diversity: track last 3 rejected Steps to avoid regenerating similar verb+object combinations
