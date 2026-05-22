# Rusty-stack cheatsheets

Just enough to defend yourself in a technical conversation on the stacks you haven't touched in a while. **Not enough to bluff being current** — and you shouldn't try. The pattern is: speak honestly about your timeline, then show you've recently refreshed.

---

## A. ASP.NET Core (2022 → today)

You shipped ASP.NET Core at IMT (2021–22) and Delaget (intern, 2019–20). What's changed since you last touched it.

### Minimal APIs (vs MVC controllers)

The default style for new services in modern .NET. Controllers still exist; minimal APIs are leaner.

```csharp
// Program.cs — a complete API in ~15 lines
var builder = WebApplication.CreateBuilder(args);
builder.Services.AddDbContext<AppDb>(o => o.UseSqlServer(connStr));
builder.Services.AddScoped<IBuildingService, BuildingService>();

var app = builder.Build();

app.MapGet("/buildings/{id:int}", async (int id, IBuildingService svc) =>
    await svc.GetByIdAsync(id) is { } b ? Results.Ok(b) : Results.NotFound());

app.MapPost("/buildings", async (BuildingDto dto, IBuildingService svc) =>
    Results.Created($"/buildings/{await svc.CreateAsync(dto)}", null));

app.Run();
```

**Talking points:**
- Routes registered on `WebApplication`, not on controllers
- DI is unchanged (`AddScoped/Singleton/Transient`)
- `Results.Ok/NotFound/Created` are the new idiomatic return types
- For complex APIs, MVC controllers still win on readability

### Entity Framework Core — changes since EF Core 6

- **Compiled models** for cold-start perf
- **Bulk operations** finally native: `ExecuteUpdate` / `ExecuteDelete` skip change-tracking for set-based updates
- **JSON columns** mapped naturally on SQL Server / Postgres
- **Migrations bundles** for shipping schema changes as standalone executables — useful for CI/CD

```csharp
// instead of: Load → mutate → SaveChanges
await db.Buildings.Where(b => b.Status == "decommissioned")
                  .ExecuteDeleteAsync();
```

### Configuration + secrets

- `IConfiguration` reads from layered providers: `appsettings.json` → env-specific → env vars → User Secrets (dev) → **Azure Key Vault** (prod via managed identity)
- Bind sections to typed classes via `IOptions<T>` — *not* magic strings everywhere

### Logging

- `ILogger<T>` injected, structured logging out-of-box
- Connect to Application Insights via `AddApplicationInsightsTelemetry()`
- For OpenTelemetry: `OpenTelemetry.Extensions.Hosting` + auto-instrumentation for ASP.NET Core, HttpClient, EF Core

### Testing

- `WebApplicationFactory<T>` for integration tests against a real in-process app
- xUnit + FluentAssertions is the common stack
- Testcontainers.NET for spinning real DB containers in test

### What to say if asked

> *"I shipped production ASP.NET Core at IMT and Delaget, but the last three years I've been deep on Java/Spring. I've refreshed on minimal APIs, current EF Core, and the Azure-native auth/secrets story — would lean on team conventions for the first sprint, expect to be at full velocity by week three."*

---

## B. MS SQL Server vs MySQL / PostgreSQL

You've done deep tuning work on MySQL/PostgreSQL at Kaiser. Translating to SQL Server is mostly a dialect shift + a few engine-specific features.

### The differences that actually matter

| Topic | PostgreSQL | MS SQL Server |
|---|---|---|
| **Dialect** | Standard SQL + Postgres extensions (CTEs, `RETURNING`, window functions) | T-SQL — proprietary extensions, `OUTPUT` clause instead of `RETURNING`, `IIF()`, `CHOOSE()` |
| **Identity** | `SERIAL`, `IDENTITY`, sequences | `IDENTITY(1,1)` column property, sequences via `CREATE SEQUENCE` (SQL Server 2012+) |
| **Booleans** | Native `BOOLEAN` | None. Use `BIT` (0/1). Trip people up. |
| **String types** | `TEXT`, `VARCHAR` interchangeable | `VARCHAR` (ASCII) vs `NVARCHAR` (Unicode) — distinct! Match what the app sends. |
| **JSON** | `JSONB` with operators (`->`, `@>`), GIN indexes | `JSON` text + `JSON_VALUE`, `OPENJSON`, computed-column indexes |
| **Stored procedures** | PL/pgSQL — fine but most teams avoid | T-SQL stored procs are **first-class** in many MS SQL shops — common to push logic in |
| **Plan inspection** | `EXPLAIN ANALYZE` | `SET STATISTICS PROFILE/IO ON`, or Query Store UI in SSMS / Azure Data Studio |
| **Plan history** | `pg_stat_statements` | **Query Store** — keeps history of plans + regressions automatically. Underused superpower. |

