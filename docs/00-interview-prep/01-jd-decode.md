# JD decode — Johnson Controls, Software Developer (Enterprise AI)

Every "what we look for" bullet from the JD → mapped to existing evidence on Kushal's resume → flagged as **Strong / Adequate / Gap**, with a one-line sharpening plan for the gaps.

| JD requirement | Evidence on resume | Strength | Sharpening plan |
|---|---|---|---|
| Experience developing with .NET | IMT (2021–22) and Delaget intern: ASP.NET Core REST APIs, .NET/C# performance fixes | **Adequate** — but ~3 years stale | Skim ASP.NET Core 8/9 minimal APIs + EF Core changes. 30 min read. Be ready to say "I shipped .NET at IMT and Delaget; happy to ramp on current LTS." |
| React | IMT: React/TS + Redux. StrengthLens: React Native | **Strong** | Mention React 19 / server components casually if it comes up |
| Java | Kaiser: Quarkus + Spring Boot microservices at scale | **Strong** | This is your home turf |
| Python | StrengthLens AI work, listed in skills | **Adequate** | The hands-on phases of this repo will push this to **Strong** |
| C++ | Not on resume | **Gap** | JCI lists this but rarely tests it for Enterprise AI roles. If asked: "It's the language I have least production time in; I've used it in coursework. I'd lean on team conventions to ramp." Don't oversell. |
| Microsoft SQL | Delaget intern (stored procs, query plans) | **Adequate** | You've also done MySQL/PostgreSQL p99 tuning at Kaiser — pivot to that depth. Index strategy stories work across all RDBMS. |
| Integrating AI models, APIs, and agentic frameworks | StrengthLens: Anthropic API + structured prompt engineering (NOT RAG/MCP — those live in this repo) | **Adequate, becoming Strong** | This repo's Phase 3 + capstone give you legitimate RAG + MCP experience to point at |
| Containerization (Docker, Kubernetes) + microservices | Kaiser: AKS, Helm charts, KEDA autoscaling, 12+ microservices on Kafka | **Strong — possibly the strongest signal you have** | Lead with this in system-design rounds |
| DevOps framework understanding | Kaiser: GitHub Actions + Jenkins CI/CD, SonarQube, Nexus IQ | **Strong** | Have a quality-gate story ready |
| ML / Agentic AI / LLM understanding | StrengthLens prompt engineering, lists LangChain basics | **Adequate** | Phase 2 + 3 of this repo turn this into **Strong** |
| Azure DevOps / Git / Visual Studio | Kaiser is on Azure (AKS); used GitHub Actions; Visual Studio at IMT/Delaget | **Strong** | Mention Azure casually — they're an Azure shop |
| Proven dev experience | 6+ years senior | **Strong** | Lead with seniority confidently |
| Client-facing + comms | Cross-team work at Kaiser (platform/security/product); ServiceNow incident triage | **Adequate** | Have one cross-functional collaboration story ready |
| MS Office, MS Project | Not on resume | **Soft Gap** | Trivial. If asked: "I've used MS Office across my career; new to MS Project specifically — would learn quickly." Don't dwell. |
| Bachelor's CS | M.Sc. + B.Sc. CS, St. Cloud State | **Exceeds** | Mention the M.Sc. when relevant |

## Headline read

You **exceed the bar** on the technical core (distributed systems, microservices, cloud, CI/CD, observability) and you **meet the bar** on the AI integration piece (RAG + MCP shipped). Real gaps are minor and admittable: rusty .NET, no C++ depth, no MS Project. None of those should sink a senior interview if you handle them honestly.

The interview risk is **not** "can you do the job" — it's:

1. **Resume-accuracy risk.** The resume currently lists "RAG" and "MCP" against StrengthLens, but the actual project was prompt engineering only. **Action:** rewrite those bullets before submitting / before the interview, and let RAG + MCP claims rest on the `applied-ai-lab` repo (where they're real). Never claim production RAG/MCP for StrengthLens — under probing you can't defend chunk size, embedding model, MCP message flow.
2. **AI depth probing.** "Talk me through your RAG eval / your MCP transport / your agent retry logic." Phase 2 + 3 of this repo make these answers airtight.
3. **Domain translation.** Healthcare ≠ smart buildings. Bridge sentences in [03-pitch-and-bridges.md](03-pitch-and-bridges.md).
4. **Why JCI?** Senior interviewers always ask. Have a 2-sentence answer that's about *the work*, not the benefits. (Draft in pitch doc.)
