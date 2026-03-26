"""
FastAPI application entry point.

Run:  cd backend && uvicorn main:app --reload
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import state, projects, steps, blocks

# LOG_LEVEL controls verbosity. Set to DEBUG to see full LLM input/output.
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="WatchYourEnergy", lifespan=lifespan)

_extra_origins = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://10.0.2.2:*"] + _extra_origins,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(state.router)
app.include_router(projects.router)
app.include_router(steps.router)
app.include_router(blocks.router)