### Indexing patterns that translate

- Composite index column order = match the predicate column order in your `WHERE`. Same on every engine.
- **Included columns** (`INCLUDE (col1, col2)` in MS SQL, `INCLUDE` in PG 11+) — same idea, covering index without bloating the key.
- Filtered indexes (`WHERE status = 'active'`) — same in both, sometimes critical when 99% of rows are one value.

### Engine-specific levers worth knowing

**MS SQL only:**
- **Columnstore indexes** — fact tables / analytics workloads, batch-mode operators, compression. Mention this if asked about reporting workloads.
- **Query Store** — pin plans, force regressions back to known-good plan
- **MERGE statement** — upsert. Has known concurrency bugs at low isolation levels; many shops avoid in favor of explicit `IF EXISTS UPDATE ELSE INSERT`.

### What to say if asked

> *"I've tuned MySQL/Postgres heavily at Kaiser — composite indexes respecting predicate order, query plan inspection, cardinality estimation. The story translates directly to MS SQL; the engine has its own dialect — T-SQL, BIT for booleans, NVARCHAR — but the principles are identical. Specific to MS SQL I'd reach for Query Store for plan-history visibility and columnstore for analytics-shaped workloads. Used SQL Server at IMT and Delaget."*

---

## C. C++ — the honest answer

You don't have production C++ experience. Don't pretend you do.

### What to say if asked

> *"It's the one on your list I have least production time with. I've used it in coursework, and I'm comfortable across statically-typed systems languages so the syntax isn't the barrier — it'd be idiomatic memory management, modern C++ features like smart pointers and RAII, and the team's specific build / test conventions. If C++ is core to the day-to-day, I'd be upfront that it's a ramp-up; if it's adjacent (e.g., occasionally reading firmware), I can navigate the code, just wouldn't be the right primary owner for a greenfield C++ component without a few months of focused work."*

### If they push: the minimum to keep the conversation going

- **RAII**: resources tied to object lifetime — destructor releases them. The thing that makes C++ memory management tractable.
- **Smart pointers**: `std::unique_ptr` (single owner, default), `std::shared_ptr` (reference counted, use sparingly). **Don't say "I just use `new` and `delete`"** — that's pre-2011 C++.
- **Move semantics**: `std::move`, rvalue references. Don't volunteer to explain unless asked.
- **Modern build**: CMake is the de facto standard; vcpkg/conan for dependencies.

This is enough to not look ignorant; not enough to fool a real C++ engineer. **The interview tactic is to be honest first.**

### Senior framing

Most JCI Enterprise AI roles will *list* C++ because some sibling teams touch device firmware or embedded code. They rarely *test* on it for an AI integration role. The bigger risk is bluffing and getting caught; the smaller risk is admitting a gap and getting "we don't really use it for this role" in response.

---

## D. Microsoft Project / Office — the throwaway

JD says: *"Strong working knowledge of Microsoft Office – specifically Microsoft Project (Online and/or Server) and Professional."*

Almost certainly boilerplate copied from a PM template. You will probably not be tested. But if asked:

### What to say

> *"I've used MS Office across my career — Word, Excel, PowerPoint, Outlook, the usual. MS Project specifically I haven't owned a plan in, though I've contributed to Gantt-style schedules in other tools (Jira plans, Notion, etc.). It's a tool I'd pick up quickly if part of the role. What I can speak to is dependency tracking, critical-path thinking, and translating engineering work into delivery commitments — those are the skills, the tool's just where you express them."*

You're reframing the question from "do you know the tool" to "do you have the underlying skill." That's the senior move.

---

## How to use these cheatsheets

- **Don't memorize.** Read each section once, internalize the *honesty pattern* + 3-4 specific technical hooks per stack.
- **The night before the interview:** re-read just the "what to say if asked" boxes. That's the speakable framing.
- **In the room:** lead with the honest timeline ("shipped X in [year], last 3 years on Y") — *then* drop one or two specific technical hooks to show you've refreshed.
- **What you're proving:** not encyclopedic knowledge — but that you (a) self-assess accurately, (b) have a learning system, and (c) know enough to be productive without bluffing. That's the senior signal for any rusty stack.
