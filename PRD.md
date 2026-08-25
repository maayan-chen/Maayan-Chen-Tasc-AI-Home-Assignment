# Customer Research RAG Tool — Product Requirements Document

## 1. Executive Summary

The Customer Research RAG Tool is an internal Streamlit application that
helps TASC consultants research and get up to speed on a customer engagement
using everything already known about that customer. Today, that knowledge
lives scattered across project files, meeting notes, and public information
about the customer — a consultant has to manually dig through folders and
ask around to reconstruct context, whether they're picking up an existing
engagement or digging into one they're already on.

This tool collects everything known about a customer — local project files,
meeting summaries, and a web search for public company info — into a shared
retrieval-augmented generation (RAG) store, tagged by customer. A consultant
then opens the same app and asks natural-language questions scoped to just
that customer, getting grounded answers with source citations.

The MVP goal is a working two-tab Streamlit app (Ingest, Ask) built on a
reused FastAPI/LangChain/Postgres-pgvector RAG base, completed within a
2-day build budget, where every architectural choice is simple enough to be
explained and defended — and the tool itself is meant to function as a real,
usable internal utility, not a demo piece.

## 2. Mission

**Mission statement:** Make everything a TASC team already knows about a
customer instantly queryable, without requiring anyone to manually re-read
or re-organize project files.

**Core principles:**
1. **Simplicity and explainability over impressiveness.** Every line must be
   narratable in one sentence. No hidden LLM judgment layers or "magic."
2. **Trust through explicit scoping.** Customer identity is always typed by
   a human, never inferred — because silently mixing up customer data is the
   one failure mode this tool cannot tolerate.
3. **One customer, one shared store, one scoping field.** Logical isolation
   (a metadata tag) is sufficient; physical isolation (separate
   tables/collections per customer) is unnecessary complexity.
4. **Deterministic where possible, agentic only where it earns its keep.**
   File reading and DB writes are plain Python; the LLM agent's job is
   narrowly scoped to web search formulation and optional summarization.
5. **Ship within the time budget.** Cut scope before adding a layer that
   needs its own justification.

## 3. Target Users

**Primary persona: TASC consultant (non-technical), researching a customer.**
- Working an existing customer engagement — whether picked up from a
  departing team or one they're already on — and needs fast, grounded
  answers about that customer.
- Comfortable with a simple web form and a chat interface; not expected to
  read code, run CLI commands, or understand vector databases.
- Needs: "What do I need to know about this customer before my first call?"
  and ongoing quick lookups ("What did we agree on for the Q2 rollout?").
- Pain point today: context is scattered across files and people's memory;
  reconstructing context on an account is slow and error-prone.

**Secondary persona: Consultant running ingestion.**
- Has a project folder full of files (specs, notes, meeting summaries) for
  a customer — whether onboarding a new engagement, handing one off, or
  just keeping an existing one's knowledge base current.
- Needs: a fast, low-friction way to package that knowledge for querying,
  without manually curating or reformatting it.
- Comfortable typing a folder path and a customer name into a form.

**Technical comfort level:** Low to moderate for both personas — this is
explicitly *not* a tool for the engineering team; it's an internal utility
for client-facing consultants. The two-tab Streamlit UI is the entire
interface; no CLI usage is expected in normal operation (a CLI wrapper exists
for developer testing only).

## 4. MVP Scope

### In Scope
**Core Functionality**
- ✅ Ingest tab: folder path input + customer name input + "Run Ingestion
  Agent" button
- ✅ Deterministic local file reading (`.txt`/`.md`/`.pdf`/`.docx`/`.xlsx`/`.pptx`)
  from a user-specified folder, no special-casing between project files and
  meeting summaries
- ✅ OCR fallback for PDFs whose embedded text layer is broken or absent
  (confirmed real-world case: Hebrew PDFs with non-standard font encoding
  that `pypdf` silently misreads as garbage characters rather than failing
  outright) — see Section 6 for the detection + fallback approach
- ✅ Image ingestion (`.png`/`.jpg`/`.jpeg`) via the same `pytesseract` OCR
  path used for the PDF fallback — always run, no "is this needed" check,
  since an image has no embedded text layer to trust in the first place.
  Covers dropped-in screenshots (slides, chat logs) in the customer folder —
  see Section 6
