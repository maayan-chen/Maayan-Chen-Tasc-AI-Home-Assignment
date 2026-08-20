<!-- This file must stay under 80 lines. If it grows, prune or move content to docs/. -->
# Customer Handoff RAG Tool — Current State
Last updated: 2026-08-20 (project scaffolded, no code written yet)

## Project Summary
A Streamlit app (Ingest tab + Ask tab) that helps a new TASC team get up to
speed on an existing customer at project handoff. Ingestion agent reads a
project folder + runs a web search, indexes everything into a shared pgvector
store tagged with a customer's `context_tag`; the Ask tab is a chat UI scoped
to one customer. Built from `References/Nivs-RAG/` (RAG base) and
`References/AI-Agent/` (tool-calling agent pattern). 2-day budget, must stay
simple enough to fully explain in an interview.

## Current Task
**Done:** Project scaffolding only — folder structure, CLAUDE.md, STATE.md,
docs/, `.claude/commands`, `.agents/` copied and filled in from
`References/project-template/`.
**Goal:** Not started — no source files copied or written yet.
**Done when:** N/A (scaffolding phase). Next real milestone is Day 1 Step 1 in
`../Basic-plan`: copy Nivs-RAG base files in, `docker compose up`, confirm
`/index` + `/query` still work against Nivs-RAG's own sample data.

## System Status
| Component | Status | Notes |
|-----------|--------|-------|
| Project scaffolding | ✅ Live | `CLAUDE.md`, `STATE.md`, `docs/`, `.claude/`, `.agents/` in place |
| RAG base (vector_store.py, create_database.py, models.py, docker-compose.yml, Dockerfile, init.sql) | ⏸ Deferred | Not yet copied from `../References/Nivs-RAG/` |
| `ingest_agent.py` / `ingest_tools.py` | ⏸ Deferred | Not started — see `../Basic-plan` Architecture section |
| `app.py` (Streamlit, Ingest + Ask tabs) | ⏸ Deferred | Not started |
| Git repo | ⏸ Deferred | Fresh `git init` not yet run |

## Next Up
1. Fresh `git init`; create a feature branch (never commit to `main` directly).
2. Copy reused files from `../References/Nivs-RAG/` per `../Basic-plan` Project Setup section.
3. `docker compose up`, sanity-check `/index` + `/query` against Nivs-RAG's own sample data before changing anything.
4. Get the real (or user-supplied mock) customer folder path to test ingestion against.
5. Write `ingest_tools.py` → `read_local_files()`, test standalone.

## Known Issues
| Issue | Severity | Notes |
|-------|----------|-------|
| No real customer folder confirmed yet | Med | Needed before Day 1 Step 2–3 can start; blocks ingestion testing |
