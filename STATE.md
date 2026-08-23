<!-- This file must stay under 80 lines. If it grows, prune or move content to docs/. -->
# Customer Handoff RAG Tool — Current State
Last updated: 2026-08-23 (chat-history-aware retrieval merged to `main` and
verified against the running app — Ronit role/salary follow-up now resolves
correctly)

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
Real customer folder used for testing:
`/Users/maayanchen/Code/Work/Teva_Org_Streamlining_Project` (mixed
Hebrew/English `.docx`/`.xlsx`/`.pptx`/`.pdf`/`.png` files). Earlier phases
(RAG base setup, ingestion CLI, Streamlit UI, xlsx tabular-retrieval fix) are
shipped and merged — see `git log` and `docs/ARCHITECTURE.md` for what/why.
**Done (chat history):** `answer_question()` (`query_rag.py`) now accepts a
`history` list (last 2 exchanges) and folds it into both the retrieval query
and the prompt, by plain concatenation — no LLM query-rewrite (see
`docs/ARCHITECTURE.md`). Fixes a real bug: a follow-up like "what's her
salary?" after "What is Ronit's role?" previously retrieved nothing, since
the pronoun-only question had no name for the embedding to match. `app.py`
passes `st.session_state["messages"]` (pre-append) as `history`. Merged to
`main`; verified live in the app against the Ronit role/salary scenario.
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
| Chat-history-aware retrieval (`answer_question(history=...)`) | ✅ Live | Merged to `main`; verified live against Ronit role/salary follow-up — see `docs/ARCHITECTURE.md` |
| Git repo | ✅ Live | `main`, author `maayan-chen <maayan18058@gmail.com>` |

## Next Up
1. None pending — decide next focus area.

## Known Issues
| Issue | Severity | Notes |
|-------|----------|-------|
| OpenAI account has a low TPM rate limit | Low | See `docs/LESSONS.md` — large folders may need batching |
