"""
3.1 — Bare LLM call. The smallest useful program.

Goal: see exactly what goes over the wire and what comes back.
No streaming, no tools, no agents. Just request → response.

Run:
    uv run python src/01-llm-basics/01_chat.py

What to observe:
1. `response` is a structured object, not just a string.
2. `response.content` is a LIST of "content blocks", not text.
3. `response.usage` gives you input/output tokens — your cost basis.
4. `response.stop_reason` tells you WHY the model stopped
   (end_turn, max_tokens, tool_use, stop_sequence).
"""

import os

import anthropic
from dotenv import load_dotenv

load_dotenv()  # reads .env, populates os.environ

# the SDK reads ANTHROPIC_API_KEY from env automatically
client = anthropic.Anthropic()

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")


def main() -> None:
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        temperature=0.2,  # low: we want consistency on a factual question
        messages=[
            {
                "role": "user",
                "content": "In one sentence, what is the Model Context Protocol (MCP)?",
            }
        ],
    )

    print("=" * 60)
    print(f"model:        {response.model}")
    print(f"stop_reason:  {response.stop_reason}")
    print(f"input_tokens: {response.usage.input_tokens}")
    print(f"output_tokens:{response.usage.output_tokens}")
    print("=" * 60)
    print("content blocks (raw):")
    for i, block in enumerate(response.content):
        print(f"  [{i}] type={block.type}")
        if block.type == "text":
            print(f"      text={block.text!r}")

    print()
    print("answer:")
    # the convenient path — but know that under the hood you're just
    # pulling the first text block out of the list above
    print(response.content[0].text)


if __name__ == "__main__":
    main()
