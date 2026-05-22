# Likely interview questions — JCI Enterprise AI Software Developer

40 questions across the **full JD scope**, not just AI. Each comes with a "shape of the answer" — beats to hit, not a memorized script. Speak naturally, hit the beats.

Drill priority:
- ⭐⭐⭐ = will almost certainly come up
- ⭐⭐ = high probability
- ⭐ = curveball / depth probe

---

## A. Backend / distributed systems (your home turf)

**A1. ⭐⭐⭐ Walk me through a backend system you designed.** → Story 1 — DXP / Kafka decoupling. Beats: tight coupling problem → event-driven decoupling, schema registry, KEDA scaling, migration playbook → result (latency tail cut, independent deploy velocity). Close with the JCI bridge sentence.

**A2. ⭐⭐⭐ How do you decide between sync REST and async event-driven?** → Coupling tolerance, latency needs, failure isolation, throughput. REST when you need request-response semantics and a real-time answer; events when you can tolerate eventual consistency, want fan-out, or when downstream may be slow/down. *"In healthcare we used both — sync for clinical flows, async via Kafka for analytics and pub/sub between services."*

**A3. ⭐⭐ Tell me about a performance tuning win.** → Story 2 — p99 latency hunt. Beats: Dynatrace trace → query plan → composite index respecting predicate order → validate in replica → roll out → add Splunk alert so the next regression is caught preemptively. Result: ~35% p99 reduction.

**A4. ⭐⭐ How do you keep services from coupling tightly over time?** → Schema contracts (registry-enforced, versioned), explicit interface boundaries, no shared databases between services, gates in CI that fail breaking changes. Mention contract testing.

**A5. ⭐⭐ Talk to me about idempotency.** → Why it matters in event-driven and retry-heavy systems. Idempotency keys, "exactly-once" is mostly a lie at the transport layer but achievable at the storage layer. Mention insert-on-conflict / upserts as a common pattern.

**A6. ⭐ Have you used circuit breakers? Why?** → Yes — protect upstream from cascading failure when a downstream is unhealthy. Resilience4j on Java side. Trip on error-rate threshold, half-open trial state, full close when healthy. Pair with sane timeouts and bulkheads.

---

## B. Languages and stacks (mixed — JCI lists .NET, React, Java, Python, C++, MS SQL)

**B1. ⭐⭐⭐ Talk through your .NET / ASP.NET Core experience.** → Be honest about the timeline. IMT 2021–22: full ASP.NET Core REST APIs + Entity Framework + complex SQL stored procs against MS SQL Server. Delaget intern: ASP.NET Core + React/TS dashboards over MS SQL. *"My .NET is my rustiest stack — I've been deep on Java/Spring Boot at Kaiser since. I'd ramp on current ASP.NET Core LTS for the first sprint and lean on the team's conventions."* See [`04-rusty-stack-cheatsheets.md`](04-rusty-stack-cheatsheets.md) for what's changed.

**B2. ⭐⭐ Walk me through how you'd structure a Spring Boot service from scratch.** → Project layout (controller / service / repository / model), DI via constructor injection (not field), config via `@ConfigurationProperties` not magic strings, profile-based env (`dev/prod`), Actuator for health + Prometheus metrics, OpenAPI spec generation, exception mapper, structured logging w/ correlation IDs propagated end-to-end.

**B3. ⭐⭐ Spring Boot vs Quarkus — when which?** → Spring Boot for ecosystem depth + team familiarity. Quarkus when fast startup + low memory matters (serverless, native compilation via GraalVM). I've used both at Kaiser. Mention reactive flavors (Mutiny / Project Reactor) only if asked.

**B4. ⭐⭐⭐ React experience and patterns.** → Hooks-first since 2019, function components, custom hooks for reusable state logic. Redux when global state has real complexity; otherwise lift state, use context selectively, or move to React Query / server state libs for server data. At IMT shipped TypeScript + Redux for the policy admin flows; at StrengthLens it's React Native (same model, different host). On the JCI dashboard side, expect a similar pattern — typed components, server state separated from UI state.

