# Feature: Phase 3 — Streamlit App (`app.py` + `query_rag.py`)

The following plan should be complete, but it's important that you validate
documentation, codebase patterns, and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import
from the right files.

## Feature Description

Build the Streamlit UI (`app.py`) that makes ingestion and retrieval usable by
a non-technical TASC consultant, per PRD §7. Two tabs: Ingest (folder path +
customer name → `run_ingestion()`) and Ask (customer picker → chat scoped by
`context_tag`). A new `query_rag.py` module holds the customer-scoped
retrieval + answer logic the Ask tab calls, separate from the existing
reference CLI script `query_data.py` (left untouched). `ingest.py` gains a
`slugify()` step so a human-typed customer name becomes a safe, consistent
`context_tag`. The app is styled to match TASC's own brand (navy header bar,
magenta accent, pill-shaped section labels) using the assignment PDF as the
visual reference.

## User Story

As a new team member picking up a handed-off customer
I want to open a simple web app, pick the customer, and ask questions in plain English
So that I can get up to speed without reading every project file myself, and trust each answer because I can see exactly which chunk of text it came from

## Problem Statement

`run_ingestion()` (`ingest.py`) and the retrieval pattern (`query_data.py`)
both work today, but only from a terminal. There is no UI yet — PRD §7 defines
one, `STATE.md` names it as the sole remaining Next Up item, but `app.py`
doesn't exist. Two behavioral gaps also exist in what's already built:
`run_ingestion()` uses the typed customer name verbatim as `context_tag`
(`ingest.py:9`, `context_tag = customer_name.strip()`) with no normalization,
so two consultants typing "Acme Retail" and "acme retail" would silently
create two different, non-matching tags; and the reference query pattern
(`query_data.py`) has no "insufficient context" instruction in its prompt, so
a low-signal-but-above-threshold retrieval could produce a confidently wrong
answer with no source verification path in the UI.

## Solution Statement

`app.py` is a single Streamlit entrypoint with `st.tabs(["Ingest", "Ask"])`.
The Ingest tab collects a folder path and customer name (prefilled from
`.last_ingest.json`), calls `ingest.run_ingestion()` inside a spinner, and
reports files-read/chunks-saved or a clean error. `ingest.py`'s
`run_ingestion()` gains a `slugify(customer_name)` step (lowercase +
non-alphanumeric → `-`) applied before the value is used as `context_tag` —
the *only* place `context_tag` is derived, so this is a one-line, one-location
change. The Ask tab queries Postgres directly for
`DISTINCT cmetadata->>'context_tag'` values to populate a customer dropdown
(chat UI hidden until one is picked, per PRD §7.2); the dropdown/banner show
the slug itself — no separate display-name field, keeping `context_tag` the
sole customer-identifying mechanism end to end, consistent with `CLAUDE.md`.
A new `query_rag.py` module (mirroring `query_data.py`'s
`similarity_search_with_relevance_scores` → prompt → `ChatOpenAI` pattern, but
importable and unit-testable) adds a `filter={"context_tag": context_tag}`
argument, a revised prompt template that instructs the model to say it
doesn't know rather than guess when context is insufficient, and returns
structured source data (filename + full chunk text) so the UI can render each
source's grounding text, not just its filename. Visual styling (navy header,
magenta accent, pill labels) is applied via `.streamlit/config.toml` theme
colors plus a small `st.markdown(..., unsafe_allow_html=True)` CSS block for
the pill-shaped labels/banner that Streamlit's theme config can't produce on
its own.

## Feature Metadata

**Feature Type**: New Capability
**Estimated Complexity**: Medium
**Primary Systems Affected**: New UI layer (`app.py`), new query module
(`query_rag.py`), one small `ingest.py` change (slugify). No changes to
`vector_store.py`, `create_database.py`, or `read_local_files.py`.
**Dependencies**: `streamlit` (already in `requirements.txt`), `psycopg`
(already a dependency, via `vector_store.get_psycopg_connection()`), no new
packages required.

---

## CONTEXT REFERENCES

### Relevant Codebase Files — READ THESE BEFORE IMPLEMENTING

