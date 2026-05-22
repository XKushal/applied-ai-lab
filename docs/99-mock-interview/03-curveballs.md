# Curveballs — the questions that wreck candidates

Not the standard list. These are the questions that separate "competent" from "the person we want." Mostly **non-AI** because the JCI role is mostly non-AI. The answers below are spoken patterns — beats, not scripts.

---

## C1. "When would you NOT use an LLM?"

This is the senior-AI litmus test. Most candidates can't answer it cleanly.

**The answer:**
> *"A few categories. Anything deterministic — arithmetic, regex parsing, schema-defined lookups — should be code or a SQL query, not a generation step. Anything where wrong-and-confident is unrecoverable: regulatory, safety-critical, monetary precision. Hot paths under ~50ms because the LLM's TTFT alone is hundreds of ms. And high-throughput identical inputs — I'd cache the response, not regenerate. The skill is putting the LLM where its strength (open-ended reasoning over context) outvalues its weakness (non-determinism, latency, cost) — not everywhere."*

Why it lands: you're showing you don't reach for an LLM by default. That's the rare instinct senior interviewers reward.

---

## C2. "Your microservice is leaking memory at 3am — walk me through your response."

The interviewer wants to see your **incident-response shape**, not a memorized runbook.

**The answer:**
> *"Acknowledge the page in under 5 minutes — that's table stakes. Then: stop the bleeding first, diagnose second. If pods are OOMKilling and the cluster is healthy, I'd scale up replicas temporarily to buy time. If memory pressure is on the node, evict the worst offender. Throughout I'm communicating in the incident channel — what I see, what I'm doing, when to expect the next update. Once stable, I pull the heap dump from a representative pod, look at trends in Dynatrace for when growth started, and correlate with deploys, traffic patterns, or external dependencies. Then fix forward or roll back. After resolution: blameless postmortem with concrete action items — a missing alert, a leaky cache, a libray upgrade. The bug doesn't get to page me again."*

What to NOT say: "I'd just restart the pods." That's first-aid; interviewer wants the second half.

---

## C3. "The spec is ambiguous. What do you do?"

Common at senior interviews because they're really asking *"are you going to bug the PM five times or move forward thoughtfully?"*

**The answer:**
> *"Two-step. First, I clarify in writing — Slack the PM with my best read on what they meant and the gaps I see. That gets a fast response and creates a paper trail. While I'm waiting, I pick the most reversible interpretation and start building behind a feature flag, focused on the parts that are unambiguous. When the answer comes back, the divergence — if any — is a small refactor instead of a rewrite. The worst pattern is freezing until the spec is perfect; the second worst is building the wrong thing because you guessed silently."*

---

## C4. "You disagree with a senior engineer or architect on a design decision. What now?"

Cultural fit probe disguised as a behavioral question.

**The answer:**
> *"I make my case clearly. Usually in writing — a short doc with the alternatives, my recommendation, and the trade-offs as I see them. Direct, not passive-aggressive. Then I make sure the right people have read it. If, after discussion, the decision goes the other way, I commit and execute. I don't undermine, don't slow-walk, don't say 'I told you so' six months later. If I genuinely think the call is dangerous — security, reliability — I escalate one level and document. Disagree-and-commit isn't agreeing; it's professional disagreement that doesn't paralyze the team."*

This is the Bezos / Amazon framing and it scans cleanly at any senior shop.

---

## C5. "How do you ramp on a stack you haven't used in 3 years?" (the .NET situation)

They probably know your .NET is stale. They want to see *honesty + a learning system*, not bluffing.

**The answer:**
> *"Honestly. I shipped .NET at IMT and Delaget but the last three years have been deep on Java/Spring Boot. For ASP.NET Core LTS specifically, I'd spend the first week reading the official docs and looking at the team's existing services — every codebase has conventions you can't get from a tutorial. I'd pair on a small ticket first — a bug fix or a clear-scope feature — and I'd be upfront in PR descriptions that I'm coming back to the stack so reviewers know to flag idioms I'd otherwise miss. After two or three weeks I'd be shipping at normal velocity. The principles transfer; it's the conventions that take a beat."*

What to NOT say: "Oh I know .NET no problem." If they test you on async/await patterns or EF Core changes since 2022, the bluff collapses immediately.

---

## C6. "Walk me through a production bug that took longer than it should have to fix."

Looking for *self-awareness* about debugging blind spots.

**The answer:**
> *Pick a real one.* Pattern: "I had X symptom. I assumed Y because it's the usual cause. Spent N hours down that path before realizing Y wasn't it — actually the cause was Z, which I'd dismissed early. Lesson: when the obvious cause doesn't pan out in [time], stop and re-enumerate from scratch instead of digging harder. I added [a specific check] to our runbook so the next person who sees this symptom checks Z first."

Senior signal: naming the specific debugging anti-pattern you fell into (confirmation bias, premature optimization of the wrong path, etc.) and the concrete artifact you produced to prevent recurrence.

