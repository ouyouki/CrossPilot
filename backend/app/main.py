"""FastAPI 适配层(装了 fastapi 时用这个;没装时退回 server.py)。

    uvicorn app.main:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from . import handlers, selection

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


@app.get("/api/v1/approvals")
def approvals() -> dict:
    return selection.approvals()


@app.post("/api/v1/approvals/selection")
def create_selection(payload: dict) -> JSONResponse:
    try:
        result = selection.create_selection(payload.get("subject_refs") or [])
    except selection.SelectionError as error:
        raise HTTPException(
            status_code=422,
            detail={"type": "about:blank", "title": error.code, "status": 422, "code": error.code, "detail": error.detail},
        ) from error
    return JSONResponse(status_code=201 if not result.get("duplicate") else 200, content=result)
