"""
3.2.1 — Ingest pipeline. Load → chunk → embed → store.

Reads every markdown file from ./corpus/, splits each on H2 headings
(structure-aware chunking — see docs/01-concepts/02-embeddings-and-retrieval.md),
embeds each chunk locally with sentence-transformers (via Chroma's default),
and stores in a persistent Chroma collection at ./data/chroma/.

Run:
    uv run python src/02-rag/01_ingest.py

Re-run safely: the script deletes the collection first to keep things clean.

What to observe:
1. First run downloads the embedding model (~80MB) — that's one-time.
2. Each chunk gets an ID like `<filename>::<section>`.
3. Metadata records source filename + section heading — used for citations later.
4. The collection count at the end = total chunks ingested.
"""

from __future__ import annotations

import re
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

CORPUS_DIR = Path(__file__).parent / "corpus"
CHROMA_DIR = Path(__file__).parent.parent.parent / "data" / "chroma"
COLLECTION_NAME = "building_manuals"


def chunk_by_h2(text: str) -> list[tuple[str, str]]:
    """Split a markdown doc into (section_title, section_body) chunks on H2 (`## `).

    Why H2 and not arbitrary size? These docs are written with H2 sections that are
    *semantically coherent units* — each section is one topic. Chunking on structure
    preserves that. Fixed-size character splits would slice mid-table or mid-paragraph,
    destroying the meaning we need for retrieval.

    For docs that lack good structure, you'd fall back to a recursive splitter on
    \\n\\n → \\n → sentence → character with overlap. See concepts doc 02.
    """
    # split on lines that start with "## " — keep the heading with the body that follows
    parts = re.split(r"^## ", text, flags=re.MULTILINE)
    # parts[0] is everything before the first H2 (usually the H1 title + preface)
    preface = parts[0].strip()
    chunks: list[tuple[str, str]] = []
    if preface:
        chunks.append(("preface", preface))
    for part in parts[1:]:
        head, _, body = part.partition("\n")
        chunks.append((head.strip(), body.strip()))
    return chunks


def main() -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # always rebuild from scratch in this learning project
    try:
        client.delete_collection(COLLECTION_NAME)
    except (chromadb.errors.NotFoundError, ValueError):
        pass

    embedder = embedding_functions.DefaultEmbeddingFunction()
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedder,
        metadata={"hnsw:space": "cosine"},  # cosine similarity, see concepts doc 02
    )

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for md_file in sorted(CORPUS_DIR.glob("*.md")):
        text = md_file.read_text()
        for section_title, section_body in chunk_by_h2(text):
            if not section_body:
                continue
            # we PREPEND the section title to the body before embedding —
            # this is structure-aware chunking: the heading is context the
            # embedder should see, not just metadata
            content = f"# {section_title}\n\n{section_body}"
            chunk_id = f"{md_file.stem}::{section_title}"
            ids.append(chunk_id)
            documents.append(content)
            metadatas.append(
                {"source": md_file.name, "section": section_title}
            )

    print(f"ingesting {len(ids)} chunks from {len(list(CORPUS_DIR.glob('*.md')))} files...")
    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"  done. collection '{COLLECTION_NAME}' has {collection.count()} items.")
    print(f"  persisted at {CHROMA_DIR}")
    print()
    print("sample of ingested IDs:")
    for i in ids[:5]:
        print(f"  - {i}")


if __name__ == "__main__":
    main()
