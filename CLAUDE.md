# Customer Handoff RAG Tool — Agent Instructions

## Your Role
You are pairing with a solo developer on a 2-day take-home assignment for the
TASC AI Team. Work fast, keep things simple, and prefer the boring, explainable
option over the clever one — every part of this must be defensible in a job
interview.

## User Context
- Solo dev, building this alone under a hard 2-day time budget.
- No end user beyond the assignment reviewers and a demo — non-technical TASC
  consultants are the persona the *product* is designed for, not this repo's
  actual audience.
- Explain decisions simply; the user needs to be able to explain every part of
  this system unprompted, so avoid "magic" (hidden LLM judgment calls, layers
  that can't be narrated in one sentence).

## Problem Solving
- NEVER patch-fix. Always find the root cause.
- Consider the broader system before implementing.
- Challenge your first assumption. Think deeper before acting.
- When multiple solutions exist, present options with tradeoffs.
- **Simplicity and explainability is the central design constraint** — every
  architectural choice serves "the user can explain every line in an
  interview," not "the most impressive-looking system." When in doubt, cut
  scope rather than add a layer that needs its own justification.

## Code Standards
- Reuse `References/Nivs-RAG/` files as-is wherever possible (`vector_store.py`,
  `create_database.py`, `docker-compose.yml`, `Dockerfile`, `init.sql`) —
  don't refactor working reference code without a reason. `api.py` and
  `models.py` were dropped (see `docs/ARCHITECTURE.md`); there is no HTTP
  service boundary in this project.
- `context_tag` is the *only* mechanism that scopes data to a customer. Never
  add a second scoping mechanism (separate tables/collections) — logical
  isolation via one metadata field is the deliberate design.
- Customer identity is always explicit user input, typed in the UI — never
  inferred from folder or project names. Guessing risks silently mixing up
  customer data, which is the one thing this tool depends on for trust.
- No LLM-based relevance filtering at ingestion time — ingest everything;
  relevance is computed once, at query time, via vector similarity.
- Prefer direct in-process Python function calls over HTTP hops within this
  same codebase (ingestion → RAG store, chat → RAG store). There is no HTTP
  service boundary in this project — `api.py` was removed as an unauthenticated
  endpoint that let `context_tag` be omitted or spoofed, breaking the one
  scoping mechanism this tool depends on for trust.
- No LLM/agent involved in ingestion at all — it's deterministic file reading
  + chunking + save, plain Python top to bottom. The web-search/tool-calling
  agent step was cut (see `docs/ARCHITECTURE.md`); don't reintroduce it
  without a concrete reason a fixed script can't do the job.

## Execution Discipline
- **Pause before chaining multi-step or destructive build steps** — confirm
  first, especially after any scaffolding/CLI tool action.
- Never use `--overwrite`/`--force` scaffolding flags on a non-empty directory
  without checking what they do first.
- **Always work on a feature branch, never commit directly to `main`.** Create
  one (e.g. `ingest-agent`, `streamlit-ui`) at the start of any session
  involving code or doc changes, before the first edit. Pushing/opening a PR
  still requires an explicit request.
- Customer project folders read during ingestion are NEVER copied into this
  repo — only a typed path and customer name are stored.
- This repo gets a fresh `git init` — do not carry over `References/` git
  history.

## Context Management
- Never update context files unless asked.
- Never write in context what you can find by reading the codebase.
- When asked "should we update context?" → read `docs/CONTEXT-PROTOCOL.md` and
  follow it.

## Pointer Index
| Domain | Path | Notes |
|--------|------|-------|
| Full implementation plan | `../Basic-plan` | Source of truth for architecture, sequencing, file-by-file plan (lives one level up, outside this repo) |
| Current state | `STATE.md` | Where the project is right now |
| Context update rules | `docs/CONTEXT-PROTOCOL.md` | How/when to update context files |
| Architecture decisions | `docs/ARCHITECTURE.md` | Why, not what |
| System-critical lessons | `docs/LESSONS.md` | Gotchas, not a changelog |
| Active plans | `.agents/plans/*.md` | Phased implementation plans |
| RAG base to build from | `../References/Nivs-RAG/` | FastAPI + LangChain + Postgres/pgvector, reused files copied in, not edited in place |

## Off-Limits
- `../References/` — read-only reference material. Never edit files there;
  copy what's needed into this repo instead.
- Do not fabricate a demo customer folder — the user supplies a real mock
  customer folder to ingest against.
