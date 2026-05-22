"""
Approximate per-token pricing in USD. Update when Anthropic changes prices.

Keeping pricing here (and not hardcoded in agent.py) means a single edit
when you switch models or when prices change.
"""

# Per 1M tokens, USD. Rough public prices — confirm against your console.
PRICES = {
    "claude-sonnet-4-5": {
        "input": 3.00,
        "output": 15.00,
        "cache_write": 3.75,    # 1.25x input
        "cache_read": 0.30,     # 0.10x input
    },
    "claude-opus-4-1": {
        "input": 15.00,
        "output": 75.00,
        "cache_write": 18.75,
        "cache_read": 1.50,
    },
}


def cost_usd(
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_creation_input_tokens: int = 0,
    cache_read_input_tokens: int = 0,
) -> float:
    p = PRICES.get(model, PRICES["claude-sonnet-4-5"])
    return (
        (input_tokens / 1_000_000) * p["input"]
        + (output_tokens / 1_000_000) * p["output"]
        + (cache_creation_input_tokens / 1_000_000) * p["cache_write"]
        + (cache_read_input_tokens / 1_000_000) * p["cache_read"]
    )