- ✅ Chunking (reuse `chunk_size=300` / `chunk_overlap=100`) and indexing
  into a shared pgvector collection, tagged with `context_tag`
- ✅ Ingestion is additive/incremental — never resets the collection
  (`pre_delete_collection=False`)
- ✅ Ask tab: mandatory customer selection (from distinct `context_tag`
  values already in Postgres) required before the chat interface is shown —
  no chatting without an active customer selected
- ✅ The currently active customer is persistently visible in the UI for
  the entire chat session (e.g. a header/banner above the chat), so it's
  never ambiguous which customer's data is in scope
- ✅ Answers scoped to the selected customer via `context_tag` filter,
  rendered with cited source filenames
- ✅ Last-used folder path + customer name persisted locally
  (`.last_ingest.json`) and prefilled on next launch

**Technical**
- ✅ Reuse `create_database.py`, `docker-compose.yml`, `init.sql` from
  `References/Nivs-RAG/` unchanged; `Dockerfile` reused with Tesseract +
  Hebrew language pack added as a system dependency; `vector_store.py`
  reused with its `extract_content_from_bytes()` extended for
  `.docx`/`.xlsx`/`.pptx` support, a PDF OCR fallback, and direct OCR for
  `.png`/`.jpg`/`.jpeg` files. `api.py` and `models.py` were dropped — see
  Section 6
- ✅ New `ingest.py` with a thin CLI wrapper (`argparse`) for standalone
  testing before the UI exists — plain orchestration, no agent/LLM step
- ✅ New `ingest_tools.py` (file reading helpers)
- ✅ New `app.py` single Streamlit entrypoint with two tabs
- ✅ Direct in-process Python function calls between app/agent and RAG store
  (no HTTP service boundary in this project)
- ✅ Basic error handling: folder path doesn't exist, OpenAI/Postgres down,
  no matching results for a query

**Deployment**
- ✅ `docker compose up --build` starts Postgres+pgvector and the app
- ✅ Submission README with setup steps and a "how it works" section

### Out of Scope
**Core Functionality**
- ❌ Automated/LLM-based relevance filtering at ingestion time
- ❌ Any LLM/agent step in ingestion — no web search, no
  `create_tool_calling_agent`/`AgentExecutor`. Considered and cut: an
  agent formulating a web search query from the customer name reduced to
  one fixed, non-judgmental tool call — functionally identical to a
  consultant Googling the company, not worth the added complexity,
  dependency, and flakiness risk (see `docs/ARCHITECTURE.md`). Ingestion is
  100% local-file processing.
- ❌ Physical per-customer data isolation (separate tables/collections)
- ❌ Calendar or notes-tool integrations (meeting summaries are just files
  a consultant drops in the folder)
- ❌ Email integration of any kind
- ❌ OS-native folder-browser dialog (text input only — Streamlit has no
  server-side folder picker)
- ❌ Fabricated/synthetic demo customer data — a real (or user-supplied
  mock) customer folder is required to test against

**Technical**
- ❌ Automated test suite (pytest) — manual verification only, documented
  as a deliberate scope gap given the 2-day budget
- ❌ HTTP-based service boundary between ingestion/chat and the RAG store —
  `api.py` was removed entirely (see Section 6) rather than kept as an
  unused escape hatch
- ❌ Multi-user auth/access control — this is a trusted-internal-users tool
- ❌ Deleting or editing already-ingested customer data via the UI

**Integration**
- ❌ Any integration beyond local filesystem reads (no web search — see
  Section 4 Core Functionality above)

**Deployment**
- ❌ Production hosting/cloud deployment — local Docker Compose only, for
  the assignment submission

## 5. User Stories

1. **As a departing consultant**, I want to point the app at my project
   folder and type the customer's name, so that everything I know about
   this engagement is captured before I hand it off.
   *Example: Point at `~/projects/acme-retail-2026/`, type "Acme Retail",
   click "Run Ingestion" — get a summary: "14 files read, 87 chunks
   saved."*

