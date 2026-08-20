<!-- This file must stay under 80 lines. If it grows, prune or move content to docs/. -->
# Customer Handoff RAG Tool — Current State
Last updated: 2026-08-20 (RAG base copied in, verified end-to-end; no ingestion/UI code yet)

## Project Summary
A Streamlit app (Ingest tab + Ask tab) that helps a new TASC team get up to
speed on an existing customer at project handoff. Ingestion agent reads a
project folder + runs a web search, indexes everything into a shared pgvector
store tagged with a customer's `context_tag`; the Ask tab is a chat UI scoped
to one customer. Built from `References/Nivs-RAG/` (RAG base) and
`References/AI-Agent/` (tool-calling agent pattern). 2-day budget, must stay
simple enough to fully explain in an interview.

## Current Task
**Done:** Fresh `git init`, `rag-base-setup` branch. Reused RAG base files
copied in from `References/Nivs-RAG/` (`api.py` since removed — see
`docs/ARCHITECTURE.md`). `docker compose up --build` runs cleanly. Verified
end-to-end in-process: `DirectoryLoader` → `split_text()` →
`set_context_tag()` → `save_to_pgvector()` → `context_tag`-filtered
`similarity_search_with_relevance_scores()` → grounded LLM answer. Isolation
confirmed: a mismatched `context_tag` returns zero results. Sanity-check rows
cleaned from Postgres afterward.
**Goal:** Extend `extract_content_from_bytes()` for `.docx`/`.xlsx`, PDF OCR
fallback, and always-on image OCR (Phase 1.5), then write `ingest_tools.py`
and `ingest_agent.py` (Phase 2).
**Done when:** A real customer folder ingests via the CLI wrapper and lands
in Postgres with the correct `context_tag`; a `context_tag`-filtered query
returns a sane, sourced answer.

## System Status
| Component | Status | Notes |
|-----------|--------|-------|
| Project scaffolding | ✅ Live | `CLAUDE.md`, `STATE.md`, `docs/`, `.claude/`, `.agents/` in place |
| RAG base (vector_store.py, create_database.py, docker-compose.yml, Dockerfile, init.sql) | ✅ Live | Copied in, verified end-to-end (indexing + scoped retrieval + isolation); `.docx`/`.xlsx`/`.pptx`/OCR parsing extended in |
| `api.py` (optional HTTP boundary) | ❌ Removed | Unauthenticated, let `context_tag` be spoofed/omitted — see `docs/ARCHITECTURE.md` |
| `ingest_agent.py` / `ingest_tools.py` | ⏸ Deferred | Not started |
| `app.py` (Streamlit, Ingest + Ask tabs) | ⏸ Deferred | Not started |
| Git repo | ✅ Live | `rag-base-setup` branch, author `maayan-chen <maayan18058@gmail.com>` |

## Next Up
1. Extend `extract_content_from_bytes()`: `.docx`/`.xlsx` parsing, PDF OCR
   fallback (Hebrew), always-on image OCR (`.png`/`.jpg`/`.jpeg`).
2. Get the real (or user-supplied mock) customer folder path to test
   ingestion against.
3. Write `ingest_tools.py` → `read_local_files()`, test standalone.
4. Write `ingest_agent.py` → `run_ingestion()`, test via CLI wrapper.

## Known Issues
| Issue | Severity | Notes |
|-------|----------|-------|
| No real customer folder confirmed yet | Med | Needed before ingestion logic can be tested end-to-end |
| OpenAI account has a low TPM rate limit | Low | See `docs/LESSONS.md` — large folders may need batching |
