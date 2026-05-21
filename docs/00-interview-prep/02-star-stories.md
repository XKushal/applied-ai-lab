# STAR story bank

7 stories, each ~150–200 words spoken. Memorize the **beats** (Situation → Task → Action → Result), not the script — you should be able to redirect into any of these from any question.

Each story header lists the **question types it answers**, so you can deploy the same story for "tell me about a challenge", "tell me about cross-team work", "describe a time you took initiative", etc.

---

## Story 1 — The DXP Kafka decoupling

**Answers:** *"Describe a system you designed." / "Tell me about a time you improved reliability at scale." / "Describe an event-driven system you built." / "How do you handle service coupling?"*

- **S** — Kaiser's KPIT platform had 12+ services tightly coupled via synchronous REST calls. One slow downstream consumer cascaded latency upstream; failures during deploys took down dependent services.
- **T** — I owned the architecture decision: cut the synchronous coupling without breaking the existing contract or migrating all consumers at once.
- **A** — Designed and built the Data eXchange Platform (DXP), a Kafka-backed event-driven layer. Producers emit domain events to topics; consumers subscribe with their own offset management. I authored the topic taxonomy, schema-registry conventions, dead-letter-queue strategy, KEDA autoscaling rules so consumers scale on lag, and the migration playbook so existing services could move one at a time behind a feature flag.
- **R** — Inter-service coupling dropped sharply, deploy velocity improved because services could ship independently, and we got a measurable resiliency win — failures became localized instead of cascading. Set the architectural template subsequent teams reused.

**JCI bridge sentence:** *"That same pattern is exactly how I'd wire up high-volume HVAC sensor telemetry — one ingest topic, multiple independent consumers for alerting, analytics, and AI inference, each scaling on lag."*

---

## Story 2 — The p99 latency hunt

**Answers:** *"Tell me about a difficult debugging session." / "Describe a performance optimization." / "How do you approach a system that's slow?"*

- **S** — A critical API at Kaiser was breaching its p99 SLO during peak load. p50 looked fine, only the tail was bad — the kind of thing that hides in averages.
- **T** — Find the root cause and fix it without taking the service down or migrating the schema.
- **A** — Pulled Dynatrace traces for the slow requests, isolated the span where time was disappearing. It was a query doing a full table scan on a high-cardinality healthcare dataset because the index covered the wrong column order. I designed a composite index respecting the query's predicate ordering, validated the plan in a non-prod replica, rolled it out behind a maintenance window, and added a Splunk alert on the regression metric so we'd catch the next one before users did.
- **R** — p99 dropped ~35%. The alert later caught two similar regressions before they hit users.

**Why this story works:** It's a 360° engineer story — observability + DB + SLOs + post-fix instrumentation. Use it when they ask anything about reliability.

---

## Story 3 — StrengthLens AI workout planner (prompt engineering with structured input)

**Answers:** *"Tell me about an AI project you built." / "How have you used LLMs in production?" / "Tell me about a time you integrated a third-party AI API."*

> **Honest framing:** This was **prompt engineering with structured user input**, *not* RAG and *not* MCP. Don't claim either of those for this project — your real RAG/MCP experience lives in the `applied-ai-lab` repo (this one). Senior interviewers respect honest scoping far more than buzzword-stretching.

- **S** — Building a cross-platform fitness app (React Native, Node/TS backend, Supabase) where the differentiator is a personalized workout plan generated for each user instead of a generic template.
- **T** — Design the AI feature so the generated plan is actually personalized — reasoning over the user's goals, equipment, injury history, and schedule — and reliably structured enough to render in the app UI.
- **A** — Built a structured **onboarding flow** that captures goals, available equipment, training experience, injuries, and weekly schedule. The backend assembles those answers into a templated prompt for the Anthropic API (Claude). I treated the prompt as code: versioned the prompt template, validated the model returns structured JSON matching a schema (workout name, sets/reps/rest, day-of-week assignment, progression notes), handled refusals and malformed outputs with retry/repair logic. Tested across model versions to catch output drift before users felt it.
- **R** — Generated plans were specific to each user's inputs instead of generic templates. Hard lessons that translate to any LLM-in-production work: prompt versioning matters as much as code versioning, structured-output reliability is the difference between "demo" and "shippable", and model-version drift is real — a prompt that worked great on one Claude version can subtly regress on the next.

**JCI bridge sentence:** *"That's the discipline that translates — treating prompts as versioned code, validating structured outputs, owning the model-version upgrade path. Same playbook applies whether the output is a workout plan or a building-ops recommendation."*