---

## C7. "Your AI agent recommends an action that turns out to be wrong. Who's responsible?"

The ethics / governance question for an AI-adjacent role. The interviewer wants to know you've thought about this.

**The answer:**
> *"The team that shipped the agent is responsible — full stop. The LLM provider isn't, the user isn't if they followed the workflow. Which means our shipping standards have to match that responsibility: grounded prompting + citation requirements so wrong answers are debuggable, output validation + refusal-when-unsupported so the failure mode is 'I don't know' not 'confidently wrong', audit logging so we can reconstruct any session post-hoc, and human-in-the-loop for any side-effecting action. The system has to fail in ways our customers can detect and our team can fix. That's not a feature, that's the table-stakes design."*

---

## C8. "What's the worst code you've ever written and why?"

Trick question. They're looking for someone who can be honest about their own work.

**The answer pattern:**
> *"Early at [IMT/Delaget], I wrote [specific thing — e.g., a tangled controller that did data access, validation, and external API calls in one method, ~400 lines]. It worked, shipped on time. Six months later when someone needed to change one piece, the cost of a 10-line change was a 2-day refactor. I should have known better — separation of concerns isn't new. Real lesson wasn't 'follow patterns more', it was 'optimize for the next reader, including future me.' I write differently now: shorter functions, named intermediate variables, fewer side effects per layer."*

What to NOT say: "I don't really write bad code." That's a junior answer.

---

## C9. "We work on legacy systems too. How do you feel about that?"

JCI is 130 years old. They want someone who's not allergic to old code.

**The answer:**
> *"I worked on IMT's Spectrum platform — mature .NET monolith with years of business rules baked in. I actually liked it once I got my head around it. Two principles: first, read before you write. Old code is the way it is for reasons that aren't always documented; spend a week understanding before you refactor. Second, prefer additive change to rewrites. The riskiest commit is 'I rewrote module X' the day before a release. Most modernization is a long series of small, reversible changes — strangling, not bulldozing."*

---

## C10. "How do you handle a situation where you don't agree with the customer?"

Client-facing question. JCI explicitly calls out "client-facing skills."

**The answer:**
> *"Listen first. Almost always when I think a customer is wrong about a technical thing, they're actually right about an underlying need I haven't fully heard. So I restate what I think they're asking for and confirm. If I still disagree after that, I lay out the trade-offs in plain language — not jargon — and say what I'd recommend and why. The decision is theirs; my job is to make sure they're making it with full information. If they go a different way, I deliver what they asked for, professionally."*

---

## C11. "What if our existing team uses [tech you don't like]?"

Cultural probe — are you the engineer who fights the team's existing choices on day 1?

**The answer:**
> *"Conform to the team's conventions for at least the first quarter. I might have personal preferences but I'm not the one who has to maintain the system for the next five years; the team is. The time to make a case for a change is after I've earned context — understand why the existing choice was made, what's been tried, what the migration cost would be. Then if I still think a change is worth it, I can make a real proposal with data. Showing up swinging at the existing stack is junior energy."*

---

## C12. "Sell me on this codebase to your friend who's a great engineer at Google."

Recruiting test. They want to see if you'd refer talent.

**The answer pattern:**
> *Adapt to what you know about JCI from prep:* "Three things: (1) the work is in a real industrial domain with hard physical constraints — far more interesting problems than another consumer SaaS. (2) [Name something specific from research — recent product launch, public engineering blog, talk]. (3) The team's mandate explicitly mixes distributed systems and applied AI in production, which is the intersection that's hardest to find right now. The thing you wouldn't get at Google: more ownership per engineer, more visible impact per quarter."

What to NOT say: anything generic ("great culture", "smart people"). The interviewer hears that ten times a day.

---

## C13. The "stretch" question — they ask something genuinely beyond you

It will happen. The interviewer asks about a technology, a paper, a concept you don't know.

**The answer:**
> *"I don't know that one off the top of my head. Can you give me the one-line on what it is? I'd rather understand it now than fake it."*

Then engage as a peer once they explain. The candidate who admits a gap and then reasons through unfamiliar territory beats the candidate who bluffs and gets caught. Every. Single. Time.

---

## C14. "What do you do on weekends?"

Sneaky behavioral filter — are you a person.

**The answer:** be a person. Brief, specific, real. Don't say "I code on weekends" unless it's true; don't lie about hobbies you don't have. If you genuinely build side projects on weekends, mention it briefly *as part of being a person*, not as a flex.

---

## The meta-strategy

For every curveball above, the senior-level answer has two parts:
1. **A concrete pattern or principle** — not a platitude.
2. **A specific example or counter-example** — proves you've lived it.

If you find yourself answering only with platitudes (*"communication is important", "I focus on quality"*), you're sounding mid-level. Pull yourself back into specifics every time.
