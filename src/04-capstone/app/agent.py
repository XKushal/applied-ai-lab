"""
Capstone agent loop — session 4b version.

Adds (vs 4a):
  • Prompt caching on system prompt + tool schemas (cache_control breakpoints).
  • Per-request cost cap (env COST_CAP_USD; default $0.50). Aborts cleanly.
  • USD cost attribute on each gen_ai.chat span (visible in Jaeger).
  • create_work_order is a SIDE-EFFECTING tool — see tool definition for the
    approval pattern. Agent treats its return as data, the UI handles approval.

Trace tree in Jaeger now includes:
  agent.run                              (with agent.cost.usd)
   ├─ agent.iter[N]
   │   ├─ gen_ai.chat                    (with cache hit/write counts + USD)
   │   └─ mcp.tool.<name>
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable

import anthropic

from .mcp_client import MCPClient
from .pricing import cost_usd
from .telemetry import tracer

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
MAX_ITERS = 8
COST_CAP_USD = float(os.environ.get("COST_CAP_USD", "0.50"))

SYSTEM_PROMPT = """\
You are a building-operations assistant for HVAC and BMS technicians.

For sensor questions, check telemetry first, then look up what readings mean.
For "what does fault X mean" questions, search the manuals. Combine info from
both tools when a sensor reading raises a question that the manuals can explain.

When proposing maintenance work, use create_work_order — but understand that
tool is GATED: it returns a PENDING_APPROVAL response, not an executed action.
After calling it, summarize the proposed work order for the user and tell them
to approve or deny it in the UI.

Cite manual sections when you reference them. Don't guess. Be concise.
"""


class CostCapExceeded(RuntimeError):
    """Raised when cumulative cost would exceed COST_CAP_USD."""


def _mcp_to_anthropic(t: dict) -> dict:
    return {
        "name": t["name"],
        "description": t.get("description", ""),
        "input_schema": t["inputSchema"],
    }


def _system_with_cache() -> list[dict]:
    """System prompt as a list with a cache_control breakpoint on the last block.

    Anthropic caches the prefix up to and including the marked block. Since
    our system prompt is stable across all requests, this turns it into a
    near-zero-cost prefix after the first call (cache reads are ~10% of
    fresh input cost).
    """
    return [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }
    ]


def _tools_with_cache(tools: list[dict]) -> list[dict]:
    """Mark the last tool's schema with cache_control so the WHOLE tools array
    is included in the cached prefix. Cache breakpoint is positional — anything
    before it (system + tools + early messages) gets cached together.
    """
    if not tools:
        return tools
    tools_copy = [dict(t) for t in tools]
    tools_copy[-1] = dict(tools_copy[-1])
    tools_copy[-1]["cache_control"] = {"type": "ephemeral"}
    return tools_copy


def run_agent(user_query: str, mcp: MCPClient) -> Iterable[dict]:
    """Generator yielding structured trace events for the SSE stream."""
    client = anthropic.Anthropic()
    anthropic_tools = _tools_with_cache(
        [_mcp_to_anthropic(t) for t in mcp.list_tools()]
    )
    messages: list[dict] = [{"role": "user", "content": user_query}]
    total_in = total_out = 0
    total_cache_write = total_cache_read = 0
    total_cost = 0.0

    with tracer.start_as_current_span("agent.run") as run_span:
        run_span.set_attribute("agent.model", MODEL)
        run_span.set_attribute("agent.max_iters", MAX_ITERS)
        run_span.set_attribute("agent.cost_cap_usd", COST_CAP_USD)

        for i in range(MAX_ITERS):
            with tracer.start_as_current_span(f"agent.iter[{i}]") as iter_span:
                with tracer.start_as_current_span("gen_ai.chat") as chat_span:
                    chat_span.set_attribute("gen_ai.system", "anthropic")
                    chat_span.set_attribute("gen_ai.request.model", MODEL)
                    chat_span.set_attribute("gen_ai.request.temperature", 0.1)
                    chat_span.set_attribute("gen_ai.operation.name", "chat")

                    response = client.messages.create(
                        model=MODEL,
                        max_tokens=2048,
                        temperature=0.1,
                        system=_system_with_cache(),
                        tools=anthropic_tools,
                        messages=messages,
                    )

                    u = response.usage
                    cw = getattr(u, "cache_creation_input_tokens", 0) or 0
                    cr = getattr(u, "cache_read_input_tokens", 0) or 0
                    call_cost = cost_usd(
                        MODEL,
                        input_tokens=u.input_tokens,
                        output_tokens=u.output_tokens,
                        cache_creation_input_tokens=cw,
                        cache_read_input_tokens=cr,
                    )
                    chat_span.set_attribute("gen_ai.usage.input_tokens", u.input_tokens)
                    chat_span.set_attribute("gen_ai.usage.output_tokens", u.output_tokens)
                    chat_span.set_attribute("gen_ai.usage.cache_creation_input_tokens", cw)
                    chat_span.set_attribute("gen_ai.usage.cache_read_input_tokens", cr)
                    chat_span.set_attribute("gen_ai.cost.usd", round(call_cost, 6))
                    chat_span.set_attribute("gen_ai.response.stop_reason", response.stop_reason or "")

                total_in += u.input_tokens
                total_out += u.output_tokens
                total_cache_write += cw
                total_cache_read += cr
                total_cost += call_cost

                if total_cost > COST_CAP_USD:
                    run_span.set_attribute("agent.cost_cap_exceeded", True)
                    yield {
                        "kind": "error",
                        "reason": "cost_cap_exceeded",
                        "cost_usd": round(total_cost, 4),
                        "cap_usd": COST_CAP_USD,
                    }
                    raise CostCapExceeded(
                        f"cost cap exceeded: ${total_cost:.4f} > ${COST_CAP_USD}"
                    )

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
                        "cache_write_tokens": total_cache_write,
                        "cache_read_tokens": total_cache_read,
                        "cost_usd": round(total_cost, 4),
                        "iterations": i + 1,
                    }
                    run_span.set_attribute("agent.iterations", i + 1)
                    run_span.set_attribute("agent.tokens.input", total_in)
                    run_span.set_attribute("agent.tokens.output", total_out)
                    run_span.set_attribute("agent.tokens.cache_write", total_cache_write)
                    run_span.set_attribute("agent.tokens.cache_read", total_cache_read)
                    run_span.set_attribute("agent.cost.usd", round(total_cost, 6))
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

                            # Detect the approval-gated tool result
                            event_kind = "tool_result"
                            extra: dict = {}
                            if block.name == "create_work_order":
                                try:
                                    parsed = json.loads(text)
                                    if parsed.get("status") == "PENDING_APPROVAL":
                                        event_kind = "approval_required"
                                        extra = {"proposed": parsed}
                                except Exception:  # noqa: BLE001
                                    pass

                            yield {
                                "kind": event_kind,
                                "name": block.name,
                                "is_error": is_error,
                                "preview": text[:240],
                                **extra,
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
