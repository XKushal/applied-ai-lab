"""
Capstone API gateway.

POST /chat   { "query": "..." }    →   Server-Sent Events stream of events
GET  /health                       →   liveness check
GET  /tools                        →   what tools MCP has discovered

Run locally:
    OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \\
    uv run uvicorn src.04-capstone.app.main:app --reload --host 0.0.0.0 --port 8000

Or just inside docker-compose (see docker/docker-compose.yml).
"""

from __future__ import annotations

import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel

from .agent import run_agent
from .mcp_client import MCPClient
from .telemetry import tracer

load_dotenv()

# Path to the MCP server we built in Phase 3.5 — reused as-is.
MCP_SERVER_PATH = (
    Path(__file__).parent.parent.parent / "03-agent" / "mcp" / "server.py"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # spawn MCP server once at startup, reuse across requests
    mcp = MCPClient([sys.executable, str(MCP_SERVER_PATH)])
    info = mcp.initialize()
    tools = mcp.list_tools()
    print(f"  [api] MCP connected: {info['serverInfo']}", flush=True)
    print(f"  [api] tools available: {[t['name'] for t in tools]}", flush=True)
    app.state.mcp = mcp
    try:
        yield
    finally:
        mcp.shutdown()


app = FastAPI(title="Building Ops Assistant API", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/tools")
def tools() -> dict:
    return {"tools": app.state.mcp.list_tools()}


@app.post("/chat")
def chat(req: ChatRequest):
    """Stream agent events as Server-Sent Events (one JSON event per line)."""

    def event_stream():
        for event in run_agent(req.query, app.state.mcp):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    # so you can also `python -m src.04-capstone.app.main` for ad-hoc runs
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
