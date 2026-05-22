"""
3.5 — Agent that gets its tools via MCP instead of in-process imports.

Same agent loop logic as src/03-agent/agent.py — but tool *discovery* and
tool *execution* go through the MCP server subprocess we wrote in server.py.

This is the real production architecture for agentic systems:
    LLM ←→ AGENT RUNTIME ←→ MCP CLIENT ←→ [MCP SERVERS (one per domain)]

Each MCP server is a separate process — written by a different team, in
any language, with its own auth/scope. The agent runtime never imports them.

Run (the Chroma collection from Phase 3.2 must exist):
    uv run python src/03-agent/mcp/agent_mcp.py
    uv run python src/03-agent/mcp/agent_mcp.py "What does fault E12 mean?"

What to observe:
1. We spawn server.py as a subprocess and do the JSON-RPC handshake before
   even calling the LLM.
2. After tools/list, we translate `inputSchema` (MCP camelCase) →
   `input_schema` (Anthropic snake_case). Schema impedance is real.
3. Each agent iteration that ends in tool_use becomes one or more
   tools/call requests over MCP — visible in the [mcp] log prefix.
4. The trace is structurally identical to Phase 3.4 — the agent loop
   doesn't know its tools live in a subprocess. THAT'S THE POINT.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

SERVER_PATH = Path(__file__).parent / "server.py"
MODEL = "claude-sonnet-4-5"
MAX_ITERS = 8
SYSTEM_PROMPT = """\
You are a building-operations assistant for HVAC and BMS technicians.

For sensor questions, check telemetry first, then look up what readings mean.
For "what does fault X mean" questions, search the manuals. Combine info from
both tools when a sensor reading raises a question that the manuals can explain.
Cite manual sections when you reference them. Don't guess. Be concise.
"""


# ---------------------------------------------------------------------------
# Minimal MCP client — just enough to do init → list → call over stdio
# ---------------------------------------------------------------------------
class MCPClient:
    def __init__(self, server_argv: list[str]) -> None:
        self.proc = subprocess.Popen(
            server_argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            text=True,
        )
        self._req_id = 0
        # surface server stderr to our stderr (dimmed) so its logs are visible
        threading.Thread(target=self._pump_stderr, daemon=True).start()

    def _pump_stderr(self) -> None:
        assert self.proc.stderr is not None
        for line in self.proc.stderr:
            sys.stderr.write(f"\033[90m  [server.stderr] {line}\033[0m")

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def _send(self, msg: dict) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def _recv(self) -> dict:
        assert self.proc.stdout is not None
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError("MCP server closed its stdout unexpectedly")
        return json.loads(line)

    def _request(self, method: str, params: dict | None = None) -> dict:
        rid = self._next_id()
        self._send(
            {"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}}
        )
        resp = self._recv()
        if "error" in resp:
            raise RuntimeError(f"MCP error from {method}: {resp['error']}")
        return resp["result"]

    def _notify(self, method: str, params: dict | None = None) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    # ----- public API -----
    def initialize(self) -> dict:
        result = self._request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "agent_mcp", "version": "0.1"},
            },
        )
        self._notify("notifications/initialized")
        return result

    def list_tools(self) -> list[dict]:
        return self._request("tools/list")["tools"]

    def call_tool(self, name: str, arguments: dict) -> str:
        result = self._request(
            "tools/call", {"name": name, "arguments": arguments}
        )
        # MCP returns content as a list of blocks; flatten to text for our use
        parts = []
        for block in result.get("content", []):
            if block.get("type") == "text":
                parts.append(block["text"])
        out = "\n".join(parts)
        return f"[isError] {out}" if result.get("isError") else out

    def shutdown(self) -> None:
        try:
            self.proc.terminate()
            self.proc.wait(timeout=2)
        except Exception:  # noqa: BLE001
            self.proc.kill()


# ---------------------------------------------------------------------------
# Schema translation: MCP tool schema → Anthropic API tool schema
# ---------------------------------------------------------------------------
def mcp_to_anthropic(t: dict) -> dict:
    return {
        "name": t["name"],
        "description": t.get("description", ""),
        "input_schema": t["inputSchema"],  # camelCase → snake_case
    }


# ---------------------------------------------------------------------------
# The agent loop — same shape as Phase 3.4, but tool execution goes to MCP
# ---------------------------------------------------------------------------
def print_iter(i: int, label: str) -> None:
    print(f"\n{'─' * 72}\n  iteration {i} — {label}\n{'─' * 72}")


def run(user_query: str) -> None:
    mcp = MCPClient(["uv", "run", "python", str(SERVER_PATH)])
    try:
        info = mcp.initialize()
        print(f"  [mcp] connected to {info['serverInfo']}")
        mcp_tools = mcp.list_tools()
        print(f"  [mcp] discovered {len(mcp_tools)} tools: {[t['name'] for t in mcp_tools]}")
        anthropic_tools = [mcp_to_anthropic(t) for t in mcp_tools]

        client = anthropic.Anthropic()
        messages: list[dict] = [{"role": "user", "content": user_query}]
        total_in = total_out = 0

        for i in range(MAX_ITERS):
            response = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                temperature=0.1,
                system=SYSTEM_PROMPT,
                tools=anthropic_tools,
                messages=messages,
            )
            total_in += response.usage.input_tokens
            total_out += response.usage.output_tokens
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                print_iter(i, "FINAL ANSWER")
                for block in response.content:
                    if block.type == "text":
                        print(block.text)
                print(f"\n  cumulative tokens: in={total_in} out={total_out}")
                return

            if response.stop_reason == "tool_use":
                print_iter(i, "TOOL CALLS (via MCP)")
                tool_results: list[dict] = []
                for block in response.content:
                    if block.type == "text" and block.text.strip():
                        print(f"  model says: {block.text.strip()[:200]}")
                    elif block.type == "tool_use":
                        print(f"  → mcp call {block.name}({json.dumps(block.input)})")
                        result_text = mcp.call_tool(block.name, block.input)
                        preview = result_text[:240].replace("\n", " ")
                        print(f"    ← {preview}{'...' if len(result_text) > 240 else ''}")
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_text,
                            }
                        )
                messages.append({"role": "user", "content": tool_results})
                continue

            raise RuntimeError(f"unexpected stop_reason: {response.stop_reason}")

        raise RuntimeError(f"agent exceeded MAX_ITERS={MAX_ITERS}")
    finally:
        mcp.shutdown()


def main() -> None:
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "Sensor S-47 is reading strange. Pull it and tell me if I should worry, "
        "and what fault code it might match if there's something wrong."
    )
    print(f"USER QUERY: {query}")
    run(query)


if __name__ == "__main__":
    main()
