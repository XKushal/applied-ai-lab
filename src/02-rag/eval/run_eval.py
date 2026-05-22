"""
3.3 — RAG eval harness. Recall@1, Recall@3, MRR.

Loads a labeled eval set, runs retrieval for each question, computes metrics.
No LLM calls — pure retrieval eval. Deterministic. Cheap. Fast.

This is the artifact you point at when asked "how do you evaluate retrieval."
Without it you're guessing whether a change helped or hurt; with it you have
a number on every commit.

Run:
    uv run python src/02-rag/eval/run_eval.py
    uv run python src/02-rag/eval/run_eval.py --k 5    # try a different top-k

What to observe:
1. Per-query report shows the actual retrieved IDs vs the gold ID(s) — so when
   a query fails you can see WHY (wrong chunk type, semantically similar but
   wrong section, etc.). This is the most useful artifact for debugging RAG.
2. The aggregate metrics let you A/B test changes — re-chunk, swap embedder,
   add reranking — and see if your change moved the numbers.
3. A "miss" doesn't always mean the system is broken: sometimes the question
   is genuinely ambiguous. Your gold set quality is itself worth iterating on.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

EVAL_PATH = Path(__file__).parent / "eval_set.json"
CHROMA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "chroma"
COLLECTION_NAME = "building_manuals"


def load_eval_set() -> list[dict]:
    return json.loads(EVAL_PATH.read_text())


def get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),
    )


def first_hit_rank(retrieved_ids: list[str], gold_ids: set[str]) -> int | None:
    """Return 1-indexed rank of the first retrieved gold ID, or None if no hit."""
    for i, rid in enumerate(retrieved_ids, start=1):
        if rid in gold_ids:
            return i
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=3, help="top-k to retrieve (default 3)")
    args = parser.parse_args()

    eval_set = load_eval_set()
    collection = get_collection()

    hits_at_1 = 0
    hits_at_k = 0
    reciprocal_ranks: list[float] = []

    print("=" * 78)
    print(f"running eval over {len(eval_set)} questions, top_k={args.k}")
    print("=" * 78)

    for item in eval_set:
        qid = item["id"]
        question = item["question"]
        gold = set(item["gold_chunk_ids"])

        res = collection.query(query_texts=[question], n_results=args.k)
        retrieved_ids = res["ids"][0]
        rank = first_hit_rank(retrieved_ids, gold)

        if rank == 1:
            hits_at_1 += 1
        if rank is not None and rank <= args.k:
            hits_at_k += 1
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)

        status = "✓" if rank else "✗"
        rank_str = f"@{rank}" if rank else "MISS"
        print(f"\n{status} [{qid}] {rank_str}  {question}")
        print(f"     gold:      {sorted(gold)}")
        print(f"     retrieved: {retrieved_ids}")

    n = len(eval_set)
    recall_at_1 = hits_at_1 / n
    recall_at_k = hits_at_k / n
    mrr = sum(reciprocal_ranks) / n

    print()
    print("=" * 78)
    print(f"Recall@1:    {recall_at_1:.2%}   ({hits_at_1}/{n})")
    print(f"Recall@{args.k}:    {recall_at_k:.2%}   ({hits_at_k}/{n})")
    print(f"MRR:         {mrr:.3f}")
    print("=" * 78)
    print()
    print("Read this as:")
    print(f"  • Recall@1: {hits_at_1} of {n} questions had the right chunk as TOP result.")
    print(f"  • Recall@{args.k}: {hits_at_k} of {n} questions had the right chunk in top {args.k}.")
    print("  • MRR: 1.0 = always #1. 0.5 ≈ usually #2. 0.0 = never found.")


if __name__ == "__main__":
    main()
