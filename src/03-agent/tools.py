"""
Tool definitions + implementations for the Phase 3.4 agent.

Two tools:
  1. query_telemetry(sensor_id)  — fake sensor reading lookup
  2. search_manual(query)        — calls our RAG retrieval from Phase 3.2

Schema design:
  Every tool has (a) a JSON schema the LLM sees, (b) a Python function the
  agent runtime executes. Same separation as 03_tool_use_preview.py.

  The schema is the CONTRACT (interface). The function is the IMPLEMENTATION.
  The LLM only sees the contract.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

# ---------------------------------------------------------------------------
# Tool 1: query_telemetry — fake but deterministic
# ---------------------------------------------------------------------------

# we hash the sensor_id to a stable "temperature" so demos are reproducible.
# in real life this would be a Kafka consumer / DB query / time-series API.
def _fake_temp_for(sensor_id: str, baseline: float = 70.0) -> float:
    h = int(hashlib.md5(sensor_id.encode()).hexdigest(), 16)
    # spread temps roughly 55–95 F across the input space
    return baseline + ((h % 41) - 15)


def query_telemetry(sensor_id: str) -> dict:
    """Look up the latest reading for a building sensor. Returns a dict."""
    temp = _fake_temp_for(sensor_id)
    baseline = 70.0
    delta = temp - baseline
    return {
        "sensor_id": sensor_id,
        "reading_f": round(temp, 1),
        "baseline_f": baseline,
        "delta_f": round(delta, 1),
        "status": "alarm" if abs(delta) > 15 else "normal",
        "timestamp": "2026-05-22T14:03:11Z",
    }


# ---------------------------------------------------------------------------
# Tool 2: search_manual — reuses the Phase 3.2 Chroma collection
# ---------------------------------------------------------------------------

CHROMA_DIR = Path(__file__).parent.parent.parent / "data" / "chroma"
COLLECTION_NAME = "building_manuals"

_collection: chromadb.Collection | None = None


def _get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_functions.DefaultEmbeddingFunction(),
        )
    return _collection


def search_manual(query: str, top_k: int = 3) -> dict:
    """Retrieve the top-k most relevant manual chunks for a query.

    Returns RAW CHUNKS, not a generated answer. The agent's outer LLM does
    the synthesis. This keeps the tool's responsibility narrow: retrieval.
    """
    res = _get_collection().query(query_texts=[query], n_results=top_k)
    chunks = [
        {
            "chunk_id": cid,
            "source": meta["source"],
            "section": meta["section"],
            "content": doc,
        }
        for cid, doc, meta in zip(
            res["ids"][0], res["documents"][0], res["metadatas"][0]
        )
    ]
    return {"query": query, "chunks": chunks}


# ---------------------------------------------------------------------------
# Schemas the LLM sees, + registry the agent runtime uses
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "query_telemetry",
        "description": (
            "Look up the latest reading for a building sensor by its ID. "
            "Returns temperature in Fahrenheit, baseline, delta, and status "
            "('normal' or 'alarm' when |delta| > 15F). "
            "Use this when you need real-time sensor data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sensor_id": {
                    "type": "string",
                    "description": "Sensor identifier, e.g. 'S-47' or 'AHU-3-supply'.",
                }
            },
            "required": ["sensor_id"],
        },
    },
    {
        "name": "search_manual",
        "description": (
            "Search the building operations manuals for relevant sections. "
            "Returns the top matching manual chunks with their source and section. "
            "Use this for any question about fault codes, alarm meanings, "
            "operating parameters, system architecture, or recommended procedures."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language search query.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "How many chunks to return (default 3).",
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
]

TOOL_REGISTRY = {
    "query_telemetry": query_telemetry,
    "search_manual": search_manual,
}
