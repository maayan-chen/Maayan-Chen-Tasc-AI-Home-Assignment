<!-- This file must stay under 80 lines. If it grows, prune or move content to docs/. -->
# Customer Handoff RAG Tool — Current State
Last updated: 2026-08-20 (RAG base verified end-to-end; web-search/agent step
cut from scope before implementation; ingestion code not yet written)

## Project Summary
A Streamlit app (Ingest tab + Ask tab) that helps a new TASC team get up to
speed on an existing customer at project handoff. Ingestion is deterministic:
reads a project folder, indexes everything into a shared pgvector store
tagged with a customer's `context_tag`; the Ask tab is a chat UI scoped to
one customer. Built from `References/Nivs-RAG/` (RAG base). No LLM/agent step
in ingestion — a web-search agent was planned, then cut before
implementation (see `docs/ARCHITECTURE.md`: it reduced to one fixed,
non-judgmental tool call, not worth the complexity). 2-day budget, must stay
simple enough to fully explain in an interview.

## Current Task
**Done:** Fresh `git init`, `rag-base-setup` branch. Reused RAG base files
copied in from `References/Nivs-RAG/` (`api.py` since removed — see
`docs/ARCHITECTURE.md`). `docker compose up --build` runs cleanly. Verified
end-to-end in-process: `DirectoryLoader` → `split_text()` →
`set_context_tag()` → `save_to_pgvector()` → `context_tag`-filtered
`similarity_search_with_relevance_scores()` → grounded LLM answer. Isolation
confirmed: a mismatched `context_tag` returns zero results. Sanity-check rows
cleaned from Postgres afterward. `extract_content_from_bytes()` extended for
`.docx`/`.xlsx`/`.pptx`, PDF OCR fallback, always-on image OCR (Phase 1.5).
Real customer folder now available:
`/Users/maayanchen/Code/Work/Teva_Org_Streamlining_Project` (mixed
Hebrew/English `.docx`/`.xlsx`/`.pptx`/`.pdf`/`.png` files).
**Goal:** Write `ingest_tools.py` (`read_local_files()`) and `ingest.py`
(`run_ingestion()` orchestration + CLI wrapper) — Phase 2, no agent involved.
**Done when:** The real Teva customer folder ingests via the CLI wrapper and
lands in Postgres with the correct `context_tag`; a `context_tag`-filtered
query returns a sane, sourced answer.

## System Status
| Component | Status | Notes |
|-----------|--------|-------|
| Project scaffolding | ✅ Live | `CLAUDE.md`, `STATE.md`, `docs/`, `.claude/`, `.agents/` in place |
| RAG base (vector_store.py, create_database.py, docker-compose.yml, Dockerfile, init.sql) | ✅ Live | Copied in, verified end-to-end (indexing + scoped retrieval + isolation); `.docx`/`.xlsx`/`.pptx`/OCR parsing extended in |
| `api.py` (optional HTTP boundary) | ❌ Removed | Unauthenticated, let `context_tag` be spoofed/omitted — see `docs/ARCHITECTURE.md` |
| Web-search/agent step | ❌ Cut | Reduced to one fixed non-judgmental tool call — see `docs/ARCHITECTURE.md` |
| `ingest.py` / `ingest_tools.py` | ⏸ Deferred | Not started |
| `app.py` (Streamlit, Ingest + Ask tabs) | ⏸ Deferred | Not started |
| Git repo | ✅ Live | `rag-base-setup` branch, author `maayan-chen <maayan18058@gmail.com>` |

## Next Up
1. Write `ingest_tools.py` → `read_local_files()`, test standalone against
   the Teva folder.
2. Write `ingest.py` → `run_ingestion()` (file reading → chunk → tag → save,
   no agent), test via CLI wrapper.

## Known Issues
| Issue | Severity | Notes |
|-------|----------|-------|
| OpenAI account has a low TPM rate limit | Low | See `docs/LESSONS.md` — large folders may need batching |
