"""
3.5 — Hand-rolled MCP server. Raw JSON-RPC 2.0 over stdio.

We are deliberately NOT using the official `mcp` SDK. The point is to write
the JSON-RPC by hand so you understand exactly what bytes go over the wire.

Transport: newline-delimited JSON on stdin/stdout.
Each line in = one JSON-RPC request or notification.
Each line out = one JSON-RPC response.

CRITICAL RULE OF MCP STDIO:
    The server MUST NOT write anything to stdout except JSON-RPC messages.
    Any print() or logging() that hits stdout will corrupt the protocol and
    the client will crash. ALL logging goes to stderr.

Methods implemented:
    initialize                  → return server capabilities (handshake)
    notifications/initialized   → fire-and-forget from client, no response
    tools/list                  → return our tool catalog
    tools/call                  → execute a tool, return its result as content

What's NOT implemented (would be in a fuller server):
    resources/* prompts/* logging/* completion/* — out of scope for this lesson.

Run (you don't usually call this directly — client_demo.py or agent_mcp.py
spawns it as a subprocess):
    uv run python src/03-agent/mcp/server.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

# Make `tools` (the Phase 3.4 module) importable even when this server is
# spawned as a subprocess from elsewhere.
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools import TOOL_REGISTRY, TOOL_SCHEMAS  # noqa: E402

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "applied-ai-lab-buildingops"
SERVER_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Wire helpers
# ---------------------------------------------------------------------------
def log(*parts) -> None:
    """ALL server logging MUST go to stderr — see file docstring."""
    print(*parts, file=sys.stderr, flush=True)


def send_message(obj: dict) -> None:
    """Write one JSON-RPC message as a single line on stdout."""
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def send_response(req_id, result: dict) -> None:
    send_message({"jsonrpc": "2.0", "id": req_id, "result": result})


def send_error(req_id, code: int, message: str) -> None:
    send_message(
        {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
    )


# ---------------------------------------------------------------------------
# Schema translation: Anthropic tool schema  →  MCP tool schema
# Anthropic uses snake_case `input_schema`. MCP spec uses camelCase `inputSchema`.
# Same JSON Schema content, different field name. Worth knowing.
# ---------------------------------------------------------------------------
def to_mcp_tool(anthro_tool: dict) -> dict:
    return {
        "name": anthro_tool["name"],
        "description": anthro_tool["description"],
        "inputSchema": anthro_tool["input_schema"],
    }


MCP_TOOLS = [to_mcp_tool(t) for t in TOOL_SCHEMAS]


# ---------------------------------------------------------------------------
# Method handlers
# ---------------------------------------------------------------------------
def handle_initialize(req_id, params: dict) -> None:
    log(f"[server] initialize from client: {params.get('clientInfo', {})}")
    send_response(
        req_id,
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        },
    )


def handle_tools_list(req_id, params: dict) -> None:
    log(f"[server] tools/list — returning {len(MCP_TOOLS)} tools")
    send_response(req_id, {"tools": MCP_TOOLS})


def handle_tools_call(req_id, params: dict) -> None:
    name = params.get("name")
    arguments = params.get("arguments", {}) or {}
    log(f"[server] tools/call name={name} args={arguments}")

    fn = TOOL_REGISTRY.get(name)
    if fn is None:
        # MCP convention: tool errors are returned as result with isError=True,
        # NOT as a JSON-RPC error. JSON-RPC errors are for PROTOCOL errors.
        send_response(
            req_id,
            {
                "content": [{"type": "text", "text": f"ERROR: unknown tool '{name}'"}],
                "isError": True,
            },
        )
        return

    try:
        result = fn(**arguments)
        text = json.dumps(result, default=str)
        send_response(
            req_id,
            {"content": [{"type": "text", "text": text}], "isError": False},
        )
    except Exception as e:  # noqa: BLE001 — tool errors are part of agent input
        send_response(
            req_id,
            {
                "content": [
                    {
                        "type": "text",
                        "text": f"ERROR running {name}: {type(e).__name__}: {e}",
                    }
                ],
                "isError": True,
            },
        )


METHODS = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
}


# ---------------------------------------------------------------------------
# Main loop — read one JSON-RPC message per line from stdin
# ---------------------------------------------------------------------------
def main() -> None:
    log(f"[server] {SERVER_NAME} v{SERVER_VERSION} starting, awaiting messages on stdin")
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError as e:
            log(f"[server] bad JSON: {e}")
            continue

        method = msg.get("method")
        req_id = msg.get("id")  # absent on notifications

        # Notifications: no response expected
        if method == "notifications/initialized":
            log("[server] client signaled initialized; ready to serve")
            continue

        handler = METHODS.get(method)
        if handler is None:
            if req_id is not None:
                send_error(req_id, -32601, f"method not found: {method}")
            else:
                log(f"[server] ignoring unknown notification: {method}")
            continue

        handler(req_id, msg.get("params", {}) or {})


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("[server] interrupted, exiting cleanly")
