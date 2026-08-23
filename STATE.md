<!-- This file must stay under 80 lines. If it grows, prune or move content to docs/. -->
# Customer Handoff RAG Tool — Current State
Last updated: 2026-08-23 (xlsx tabular-retrieval fix shipped on
`improve-rag-tabular-retrieval` branch; real Teva xlsx data re-ingested with
header-labeled chunks)

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
**Done (Phase 3):** `app.py` built on `streamlit-ui` branch — sidebar Ingest
form (folder path + customer name, calls `run_ingestion()`) and main-page Ask
chat (`context_tag`-scoped, sourced answers). Switched from `st.tabs` to
sidebar+main-page layout so `st.chat_input` docks to the viewport bottom (see
`docs/ARCHITECTURE.md`). Since initial ship: fixed a delete-before-insert
data-loss bug in `ingest.py`'s dedup path (old chunks now deleted only after
new ones save successfully) and added unhandled chat error handling in
`app.py`.
**Done (tabular retrieval fix):** `_extract_xlsx()` now labels every cell
with its column header (heuristic-detected header row, not assumed to be
row 1 — see `docs/ARCHITECTURE.md`); `.xlsx` documents are chunked one row
per chunk in `ingest.py` instead of the shared character splitter; the
`query_rag.py` prompt uses `<documents>` XML tags with per-chunk source
attribution. Real `teva` context_tag's stale xlsx chunks deleted and
re-ingested (dedup-by-hash skips unchanged files — see `docs/LESSONS.md`);
verified against a real salary question, correct sourced answer.
**Goal:** Further RAG quality improvements, if any — scope not yet decided.

## System Status
| Component | Status | Notes |
|-----------|--------|-------|
| Project scaffolding | ✅ Live | `CLAUDE.md`, `STATE.md`, `docs/`, `.claude/`, `.agents/` in place |
| RAG base (vector_store.py, create_database.py, docker-compose.yml, Dockerfile, init.sql) | ✅ Live | Copied in, verified end-to-end (indexing + scoped retrieval + isolation); `.docx`/`.xlsx`/`.pptx`/OCR parsing extended in |
| `api.py` (optional HTTP boundary) | ❌ Removed | Unauthenticated, let `context_tag` be spoofed/omitted — see `docs/ARCHITECTURE.md` |
| Web-search/agent step | ❌ Cut | Reduced to one fixed non-judgmental tool call — see `docs/ARCHITECTURE.md` |
| `ingest.py` / `read_local_files.py` | ✅ Live | Verified end-to-end against real Teva folder; merged to `main` |
| `app.py` (Streamlit, sidebar Ingest + main-page Ask) | ✅ Live | Shipped on `streamlit-ui` branch; delete-before-insert bug and chat error handling fixed since |
| xlsx tabular retrieval (header-labeled extraction, row-based chunking, XML-tagged prompt) | ✅ Live | On `improve-rag-tabular-retrieval` branch; real `teva` xlsx data re-ingested — see `docs/ARCHITECTURE.md` |
| Git repo | ✅ Live | `main`, author `maayan-chen <maayan18058@gmail.com>` |

## Next Up
1. None pending — decide next focus area.

## Known Issues
| Issue | Severity | Notes |
|-------|----------|-------|
| OpenAI account has a low TPM rate limit | Low | See `docs/LESSONS.md` — large folders may need batching |
