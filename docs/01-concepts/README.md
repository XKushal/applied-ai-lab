# Concepts — depth, not skim

Six docs. Each is built to be re-read, not skimmed once. Every doc ends with a **"Questions worth being able to answer"** section that turns the concept into the kind of probing you'd get in a design discussion.

Reading order:

1. **[01-llm-mental-model.md](01-llm-mental-model.md)** — tokens, context windows, sampling, when an LLM is the wrong tool
2. **[02-embeddings-and-retrieval.md](02-embeddings-and-retrieval.md)** — embedding models, chunking, hybrid search + reranking, vector DBs
3. **[03-rag-architecture.md](03-rag-architecture.md)** — naïve vs production RAG, eval (Recall@k, LLM-as-judge), failure modes
4. **[04-agent-loop.md](04-agent-loop.md)** — the actual control flow, tool-use, retry/safety, multi-agent ≠ always better
5. **[05-mcp-deep-dive.md](05-mcp-deep-dive.md)** — JSON-RPC lifecycle, three primitives, transports, MCP at enterprise scope
6. **[06-observability.md](06-observability.md)** — OTel GenAI semconv, eval-in-production, audit logging

Each doc has at least one Mermaid diagram (GitHub renders them natively — just open the file in the web UI).

## Where the payoff is highest

Roughly highest → lowest in how often these come up for an applied-AI backend role:

1. **RAG architecture + eval** — "walk me through your RAG pipeline" and "how do you measure retrieval quality" are *the* core AI questions
2. **Agent loop mechanics** — "what is an agent really doing?" — easy to flunk if you've only used a framework
3. **MCP deep-dive** — fewer people probe this, but the ones who do go hard. High payoff for knowing it cold.
4. **LLM mental model** — "when would you not use an LLM" is a senior-signal question
5. **Observability** — distributed-systems experience already covers most of this; the AI-specific vocabulary is the gap to close
6. **Embeddings + retrieval** — supports #1; standalone questions less common
