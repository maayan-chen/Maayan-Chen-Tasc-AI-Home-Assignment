<!-- This file must stay under 80 lines. If it grows, prune or move content to docs/. -->
# Customer Handoff RAG Tool — Current State
Last updated: 2026-08-20 (Phase 2 ingestion shipped and merged to `main`;
real Teva data indexed in Postgres; Phase 3 Streamlit UI not yet started)

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
**Done (Phase 2):** `read_local_files.py` (`read_local_files()`) and
`ingest.py` (`run_ingestion()` + CLI wrapper) written, reviewed, and merged to
`main`. Real Teva customer folder ingested via the CLI wrapper: 11 files →
167 chunks, correct `context_tag`, zero untagged rows, `query_data.py`
returns a grounded, sourced answer. These 334 rows (two ingestion runs,
verifying additive writes) are kept in Postgres, not cleaned up — deliberate,
so Phase 3 has real data to test against.
**Goal:** Build `app.py` (Streamlit, Ingest + Ask tabs) — Phase 3.
**Done when:** `streamlit run app.py` lets a user type a folder path +
customer name to ingest, then pick a customer from a dropdown and get a
grounded, sourced chat answer scoped to that customer.

## System Status
| Component | Status | Notes |
|-----------|--------|-------|
| Project scaffolding | ✅ Live | `CLAUDE.md`, `STATE.md`, `docs/`, `.claude/`, `.agents/` in place |
| RAG base (vector_store.py, create_database.py, docker-compose.yml, Dockerfile, init.sql) | ✅ Live | Copied in, verified end-to-end (indexing + scoped retrieval + isolation); `.docx`/`.xlsx`/`.pptx`/OCR parsing extended in |
| `api.py` (optional HTTP boundary) | ❌ Removed | Unauthenticated, let `context_tag` be spoofed/omitted — see `docs/ARCHITECTURE.md` |
| Web-search/agent step | ❌ Cut | Reduced to one fixed non-judgmental tool call — see `docs/ARCHITECTURE.md` |
| `ingest.py` / `read_local_files.py` | ✅ Live | Verified end-to-end against real Teva folder; merged to `main` |
| `app.py` (Streamlit, Ingest + Ask tabs) | ⏸ Deferred | Not started |
| Git repo | ✅ Live | `main`, author `maayan-chen <maayan18058@gmail.com>` |

## Next Up
1. Write `app.py` — Ingest tab (folder path + customer name inputs,
   calls `run_ingestion()`) and Ask tab (customer dropdown, chat UI scoped by
   `context_tag`).

## Known Issues
| Issue | Severity | Notes |
|-------|----------|-------|
| OpenAI account has a low TPM rate limit | Low | See `docs/LESSONS.md` — large folders may need batching |