**B5. ⭐⭐ Why TypeScript over plain JS for a real codebase?** → Compile-time guarantee on prop/return shapes, refactor safety, IDE assistance, narrows bug class to runtime-only. Strict mode + no-implicit-any non-negotiable on a senior team. Most useful when the codebase has multiple contributors.

**B6. ⭐⭐⭐ Python — talk about how you've used it.** → Backend tooling, scripting, and the applied-AI-lab work (RAG, agent loops, MCP, FastAPI). For agentic / data work it's the lingua franca. If asked about web backends specifically: FastAPI for new services, async patterns, Pydantic for validation. Honest about: it's not my primary production language at Kaiser (that's Java).

**B7. ⭐⭐ MS SQL specifically — what's different from MySQL / Postgres?** → T-SQL dialect, query store for plan history, columnstore indexes for analytics workloads, included columns in indexes (similar to Postgres INCLUDE), MERGE statement, CLR integration. I've tuned indexes and stored procs against MS SQL at IMT/Delaget. Pivot to "the index strategy story translates regardless of engine."

**B8. ⭐ C++ — have you used it?** → Honest answer: "I've used it in coursework. It's the language on the JCI list I have least production time in. I'd lean on team conventions and reviews to ramp; I'm comfortable across statically-typed languages so the syntax isn't the barrier — it'd be idiomatic memory management and the team's build/test patterns." Don't oversell. JCI rarely tests C++ for this role; they list it because some teams touch device firmware adjacencies.

---

## C. Cloud, containers, microservices

**C1. ⭐⭐⭐ Walk me through how you containerize a service.** → Multi-stage Dockerfile, distroless or slim base, non-root user, drop capabilities, pin versions, vulnerability scan in CI. For Java: layered JAR, jlink-trimmed JRE. For Python: `uv` for deterministic deps, no global pip. Bake config from env, not files. Healthcheck + graceful shutdown.

**C2. ⭐⭐⭐ Tell me about your Kubernetes experience.** → Story 5 — AKS + Helm + KEDA at Kaiser. Beats: Helm charts for declarative cross-env, resource requests at p50 + limits at p99+headroom, KEDA on Kafka consumer lag (not CPU) for event-driven services. Hit the senior point: "the right scaling signal is *work to do*, not CPU after work piled up."

**C3. ⭐⭐ How do you handle secrets in K8s?** → Never in image or env files in Git. Managed identity / Workload Identity binding pods to cloud-native secret stores (Azure Key Vault for AKS, AWS Secrets Manager via IRSA on EKS). External Secrets Operator or CSI driver mounts them. Rotate without re-deploying.

**C4. ⭐⭐ Service mesh — opinions?** → Istio / Linkerd add mTLS, retries, traffic shifting, observability. **Don't reach for it on day 1.** Adds operational complexity. Add when you've outgrown sidecarless patterns and your security model requires zero-trust east-west. For most teams, OpenTelemetry + a good ingress + library-level retries is enough.

**C5. ⭐⭐ How do you do canary deploys / blue-green?** → Argo Rollouts on K8s for canaries with traffic splitting + automatic rollback on metric SLO breach. Or feature flags + percentage rollout at the application layer. Blue-green when state migration is risky and you want a hard cutover.

**C6. ⭐ Stateless vs stateful — when do you accept stateful?** → Default stateless. Accept stateful when the persistence is genuinely the value (databases, message brokers, search). For those use a managed service or operator-managed StatefulSets, never hand-rolled.

---

## D. DevOps, CI/CD, Azure (JCI is an Azure shop)

**D1. ⭐⭐⭐ Walk me through a CI/CD pipeline you've owned.** → Story 4 — GitHub Actions + Jenkins + SonarQube + Nexus IQ at Kaiser. Beats: PR triggers build + tests + static analysis + dependency vuln scan + contract tests. Merge to main builds image + pushes to registry + Helm rolls out to dev. Promotion to UAT/PROD via approvals + auto rollback on SLO breach. Quality gates are *gating* — if SonarQube finds a critical hotspot, the build is red, period.

**D2. ⭐⭐ Azure DevOps vs GitHub Actions.** → Same shape (pipelines as YAML, agents/runners, marketplace tasks). Azure DevOps shines for Boards/Repos integration and enterprise on-prem agents; GH Actions wins for OSS and ecosystem velocity. I've worked with GH Actions + Jenkins at Kaiser. Comfortable with Azure DevOps — it's `azure-pipelines.yml` and tasks, same mental model.

