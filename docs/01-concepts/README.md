# Concepts — interview-defensible depth

Six docs. Each is built to be re-read 3× before the interview, not skimmed once. Every doc ends with a **"What an interviewer will probe"** section — drill on those.

Reading order:

1. **[01-llm-mental-model.md](01-llm-mental-model.md)** — tokens, context windows, sampling, when an LLM is the wrong tool
2. **[02-embeddings-and-retrieval.md](02-embeddings-and-retrieval.md)** — embedding models, chunking, hybrid search + reranking, vector DBs
3. **[03-rag-architecture.md](03-rag-architecture.md)** — naïve vs production RAG, eval (Recall@k, LLM-as-judge), failure modes
4. **[04-agent-loop.md](04-agent-loop.md)** — the actual control flow, tool-use, retry/safety, multi-agent ≠ always better
5. **[05-mcp-deep-dive.md](05-mcp-deep-dive.md)** — JSON-RPC lifecycle, three primitives, transports, MCP at enterprise scope
6. **[06-observability.md](06-observability.md)** — OTel GenAI semconv, eval-in-production, audit logging

Each doc has at least one Mermaid diagram (GitHub renders them natively — just open the file in the web UI).

## Drill priority for a JCI interview

Highest → lowest probability of coming up:

1. **RAG architecture + eval** — "walk me through your RAG pipeline" and "how do you measure retrieval quality" are *the* AI questions for this role
2. **Agent loop mechanics** — "what is an agent really doing?" — easy to flunk if you've only used a framework
3. **MCP deep-dive** — fewer interviewers will probe this, but the ones who do go hard. High payoff if you know it cold.
4. **LLM mental model** — "when would you not use an LLM" is a senior-signal question
5. **Observability** — your Kaiser experience already covers this; just need the AI-specific vocabulary
6. **Embeddings + retrieval** — supports #1; standalone questions less common