2. **As a new team member**, I want to be required to pick a customer before
   I can chat, and see who I'm asking about at all times, so that I never
   accidentally ask a question against the wrong customer's data.
   *Example: Opening the Ask tab shows a customer picker with no chat box
   yet. After selecting "Acme Retail," a banner reading "Asking about: Acme
   Retail" appears above the chat, staying visible for the whole session.*

3. **As a new team member**, I want to ask questions in plain English about
   the selected customer, so that I can get up to speed without reading
   every file myself.
   *Example: With "Acme Retail" selected, ask "What was agreed in the last
   contract renewal?" and get a grounded answer citing
   `contract_renewal_notes.md`.*

4. **As a new team member**, I want every answer to show its sources, so
   that I can verify the answer against the original document instead of
   blindly trusting the AI.
   *Example: Answer is followed by a "Sources" caption listing
   `kickoff_meeting_notes.md`, `scope_doc.pdf`.*

5. **As a departing consultant**, I want to re-run ingestion after a new
   meeting without wiping out what's already indexed, so that the knowledge
   base only grows over time.
   *Example: Run ingestion in week 1 with 10 files, run it again in week 3
   with 3 new meeting notes — all 13 files' worth of content is searchable.*

6. **As a consultant re-using the tool**, I want my last folder path and
   customer name remembered, so that re-running ingestion for the same
   customer is a single click.
   *Example: Reopen the app next week — the Ingest tab is prefilled with
   last week's folder path and "Acme Retail."*

7. **As a new team member**, I want questions about one customer to never
   surface another customer's data, so that I can trust the tool with
   confidential client information.
   *Example: Ask the same question against "Acme Retail" and "Globex Corp"
   — get two different, correctly-scoped answers, never cross-contaminated.*

8. **(Technical) As the developer**, I want a CLI wrapper for the ingestion
   logic, so that I can test `read_local_files()` → indexing end-to-end
   before the Streamlit UI exists.
   *Example: `python ingest.py --customer "Acme Retail" --folder
   /path` completes and reports chunks saved, runnable from a terminal on
   Day 1.*

9. **(Technical) As the developer**, I want every architectural decision to
   be simple and well-justified, so that the tool is maintainable as a real
   piece of internal software, not just a one-off demo.
   *Example: "Why not separate vector collections per customer?" — "Logical
   isolation via one indexed metadata field is sufficient at this scale;
   physical isolation adds complexity for no real benefit."*

## 6. Core Architecture & Patterns

**High-level approach:** A single Streamlit process with two tabs, backed by
a shared Postgres/pgvector store. Both tabs call into the same RAG
primitives (`vector_store.py`, `create_database.py`) via direct in-process
Python function calls — no internal network hop.

```
customer-handoff-rag/
├── .env                    # OPENAI_API_KEY, PGVECTOR_* (from Nivs-RAG, gitignored)
├── .gitignore
├── docker-compose.yml      # Postgres+pgvector + app service (unchanged from Nivs-RAG)
├── Dockerfile               # REUSED, EXTENDED — adds tesseract-ocr + tesseract-ocr-heb system packages
├── init.sql                 # unchanged from Nivs-RAG
├── requirements.txt         # Nivs-RAG deps + streamlit + python-docx + openpyxl + python-pptx + pytesseract + Pillow
├── vector_store.py          # REUSED, EXTENDED — pgvector connection; extract_content_from_bytes() gains .docx/.xlsx/.pptx parsing + PDF OCR fallback + image OCR
├── create_database.py       # REUSED — split_text(), save_to_pgvector(), set_context_tag()
├── query_data.py             # REUSED UNCHANGED — CLI reference for querying
├── ingest.py                  # NEW — run_ingestion(customer_name, folder_path) orchestration + CLI wrapper, no agent
├── ingest_tools.py           # NEW — read_local_files()
├── app.py                    # NEW — Streamlit entrypoint, st.tabs(["Ingest", "Ask"])
├── .last_ingest.json          # NEW, gitignored — remembers last folder path + customer name
├── CLAUDE.md                  # Agent operating instructions (trimmed from project-template)
└── STATE.md                   # Session-to-session project state
```

**Key design patterns:**
- **Single scoping field (`context_tag`):** one indexed JSONB metadata
  field on each chunk, filtered on at query time. This is the sole customer
  isolation mechanism — no per-customer tables or pgvector collections.
