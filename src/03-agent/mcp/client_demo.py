"""
3.5 — Tiny MCP client demo. Walks the protocol WITHOUT an LLM.

Spawns server.py as a subprocess, talks JSON-RPC over its stdin/stdout, and
prints every message that crosses the wire. This is the "naked protocol"
view — same purpose as 02_retrieve.py was for RAG: see the primitive
without a model muddying the picture.

Run:
    uv run python src/03-agent/mcp/client_demo.py

What to observe:
1. The handshake — `initialize` request, server response, then the
   `notifications/initialized` (no response — it's fire-and-forget).
2. `tools/list` — server returns the same two tools we have in tools.py,
   with `inputSchema` (camelCase, MCP-flavor — NOT `input_schema`).
3. `tools/call` — server returns `content` (list of blocks), with
   `isError` boolean. Note that tool ERRORS come back as result+isError,
   NOT as JSON-RPC errors. Only PROTOCOL errors use JSON-RPC error.
4. Server logs appear on stderr (we route them to print() so you can see them
   interleaved with the wire transcript).
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path

SERVER_PATH = Path(__file__).parent / "server.py"


def pretty(direction: str, msg: dict) -> None:
    arrow = "→" if direction == "send" else "←"
    color = "\033[34m" if direction == "send" else "\033[32m"
    reset = "\033[0m"
    print(f"\n{color}{arrow} {direction.upper()}{reset}")
    print(json.dumps(msg, indent=2))


def main() -> None:
    proc = subprocess.Popen(
        ["uv", "run", "python", str(SERVER_PATH)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        text=True,
    )

    # bleed server stderr to our stderr in a background thread
    def pump_stderr() -> None:
        assert proc.stderr is not None
        for line in proc.stderr:
            sys.stderr.write(f"\033[90m{line}\033[0m")

    threading.Thread(target=pump_stderr, daemon=True).start()

    def send(msg: dict) -> None:
        pretty("send", msg)
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()

    def recv() -> dict:
        assert proc.stdout is not None
        line = proc.stdout.readline()
        msg = json.loads(line)
        pretty("recv", msg)
        return msg

    try:
        # 1) initialize
        send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "client_demo", "version": "0.1"},
                },
            }
        )
        recv()

        # 2) initialized notification (no response expected)
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})

        # 3) discover tools
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        recv()

        # 4) call query_telemetry
        send(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "query_telemetry",
                    "arguments": {"sensor_id": "S-47"},
                },
            }
        )
        recv()

        # 5) call search_manual
        send(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "search_manual",
                    "arguments": {"query": "high temperature alarm chiller"},
                },
            }
        )
        recv()

        # 6) deliberately call an unknown tool — see how the server handles it
        send(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {"name": "nope_this_tool_does_not_exist", "arguments": {}},
            }
        )
        recv()

    finally:
        proc.terminate()
        proc.wait(timeout=2)


if __name__ == "__main__":
    main()