- `ingest.py:1-46` (full file) — Why: `run_ingestion(customer_name, folder_path)`
  is the exact function the Ingest tab calls. Note line 9:
  `context_tag = customer_name.strip()` — this is the ONE line to change (add
  slugify before/in place of `.strip()`). Line 14 already handles the "no
  ingestible files" case by returning `{"files_read": 0, "chunks_saved": 0}`
  — `app.py` should branch on `chunks_saved == 0` to show a distinct
  "no files found" message vs. a success message.
- `query_data.py:1-49` (full file) — Why: the retrieval pattern `query_rag.py`
  must mirror: `OpenAIEmbeddings()` → `create_vector_store(embedding_function)`
  → `similarity_search_with_relevance_scores(query_text, k=3)` → threshold
  check (`results[0][1] < 0.7`) → `ChatPromptTemplate` → `ChatOpenAI().predict()`
  → sources from `doc.metadata.get("source")`. `query_rag.py` extends this
  with a `filter` kwarg and returns chunk text, not just filenames — see
  Patterns below.
- `vector_store.py:61-70` (`create_vector_store`) — Why: `query_rag.py` calls
  this unchanged (`create_vector_store(embeddings)` → `PGVector` instance);
  no new connection logic needed.
- `vector_store.py:24-41` (`get_pgvector_connection`, `get_collection_name`,
  `get_psycopg_connection`) — Why: `app.py`'s Ask-tab customer-dropdown query
  needs a raw `psycopg` connection — reuse `get_psycopg_connection()`
  directly rather than adding a second connection-string builder.
- `langchain_postgres/vectorstores.py` (installed package, `PGVector` class
  docstring, "Supported filter operators" section — confirmed via
  `grep -n "Supported filter operators" -A 20` in
  `venv/lib/python3.11/site-packages/langchain_postgres/vectorstores.py`) —
  Why: confirms `similarity_search_with_relevance_scores(query, k=3,
  filter={"context_tag": context_tag})` is valid — a bare dict with one field
  and no operator is an equality/AND filter, exactly what's needed here. No
  `$eq` operator wrapping required for a single-field exact match.
