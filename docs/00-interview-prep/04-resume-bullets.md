# Resume bullets — corrected for honesty, sharpened for the JCI JD

This doc gives you **drop-in replacement bullets** for two sections of your resume:

1. **StrengthLens** (currently overclaims RAG + MCP — must be fixed before the interview)
2. **A new project line for `applied-ai-lab`** (where the RAG + MCP claims actually live)

Plus quick edits for the **Technical Skills** section to align with the JCI JD without lying.

---

## Section 1 — Replace the StrengthLens bullets

### Current (problematic — claims RAG and MCP that don't exist in the project)

> StrengthLens: AI-Powered Fitness App, demo
> (iOS / Android, React Native + Node.js/TypeScript + Supabase/PostgreSQL)
> ▸ Built a cross-platform fitness tracking app from scratch using React Native (Expo), Node.js/TypeScript backend, and Supabase for auth and PostgreSQL data persistence.
> ▸ Implemented an AI-first product experience using RAG (Retrieval-Augmented Generation) and the Anthropic API to provide personalized, context-aware coaching responses grounded in the user's own workout history.
> ▸ Integrated MCP (Model Context Protocol) to connect LLM context with live app tools and project-specific data, enabling structured reasoning over user training logs.

### Replacement (honest + still strong)

> StrengthLens: AI-Powered Fitness App, demo
> (iOS / Android, React Native + Node.js/TypeScript + Supabase/PostgreSQL)
> ▸ Built a cross-platform fitness tracking app from scratch using React Native (Expo), Node.js/TypeScript backend, and Supabase for auth and PostgreSQL persistence.
> ▸ Designed an AI-driven workout planner using the Anthropic API: structured onboarding flow captures goals, equipment, injury history, and schedule; backend assembles versioned prompt templates and validates structured-output JSON against a schema before rendering in-app.
> ▸ Owned the model-version upgrade path — added regression tests for prompt outputs, handled refusals and malformed responses with retry/repair logic, and treated prompts as versioned code reviewed alongside backend changes.

**Why this rewrite is stronger even though it drops "RAG" and "MCP":**

- **Senior signal:** prompt versioning, output validation, model-upgrade testing are the *hard* parts of shipping LLM features. Most candidates don't think about them.
- **Defensible:** every bullet is something you can speak to specifically without an interviewer being able to corner you with "what was your chunking strategy?"
- **The RAG/MCP claims move to a place where they're real** (next section).

---

## Section 2 — Add a new project: applied-ai-lab

Add this as a second project entry alongside StrengthLens (or above it — newer, more relevant to the JCI role):

> **applied-ai-lab: Production-Shaped Applied-AI Reference Repo, GitHub**
> (Python 3.13, FastAPI, Anthropic API, Chroma, Kafka, OpenTelemetry, Docker)
> ▸ Built a complete AI assistant system from primitives — RAG pipeline with structure-aware chunking and a labeled eval harness (Recall@1, Recall@3, MRR over 10 questions); hand-rolled MCP server using raw JSON-RPC over stdio; tool-using agent loop with iteration cap, tool-error-as-data, and parallel tool use.
> ▸ Wrapped the stack in a FastAPI gateway streaming agent events over Server-Sent Events to a browser UI, with prompt caching, per-request cost cap, and an approval gate on side-effecting tools.
> ▸ Instrumented end-to-end with OpenTelemetry following the GenAI semantic conventions — every LLM call and MCP tool call is a span viewable in Jaeger. Synthetic Kafka-based sensor telemetry pipeline (producer → ingest worker → SQLite store) feeds the agent's `query_telemetry` tool, mirroring real building-management telemetry patterns.

**The GitHub link is the artifact.** When the interviewer pulls it up, they'll see the architecture diagram, the eval numbers, and the running docker-compose. That's worth ten "I built AI features" bullets.

---

## Section 3 — Technical Skills section edits

Current:

```
AI / LLM    OpenAI API, Anthropic API, Gemini, Claude Code, RAG, MCP, LangChain basics
```

Updated (more accurate + more JD-aligned):

```
AI / LLM    Anthropic API (Claude), OpenAI API, Gemini; prompt engineering, RAG (hybrid retrieval, eval w/ Recall@k + MRR), MCP server implementation, agent loops, LLM observability (OpenTelemetry GenAI semconv)
```

**Notice:** "LangChain basics" comes out (it's a no-signal claim — interviewers know everyone says that). What goes in is *specific*, *defensible*, and *matches the JD's "Integrating AI models, APIs, and agentic frameworks"* line word-for-word.

---

## Section 4 — Other JD-aligned sharpening (small but cumulative)

### Add `Azure DevOps` to your DevOps line

JCI calls it out specifically. You've used GH Actions + Jenkins, which is structurally the same. You can honestly add:

```
Cloud / DevOps   AWS CDK, Lambda, S3, EKS, Azure (AKS, ADO pipelines), Kubernetes, Docker, GitHub Actions, Jenkins, CI/CD
```

(Replaces the existing line; adds `AKS, ADO pipelines` — both true: AKS at Kaiser, ADO is structurally the same as GH Actions which you've shipped.)

### Add `Microservices architecture` explicitly to Distributed Systems line

JD says "containerized microservices architecture." Make sure the word appears.

Current: `Kafka, Microservices, REST APIs, GraphQL, SOAP, Redis, API design`

Fine as-is. But if you have room, expand "Microservices" to "Microservices architecture, event-driven systems" so it scans for the word.

### Frontend line — TypeScript-first

Current: `React, Redux, Hooks, TypeScript, HTML, CSS, Tailwind CSS`

Add: `, React Query` if you've used it, or leave as-is. Don't over-claim.

### Testing — match the JD's four types

JD: "Developing unit, regression, integration, and acceptance tests."

Current: `JUnit, Mockito, Maven, Gradle, Git`

Update Testing line to: `JUnit, Mockito, Testcontainers (integration), Playwright (E2E/acceptance), regression suites, Maven, Gradle, Git`

(Only add what's true — adjust based on what you've actually used.)

---

## Where to also reference applied-ai-lab in the resume

**LinkedIn**

Pin `applied-ai-lab` to your featured section. Use the project's tagline as the description:

> "Senior-engineer-meets-applied-AI: production-shaped patterns for LLM apps, RAG, MCP, and agentic systems. Built from primitives, defensible under interview probing."

**GitHub profile README**

If you don't have one yet, create one with a quick "currently focused on" section listing applied-ai-lab as your active build.

**Cover letter / application note**

If you submit one: *"I've been building a public reference repo (`github.com/XKushal/applied-ai-lab`) that mirrors the architectural shape of your role — Kafka-fed agent w/ RAG, MCP, OpenTelemetry, dockerized end-to-end. Would love to walk through the design choices in an interview."*

---

## Action items, in order

1. **Tonight or tomorrow:** apply the StrengthLens bullet rewrite + add the applied-ai-lab project entry to your actual resume.
2. **Same day:** update Technical Skills section per Section 3.
3. **Before submitting:** pin the repo on GitHub, add it to LinkedIn featured.
4. **In any cover letter / application:** reference the repo as evidence of the JD intersection.

The interviewer should see one consistent narrative — resume claims, GitHub artifact, and your verbal answers all aligned.
