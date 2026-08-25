<!-- This file must stay under 80 lines. If it grows, prune or move content to docs/. -->
# Customer Research RAG Tool — Current State
Last updated: 2026-08-25 (pivoted framing from handoff-only to general
customer research; sources UI polish; Hebrew RAG quality + Hebrew/RTL UI
merged to `main` from `improve-hebrew-retrieval-ocr`)

## Project Summary
A Streamlit app (Ingest tab + Ask tab) that helps a TASC team research and
get up to speed on a customer — whether picking up an existing engagement
or working one they're already on. Ingestion is deterministic: reads a
project folder, indexes everything into a shared pgvector store tagged with
a customer's `context_tag`; the Ask tab is a chat UI scoped to one customer.
Built from `References/Nivs-RAG/` (RAG base). No LLM/agent step in
ingestion — a web-search agent was planned, then cut before implementation
(see `docs/ARCHITECTURE.md`: it reduced to one fixed, non-judgmental tool
call, not worth the complexity). 2-day budget, must stay simple enough to
fully explain in an interview.

## Current Task
Real customer folders used for testing: `Teva_Org_Streamlining_Project` and
`Teva_PGTech_Acquisition_Project` (mixed Hebrew/English `.docx`/`.xlsx`/
`.pptx`/`.pdf`/`.png` files), both ingested under `context_tag='teva'`.
Earlier phases (RAG base setup, ingestion CLI, Streamlit UI, xlsx
tabular-retrieval fix, chat history, Hebrew RAG quality + RTL UI) are
shipped and merged to `main` — see `git log` and `docs/ARCHITECTURE.md`
for what/why.

**Merged to `main` (from `improve-hebrew-retrieval-ocr`):** a real bug
report (broad Hebrew questions returning "I don't know") led to several
fixes, all in `docs/ARCHITECTURE.md`: `query_rag.py`'s `ChatOpenAI()` was
silently defaulting to `gpt-3.5-turbo` (now `gpt-4o`); `k` raised 3→8;
non-Hebrew documents are now translated to Hebrew at ingestion to close a
measured cross-lingual embedding gap; the prompt answers in the question's
language and formats with Markdown bullets/paragraphs; the whole UI
(`app.py`) is translated to Hebrew and RTL. **Known gap:** an English
question now often gets answered in Hebrew anyway (regression from the
translation-at-ingestion fix) — accepted since real usage is expected to
be Hebrew-majority, see `docs/ARCHITECTURE.md`.

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
| Hebrew RAG quality fixes (gpt-4o, k=8, translation-at-ingestion, language-matched Markdown answers) + Hebrew/RTL UI | ✅ Live | Merged to `main` from `improve-hebrew-retrieval-ocr` — see `docs/ARCHITECTURE.md` |
| Sources UI (click-to-reveal per source, `FILE (parent folder)` labels, RTL chunk text) | ✅ Live | On `main`; see `.agents/execution-reports/sources-ui-polish.md` |
| Git repo | ✅ Live | `main`, author `maayan-chen <maayan18058@gmail.com>` |

## Next Up
1. Further RAG quality work TBD (see Known Issues below).

## Known Issues
| Issue | Severity | Notes |
|-------|----------|-------|
| OpenAI account has a low TPM rate limit | Low | See `docs/LESSONS.md` — large folders may need batching |
| English questions often answered in Hebrew | Low | Post translation-at-ingestion, most context is Hebrew and outweighs the prompt's language instruction for English questions — see `docs/ARCHITECTURE.md` |