**D3. ⭐⭐ What's a quality gate and how do you set thresholds?** → Hard threshold for code coverage delta (no new untested code), zero critical SonarQube hotspots, zero critical CVEs from dependency scan. Soft thresholds (warnings) for new complexity, line count drift. Thresholds tuned per repo — too tight = devs work around it.

**D4. ⭐⭐ How do you handle a broken build at 5pm on Friday?** → Revert > forward-fix when the failure is unclear. Communicate in team channel. If the revert isn't clean, freeze main, page the owner, fix forward. Postmortem next business day. Never ship-and-hope into a long weekend.

**D5. ⭐ Talk about your testing pyramid.** → Lots of unit tests (fast, cheap), fewer integration tests (real wire, real DB in containers via Testcontainers), few E2E (Playwright / Selenium against full env). Contract tests (Pact, schema registry) for service boundaries. JCI's JD specifically lists unit/regression/integration/acceptance — be ready to talk through all four: unit at code, regression as a managed suite that catches old bugs, integration across components, acceptance against business requirements.

---

## E. Observability, reliability, incidents

**E1. ⭐⭐⭐ How do you set SLOs / SLIs?** → SLI = a measurable quantity that maps to user-visible behavior (request latency p99 < X, error rate < Y%). SLO = the target. Error budget = (1 - SLO) over a window — when you blow it, freeze risky changes and harden. **Never set SLOs on CPU or memory** — those are infra signals, not user signals. Story 7 covers this in production form.

**E2. ⭐⭐⭐ Walk me through how you'd respond to a 3am page.** → Acknowledge → assess severity → mitigate (rollback / scale / circuit-break) → communicate (status page + on-call channel) → resolve → write the postmortem (blameless, action items, timeline). Don't fix-and-forget; the bug that paged you tonight will page you again unless you change something.

**E3. ⭐⭐ Splunk vs Dynatrace — what's each for?** → Splunk = log search + dashboards. Dynatrace = APM + distributed traces + RUM + infra metrics with auto-instrumentation. They overlap but are complementary — Splunk for "what happened at 14:32 in module X" via free-text search, Dynatrace for "where is the latency coming from in this request tree" via traces. I've used both at Kaiser; defined SLOs through Splunk dashboards backed by Dynatrace span data.

**E4. ⭐⭐ How does observability change for an AI app?** → Add: token counts (input/output/cache), per-request USD cost, retrieval quality metrics (Recall@k), refusal rate, citation-validity rate, agent loop iterations, drift on output schema validation. Span attributes per OTel GenAI semconv. Otherwise it's the same playbook as any service — define SLOs that map to user-visible behavior.

---

## F. AI / RAG / MCP / agents (the lab speaks for you)

**F1. ⭐⭐⭐ Tell me about an AI project you built.** → Now you have two: (1) StrengthLens — structured prompt engineering w/ Anthropic API, versioned prompts, schema validation, model-version-drift handling. *Be careful not to over-claim RAG/MCP here.* (2) `applied-ai-lab` — production-shaped repo demonstrating RAG with eval, hand-rolled MCP server, agent loop, OTel-instrumented FastAPI, Kafka ingest. Point at the GitHub.

**F2. ⭐⭐⭐ Walk me through your RAG pipeline.** → Use the production RAG diagram from concepts doc 03. Beats: structure-aware chunking → embedder choice (and why same-model-only across an index) → hybrid retrieve (vector + BM25) → reranker → grounded prompt with citation requirement → output validation. In the lab: baseline Recall@1 60% / Recall@3 80% / MRR 0.68 over a labeled eval set; two specific misses (E47 query, certs query) are the textbook cases for adding BM25 and a reranker. *That's a real number from a real eval, not hand-waving.*

**F3. ⭐⭐ How do you evaluate retrieval quality?** → Labeled question set (gold chunk IDs). Recall@1, Recall@3, MRR — deterministic, fast, cheap. Layer LLM-as-judge faithfulness for generation eval. Re-run on every chunking / embedding / hybrid-weight / reranker change. **Without an eval, you're guessing whether a change helped.**