- **Direct function calls, not HTTP:** ingestion and chat both import and
  call `vector_store.py`/`create_database.py` functions directly, since
  ingestion and chat share one codebase. Nivs-RAG's `api.py` (and the
  `models.py` schemas it depended on) was removed rather than kept as an
  unused escape hatch — it let `context_tag` be omitted or spoofed with no
  auth, and was the container's actual `CMD`, not dead code. See
  `docs/ARCHITECTURE.md`.
- **Deterministic ingestion, no agent:** file reading and the pgvector write
  path are plain Python, always executed the same way for the same input. No
  LLM or `create_tool_calling_agent`/`AgentExecutor` step exists in
  ingestion — a web-search agent step was planned, then cut before
  implementation once it reduced to one fixed, non-judgmental tool call. See
  `docs/ARCHITECTURE.md`.
- **No ingestion-time relevance filtering:** everything found (every local
  file, the web search result) is indexed unfiltered. Relevance is computed
  once, at query time, via vector similarity + `min_relevance` threshold —
  avoiding a second, harder-to-explain judgment layer.
- **Additive indexing:** ingestion always runs with
  `pre_delete_collection=False`, so re-running for the same or a different
  folder only ever adds to a customer's knowledge base.
- **PDF OCR fallback for broken text layers:** some real-world PDFs (e.g.
  Hebrew documents generated with non-standard/embedded font encodings —
  confirmed by testing against a real Hebrew contract) have a text layer
  that `pypdf` reads as valid-looking but wrong Unicode — the extracted
  string is not empty, so a naive "retry OCR only if empty" check would
  miss it. Detection instead checks the *character makeup* of the extracted
  text: if the source filename or a language hint suggests non-Latin script
  (or, more robustly, if the extracted text's ratio of recognized-alphabet
  characters is too low / it's dominated by punctuation-like symbols), the
  page is rasterized (via PyMuPDF, image-rendering only, not text
  extraction) and re-read with `pytesseract` (`lang="heb"`). This keeps the
  fast/free path (`pypdf`) as the default and only pays the OCR cost when
  the text layer is actually untrustworthy. Deterministic rule, not an LLM
  judgment call — consistent with the ingestion-time no-LLM-filtering
  principle. **Validated against a real Hebrew rental contract:** `pypdf`
  produced unreadable garbage; OCR with `lang="heb"` produced coherent,
  correct Hebrew text (names, ID numbers, dates, rent amount all legible).
  `lang="heb+eng"` was tested too but performed slightly worse on this
  Hebrew-only document — the mixed language model introduced extra
  misreads on ambiguous glyphs — so `heb`-only is the better default for
  documents that are Hebrew apart from embedded digits/dates (which OCR
  correctly regardless of language setting).
- **Direct OCR for image files:** `.png`/`.jpg`/`.jpeg` files found in the
  customer folder (e.g. a slide export or a chat-log screenshot) are always
  routed straight to `pytesseract` — no "should I OCR this" detection step,
  since an image file has no embedded text layer to check in the first
  place, unlike a PDF. Same deterministic, no-LLM-judgment principle as the
  rest of ingestion: OCR either extracts legible text or it doesn't, and a
  low-yield/garbled OCR result is just weaker source content, filtered out
  the same way any other low-relevance chunk is — at query time, not
  ingestion time. **Uses `lang="heb+eng"`, unlike the PDF fallback's
  `lang="heb"`:** an arbitrary dropped-in image has no known language ahead
  of time (could be an English email screenshot or a Hebrew WhatsApp
  screenshot), unlike a PDF already routed to OCR because its known-Hebrew
  text layer is untrustworthy. Validated against two real screenshots:
  `lang="heb"` badly garbled an all-English screenshot, while `lang="heb+eng"`
  correctly read both an all-English and an all-Hebrew one — see
  `docs/ARCHITECTURE.md`.

## 7. Features

### 7.1 Ingest Tab
- Two `st.text_input` fields: project folder path, customer name — both
  prefilled from `.last_ingest.json` if present.
- "Run Ingestion" button. On click:
  1. Save both inputs to `.last_ingest.json`.
  2. Slugify the customer name into `context_tag` (e.g. "Acme Retail" →
     `acme-retail`).
  3. Call `ingest.run_ingestion(customer_name, folder_path)` synchronously,
     wrapped in `st.spinner`.
  4. Deterministically walk the folder, read each
     `.txt`/`.md`/`.pdf`/`.docx`/`.xlsx`/`.pptx`/`.png`/`.jpg`/`.jpeg` via an
     extended `extract_content_from_bytes()` (reused from `vector_store.py`,
     adding `python-docx`, `openpyxl`, and `python-pptx` parsing branches
     alongside the existing `pypdf`/UTF-8 paths) — no distinction made
     between project files and meeting summaries. For PDFs, if `pypdf`'s
     extracted text looks unreliable (see OCR fallback rule in Section 6),
     the page is re-read via OCR instead. Image files are always routed
     straight to OCR (see Section 6). Other unsupported file types are
     skipped, not errored.
  5. Wrap each local file as a `Document` (`page_content`,
     `metadata={"source": ..., "context_tag": ...}`). No web search step —
     cut, see `docs/ARCHITECTURE.md`.
  6. Chunk via `create_database.py`'s `split_text()` (chunk_size=300,
     chunk_overlap=100), tag via `set_context_tag()`, save via
     `save_to_pgvector(chunks, pre_delete_collection=False)`.
  7. Show a success summary (files read, chunks saved) or a clear error
     message.

