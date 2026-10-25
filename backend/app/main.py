"""FastAPI 适配层(装了 fastapi 时用这个;没装时退回 server.py)。

    uvicorn app.main:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI

from . import handlers

app = FastAPI(title="CrossPilot", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return handlers.health()


@app.get("/api/v1/today")
def today() -> dict:
    return handlers.today()


@app.get("/api/v1/candidates")
def candidates() -> dict:
    return handlers.candidates()
