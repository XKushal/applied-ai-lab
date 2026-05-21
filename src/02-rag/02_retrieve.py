"""
3.2.2 — Retrieval ONLY (no LLM yet).

This script intentionally has no LLM call. We're isolating retrieval so you
can see — naked, without a generator papering over its mistakes — what
chunks actually come back for a query and at what distance.

Run:
    uv run python src/02-rag/02_retrieve.py "low refrigerant pressure"
    uv run python src/02-rag/02_retrieve.py "how does BACnet addressing work"
    uv run python src/02-rag/02_retrieve.py "weather in Milwaukee"   # ← intentionally off-corpus

What to observe:
1. The on-corpus queries return chunks that obviously match the topic.
2. The off-corpus query ("weather") ALSO returns chunks — distance is just
   higher. This is the silent failure mode of naïve RAG: it ALWAYS returns
   something, even when nothing is relevant. The LLM will then "ground"
   itself in garbage. Production RAG sets a distance threshold or asks
   the LLM to refuse when nothing is sufficiently close.
3. The distance numbers are cosine distances (1 - cosine similarity).
   Lower = closer = better. Anything ~0.0–0.5 is a strong match,
   ~0.5–1.0 is weak, >1.0 is essentially random.
"""

from __future__ import annotations

import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

CHROMA_DIR = Path(__file__).parent.parent.parent / "data" / "chroma"
COLLECTION_NAME = "building_manuals"


def main() -> None:
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "what's the chiller fault code E47?"
    top_k = 3

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),
    )

    print("=" * 70)
    print(f"query: {query!r}")
    print(f"top_k: {top_k}")
    print("=" * 70)

    results = collection.query(query_texts=[query], n_results=top_k)
    # results is a dict of lists-of-lists because query() supports batched queries.
    # We only sent one query so we index [0].
    for rank, (chunk_id, document, metadata, distance) in enumerate(
        zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ),
        start=1,
    ):
        print(f"\n[{rank}] id={chunk_id}")
        print(f"    distance={distance:.4f}  (lower = closer)")
        print(f"    source={metadata['source']}  section={metadata['section']!r}")
        preview = document[:240].replace("\n", " ")
        print(f"    preview: {preview}...")


if __name__ == "__main__":
    main()