### 7.2 Ask Tab
- On entering the tab, the user sees only a customer selector (populated
  live from `SELECT DISTINCT cmetadata->>'context_tag' FROM
  langchain_pg_embedding`) — the chat interface itself is not rendered
  until a customer is chosen. There is no "all customers" or unscoped
  option.
- Once a customer is selected, a persistent banner/header (e.g. "Asking
  about: Acme Retail") is shown above the chat for the entire session, and
  a control to switch customers (which resets the chat history) is always
  available.
- `st.chat_input`/`st.chat_message` loop, scoped to the selected customer.
- On each question: use the selected `context_tag` (already stored, no
  re-typing/re-slugifying) to filter retrieval via
  `vector_store.create_vector_store()` and a `context_tag`-filtered
  `similarity_search_with_relevance_scores()` call, in-process.
- Render the LLM's answer as a chat bubble; render source filenames
  underneath as a "Sources" caption.
- Empty-state message when no matching results are found (below
  `min_relevance`).

### 7.3 Ingestion CLI Wrapper (developer-only)
- `ingest.py` includes a thin `if __name__ == "__main__":` block with
  `argparse` (`--customer`, `--folder`), so ingestion logic is testable from
  a terminal on Day 1 before the UI exists. Not part of the end-user
  product surface.

## 8. Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| UI | Streamlit | Single app, `st.tabs(["Ingest", "Ask"])`, zero frontend build step |
| LLM | OpenAI (`langchain-openai`, `ChatOpenAI`) | Single provider throughout — chat and embeddings both OpenAI. No agent/LLM step in ingestion — see `docs/ARCHITECTURE.md` |
| Embeddings | `OpenAIEmbeddings` | Reused from `vector_store.py`, unchanged |
| Vector store | Postgres + pgvector (`langchain-postgres` `PGVector`) | Shared collection across all customers |
| File parsing | `pypdf`, plain UTF-8 decode, `python-docx`, `openpyxl`, `python-pptx` | Via extended `extract_content_from_bytes()` |
| OCR | `pytesseract` + `tesseract-ocr`/`tesseract-ocr-heb` (system), `PyMuPDF` (page rasterization), `Pillow` | PDF fallback triggered only when `pypdf`'s text extraction looks unreliable; always-on for `.png`/`.jpg`/`.jpeg` files — see Section 6 |
| DB driver | `psycopg` | Reused connection helpers in `vector_store.py` |
| Containerization | Docker Compose | `pgvector/pgvector:pg16` + app service; `Dockerfile` extended with Tesseract system packages |
| Config | `python-dotenv`, `.env` | `OPENAI_API_KEY`, `PGVECTOR_CONNECTION`/`PGVECTOR_COLLECTION`, `POSTGRES_*` |

**New dependencies to add to `requirements.txt`:** `streamlit`,
`python-docx`, `openpyxl`, `python-pptx`, `pytesseract`, `Pillow`, `PyMuPDF`.

**New system dependency (`Dockerfile`):** `tesseract-ocr` and
`tesseract-ocr-heb` (the Hebrew language pack) via `apt-get`. Confirmed
necessary by testing `pypdf` against a real Hebrew PDF: the extraction
returned 2000+ characters of well-formed-looking but completely wrong text
(broken font-to-Unicode glyph mapping, not an RTL ordering issue) — no
Python PDF library fixes this, since they all trust the same broken
encoding. OCR is the only reliable extraction path for such files.

**Provider decision:** OpenAI is used exclusively (chat, agent, and
embeddings) rather than mixing in Anthropic. Anthropic has no embeddings
API, and `vector_store.py`'s `PGVector` store (a "reuse as-is" file) is
built entirely around `OpenAIEmbeddings` — introducing Anthropic would mean
either modifying that reused file or running two LLM providers
side-by-side for no benefit. Single-provider keeps the reused RAG base
untouched and the stack simpler to explain.

## 9. Security & Configuration

- **Authentication/authorization:** None. This is an internal tool for
  trusted TASC staff; no login flow is in scope for the MVP.
- **Configuration management:** All secrets (`OPENAI_API_KEY`,
  `PGVECTOR_CONNECTION`/`POSTGRES_*`) live in a gitignored `.env` file,
  following the existing `.env.example` template. Docker Compose injects
  `POSTGRES_HOST`/`PGVECTOR_CONNECTION` for the containerized app.
- **Customer data isolation (the core trust boundary):** `context_tag` is
  the sole scoping mechanism. It is always derived from an explicit,
  human-typed customer name — never inferred from folder or project names,
  since a folder is typically named after the project, not the customer,
  and a wrong guess would silently leak one customer's data into another's
  answers.
- **In scope for security:** correct `context_tag` filtering on every query
  (verified via manual `psql` check and the two-customer isolation test in
  Verification below); no secrets committed to git; customer project
  folders are never copied into the repo (only a typed path is used at
  ingestion time, transiently).
- **Out of scope for security:** authN/authZ, encryption at rest beyond
  Postgres defaults, rate limiting, audit logging, PII redaction. These are
  explicitly deferred given the internal-tool nature and 2-day budget.
- **Deployment considerations:** Local Docker Compose only for this
  assignment. No production hosting, TLS termination, or secrets manager
  integration is in scope.

## 10. API Specification

No HTTP API. `app.py`/`ingest.py` call `vector_store.py`/
`create_database.py` functions directly, in-process. Nivs-RAG's `api.py`
(and the `models.py` Pydantic schemas it depended on) were removed rather
than kept as an unused service boundary — it was unauthenticated and let
`context_tag` be omitted or spoofed on both its `/index` and `/query`
endpoints, and it was the container's actual `CMD` (port 8000 exposed), not
dead code. See `docs/ARCHITECTURE.md` for the full rationale. If a real need
for a separately-owned RAG service ever arises, a new HTTP surface should be
added deliberately, with auth and a mandatory `context_tag`.

## 11. Success Criteria

**MVP is successful when:**
- ✅ `docker compose up --build` starts Postgres+pgvector and the app
  cleanly
- ✅ Ingestion against a real (or user-supplied mock) customer folder
  completes without error and reports files read / chunks saved
- ✅ Rows in `langchain_pg_embedding` carry the correct `context_tag`
  (verified via `psql`)
- ✅ Ask tab's customer dropdown accurately reflects what's been ingested,
  read live from Postgres, and the chat UI is inaccessible until a customer
  is selected
- ✅ A real question about the ingested customer returns a grounded answer
  with correct source filenames
- ✅ If a second customer is ingested, the same question against both
  returns different, correctly-scoped answers — proving `context_tag`
  isolation works
- ✅ Both folder path and customer name persist across app restarts via
  `.last_ingest.json`

**Quality indicators:**
- Every architectural decision (see `docs/ARCHITECTURE.md`) can be
  explained in one sentence without hand-waving
- No component requires "trust me, it just works" — file reading, chunking,
  and retrieval are all inspectable, deterministic steps
- Errors (bad folder path, OpenAI/Postgres down, no matching results) fail
  with a clear message, not a stack trace in the UI

**User experience goals:**
- A non-technical consultant can complete an ingestion run and ask a
  question without any explanation beyond the two tab labels
- Source citations are visible enough that a consultant would actually
  trust and verify an answer rather than blindly accept it

## 12. Implementation Phases

### Phase 1 — Scaffolding & RAG base (Day 1, morning)
**Goal:** Confirm the reused RAG base works before building anything new.
**Deliverables:**
- ✅ `git init` at `customer-handoff-rag/`, feature branch created
- ✅ `vector_store.py`, `create_database.py`, `models.py`, `api.py`,
  `query_data.py`, `docker-compose.yml`, `Dockerfile`, `init.sql` copied
  in unchanged from `References/Nivs-RAG/` (`models.py`/`api.py` later
  removed — see Section 6)
- ✅ `docker compose up --build` runs cleanly
**Validation:** `/index` and `/query` still work against Nivs-RAG's own
sample data (`data/alice_in_wonderland.md`) before any new code is written.

### Phase 1.5 — Extend file parsing (Day 1, before real ingestion testing)
**Goal:** `extract_content_from_bytes()` handles every file type expected in
real customer folders, including the Hebrew-PDF OCR fallback and image OCR.
**Deliverables:**
- ✅ `.docx` (`python-docx`), `.xlsx` (`openpyxl`), and `.pptx`
  (`python-pptx`) parsing branches added
- ✅ PDF OCR fallback added: detect unreliable `pypdf` extraction, rasterize
  via PyMuPDF, OCR via `pytesseract` (`lang="heb"`)
- ✅ `.png`/`.jpg`/`.jpeg` branch added: load via Pillow, OCR directly via
  the same `pytesseract` call as the PDF fallback, no detection step
- ✅ `Dockerfile` updated with `tesseract-ocr` + `tesseract-ocr-heb` system
  packages; `requirements.txt` updated with new Python deps
**Validation:** Already spiked standalone (outside the repo, via a local
venv) against a real Hebrew rental contract PDF — confirmed `pypdf` alone
returns garbled/unusable text, while rasterizing + `pytesseract(lang="heb")`
correctly recovers legible Hebrew (party names, ID numbers, dates, rent
amount). Once implemented in `vector_store.py`, re-run the same file
through the real `extract_content_from_bytes()` path to confirm parity.

### Phase 2 — Ingestion logic (Day 1, afternoon)
**Goal:** Real customer data lands in Postgres with correct `context_tag`.
**Deliverables:**
- ✅ `ingest_tools.py`: `read_local_files()` tested standalone against the
  real customer folder
- ✅ `ingest.py`: `run_ingestion()` wiring file reading + chunk/tag/save
  (no agent/web search step), tested via CLI wrapper (no UI yet)
**Validation:** `psql` check confirms rows in `langchain_pg_embedding` with
the right `context_tag`; a `query_data.py`/curl query with `context_tag`
filter returns a sane, sourced answer.

### Phase 3 — Streamlit app (Day 2, morning)
**Goal:** End-to-end UI a consultant can actually use.
**Deliverables:**
- ✅ `app.py` with Ingest tab (wired to `run_ingestion()`,
  `.last_ingest.json` persistence) and Ask tab (`context_tag` dropdown +
  chat loop)
- ✅ (Nice-to-have, not required) second real customer folder ingested to
  demonstrate isolation
**Validation:** Full UI walkthrough — ingest, ask, verify sources; if a
second customer exists, confirm scoped answers differ correctly.

### Phase 4 — Polish & submission (Day 2, afternoon)
**Goal:** Submission-ready.
**Deliverables:**
- ✅ Empty-state message, loading spinners, basic error handling (bad path,
  OpenAI/Postgres down)
- ✅ Submission README (setup steps + "how it works")
- ✅ Fresh `docker compose up --build`, re-run ingestion from scratch,
  re-walk the ask flow once more before submitting
**Validation:** A stranger following only the README can start the app and
complete one ingest + one ask cycle.

## 13. Future Considerations

*(Explicitly post-MVP — not part of this 2-day build.)*
- Automated pytest coverage, especially for `context_tag` isolation
  specifically, since it's the entire trust boundary
- Vision-model captioning for images with little/no extractable text
  (diagrams, photos, non-text screenshots) — OCR only recovers text that's
  actually rendered in the image; deferred because it introduces an
  ingestion-time LLM judgment layer and added cost, unlike plain OCR
- OS-native folder picker or drag-and-drop file upload instead of a raw
  text path input
- Calendar/notes-tool/email integrations as additional ingestion sources
- Ability to delete or re-scope previously ingested data from the UI
- Multi-user auth if the tool moves beyond a trusted internal audience
- Splitting the RAG store into a standalone, properly-authenticated HTTP
  service if it ever needs to be shared with systems outside this
  codebase (see `docs/ARCHITECTURE.md` for why the original `api.py` was
  removed rather than kept as that boundary)

## 14. Risks & Mitigations

1. **Risk:** A bug in the `context_tag` filter leaks one customer's data
   into another's answer, breaking the tool's core trust promise.
   **Mitigation:** `context_tag` is the *only* scoping mechanism by design
   (simpler surface area to get right); manual two-customer isolation test
   in Verification catches regressions before submission; the mandatory
   customer-selection step in the Ask tab (Section 4) adds a second layer
   of protection against accidentally querying the wrong customer.

2. **Risk:** 2-day budget is tight; scope creep (e.g. building a real
   folder-browser UI, adding calendar integrations, vision-model image
   captioning) eats time needed for the core ingest→index→ask loop.
   **Mitigation:** Out-of-scope list above is explicit and was agreed up
   front; every deferred item has a one-sentence justification for why it's
   not in the MVP ("would burn the budget on plumbing unrelated to the core
   RAG/agent functionality being delivered").

3. **Risk:** No real customer folder available blocks Day 1 ingestion
   testing, cascading delays into Day 2.
   **Mitigation:** Flagged as the top blocking item in `STATE.md`; Phase 1
   (scaffolding + RAG base sanity check) doesn't require it, so that work
   can proceed in parallel while the folder is sourced.

4. **Risk (retired):** Web search agent step (`DuckDuckGoSearchRun`) being
   flaky/rate-limited and failing ingestion. No longer applicable — the
   web-search/agent step was cut entirely before implementation (see
   `docs/ARCHITECTURE.md`); ingestion is local-file-only and has no external
   network dependency to be flaky.

5. **Risk:** No automated tests means a regression in `create_database.py`
   reuse or the retrieval path could go unnoticed until manual QA.
   **Mitigation:** Documented as a deliberate, named scope gap (see
   `docs/ARCHITECTURE.md`) rather than an oversight; manual verification
   checklist (Section 11) is run before submission as compensating
   coverage.

6. **Risk:** OCR text quality is lower than native text extraction —
   misread characters, dropped words, or garbled formatting from imperfect
   OCR could degrade retrieval quality or produce slightly wrong answers
   for OCR'd documents (confirmed necessary for Hebrew PDFs with broken
   font encoding, see Section 6). OCR also adds ingestion latency (page
   rasterization + Tesseract run) compared to native text extraction.
   **Mitigation:** OCR is a fallback, not the default path — used only when
   `pypdf`'s native extraction looks unreliable, so clean-encoding PDFs pay
   no cost. Source filenames are still cited on every answer, so a
   consultant can always open the original PDF to verify anything that
   looks off in an OCR'd answer.

## 15. Appendix

**Related documents:**
- `Basic-plan` (project root, one level up from this repo per `CLAUDE.md`)
  — the original, more granular implementation plan this PRD is derived
  from
- `docs/ARCHITECTURE.md` — the "why" behind each architectural decision
- `docs/LESSONS.md` — gotchas to be filled in as the build proceeds
- `STATE.md` — session-to-session current state tracker

**Key dependencies (reference implementations, read-only):**
- `References/Nivs-RAG/` — FastAPI + LangChain + Postgres/pgvector RAG base
  (`References/AI-Agent/`'s tool-calling agent pattern was evaluated and not
  used — see `docs/ARCHITECTURE.md`)
- `References/project-template/` — CLAUDE.md/STATE.md scaffolding
  conventions
