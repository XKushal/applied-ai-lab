# 60-second pitch + bridge sentences

## The pitch — your answer to "tell me about yourself"

Memorize the *shape*, not the words. Three beats, ~60 seconds spoken.

---

> "I'm a senior software engineer with 6+ years building distributed backend systems — most recently at Kaiser Permanente, where I architect Quarkus and Spring Boot microservices serving millions of members on the digital health platform.
>
> The work I'm proudest of is the Data eXchange Platform — a Kafka-backed event-driven layer that decoupled 12+ services, cut their latency tails, and gave the team independent deploy velocity. Same DNA you'd see in any high-throughput IoT or telemetry pipeline.
>
> What's been pulling me lately is **applied AI** — I shipped an Anthropic-API-powered workout planner in my StrengthLens project (structured prompt engineering, versioned prompts, reliable JSON outputs), and I've gone deeper since in a personal lab — hand-rolling an MCP server and a RAG pipeline with eval to actually understand the primitives. The hard parts I've been learning to care about are retrieval quality, agent reliability, hallucination mitigation, and the production observability story for LLM apps. That's the intersection your Enterprise AI team sits at — distributed systems meeting applied AI — and it's why I'm in this conversation."

---

**Why this works:**

- Opens with **seniority + concrete current role** (Kaiser is a name they'll know).
- Middle beat anchors a **specific architecture you built** (DXP) and quietly translates it to *their* domain (IoT/telemetry).
- Closing beat says "I'm not new to AI, I've shipped it, and I've started caring about the hard parts" — that last clause is the senior signal.
- Ends with a **"why JCI"** lead-in so they don't have to ask it next.

---

## "Why JCI?" — the follow-up that always comes

> "Two reasons. One — the Enterprise AI team's mandate is exactly the intersection I want to deepen in: large-scale backend systems meeting agentic AI in a real industrial domain, not a chatbot wrapper on a SaaS API. Smart buildings have IoT telemetry, real safety constraints, real ROI metrics — that's a far more interesting problem space for AI than the consumer side of it. Two — JCI is an Azure shop and I've been on AKS in production for years; that's a fast ramp on the cloud side so I can spend my energy on the AI integration work."

Adjust freely. Don't say "compensation" or "remote", don't say "I want to learn AI" (you've already shipped it).

---

## Bridge sentences — translating healthcare → smart buildings on the fly

These are pre-written one-liners you can drop into any answer to make your healthcare experience land in JCI's domain. Memorize 3–4 and they'll feel natural in conversation.

| When you say… | …drop in this bridge |
|---|---|
| "At Kaiser we have 12 services on Kafka…" | *"…which is structurally the same as a building-sensor telemetry fan-out — one ingest topic, multiple independent consumers for alerting, analytics, AI inference."* |
| "We tune p99 latency on healthcare APIs…" | *"…and the same SLO discipline applies to anything where the user is a human in the loop — a building operator needs the same response time guarantees a clinician does."* |
| "We use Dynatrace + Splunk for observability…" | *"…and the LLM observability story is even harder — you also need to track which retrieval chunks were used, which tool calls fired, and whether the model's output was grounded. That's where OpenTelemetry semantic conventions for GenAI come in."* |
| "I shipped structured prompt engineering in StrengthLens…" | *"…and the same discipline applies here at a bigger scope — versioned prompts, structured outputs, model-upgrade testing, plus RAG over building manuals and MCP for live tool calls as the next layer up."* |
| "AKS production ops, Helm, KEDA…" | *"…that experience transfers cleanly to any Azure-native deployment; AKS is AKS whether it's serving health data or smart-building inference."* |

---

## The "what's your weakness / what are you working on" answer

> "Honestly, my .NET is the rustiest piece of my stack — I shipped it at IMT in 2021–22 but I've been deep on the Java side at Kaiser since. I'm comfortable ramping back up on current ASP.NET Core, but I'd be upfront that I'd lean on the team's conventions for the first sprint or two rather than pretending it's fresh. Other than that, the place I'm actively investing is **production-grade AI evals** — anyone can call an LLM API; building the eval harness that tells you whether a retrieval change actually helped is the discipline I'm sharpening right now."

That answer does three jobs: it's honest about the .NET gap (they'll respect that more than a fake answer), it shows self-awareness, and the second sentence flexes that you're already thinking about the *hardest* part of AI engineering — eval — which puts you ahead of most candidates who only talk about prompts.
