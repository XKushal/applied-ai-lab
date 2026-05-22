"""
Capstone API gateway — session 4b.

Endpoints:
  GET  /                          → serve the chat UI (index.html)
  GET  /health                    → liveness check
  GET  /tools                     → discovered MCP tools (handy for debugging)
  POST /chat                      → SSE stream of agent events
  POST /approvals/{approval_id}   → log a user's Approve/Deny decision

Run locally:
    cd src/04-capstone
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel

from .agent import CostCapExceeded, run_agent
from .mcp_client import MCPClient

load_dotenv()

ROOT = Path(__file__).parent.parent  # src/04-capstone/
MCP_SERVER_PATH = ROOT.parent / "03-agent" / "mcp" / "server.py"
FRONTEND_PATH = ROOT / "frontend" / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    mcp = MCPClient([sys.executable, str(MCP_SERVER_PATH)])
    info = mcp.initialize()
    tools = mcp.list_tools()
    print(f"  [api] MCP connected: {info['serverInfo']}", flush=True)
    print(f"  [api] tools available: {[t['name'] for t in tools]}", flush=True)
    app.state.mcp = mcp
    app.state.approvals: dict[str, dict] = {}
    try:
        yield
    finally:
        mcp.shutdown()


app = FastAPI(title="Building Ops Assistant API", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)


# -----------------------------------------------------------------------
class ChatRequest(BaseModel):
    query: str


class ApprovalDecision(BaseModel):
    approved: bool
    note: str | None = None


# -----------------------------------------------------------------------
@app.get("/")
def root() -> FileResponse:
    return FileResponse(FRONTEND_PATH)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/tools")
def tools() -> dict:
    return {"tools": app.state.mcp.list_tools()}


@app.post("/chat")
def chat(req: ChatRequest):
    """Stream agent events as Server-Sent Events (one JSON event per chunk)."""

    def event_stream():
        try:
            for event in run_agent(req.query, app.state.mcp):
                yield f"data: {json.dumps(event)}\n\n"
        except CostCapExceeded:
            # error event already yielded by the agent before raising
            pass
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/approvals/{approval_id}")
def record_approval(approval_id: str, decision: ApprovalDecision) -> dict:
    """Record a user decision on a pending approval.

    This is a PEDAGOGICAL stand-in for a real approval-gated workflow.
    In production: server would hold the agent loop in a session keyed by
    approval_id, and only resume on approve=True. Here we just log the
    decision so you can see the gate concept end-to-end in the UI.
    """
    app.state.approvals[approval_id] = decision.model_dump()
    print(f"  [api] approval {approval_id}: {decision}", flush=True)
    return {"approval_id": approval_id, "recorded": decision.model_dump()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