**F4. ⭐⭐⭐ Walk me through MCP.** → Concepts doc 05 + your hand-rolled server is the evidence. Beats: open standard, JSON-RPC over stdio or HTTP, three primitives (tools / resources / prompts) controlled by model / app / user respectively, message lifecycle (initialize → tools/list → tools/call). Mention the stdout-is-sacred and `inputSchema` vs `input_schema` gotchas unprompted — that's the senior signal.

**F5. ⭐⭐⭐ What is an agent really?** → An LLM in a loop that emits `tool_use` intents and a runtime that executes the tools and feeds results back. ~25 lines in `src/03-agent/agent.py`. The model never executes anything; the runtime is the bridge. Multi-agent / planners / ReAct are patterns on top of this primitive.

**F6. ⭐⭐ When would you NOT use an LLM?** → Deterministic compute (sum a column, regex parse). Exact lookups in a known schema (SQL beats RAG). Anything regulatory / numerical-precision-critical. Low-latency hot paths (LLM TTFT alone is hundreds of ms). High-throughput identical inputs — cache the output, don't re-spend tokens.

**F7. ⭐⭐ How do you handle hallucination?** → Layered. Grounding via RAG. System prompt with refuse-if-unsupported. Citation requirement + post-hoc validation that cited IDs were actually retrieved. Output schema validation. LLM-as-judge faithfulness eval in CI and sampled in prod.

**F8. ⭐⭐ Prompt injection — how do you defend?** → Treat retrieved content as untrusted data, not instructions. Sandwich it between unambiguous delimiters (XML tags). System prompt instructs the model that retrieved text is data. Input guard for obvious injection patterns. Output guard for unexpected actions (e.g., agent suddenly trying to call admin tools). Audit every tool call.

**F9. ⭐⭐ How does prompt caching work and why does it matter?** → Anthropic caches identical prompt prefixes for ~5 min. Mark a stable region (system + tools) with a `cache_control` breakpoint. Cache reads cost ~10% of fresh input tokens. **Cache hit rate >70% is the bar** for any agent with a stable surface. Cost dropped meaningfully in the lab after wiring caching to the system + tools.

**F10. ⭐⭐⭐ How would you architect an AI assistant for JCI's building operators?** → The capstone diagram. Event-driven sensor telemetry (Kafka → time-series store), RAG over building manuals (BACnet/Modbus docs, SOPs), MCP servers per domain owned by domain teams (telemetry team owns telemetry MCP, work-order team owns WO MCP). Agent in a FastAPI gateway w/ OTel tracing. Approval gate on side-effecting tools. Audit logging for everything. *"Same DNA as Kaiser's DXP, applied to building data."*

---

## G. System design / enterprise architecture

**G1. ⭐⭐ How do you approach integrating into a large enterprise system?** → Read the system first. Map the existing seams — what services exist, what message formats are used, what auth model. Don't impose patterns; conform to enterprise conventions unless you have a strong reason. New integrations expose their interface; consumers depend on the interface, not on you. Versioning + deprecation policy from day 1.

**G2. ⭐⭐⭐ How do you design a multi-tenant API?** → Tenant ID propagated end-to-end (header, JWT claim). Row-level security (RLS) in DB OR separate schemas per tenant — RLS scales better, schemas isolate better. Rate limiting per tenant, not just per IP. Tenant-scoped audit logs. Quota per plan. **Never let tenant A's query plan affect tenant B's latency** — connection pooling and query cost limits matter.

**G3. ⭐⭐ How do you handle backward compatibility on a public API?** → Additive changes only on existing versions (new optional fields OK; removing fields or changing types is breaking). New versions live alongside old, with a deprecation timeline. Schema registry for events. Contract tests in CI.

**G4. ⭐ How do you design for client-facing integrations (since JCI calls this out)?** → Versioned APIs, OpenAPI specs published, SDKs generated. Webhook delivery with idempotency keys + signed payloads + exponential backoff retry on 5xx. Per-customer rate limits, per-customer sandbox creds. Status page + customer-facing changelog. Treat your API as a product.

---

## H. Behavioral

