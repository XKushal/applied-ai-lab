# 3.1–3.3 — LLM basics, no frameworks

Three small scripts. Each runs in seconds, each demonstrates one mechanic.

Don't just run them — **read the output and reconcile what you see against [the LLM mental model doc](../../docs/01-concepts/01-llm-mental-model.md)**. That's where the learning is.

## Setup (one-time)

```bash
# from repo root
cp .env.example .env
# edit .env, paste your ANTHROPIC_API_KEY
```

Then sync the venv:

```bash
uv sync
```

## Run

```bash
uv run python src/01-llm-basics/01_chat.py
uv run python src/01-llm-basics/02_streaming.py
uv run python src/01-llm-basics/03_tool_use_preview.py
```

## What you're learning, script by script

### `01_chat.py` — the smallest call

The whole "LLM API" is one HTTP POST. The SDK wraps it. The interesting part of the response is **not** the text — it's the shape:

- `response.content` is a **list of content blocks**, not a string. Each block has a `type`. For now you'll only see `type=text`, but `tool_use` and `thinking` blocks live in the same list.
- `response.usage` is your **cost basis**. Multiply by the model's per-token price. Senior engineers track this metric.
- `response.stop_reason` tells you **why** generation ended:
  - `end_turn` — model finished naturally (most common)
  - `max_tokens` — you didn't allow enough output; truncated
  - `tool_use` — model wants to call a tool (see script 3)
  - `stop_sequence` — you specified a custom stop string and it appeared

> **Worth knowing:** an Anthropic API response is a structured object — a list of typed content blocks, usage stats, and a stop reason. It is *not* just a string. Treating it as a string is the most common early mistake.

### `02_streaming.py` — TTFT vs. total time

Streaming doesn't make the model faster. It makes the **first chunk arrive sooner**. Compare TTFT (typically a few hundred ms) to total time (typically a few seconds). In a UI, that gap is the difference between "feels broken" and "feels fast."

Under the hood: Server-Sent Events (SSE). The SDK hides the transport but you can think of it as "HTTP response that flushes incrementally."

> **Why this matters:** in a building-ops chatbot, the technician is standing in front of broken equipment. TTFT is UX.

### `03_tool_use_preview.py` — what an agent's atom looks like

The most important script in this folder.

You'll see `stop_reason = "tool_use"` and a content block with `type=tool_use`. The model **didn't answer**. It emitted a structured request: "please call `get_weather` with `city='Milwaukee'`."

**The model has no ability to execute anything.** It just emits the request. Your code (the "agent runtime") decides whether to:

1. Actually run the tool
2. Append the result as a `tool_result` content block
3. Re-call the LLM with the updated message history

Repeat until the model returns `stop_reason="end_turn"`. **That is the agent loop.** Everything beyond it — multi-agent, planners, ReAct prompting — is patterns on top of this two-step exchange.

> **Worth knowing:** "what is an agent, really?" is answered by this script — an LLM that can emit tool_use, plus a runtime that honors those requests and loops. It's ~25 lines of Python, built out in `src/03-agent/`.

## Common gotchas

| Symptom | Cause |
|---|---|
| `anthropic.AuthenticationError` | `.env` not loaded, or API key wrong. Check `echo $ANTHROPIC_API_KEY` is empty (it should be — load_dotenv handles it). |
| Different output every time | Sampling. Set `temperature=0.0` for max consistency. Won't be bit-exact even at 0; that's a feature of the inference stack. |
| Hits `max_tokens` mid-sentence | Raise `max_tokens`. For long outputs, also consider streaming so you can cut early. |
| Tool-use script returns text instead of tool_use | The model decided it could answer without the tool. Phrase the question so the tool is the only way to know. |
