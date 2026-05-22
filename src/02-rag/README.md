# 3.2 — RAG from scratch

A complete RAG pipeline in ~150 lines across 3 scripts. No framework. Local embeddings, local vector DB, your existing Anthropic API key.

This builds the foundation for Phase 4's capstone — the same corpus + ingestion pipeline gets reused there, just behind an MCP tool instead of called directly.

## File map

```
src/02-rag/
├── corpus/                       # 3 fake building manuals to retrieve over
│   ├── chiller-system-overview.md
│   ├── fault-codes-reference.md
│   └── bms-network-architecture.md
├── 01_ingest.py                  # load + chunk + embed + store
├── 02_retrieve.py                # retrieval ONLY (no LLM)
├── 03_rag.py                     # full pipeline w/ grounded prompting + citations
└── eval/
    ├── eval_set.json             # 10 labeled questions w/ gold chunk IDs
    └── run_eval.py               # Recall@1, Recall@3, MRR — see Phase 3.3
```

The Chroma DB persists under `data/chroma/` (gitignored).

## Run order

```bash
# 1) ingest the corpus (once; first run downloads embedding model ~80MB)
uv run python src/02-rag/01_ingest.py

# 2) inspect retrieval in isolation (try several queries)
uv run python src/02-rag/02_retrieve.py "low refrigerant pressure"
uv run python src/02-rag/02_retrieve.py "how does BACnet addressing work"
uv run python src/02-rag/02_retrieve.py "weather in Milwaukee"   # off-corpus on purpose

# 3) full RAG (retrieve + grounded prompt + citations)
uv run python src/02-rag/03_rag.py "What does chiller fault E47 mean and what should I do?"
uv run python src/02-rag/03_rag.py "How is the BMS network secured?"
uv run python src/02-rag/03_rag.py "What's the weather in Milwaukee?"   # should refuse
```

## What each script teaches

### `01_ingest.py` — structure-aware chunking

Critical detail: **we chunk on H2 (`##`) headings**, not by character count. Why:

- These docs are written with sections that are *semantically coherent units*.
- Fixed-character splits would slice mid-table or mid-paragraph and destroy meaning.
- We also **prepend the heading to the chunk body before embedding** — so the embedder sees "Common alarms / E47 means..." instead of just "E47 means..." — which makes the chunk's vector capture both topic and detail.

This matches the strategy described in [concepts doc 02 → Chunking strategies](../../docs/01-concepts/02-embeddings-and-retrieval.md#chunking-strategies-worst-→-best-for-typical-docs), tier 4 ("structure-aware"). For docs without good structure (random PDFs, transcripts), you'd fall back to recursive splitting on `\n\n` → `\n` → sentence → character with overlap.

### `02_retrieve.py` — retrieval naked

The most valuable script in this folder. **Try the off-corpus query** (`"weather in Milwaukee"`) and watch what comes back: three chunks, with higher distances than the on-corpus queries — but **still three chunks**. The DB always returns top-k. There's no "no results" — the model would happily ground itself in those irrelevant chunks if you fed them in blindly.

**Senior takeaway** — production RAG needs either:
- A **distance threshold** (drop chunks with distance > X)
- A **refuse-when-unsupported** instruction in the system prompt (`03_rag.py` uses this approach)
- Preferably both, plus an **eval** measuring refusal rate so you catch drift

### `03_rag.py` — the whole pipeline

Three things to look at after running it:

1. **The system prompt.** Read it. It does three jobs: (a) restricts the model to the provided context only, (b) requires citations in `[citation: <chunk_id>]` format, (c) provides an exact refusal phrase for insufficient context. This is "grounded prompting" — the most important hallucination defense.

2. **The user prompt structure.** Retrieved chunks are wrapped in `<context>...<chunk id="..." source="...">...</chunk>...</context>`. The XML-style tags are a real signal the model is trained on for "this block of text is data, not instructions" — and it also makes parsing/inspection trivial later.

3. **Citation validation** (end of the script). We `re.findall` for `[citation: ...]` patterns and check each cited ID was actually retrieved. If the model invents an ID (`"chunk_42"` that doesn't exist), we flag it. **That is a real production check** — hallucinated citations are one of the most common ways RAG fools its users.

## What's missing (deliberately) — and what we'd add for production

This is naïve RAG. It works for the demo. Things we have *not* done that the concepts doc says you'd need in production:

| Missing | When you'd add it |
|---|---|
| **Hybrid search (BM25 + vector)** | When users search for exact codes/model numbers ("E47") that vector alone might miss in synonym-rich corpora |
| **Reranker** | When top-k recall is good but top-1 precision isn't — a cross-encoder reorders the top-20 into the best top-3 |
| **Query rewrite** | When user queries are short and ambiguous; an LLM expansion catches more |
| **Distance threshold** | When you'd rather refuse than ground in weak matches |
| **Eval harness** | Always. Phase 3.3 (next) builds this. |
| **Real-world embedding model** | Voyage-3 or text-embedding-3-large for English; domain-tuned for specialty corpora. MiniLM is fine for prototyping, weak for production. |

## Tying this back to interviews

You can now legitimately say:

> "I built a RAG pipeline from scratch — structure-aware chunking on document hierarchy, persisted vector store in Chroma, grounded prompting with citation requirement, and runtime citation validation to catch hallucinated chunk IDs. Repo's public."

That's a real answer, not a hand-wave. It maps directly to the production RAG diagram in [concepts doc 03](../../docs/01-concepts/03-rag-architecture.md), which means you can walk an interviewer up the maturity ladder from what you built → what production would add → why you'd add it.
