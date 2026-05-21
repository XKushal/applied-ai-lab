"""
3.2.3 — Full RAG. Retrieve + prompt the LLM with chunks + return grounded answer with citations.

This is the WHOLE PIPELINE in one file. ~70 lines. No frameworks.

Run:
    uv run python src/02-rag/03_rag.py "What does chiller fault E47 mean and what should I do?"
    uv run python src/02-rag/03_rag.py "How is the BMS network secured?"
    uv run python src/02-rag/03_rag.py "What's the weather in Milwaukee?"   # ← off-corpus on purpose

What to observe:
1. The system prompt EXPLICITLY tells the model to only use the provided
   context, to cite chunk IDs, and to refuse when the context is insufficient.
   This is "grounded prompting" — the most important guard against hallucination.
2. We pass retrieved chunks AS A FORMATTED LIST inside the user message,
   each with its ID. The model sees IDs because we want it to cite them.
3. The model response should include `[citation: <chunk_id>]` markers. We
   programmatically verify those IDs were actually retrieved — that catches
   hallucinated citations (the model inventing IDs not in our list).
4. On the off-corpus query, the model SHOULD refuse. If it doesn't, that's
   the failure mode you'd catch with a refusal metric in production.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import anthropic
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = Path(__file__).parent.parent.parent / "data" / "chroma"
COLLECTION_NAME = "building_manuals"
MODEL = "claude-sonnet-4-5"
TOP_K = 4

SYSTEM_PROMPT = """\
You are a building-operations assistant. You answer questions ONLY using the
context provided to you inside <context>...</context> tags. Each context chunk
has an id like `<chunk id="...">`. When you use information from a chunk in
your answer, cite it using the form `[citation: <chunk_id>]` at the end of
the relevant sentence.

Rules:
- If the provided context does not contain enough information to answer the
  question, reply exactly: "I don't have enough information in the building
  manuals to answer that." Do not guess.
- Do not use outside knowledge. Only the context.
- Be concise. Operators are reading this on a phone in front of equipment.
"""


def build_user_prompt(question: str, chunks: list[dict]) -> str:
    """Compose the user message with retrieved context wrapped in delimited tags."""
    lines = ["<context>"]
    for c in chunks:
        lines.append(f'<chunk id="{c["id"]}" source="{c["source"]}">')
        lines.append(c["content"])
        lines.append("</chunk>")
    lines.append("</context>")
    lines.append("")
    lines.append(f"Question: {question}")
    return "\n".join(lines)


def retrieve(query: str, k: int) -> list[dict]:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),
    )
    res = collection.query(query_texts=[query], n_results=k)
    return [
        {
            "id": cid,
            "source": meta["source"],
            "content": doc,
            "distance": dist,
        }
        for cid, doc, meta, dist in zip(
            res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
        )
    ]


def validate_citations(answer: str, retrieved_ids: set[str]) -> tuple[set[str], set[str]]:
    """Return (valid_citations, hallucinated_citations) found in the answer text."""
    cited = set(re.findall(r"\[citation:\s*([^\]]+?)\s*\]", answer))
    valid = cited & retrieved_ids
    halluc = cited - retrieved_ids
    return valid, halluc


def main() -> None:
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "What does chiller fault E47 mean and what should I do?"
    )

    chunks = retrieve(question, TOP_K)
    print("=" * 70)
    print(f"question: {question}")
    print("-" * 70)
    print(f"retrieved {len(chunks)} chunks:")
    for c in chunks:
        print(f"  · {c['id']:60s} distance={c['distance']:.3f}")
    print("=" * 70)

    user_prompt = build_user_prompt(question, chunks)
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        temperature=0.1,  # low: factual grounded answer, no creative drift
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    answer = response.content[0].text

    print("\nANSWER:")
    print(answer)
    print()
    print("-" * 70)
    print(
        f"tokens: in={response.usage.input_tokens} "
        f"out={response.usage.output_tokens}"
    )

    valid, halluc = validate_citations(answer, {c["id"] for c in chunks})
    print(f"citations: valid={sorted(valid)}")
    if halluc:
        print(f"  ⚠ HALLUCINATED citations (not in retrieved set): {sorted(halluc)}")
    elif not valid and "don't have enough information" not in answer:
        print("  ⚠ no citations found — model may not have grounded its answer")


if __name__ == "__main__":
    main()
