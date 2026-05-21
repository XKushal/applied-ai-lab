"""
3.2 — Streaming. Same call as 01_chat.py, but tokens stream as they're generated.

Goal: see why streaming matters in real UX.

Run:
    uv run python src/01-llm-basics/02_streaming.py

What to observe:
1. The first chunk appears in ~hundreds of ms (TTFT — time to first token).
2. Subsequent chunks arrive every few ms.
3. The total wall-clock time is the same as non-streaming, BUT the user
   sees output starting much sooner. That's the whole UX argument for streaming.
4. Streaming uses Server-Sent Events (SSE) under the hood — the SDK hides this.
"""

import time

import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()


def main() -> None:
    start = time.perf_counter()
    ttft: float | None = None
    char_count = 0

    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=512,
        temperature=0.2,
        messages=[
            {
                "role": "user",
                "content": "Explain in 4 sentences why streaming matters in LLM UX.",
            }
        ],
    ) as stream:
        for text_chunk in stream.text_stream:
            if ttft is None:
                ttft = time.perf_counter() - start
            print(text_chunk, end="", flush=True)
            char_count += len(text_chunk)

        # the final_message has full content + usage, available after the stream closes
        final = stream.get_final_message()

    total = time.perf_counter() - start
    print()
    print()
    print(f"TTFT:        {ttft:.2f}s")
    print(f"total time:  {total:.2f}s")
    print(f"chars:       {char_count}")
    print(f"tokens out:  {final.usage.output_tokens}")
    print(f"tokens in:   {final.usage.input_tokens}")


if __name__ == "__main__":
    main()
