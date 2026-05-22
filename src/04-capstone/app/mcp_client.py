"""
MCP client — refactored from src/03-agent/mcp/agent_mcp.py.

Same minimal stdio JSON-RPC client. Add OpenTelemetry spans for each
request so the trace shows time spent in the MCP server vs the LLM.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading

from .telemetry import tracer


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
        threading.Thread(target=self._pump_stderr, daemon=True).start()

    def _pump_stderr(self) -> None:
        assert self.proc.stderr is not None
        for line in self.proc.stderr:
            sys.stderr.write(f"  [mcp.server] {line}")

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
            raise RuntimeError("MCP server closed stdout")
        return json.loads(line)

    def _request(self, method: str, params: dict | None = None) -> dict:
        with tracer.start_as_current_span(f"mcp.{method}") as span:
            rid = self._next_id()
            self._send(
                {"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}}
            )
            resp = self._recv()
            if "error" in resp:
                span.set_attribute("mcp.error.code", resp["error"].get("code", 0))
                span.set_attribute("mcp.error.message", resp["error"].get("message", ""))
                raise RuntimeError(f"MCP error from {method}: {resp['error']}")
            return resp["result"]

    def _notify(self, method: str, params: dict | None = None) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def initialize(self) -> dict:
        result = self._request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "capstone-api", "version": "0.1"},
            },
        )
        self._notify("notifications/initialized")
        return result

    def list_tools(self) -> list[dict]:
        return self._request("tools/list")["tools"]

    def call_tool(self, name: str, arguments: dict) -> tuple[str, bool]:
        """Returns (text, is_error)."""
        with tracer.start_as_current_span(f"mcp.tool.{name}") as span:
            span.set_attribute("mcp.tool.name", name)
            span.set_attribute("mcp.tool.arguments", json.dumps(arguments))
            result = self._request(
                "tools/call", {"name": name, "arguments": arguments}
            )
            is_error = bool(result.get("isError"))
            span.set_attribute("mcp.tool.is_error", is_error)
            parts = [
                b["text"]
                for b in result.get("content", [])
                if b.get("type") == "text"
            ]
            text = "\n".join(parts)
            return text, is_error

    def shutdown(self) -> None:
        try:
            self.proc.terminate()
            self.proc.wait(timeout=2)
        except Exception:  # noqa: BLE001
            self.proc.kill()