**If they ask about RAG/MCP:** *"Not in StrengthLens — that was prompt engineering. I've been building the RAG + MCP pieces in a personal lab — `applied-ai-lab` on my GitHub — because I wanted to understand the primitives without leaning on a framework. Hand-rolled MCP server, RAG pipeline with eval. Happy to walk through it."*

---

## Story 4 — Quality gates that actually shipped fewer bugs

**Answers:** *"Tell me about your CI/CD experience." / "How do you ensure code quality on a team?" / "Tell me about DevOps work."*

- **S** — Releases at Kaiser sometimes shipped regressions caught only in UAT or, worse, prod. Felt like the tests existed but weren't *gating* anything.
- **T** — Tighten the release pipeline so quality issues fail the build, not the release.
- **A** — Reworked the GitHub Actions + Jenkins pipeline. Added SonarQube as a hard gate on code coverage delta and security hotspots, Nexus IQ for dependency vulnerability scanning, and a contract-test stage between consumer/producer services using the schema registry. Wrote the runbook explaining what each gate does and how to override (rare, audited).
- **R** — Near-zero-defect releases over the following quarters on the services we adopted it on. The cultural shift was bigger than the tooling one — devs started writing tests they'd skipped before because they wanted the build to go green on first push.

---

## Story 5 — Containerization + autoscaling at scale

**Answers:** *"Tell me about Kubernetes experience." / "How do you handle scale?" / "Describe a containerized deployment you owned."*

- **S** — Services running on AKS at Kaiser, but resource limits were guesses and HPA wasn't tracking the right signal — services would over-provision off-peak and still get throttled at peak.
- **T** — Right-size and right-scale a fleet of services running real production traffic.
- **A** — Profiled actual CPU/memory under load using Dynatrace, set resource requests to p50 and limits to p99-with-headroom. Replaced CPU-based HPA with **KEDA** triggers tied to Kafka consumer lag for the event-driven services — meaning the consumers scaled on *work to do*, not on CPU after work was already piling up. Authored the Helm charts to make this declarative across environments.
- **R** — Cost dropped at off-peak, and lag-based scaling caught load spikes before users felt them. The pattern became the template for new services.

---

## Story 6 — IMT: shipping in a legacy stack

**Answers:** *"Tell me about working on a legacy codebase." / "Tell me about full-stack work." / "Describe a time you owned a feature end-to-end."*

- **S** — IMT's Spectrum insurance platform was a mature .NET monolith with complex policy/endorsement/billing logic. New features had to thread through years of business rules without breaking the regression suite.
- **T** — Ship endorsement and billing workflow enhancements without destabilizing live insurance operations.
- **A** — Spent the first two weeks reading code and writing notes on the policy-state machine — there was no current diagram. Built the new endorsement flow by extending existing patterns instead of inventing new ones. On the frontend, built React/TypeScript screens against pixel-spec mockups with Redux for the cross-screen workflow state. On the backend, authored the SQL stored procedures for premium recalculation and tuned the query plans to hit sub-second SLAs. Wrote tests at every layer.
- **R** — Features shipped on time, no regressions, and the state-machine notes became the team's onboarding doc.

**Use this story when:** they ask anything full-stack or anything about working in unfamiliar code.

---

## Story 7 — Observability-driven incident response

**Answers:** *"Tell me about an incident you led." / "How do you reduce MTTD/MTTR?" / "How do you collaborate cross-team?"*

- **S** — Backend integrations at Kaiser served clinical workflows where downtime has real patient-facing impact. Incidents were getting detected too late — usually a downstream team would call us before our own dashboards lit up.
- **T** — Make our team detect issues before anyone else did.
- **A** — Worked with platform and product to define SLOs that mapped to *user-visible* behavior (not just CPU). Built Splunk dashboards per SLO and wired Dynatrace distributed traces into them. Walked through 3 prior incidents and added the early-warning signal each one would have shown if we'd been watching the right metric. Collaborated with the security team on the same dashboards for compliance visibility.
- **R** — MTTD dropped ~40% on critical services. The next two P1s were caught by alerts, not phone calls.

---

## How to deploy these in the room

- **Practice each one out loud** — *spoken* timing is what matters, not written length. Aim for 90–120 seconds per story.
- **Lead with the "S" in one sentence**, then linger in the "A" — that's where senior signal lives.
- **Always end with a result that's specific**: a number, a behavior change, an architectural pattern that propagated. Vague results sound junior.
- When asked a question that *could* land on two of these stories, pick the one with the **harder technical depth** — interviewers reward depth over breadth.
