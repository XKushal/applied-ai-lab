"""
3.3 — Tool-use, ONE TURN ONLY.

Goal: see what a `tool_use` content block actually looks like — the building
block we'll loop in Phase 3.4 to make a real agent.

This script:
1. Sends the model a question.
2. Tells the model a `get_weather` tool exists.
3. Prints what the model decides to do.

It does NOT actually run the tool or feed results back. That's the next phase.
That's the point — we want to see the request without the loop, so the
mechanic is naked.

Run:
    uv run python src/01-llm-basics/03_tool_use_preview.py

What to observe:
1. `stop_reason == "tool_use"` — the model didn't answer, it asked for a tool call.
2. Content blocks contain a `ToolUseBlock` with:
   - `id`         — opaque ID, used to correlate the eventual tool_result
   - `name`       — which tool the model wants
   - `input`      — JSON args matching the tool's input_schema
3. The model has NO IDEA whether the tool exists or works. It just emits a request.
   YOUR code is the agent runtime that decides whether to honor it.
"""

import json

import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

# Tool definitions are JUST JSON SCHEMAS. Nothing else.
# The model sees `name`, `description`, and `input_schema` to decide
# whether and how to call it.
WEATHER_TOOL = {
    "name": "get_weather",
    "description": (
        "Look up the current weather for a given city. "
        "Returns temperature in Fahrenheit and a brief condition string."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name, e.g., 'Milwaukee' or 'Jersey City'.",
            },
        },
        "required": ["city"],
    },
}


def main() -> None:
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=512,
        tools=[WEATHER_TOOL],
        messages=[
            {
                "role": "user",
                "content": "What's the weather in Milwaukee right now?",
            }
        ],
    )

    print("=" * 60)
    print(f"stop_reason:  {response.stop_reason}")
    print(f"input_tokens: {response.usage.input_tokens}")
    print(f"output_tokens:{response.usage.output_tokens}")
    print("=" * 60)

    for i, block in enumerate(response.content):
        print(f"[{i}] type={block.type}")
        if block.type == "text":
            print(f"    text: {block.text!r}")
        elif block.type == "tool_use":
            print(f"    id:    {block.id}")
            print(f"    name:  {block.name}")
            print(f"    input: {json.dumps(block.input, indent=6)}")

    print()
    print("⤷ The model didn't answer. It emitted a tool_use block.")
    print("⤷ In a real agent, your code would now CALL get_weather('Milwaukee'),")
    print("  build a tool_result, append it to messages, and re-call the model.")
    print("⤷ That's the loop. We build it for real in Phase 3.4.")


if __name__ == "__main__":
    main()
