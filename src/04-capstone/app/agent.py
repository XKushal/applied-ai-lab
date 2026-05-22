"""
Capstone agent loop — refactored from src/03-agent/mcp/agent_mcp.py.

Adds OpenTelemetry spans for each iteration and each LLM call, following
the OTel GenAI semantic conventions. The trace tree you'll see in Jaeger:

  agent.run
   ├─ agent.iter[0]
   │   ├─ gen_ai.chat (claude call)        ← spec-aligned span name
   │   └─ mcp.tool.query_telemetry         ← from mcp_client.py
   ├─ agent.iter[1]
   │   ├─ gen_ai.chat
   │   └─ mcp.tool.search_manual
   └─ agent.iter[2]
       └─ gen_ai.chat                      ← final answer, no tool call
"""

from __future__ import annotations

import json
from collections.abc import Iterable

import anthropic

from .mcp_client import MCPClient
from .telemetry import tracer

MODEL = "claude-sonnet-4-5"
MAX_ITERS = 8
SYSTEM_PROMPT = """\
You are a building-operations assistant for HVAC and BMS technicians.

For sensor questions, check telemetry first, then look up what readings mean.
For "what does fault X mean" questions, search the manuals. Combine info from
both tools when a sensor reading raises a question that the manuals can explain.
Cite manual sections when you reference them. Don't guess. Be concise.
"""


def _mcp_to_anthropic(t: dict) -> dict:
    return {
        "name": t["name"],
        "description": t.get("description", ""),
        "input_schema": t["inputSchema"],
    }


def run_agent(user_query: str, mcp: MCPClient) -> Iterable[dict]:
    """Generator yielding structured trace events.

    Each yielded dict has a 'kind' (one of: 'tool_call', 'tool_result',
    'final', 'usage') and event-specific keys. The FastAPI route turns
    these into Server-Sent Events for the client.
    """
    client = anthropic.Anthropic()
    anthropic_tools = [_mcp_to_anthropic(t) for t in mcp.list_tools()]
    messages: list[dict] = [{"role": "user", "content": user_query}]
    total_in = total_out = 0

    with tracer.start_as_current_span("agent.run") as run_span:
        run_span.set_attribute("agent.model", MODEL)
        run_span.set_attribute("agent.max_iters", MAX_ITERS)

        for i in range(MAX_ITERS):
            with tracer.start_as_current_span(f"agent.iter[{i}]") as iter_span:
                with tracer.start_as_current_span("gen_ai.chat") as chat_span:
                    # spec-aligned attributes — see concepts doc 06
                    chat_span.set_attribute("gen_ai.system", "anthropic")
                    chat_span.set_attribute("gen_ai.request.model", MODEL)
                    chat_span.set_attribute("gen_ai.request.temperature", 0.1)
                    chat_span.set_attribute("gen_ai.operation.name", "chat")

                    response = client.messages.create(
                        model=MODEL,
                        max_tokens=2048,
                        temperature=0.1,
                        system=SYSTEM_PROMPT,
                        tools=anthropic_tools,
                        messages=messages,
                    )

                    chat_span.set_attribute(
                        "gen_ai.usage.input_tokens", response.usage.input_tokens
                    )
                    chat_span.set_attribute(
                        "gen_ai.usage.output_tokens", response.usage.output_tokens
                    )
                    chat_span.set_attribute(
                        "gen_ai.response.stop_reason", response.stop_reason or ""
                    )

                total_in += response.usage.input_tokens
                total_out += response.usage.output_tokens
                messages.append({"role": "assistant", "content": response.content})
                iter_span.set_attribute("agent.stop_reason", response.stop_reason or "")

                if response.stop_reason == "end_turn":
                    final_text = "".join(
                        b.text for b in response.content if b.type == "text"
                    )
                    yield {"kind": "final", "text": final_text}
                    yield {
                        "kind": "usage",
                        "input_tokens": total_in,
                        "output_tokens": total_out,
                        "iterations": i + 1,
                    }
                    run_span.set_attribute("agent.iterations", i + 1)
                    run_span.set_attribute("agent.tokens.input", total_in)
                    run_span.set_attribute("agent.tokens.output", total_out)
                    return

                if response.stop_reason == "tool_use":
                    tool_results: list[dict] = []
                    for block in response.content:
                        if block.type == "tool_use":
                            yield {
                                "kind": "tool_call",
                                "name": block.name,
                                "input": block.input,
                            }
                            text, is_error = mcp.call_tool(block.name, block.input)
                            yield {
                                "kind": "tool_result",
                                "name": block.name,
                                "is_error": is_error,
                                "preview": text[:240],
                            }
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": text,
                                    "is_error": is_error,
                                }
                            )
                    messages.append({"role": "user", "content": tool_results})
                    continue

                raise RuntimeError(f"unexpected stop_reason: {response.stop_reason}")

        raise RuntimeError(f"agent exceeded MAX_ITERS={MAX_ITERS}")