- `create_database.py:32-48` (`split_text`) — Why: confirms
  `add_start_index=True` is set, so every chunk has a `start_index` metadata
  field — NOT used in this plan (decision below: show chunk text, not
  location, to sidestep the fact that `start_index` is meaningless for
  `.xlsx`/`.pptx`/image-OCR chunks where there's no natural "character
  offset in the original file" concept). Do not add location display in this
  phase.
- `PRD.md:311-338` (§7.1 Ingest Tab, §7.2 Ask Tab) — Why: canonical UI flow
  and copy expectations (e.g. "Asking about: X" banner, mandatory customer
  selection before chat renders, empty-state message).
- `docs/ARCHITECTURE.md:77-84` ("Customer name is always explicit user
  input, never inferred") — Why: confirms the folder path and customer name
  stay as separate typed fields; `.last_ingest.json` only ever persists what
  the user already typed, never derives a name from the folder path.
- `.env.example` (full file) — Why: `PGVECTOR_COLLECTION` defaults to
  `"default"` via `get_collection_name()`; no new env vars needed for this
  phase.
- `.gitignore:8-9` — Why: `.last_ingest.json` is ALREADY gitignored; no
  `.gitignore` change needed in this phase.

### New Files to Create

- `query_rag.py` — `answer_question(question: str, context_tag: str, k: int
  = 3, min_relevance: float = 0.7) -> dict`. Returns
  `{"answer": str, "sources": list[dict]}` where each source dict is
  `{"source": str, "content": str}` (filename + full chunk text). Returns
  `{"answer": None, "sources": []}` (or a documented sentinel) when no result
  clears `min_relevance` — caller (`app.py`) renders the empty-state message.
- `app.py` — Streamlit entrypoint. `st.tabs(["Ingest", "Ask"])`. Reads/writes
  `.last_ingest.json` for folder-path/customer-name persistence. Ingest tab
  calls `ingest.run_ingestion()`. Ask tab queries distinct `context_tag`
  values via `psycopg`, then calls `query_rag.answer_question()` per chat
  turn.
- `.streamlit/config.toml` — Theme colors (navy primary background for
  header styling context, magenta `primaryColor`) matching
  `TASC-AI-Home-Assignment 2026.pdf`'s dark navy header bar / magenta accent
  palette. Streamlit's native theme config covers base colors and font but
  NOT the pill-shaped labels — those need the CSS block in `app.py`.

### Relevant Documentation — READ THESE BEFORE IMPLEMENTING

- [Streamlit `st.tabs`](https://docs.streamlit.io/develop/api-reference/layout/st.tabs)
  - Why: confirms tabs don't preserve widget state across reruns by
    identity — session state (`st.session_state`) is required to persist the
    selected customer/chat history across reruns within the Ask tab, and to
    avoid re-running ingestion on every Streamlit script rerun.
- [Streamlit `st.chat_message` / `st.chat_input`](https://docs.streamlit.io/develop/api-reference/chat)
  - Why: canonical chat UI pattern PRD §7.2 specifies; `st.chat_input` returns
    `None` until the user submits, must be handled at the bottom of a
    `st.session_state`-backed message loop.
- [Streamlit theming (`config.toml`)](https://docs.streamlit.io/develop/concepts/configuration/theming)
  - Why: exact key names (`primaryColor`, `backgroundColor`,
    `secondaryBackgroundColor`, `textColor`, `font`) needed for the TASC
    navy/magenta palette.
- [langchain-postgres `PGVector` metadata filtering](https://github.com/langchain-ai/langchain-postgres)
  (installed source is authoritative here — no version drift risk since it's
  already vendored in `venv/`; see codebase reference above instead of
  fetching external docs)

### Patterns to Follow

**Retrieval + answer pattern to extend (from `query_data.py:26-44`):**
```python
embedding_function = OpenAIEmbeddings()
db = create_vector_store(embedding_function)
results = db.similarity_search_with_relevance_scores(query_text, k=3)
if len(results) == 0 or results[0][1] < 0.7:
    print(f"Unable to find matching results.")
    return
context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
prompt = prompt_template.format(context=context_text, question=query_text)
model = ChatOpenAI()
response_text = model.predict(prompt)
sources = [doc.metadata.get("source", None) for doc, _score in results]
```
`query_rag.py`'s `answer_question()` mirrors this exactly, adding
`filter={"context_tag": context_tag}` to the `similarity_search_with_relevance_scores`
call, and building `sources` as `[{"source": doc.metadata.get("source"),
"content": doc.page_content} for doc, _score in results]` instead of a bare
filename list.

**Revised prompt template (new, replaces the bare "answer from context" instruction):**
```python
PROMPT_TEMPLATE = """
Answer the question based only on the following context. If the context does
not contain enough information to answer the question, say you don't know —
do not guess or use information outside the context.

{context}

---

Answer the question based on the above context: {question}
"""
```
One added sentence, no persona framing, no multi-part instructions — keeps
the "narratable in one sentence" bar from `CLAUDE.md`.

**Slugify pattern (new, single call site in `ingest.py`):**
```python
import re

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
```
Applied at `ingest.py:9` in place of `customer_name.strip()`:
```python
context_tag = slugify(customer_name)
if not context_tag:
    raise ValueError("customer_name is required")
```
Note: validate `context_tag` truthiness AFTER slugifying (not before) — a
name of e.g. `"---"` strips to `.strip()`-truthy but slugifies to `""`, and
the existing empty-tag guard (mirrored from Phase 2's `run_ingestion()`) must
catch that post-slugify, matching the "block on empty tag" behavior already
established for `set_context_tag()` per `.agents/plans/phase-2-ingestion-logic.md`
lines 73-77.

**`.last_ingest.json` read/write (new, no existing pattern in repo — first use):**
```python
import json
from pathlib import Path

LAST_INGEST_PATH = Path(".last_ingest.json")

def load_last_ingest() -> dict:
    if LAST_INGEST_PATH.exists():
        return json.loads(LAST_INGEST_PATH.read_text())
    return {"folder_path": "", "customer_name": ""}

def save_last_ingest(folder_path: str, customer_name: str) -> None:
    LAST_INGEST_PATH.write_text(json.dumps({"folder_path": folder_path, "customer_name": customer_name}))
```
Keep this inline in `app.py` — it's UI-persistence glue, not RAG logic, and
doesn't warrant its own module (consistent with "cut scope rather than add a
layer that needs its own justification").

**Distinct customer query (new, first use of raw SQL in this repo outside `init.sql`):**
```python
import psycopg
from vector_store import get_psycopg_connection

def list_customers() -> list[str]:
    with psycopg.connect(get_psycopg_connection()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT cmetadata->>'context_tag' FROM langchain_pg_embedding "
                "WHERE cmetadata->>'context_tag' IS NOT NULL ORDER BY 1"
            )
            return [row[0] for row in cur.fetchall()]
```
Mirrors the connection pattern already used in `vector_store.py:44-58`
(`ensure_context_tag_index`) — `with psycopg.connect(...) as conn: with
conn.cursor() as cur:`. Table name `langchain_pg_embedding` and column
`cmetadata` (JSONB) confirmed via `vector_store.py:52-53`.

**Error handling (existing, mirror this):**
`read_local_files.py` raises `FileNotFoundError`/`NotADirectoryError` for bad
folder paths (lines 8-11). `app.py`'s Ingest tab must catch these specific
exceptions (plus a general `Exception` fallback for OpenAI/Postgres
connectivity failures) and render `st.error(str(e))` — never let a raw
traceback reach the Streamlit UI, per PRD §4 "Basic error handling."

### Known Traps

- `docs/LESSONS.md:60-75` ("`PGVector.from_documents([])` doesn't no-op on an
  empty list — it throws") — Already guarded in `ingest.py:14`
  (`if not results:` early return before `save_to_pgvector` is ever called).
  **Do not remove this guard** when adding slugify — the empty-tag check and
  the empty-results check are two separate guards for two separate failure
  modes; both must remain.
- `docs/LESSONS.md:46-58` (OpenAI embeddings TPM limit on large single-batch
  writes) — Not directly triggered by Phase 3 (ingestion batching is
  unchanged), but the Ask tab's `ChatOpenAI()` calls are a NEW per-question
  OpenAI request path. No batching concern here (one question = one small
  request), but note it if manual testing hits rate limits during a rapid
  back-and-forth chat session — that's a rate-limit issue, not a bug in
  `query_rag.py`.
- `docs/ARCHITECTURE.md:77-84` ("Customer name is always explicit user
  input, never inferred") — Do NOT let `app.py` pre-fill the customer-name
  field by guessing from the folder path's basename. `.last_ingest.json`
  persistence is fine (it replays what the user already typed); inference
  from a NEW, never-before-seen folder path is the thing this doc forbids.
- `CLAUDE.md` ("`context_tag` is the *only* mechanism that scopes data to a
  customer... Never add a second scoping mechanism") — The "show slug as-is"
  decision (already made — see conversation) means `app.py` must NOT add a
  `display_name` metadata field or a second lookup table mapping slugs to
  pretty names. The dropdown and banner render the raw `context_tag` string.
- `CLAUDE.md` ("Always work on a feature branch, never commit directly to
  `main`") — Confirm a feature branch (e.g. `streamlit-ui`) is checked out
  BEFORE Task 1 below. Repo is currently on `main`.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation
Add `slugify()` to `ingest.py` and wire it into `run_ingestion()`. This is a
prerequisite for both tabs (Ingest produces slugified tags; Ask must query
for and filter on the same slugified tags), so it must land first and be
independently validated via the existing CLI wrapper before any UI code is
written.

### Phase 2: Core Implementation
Build `query_rag.py` (`answer_question()`) as a standalone, Streamlit-free
module — validate it from a plain Python REPL/script against the real Teva
data already in Postgres (per `STATE.md`, 334 rows already indexed) before
wiring it into any UI.

### Phase 3: Integration
Build `app.py`: Ingest tab wired to `run_ingestion()` +
`.last_ingest.json`, Ask tab wired to `list_customers()` + `query_rag.answer_question()`,
plus the TASC visual theme (`.streamlit/config.toml` + CSS block for pill
labels/banner).

### Phase 4: Testing & Validation
Manual UI walkthrough per PRD §11 Success Criteria: ingest a folder, ask a
question, verify sources show chunk text, verify a mismatched/second
customer never leaks into the first customer's answers, verify persistence
across an app restart.

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and
independently testable.

### CREATE feature branch

- **IMPLEMENT**: `git checkout -b streamlit-ui` from `main` (currently clean,
  up to date with origin per repo state).
- **GOTCHA**: Per `CLAUDE.md`, this must happen before the first edit of this
  plan — do not skip even though this task has no code diff.
- **VALIDATE**: `git branch --show-current` → `streamlit-ui`

### UPDATE `ingest.py`

- **IMPLEMENT**: Add `import re` and a `slugify(name: str) -> str` function
  (lowercase, `[^a-z0-9]+` → `-`, strip leading/trailing `-`). Replace line 9
  (`context_tag = customer_name.strip()`) with
  `context_tag = slugify(customer_name)`. Keep the existing `if not
  context_tag: raise ValueError(...)` guard immediately after — it now also
  catches names that slugify to empty (e.g. `"---"`, `"!!!"`), not just
  originally-empty strings.
- **PATTERN**: `ingest.py:8-11` (current `run_ingestion` opening) — see
  Patterns section above for the exact replacement.
- **IMPORTS**: `re` (stdlib, no requirements.txt change).
- **GOTCHA**: Do not slugify anywhere else (e.g. don't also slugify in
  `app.py` before calling `run_ingestion` — `context_tag` derivation must
  stay in exactly one place, `ingest.py`, per the "single scoping mechanism"
  principle applied to its derivation logic too).
- **VALIDATE**: `python -c "from ingest import slugify; assert slugify('Acme Retail') == 'acme-retail'; assert slugify('  Ac--me!! Co ') == 'ac-me-co'; assert slugify('---') == ''; print('ok')"`

### CREATE `query_rag.py`

- **IMPLEMENT**: `answer_question(question: str, context_tag: str, k: int =
  3, min_relevance: float = 0.7) -> dict`. Mirror `query_data.py`'s flow
  (embeddings → `create_vector_store` → `similarity_search_with_relevance_scores(question,
  k=k, filter={"context_tag": context_tag})` → threshold check → prompt →
  `ChatOpenAI().predict()`), returning
  `{"answer": <str or None>, "sources": [{"source": ..., "content": ...}, ...]}`.
  When no result clears `min_relevance` (or the result list is empty),
  return `{"answer": None, "sources": []}` — caller renders the PRD §7.2
  empty-state message, not `query_rag.py` (keep this module UI-agnostic, no
  `print`/`st.*` calls, unlike `query_data.py` which is a CLI script and
  prints directly).
- **PATTERN**: `query_data.py:1-49` full file — see Patterns section above
  for the exact extension (added `filter` kwarg, richer `sources`, revised
  `PROMPT_TEMPLATE` with the "say you don't know" instruction).
- **IMPORTS**: `from langchain_openai import OpenAIEmbeddings, ChatOpenAI`,
  `from langchain.prompts import ChatPromptTemplate`, `from vector_store
  import create_vector_store` — identical imports to `query_data.py`.
- **GOTCHA**: `query_data.py` uses `model.predict(prompt)` (deprecated
  LangChain API but confirmed working at this pinned version,
  `langchain-openai==0.1.8`) — reuse `.predict()` for consistency with the
  reused reference file rather than migrating to `.invoke()`, since this
  isn't a bug being fixed, just a pattern being extended.
- **VALIDATE**: `python -c "from query_rag import answer_question; r = answer_question('What is this project about?', 'teva-org-streamlining-project'); print(r['answer']); print(len(r['sources']))"`
  (adjust the `context_tag` string to match whatever slug the real Teva data
  was ingested under — check via
  `psql "$(python -c 'from vector_store import get_psycopg_connection as g; print(g())')" -c "SELECT DISTINCT cmetadata->>'context_tag' FROM langchain_pg_embedding;"`
  if unsure, since Phase 2's ingestion ran before slugify existed and may
  have used the raw customer name string as-is).

### CREATE `.streamlit/config.toml`

- **IMPLEMENT**: Set `[theme]` with `primaryColor` (magenta, sampled from
  `TASC-AI-Home-Assignment 2026.pdf`'s pill-label/accent color),
  `backgroundColor` (white/light, matching the PDF's content-card
  background), `secondaryBackgroundColor` (light gray/pink-tinted, matching
  the PDF's callout boxes), `textColor` (dark navy or near-black), and
  `font = "sans serif"`.
- **GOTCHA**: `.streamlit/config.toml` sets base app colors only — it cannot
  produce the pill-shaped labels or the dark navy header bar seen in the PDF.
  Those are handled by a small CSS injection in `app.py` (next task), not
  here.
- **VALIDATE**: `streamlit run app.py` (after `app.py` exists) and visually
  confirm the base background/accent colors match the PDF's palette.

### CREATE `app.py`

- **IMPLEMENT**:
  1. `st.set_page_config(page_title=..., layout="wide")` at the top.
  2. A CSS block (`st.markdown("<style>...</style>", unsafe_allow_html=True)`)
     defining a `.pill-label` class (magenta background, white text, rounded
     `border-radius: 999px`, small padding) and a dark navy `.header-bar`
     class, applied to a page header rendered above `st.tabs`.
  3. `st.tabs(["Ingest", "Ask"])`.
  4. **Ingest tab**: `st.text_input` for folder path and customer name,
     prefilled via `load_last_ingest()`; `st.button("Run Ingestion")` → on
     click: `save_last_ingest(...)`, then `with st.spinner(...):
     result = run_ingestion(customer_name, folder_path)` wrapped in
     `try/except (FileNotFoundError, NotADirectoryError, ValueError) as e:
     st.error(str(e))` plus a broad `except Exception as e: st.error(...)`
     fallback for OpenAI/Postgres connectivity issues; on success, branch on
     `result["chunks_saved"] == 0` (PRD's "no ingestible files" case) vs.
     `st.success(f"{result['files_read']} files read, {result['chunks_saved']} chunks saved.")`.
  5. **Ask tab**: call `list_customers()`; if empty, show a message ("No
     customers ingested yet — use the Ingest tab first") and stop (no
     dropdown). Otherwise `st.selectbox` for customer choice, stored in
     `st.session_state["context_tag"]`; on change, reset
     `st.session_state["messages"] = []` (PRD §7.2: switching customers
     resets chat history). Once selected, render a persistent banner (using
     the `.pill-label`/banner CSS class) reading `f"Asking about: {context_tag}"`.
     Then a standard `st.chat_message` loop over `st.session_state["messages"]`,
     `st.chat_input(...)` at the bottom → on submit, append the user message,
     call `query_rag.answer_question(question, context_tag)`, append the
     assistant message. If `result["answer"] is None`, render the PRD
     empty-state message instead of a chat bubble. Otherwise render the
     answer, then a "Sources" section listing each `source["source"]`
     (filename) with its `source["content"]` shown underneath (e.g. inside
     an `st.expander` or blockquote per source) — this is the "show the
     retrieved chunk text" decision from the conversation, not a file
     location/page number.
- **PATTERN**: See all four inline code patterns in the Patterns section
  above (`.last_ingest.json` helpers, `list_customers()`, the
  `run_ingestion`/`answer_question` call sites).
- **IMPORTS**: `streamlit as st`, `json`, `pathlib.Path`, `psycopg`,
  `from ingest import run_ingestion`, `from query_rag import answer_question`,
  `from vector_store import get_psycopg_connection`.
- **GOTCHA**: Streamlit reruns the entire script top-to-bottom on every
  interaction — `run_ingestion()` must only be called inside the button's
  `if st.button(...):` block, never at module level, or it would re-run on
  every widget interaction anywhere in the app. Same for
  `answer_question()` — only inside the `if user_input := st.chat_input(...):`
  block.
- **VALIDATE**: `streamlit run app.py` — manual walkthrough (see Level 4
  below).

---

## TESTING STRATEGY

### Unit Tests
None planned — per `docs/ARCHITECTURE.md` ("Gap: no automated tests"), this
is a documented, deliberate scope gap for the 2-day budget. `slugify()` and
`answer_question()` are validated via the inline `python -c` commands in the
Step-by-Step Tasks above, not a pytest suite.

### Integration Tests
None — manual verification only, consistent with the existing project-wide
approach (`PRD.md` §11).

### Edge Cases
- Empty/whitespace-only customer name → `slugify()` returns `""` →
  `ValueError` raised → `app.py` shows `st.error`, not a crash.
- Customer name that collides after slugifying with an existing customer
  (e.g. "Acme Retail" and "ACME RETAIL" both → `acme-retail`) — **accepted
  behavior per decision already made in conversation**: silent merge, no
  collision warning. Do not add detection/warning logic for this in Phase 3.
- Folder path that doesn't exist → `FileNotFoundError` from
  `read_local_files()` (via `run_ingestion()`) → caught, shown as
  `st.error`.
- Folder with zero ingestible files → `run_ingestion()` returns
  `{"files_read": 0, "chunks_saved": 0}` → `app.py` shows a distinct
  "no ingestible files found" message, not a success/failure ambiguity.
- Ask tab with zero customers ingested yet → `list_customers()` returns
  `[]` → dropdown/chat hidden, guidance message shown instead (PRD §7.2
  "chat interface itself is not rendered until a customer is chosen" implies
  the empty-list case must be handled distinctly too, even though PRD
  doesn't spell this exact sub-case out).
- Question with no result clearing `min_relevance` → `answer_question()`
  returns `{"answer": None, "sources": []}` → empty-state message rendered,
  not an empty chat bubble.
- Two different customers, same question → must return different, correctly
  `context_tag`-scoped answers (PRD §11 core isolation check) — manual test
  only if a second real customer folder is available; otherwise this is
  already covered by the isolation testing done in Phase 1/2 (per
  `STATE.md`), and Phase 3 doesn't need to re-derive that proof, only not
  break it (the `filter={"context_tag": ...}` kwarg is the only new
  isolation-relevant code, and it's exercised by every single Ask-tab query).

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and feature correctness.

### Level 1: Syntax & Style
```bash
python -m py_compile app.py query_rag.py ingest.py
```

### Level 2: Unit Tests
```bash
python -c "from ingest import slugify; assert slugify('Acme Retail') == 'acme-retail'; assert slugify('---') == ''; print('slugify ok')"
```

### Level 3: Integration Tests
```bash
# Confirm run_ingestion still works end-to-end with the new slugify step,
# against the existing real Teva folder (path per STATE.md):
python ingest.py --customer "Teva Org Streamlining Project" --folder "/Users/maayanchen/Code/Work/Teva_Org_Streamlining_Project"
# Then confirm the resulting context_tag is the slugified form:
psql "$(python -c 'from vector_store import get_psycopg_connection as g; print(g())')" -c "SELECT DISTINCT cmetadata->>'context_tag' FROM langchain_pg_embedding;"
```

### Level 4: Manual Validation
1. `docker compose up --build` (or run Postgres via compose + `streamlit run
   app.py` locally, matching however Phase 1/2 were validated).
2. Ingest tab: enter a real customer folder + name, click "Run Ingestion",
   confirm the success message shows correct files-read/chunks-saved counts.
3. Restart the app (`streamlit run app.py` again) — confirm the Ingest tab's
   fields are prefilled from `.last_ingest.json`.
4. Ask tab: confirm the customer dropdown lists the slugified tag; confirm
   no chat box appears before a customer is selected.
5. Select the customer, confirm the "Asking about: <tag>" banner appears and
   persists while chatting.
6. Ask a real question, confirm a grounded answer appears with a "Sources"
   section showing filename + the actual retrieved chunk text underneath
   each source (not a page/character-location number).
7. Ask an unrelated/nonsense question, confirm the empty-state message
   appears instead of a hallucinated answer.
8. If a second customer folder is available: ingest it under a different
   name, switch the Ask-tab dropdown, confirm chat history resets and a
   shared question returns a different, correctly-scoped answer.
9. Visually compare the running app against
   `TASC-AI-Home-Assignment 2026.pdf` — confirm the navy/magenta palette and
   pill-shaped labels are recognizably applied, not necessarily pixel-exact.

---

## ACCEPTANCE CRITERIA

- [ ] `slugify()` added to `ingest.py`, applied as the sole `context_tag`
      derivation point, empty-after-slugify still raises `ValueError`
- [ ] `query_rag.py` created, `answer_question()` filters by `context_tag`,
      returns `None` answer + empty sources on low relevance, returns full
      chunk text (not just filenames) per source
- [ ] Revised prompt template instructs the model to say "I don't know" on
      insufficient context
- [ ] `app.py` created with Ingest tab (folder + name inputs,
      `.last_ingest.json` persistence, `run_ingestion()` wired, clean error
      handling) and Ask tab (customer dropdown gating chat visibility,
      persistent banner, chat loop, sources with chunk text)
- [ ] `.streamlit/config.toml` applies the TASC navy/magenta palette; pill
      labels/banner styled via CSS block in `app.py`
- [ ] All validation commands pass with zero errors
- [ ] No regressions in existing functionality (`ingest.py` CLI wrapper,
      `query_data.py` reference script, `vector_store.py`/`create_database.py`
      unchanged)
- [ ] Manual UI walkthrough (Level 4) completed end-to-end
- [ ] `context_tag` remains the sole customer-scoping mechanism — no
      `display_name` field, no second lookup table, no collision-detection
      logic added

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed immediately
- [ ] All validation commands executed successfully
- [ ] No linting or type checking errors (`py_compile` clean)
- [ ] Manual testing confirms the feature works
- [ ] Acceptance criteria all met

---

## NOTES

**Deliberately deferred / out of scope for this plan:**
- Per-format source location (PDF page number, xlsx sheet/row, pptx slide
  number) — considered and rejected in favor of showing full chunk text,
  which sidesteps the fact that "location" is meaningless or inconsistent
  across `.txt`/`.pdf`/`.xlsx`/`.pptx`/OCR'd-image chunks. Revisit only if
  a reviewer specifically asks for page/slide numbers.
- Slug-collision detection/preview UI — explicitly decided against in favor
  of silent slugification; two typed names that normalize to the same slug
  will silently share one customer's data. This is a conscious tradeoff, not
  an oversight — documented here so it isn't "fixed" without a deliberate
  re-decision, per this project's own `docs/ARCHITECTURE.md` convention.
- Storing a human-readable `display_name` separate from `context_tag` —
  rejected to keep `context_tag` the single scoping/display mechanism
  end-to-end (`CLAUDE.md`).
- Automated tests (pytest) — consistent with the project-wide documented gap
  in `docs/ARCHITECTURE.md`.
- A second real customer folder for isolation demo — "nice-to-have, not
  required" per PRD §12 Phase 3; Task list above treats it as optional
  manual validation (Level 4, step 8), not a blocking task.
- `query_data.py` is left completely unchanged — it remains the Nivs-RAG
  reference CLI script; `query_rag.py` is a new, separate module, not a
  refactor of it, per `CLAUDE.md`'s "don't refactor working reference code
  without a reason."

**Open item to confirm during implementation, not before:** the exact
`context_tag` value already in Postgres for the real Teva data ingested in
Phase 2 (per `STATE.md`, ingested BEFORE `slugify()` existed, so it may be
the raw customer name string, not a slugified form). The Level 3 validation
command above includes a `psql` check to confirm this — if the existing rows
carry a non-slugified tag, a fresh `run_ingestion()` call for the same
customer name will now produce a DIFFERENT (slugified) tag, effectively
starting a new "customer" in the dropdown rather than adding to the existing
334 rows. This is expected and acceptable (slugify changes tag derivation
going forward; it does not retroactively migrate existing rows), but should
be visible during manual testing, not silently confusing.
