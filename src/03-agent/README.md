# 3.4 — Agent loop, from scratch

A real agent in two files: `tools.py` defines what the model can do, `agent.py` runs the loop. ~150 lines total. No framework.

The agent has access to:

- **`query_telemetry(sensor_id)`** — returns a fake-but-deterministic sensor reading (hash-derived so demos are reproducible). Stands in for what would be a Kafka consumer / time-series query in real life.
- **`search_manual(query)`** — *the same RAG retrieval from Phase 3.2*, exposed as a tool. Returns raw chunks, not generated answers.

## Why `search_manual` returns raw chunks (not generated answers)

Design choice worth defending in an interview. By keeping retrieval pure and letting the *outer* agent LLM do the synthesis, we get:

- **Single source of reasoning.** No conflicting "this LLM said X, that LLM said Y" between tool and agent.
- **Token efficiency.** One generation step per user turn, not one per retrieval.
- **Easier eval.** Retrieval eval (deterministic, fast — see Phase 3.3) is separate from generation eval (LLM-as-judge, slow). You can A/B each independently.

The downside: more retrieved-chunk tokens go into the agent's context. For very large retrievals that doesn't scale, and you'd push synthesis back into the tool. But for any reasonable top-k, this design wins.

## Run

```bash
# the default query exercises BOTH tools in a single agent run:
uv run python src/03-agent/agent.py

# or try your own:
uv run python src/03-agent/agent.py "What does fault E12 mean?"
uv run python src/03-agent/agent.py "Check sensor AHU-3-supply and tell me if I should worry."
uv run python src/03-agent/agent.py "What's the chilled water setpoint and is sensor S-12 within tolerance?"
```

## What you're looking at in the output

The runner prints **every iteration** of the loop so you see the trajectory:

```
iteration 0 — TOOL CALLS
  model says: I'll check the sensor first, then look up what high readings mean.
  → call query_telemetry({"sensor_id": "S-47"})
    ← {"sensor_id": "S-47", "reading_f": 89.0, "baseline_f": 70.0, "delta_f": 19.0, "status": "alarm", ...}
  → call search_manual({"query": "high temperature alarm chiller"})
    ← {"query": "...", "chunks": [{"chunk_id": "chiller-system-overview::Common alarms", ...}]}

iteration 1 — FINAL ANSWER
Sensor S-47 is in alarm: 89°F vs 70°F baseline (Δ19°F). This matches fault E12...
```

Three things to notice every time:

1. **The model often calls multiple tools in one iteration.** That's *parallel tool use* — Claude can emit several `tool_use` blocks in one response. Our runtime executes them all and packages all results together for the next iteration. Notice we do NOT call the LLM once per tool — that would be wasteful.

2. **The final answer arrives in an iteration that has `stop_reason="end_turn"`** — i.e. no more tool calls, just text. That's the loop's natural exit. If the model kept calling tools forever, our `MAX_ITERS=8` cap would raise — and you should keep that cap in production for the same reason you wouldn't run an unbounded `while True`.

3. **The cumulative token count at the end.** Agents are expensive because they call the LLM multiple times per user turn. Cumulative tokens × per-token price = the metric your finance team will care about. Always track it.

## Safety mechanics in the code

Look at these four lines specifically — they're the difference between "demo" and "production-shaped":

| Code | What it prevents |
|---|---|
| `for i in range(MAX_ITERS):` | Infinite tool loops. Hard cap, period. |
| `except Exception as e: return f"ERROR ..."` (in `execute_tool`) | Silent crashes. Tool errors come back as data the model can react to. |
| `temperature=0.1` | Drift between identical runs on factual queries. |
| `if response.stop_reason == "end_turn": return ...` | Cleanly distinguish "model is done" from "model wants more tools". |

These are the four production-shaping decisions an interviewer will want to hear about when they ask "how do you keep an agent stable in production?"

## How this maps to the concepts doc

This script is the *executable form* of [concepts doc 04 — agent loop](../../docs/01-concepts/04-agent-loop.md). After running it:

- "What is an agent?" → point at this script, walk through one iteration.
- "How do you handle tool errors?" → point at `execute_tool`'s `try/except`.
- "How do you prevent infinite loops?" → point at `MAX_ITERS`.
- "What does parallel tool use look like?" → point at the `for block in response.content` that collects multiple `tool_use` blocks per iteration.

## What's missing (deliberately) — production additions

For the capstone (Phase 4), we'll add:

- **OpenTelemetry tracing** — every iteration + tool call as a span. So you can pull up any agent run in your trace backend.
- **Per-request cost cap** — abort if cumulative tokens exceed a budget. Currently we only print.
- **Approval gates** — mark some tools as "human must approve before executing" (e.g., the day you add `create_work_order`, you want a human in the loop).
- **Streaming** — stream both assistant text and tool-use events to the client so a UI shows progress.
- **MCP transport** — Phase 3.5 takes these same tools and exposes them via an MCP server. Same logic, different transport.

## Tying this back to interviews

You now have, in code:

- A working tool-using agent loop, ~80 lines, with safety + observability hooks
- An LLM that calls *your own RAG pipeline* as one of its tools — the production architecture from concepts doc 04
- A printable trace of every iteration that you can screenshot for a portfolio readme

The interview answer:

> "I built an agent loop from scratch — bare Anthropic API, two tools (telemetry + RAG search), with iteration cap, tool-error-as-data, and per-run token tracking. The RAG retrieval from earlier is wired in as one of the tools, so the agent decides when to retrieve instead of always retrieving. Repo's public."

Three things to say next if probed: parallel tool use, why retrieval returns raw chunks (not generated answers), and what production additions live in the capstone.
