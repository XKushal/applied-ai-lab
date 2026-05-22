"""
3.4 — The agent loop. The whole thing. ~80 lines including pretty printing.

This is the ~25-line loop from concepts doc 04, wrapped with safety + a
trace-style printer so you can see every iteration.

Run:
    uv run python src/03-agent/agent.py
    uv run python src/03-agent/agent.py "Sensor S-47 is reading strange, what should I do?"
    uv run python src/03-agent/agent.py "What does fault E12 mean?"
    uv run python src/03-agent/agent.py "Check sensor AHU-3-supply and tell me if I should worry."

What to observe:
1. Iteration 0: model receives the question + tool schemas, decides what to do.
2. If `stop_reason == "tool_use"`, the runtime extracts the tool calls,
   executes them, appends results, re-calls the model.
3. The model may call MULTIPLE tools per iteration (parallel tool calls) —
   the runtime handles them all and feeds all results back together.
4. Loop ends when `stop_reason == "end_turn"` OR `max_iters` reached.
5. Notice: the LLM never runs a single line of Python. Every tool execution
   happens in this file. The LLM only emits intents.
"""

from __future__ import annotations

import json
import sys

import anthropic
from dotenv import load_dotenv

from tools import TOOL_REGISTRY, TOOL_SCHEMAS

load_dotenv()

MODEL = "claude-sonnet-4-5"
MAX_ITERS = 8
SYSTEM_PROMPT = """\
You are a building-operations assistant for HVAC and BMS technicians.

You have two tools:
- query_telemetry: get the latest reading for a sensor by ID
- search_manual: find relevant sections of the building operations manuals

Approach:
- For sensor questions, check telemetry first, then look up what readings mean.
- For "what does fault X mean" questions, search the manuals.
- Combine info from both tools when a sensor reading raises a question
  that the manuals can explain (e.g. high temp → look up high-temp alarms).
- Always cite the manual section when you reference it.
- If you don't have enough information, say so. Don't guess.

Be concise. Technicians are reading this on a phone in front of equipment.
"""


def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool. Return the string we'll send back as tool_result.

    Errors are returned AS tool_result content, not raised, so the model
    can read the error and decide to recover (try different args, give up
    cleanly, etc). Silently swallowing or crashing on tool errors is the
    worst pattern — see concepts doc 04.
    """
    fn = TOOL_REGISTRY.get(name)
    if fn is None:
        return f"ERROR: unknown tool '{name}'"
    try:
        result = fn(**arguments)
        return json.dumps(result, default=str)
    except Exception as e:  # noqa: BLE001 — tool errors are part of agent input
        return f"ERROR running {name}({arguments!r}): {type(e).__name__}: {e}"


def print_iteration(i: int, label: str) -> None:
    print(f"\n{'─' * 70}\n  iteration {i} — {label}\n{'─' * 70}")


def run_agent(user_query: str) -> str:
    client = anthropic.Anthropic()
    messages: list[dict] = [{"role": "user", "content": user_query}]
    total_in = total_out = 0

    for i in range(MAX_ITERS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            temperature=0.1,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )
        total_in += response.usage.input_tokens
        total_out += response.usage.output_tokens
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            print_iteration(i, "FINAL ANSWER")
            final_text = ""
            for block in response.content:
                if block.type == "text":
                    final_text += block.text
            print(final_text)
            print(f"\n  cumulative tokens: in={total_in} out={total_out}")
            return final_text

        if response.stop_reason == "tool_use":
            print_iteration(i, "TOOL CALLS")
            tool_results: list[dict] = []
            for block in response.content:
                if block.type == "text" and block.text.strip():
                    print(f"  model says: {block.text.strip()[:200]}")
                elif block.type == "tool_use":
                    print(f"  → call {block.name}({json.dumps(block.input)})")
                    result = execute_tool(block.name, block.input)
                    preview = result[:240].replace("\n", " ")
                    print(f"    ← {preview}{'...' if len(result) > 240 else ''}")
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )
            messages.append({"role": "user", "content": tool_results})
            continue

        raise RuntimeError(f"unexpected stop_reason: {response.stop_reason}")

    raise RuntimeError(f"agent exceeded MAX_ITERS={MAX_ITERS} without finishing")


def main() -> None:
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "Sensor S-47 is reading strange. Pull it and tell me if I should worry, "
        "and what fault code it might match if there's something wrong."
    )
    print(f"USER QUERY: {query}")
    run_agent(query)


if __name__ == "__main__":
    main()