**H1. ⭐⭐⭐ Tell me about yourself.** → The pitch in [`docs/00-interview-prep/03-pitch-and-bridges.md`](../00-interview-prep/03-pitch-and-bridges.md). 60 seconds, three beats, ends with the "why JCI" lead-in.

**H2. ⭐⭐⭐ Why JCI?** → The answer in the pitch doc. Two reasons: (1) Enterprise AI team's mandate is the intersection of distributed systems + agentic AI in a real industrial domain, not chatbot SaaS. (2) Azure shop = fast ramp on cloud, energy goes into the AI integration work.

**H3. ⭐⭐⭐ Tell me about a time you led a technical decision.** → Story 1 (DXP) is the strongest. Alternative: Story 4 (quality gates) if they want a process-focused answer.

**H4. ⭐⭐ Tell me about cross-functional collaboration.** → Story 7 covers it — partnered with platform, security, and product on SLO definitions and dashboard buy-in. Senior signal: drove the cross-team alignment, didn't just contribute to it.

**H5. ⭐⭐ Tell me about a time you disagreed with a teammate or manager.** → Pick a real one. Don't make it about a personality clash. Beat: "I had a different read on X. I made my case in writing with the trade-offs. The decision went their way and I supported the execution. Six months later [outcome] — sometimes I was right, sometimes they were. The point is the *process* — disagree, commit, and own the outcome together."

**H6. ⭐⭐ What's your biggest weakness?** → From the pitch doc: rusty .NET (honest) + actively investing in production-grade AI evals (forward-looking). Don't say "I work too hard" — eye-roll material at a senior interview.

**H7. ⭐⭐ Where do you see yourself in 3 years?** → Senior IC depth-broadening into AI integration at production scale. Not "I want to manage" unless that's true. *"I'm in a place where each year deepens systems architecture and broadens applied AI judgment — three years from now I'd want to be the engineer the team trusts to architect both halves of an AI-meets-distributed-systems project."*

**H8. ⭐ Why are you leaving Kaiser?** → Be careful. Don't badmouth. *"Kaiser has been a great senior backend platform — I've grown deeply on Kafka, AKS, distributed systems patterns at healthcare scale. What's pulling me is the chance to move closer to applied AI in a domain with hard industrial constraints. JCI's Enterprise AI team is exactly that."*

**H9. ⭐⭐ Tell me about a time you learned a new technology quickly.** → Pick a real one. Beat: "I had X to do, didn't know Y. Spent the first week reading the official docs + existing code in the repo, wrote notes, paired with someone who knew it, shipped a small thing first. Two weeks in I was contributing real PRs." The pattern matters more than the specific tech.

**H10. ⭐ How do you stay current?** → Concrete sources: Anthropic / OpenAI release notes, OpenTelemetry blog, specific newsletters (e.g., MIT TR Algorithm, AI Snake Oil — pick real ones you actually read), conference talks (KubeCon, RailsConf, etc., pick relevant ones). Demonstrating *one specific recent thing you learned* (e.g., "I went deep on MCP after it dropped because I wanted to understand the JSON-RPC layer myself") is more powerful than listing sources.

---

## I. The closing — questions YOU ask them

You will be asked "do you have questions for us?" **You must have 3.** Generic questions ("what's the culture?") signal disinterest. Specific questions signal you've thought about the role.

**I1.** "What does the Enterprise AI team's roadmap look like over the next 12 months? Where does this role sit in it?"

**I2.** "How are decisions made about which existing JCI systems get AI integrations first vs which wait? Is there a prioritization framework or is it product-led?"

**I3.** "What's the biggest unsolved technical problem the team is working on right now? I'm curious what the conversations are about."

**I4 (if you have time).** "If I joined and looked back in six months, what would success in this role look like to you specifically?"

Take *one note* from each answer — that's your follow-up email material the next day.

---

## How to drill these

- **Day 1 (today):** read all 40 questions, mark the ones you can't answer cold. That's your hit list.
- **Day 2–3:** for each hit-list question, draft a one-paragraph answer in your own voice. *Don't memorize this doc — make it yours.*
- **Day 4:** record yourself answering 10 random questions out loud. Listen back. Cut anything that drifts.
- **Day before interview:** read Section H (behavioral) + your pitch + your 3 closing questions. That's it. Don't cram the morning of.
