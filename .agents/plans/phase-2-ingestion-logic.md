# Feature: Phase 2 — Ingestion Logic (`read_local_files.py` + `ingest.py`)

The following plan should be complete, but it's important that you validate
documentation, codebase patterns, and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import
from the right files.

## Feature Description

Get a real customer project folder from disk into Postgres/pgvector with the
correct `context_tag`, using two new, deterministic (no-LLM, no-agent) Python
modules: `read_local_files.py` (file discovery + content extraction) and
`ingest.py` (orchestration + CLI wrapper). This is Phase 2 of the PRD — the
last piece before the Streamlit UI (Phase 3) exists.

## User Story

As a departing consultant
I want to point a CLI command at my project folder and type the customer's name
So that everything in that folder is chunked, tagged, and searchable before I hand off — testable from a terminal before any UI exists

## Problem Statement

The RAG base (`vector_store.py`, `create_database.py`) and the extended
`extract_content_from_bytes()` (docx/xlsx/pptx/OCR) are verified and working
in isolation, but nothing yet walks a real folder end-to-end, applies a
customer's `context_tag`, and writes to Postgres without wiping prior
customers' data. There's also a live correctness bug in the reused
`set_context_tag()`: it silently no-ops on an empty tag rather than blocking
the write, which is exactly the kind of silent trust-boundary failure this
project can't tolerate.

## Solution Statement

`read_local_files(folder_path)` recursively walks the folder, reads each
file's raw bytes, and calls the already-extended
`vector_store.extract_content_from_bytes()` per file, skipping (not erroring)
files that fail extraction — logging each skip with a reason. `ingest.py`'s
`run_ingestion(customer_name, folder_path)` validates inputs (folder exists,
`context_tag` non-empty — the customer name IS the tag verbatim, no
slugifying), wraps extracted content into LangChain `Document`s, and calls
the existing `split_text()` → `set_context_tag()` →
`save_to_pgvector(..., pre_delete_collection=False)` pipeline unchanged. A
thin `argparse` CLI (`--customer`, `--folder`) makes this testable from a
terminal today, ahead of the Phase 3 Streamlit UI.

## Feature Metadata

**Feature Type**: New Capability
**Estimated Complexity**: Low
**Primary Systems Affected**: Ingestion pipeline (new files only — no changes
to `vector_store.py` or `create_database.py`)
**Dependencies**: None new — reuses `langchain.schema.Document`,
`create_database.split_text`/`set_context_tag`/`save_to_pgvector`,
`vector_store.extract_content_from_bytes`/`ContentExtractionError`, all
already in `requirements.txt`.

---

## CONTEXT REFERENCES

### Relevant Codebase Files — READ THESE BEFORE IMPLEMENTING

- `vector_store.py:166-188` (`extract_content_from_bytes`) — Why: the single
  entry point `read_local_files()` must call per file; already dispatches on
  extension (`pdf`/`png`/`jpg`/`jpeg`/`docx`/`xlsx`/`pptx`/fallback UTF-8) and
  raises `ContentExtractionError` (line 20-21) for anything that fails —
  that's the exception type to catch-and-skip on.
- `create_database.py:32-48` (`split_text`, `set_context_tag`) — Why: reuse
  unchanged. `split_text` uses `RecursiveCharacterTextSplitter(chunk_size=300,
  chunk_overlap=100, add_start_index=True)` on `list[Document]`.
  `set_context_tag` (lines 51-56) is the function with the bug: `if not
  context_tag: return chunks` silently no-ops instead of blocking — **do not
  fix this function** (it's reused RAG-base code per `CLAUDE.md`); instead
  validate `context_tag` truthiness in `ingest.py` *before* calling it, so the
  no-op path is simply never reachable with an empty tag.
- `create_database.py:59-61` (`save_to_pgvector`) — Why: signature is
  `save_to_pgvector(chunks, pre_delete_collection=True)`. **Must be called
  with `pre_delete_collection=False`** from `ingest.py` — the default `True`
  wipes the entire shared collection (all customers), which directly
  contradicts PRD §4 "Ingestion is additive/incremental."
- `create_database.py:22-29` (`load_documents`, `load_documents_from_path`) —
  Why: shows the existing `Document`-producing pattern
  (`langchain_community.document_loaders.DirectoryLoader`) that
  `read_local_files()` deliberately does NOT reuse — `DirectoryLoader` calls
  `unstructured` under the hood, which only handles a narrow set of types and
  doesn't know about the OCR/docx/xlsx/pptx extraction already built into
  `extract_content_from_bytes()`. `read_local_files()` needs its own walk +
  raw-bytes read, not `DirectoryLoader`.
- `docs/LESSONS.md:46-58` — Why: documents the OpenAI embeddings TPM limit
  (40,000 TPM on this account) tripped by `PGVector.from_documents()`
  embedding all chunks in one unbatched call. Real customer folders may
  exceed this. Per the agreed approach: **do not pre-emptively batch** —
  Task 5 below is to run `run_ingestion()` against the real Teva folder and
  observe whether it actually trips the limit before adding any batching
  logic.
- `docs/ARCHITECTURE.md:36-43` (No LLM-driven relevance filtering) — Why:
  confirms nothing in `read_local_files()`/`run_ingestion()` should judge
  file relevance — every readable file is ingested unconditionally.
- `docs/ARCHITECTURE.md:110-123` (Images always OCR'd) — Why: confirms
  `read_local_files()` must not add its own "is this image text-like" check
  before calling `extract_content_from_bytes()` — that decision already lives
  inside `extract_content_from_bytes()`.
- `PRD.md:75-92` (§4 In Scope, Core Functionality) — Why: canonical list of
  supported extensions (`.txt`/`.md`/`.pdf`/`.docx`/`.xlsx`/`.pptx`/
  `.png`/`.jpg`/`.jpeg`) and the "additive, never reset" requirement.
- `PRD.md:317-338` (§7.1 Ingest Tab steps 4-7) — Why: the exact pipeline order
  `run_ingestion()` must follow (read → wrap as `Document` → chunk → tag →
  save → report counts), so `app.py` in Phase 3 can call `run_ingestion()`
  directly without re-deriving this order.

### New Files to Create

- `read_local_files.py` — `read_local_files(folder_path: str) ->
  list[tuple[str, str]]`: recursively walks `folder_path`, returns a list of
  `(page_content, source_path)` pairs for every file that extracted
  successfully; prints one line per skipped file with the reason.
- `ingest.py` — `run_ingestion(customer_name: str, folder_path: str) ->
  dict` (files read, files skipped, chunks saved) + `if __name__ ==
  "__main__":` `argparse` CLI wrapper (`--customer`, `--folder`).

### Patterns to Follow

**Error handling (existing, mirror this):**
```python
# vector_store.py:20-21
class ContentExtractionError(Exception):
    """Raised when a file's content can't be extracted as usable text."""
```
`read_local_files()` catches this specific exception type per-file — nothing
broader (a bare `except Exception` would also swallow real bugs like a typo
in `extract_content_from_bytes`, which is not what "skip unsupported files"
means).

**Document construction (existing pattern to mirror, from PRD §7.1 step 5):**
```python
Document(page_content=..., metadata={"source": ..., "context_tag": ...})
```
Note `context_tag` is set via `set_context_tag()` (already handles this loop,
`create_database.py:51-56`), so `ingest.py` only needs
`metadata={"source": source_path}` when constructing `Document`s;
`set_context_tag()` adds the tag afterward, same as `create_database.py`'s
own flow does for `metadata["source"]` via `DirectoryLoader`.

**CLI wrapper pattern (existing, mirror from `query_data.py:18-23`):**
```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(...)
    args = parser.parse_args()
    ...

if __name__ == "__main__":
    main()
```

**Naming conventions:** snake_case functions/files, no classes for this kind
of orchestration code (matches `create_database.py`, `vector_store.py`,
`query_data.py` — all plain functions, no classes except the one custom
exception).

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation
Confirm `python-docx`/`openpyxl`/`python-pptx`/`pytesseract` extraction
already works standalone (it does — verified in `STATE.md`); no new
dependencies needed for this phase.

### Phase 2: Core Implementation
Write `read_local_files.py` (pure file I/O + extraction, no DB/embedding
calls — independently testable). Then write `ingest.py`, which imports
`read_local_files` and wires it to the existing `create_database.py`
pipeline.

### Phase 3: Integration
None required — both new files are leaf consumers of existing modules; no
existing file needs to change.

### Phase 4: Testing & Validation
Manual verification only (per `docs/ARCHITECTURE.md`'s documented "Gap: no
automated tests" scope decision) — run the CLI wrapper against the real Teva
folder, inspect Postgres via `psql`, run a `context_tag`-filtered query.

---

## STEP-BY-STEP TASKS

### Task 1: CREATE `read_local_files.py`

- **IMPLEMENT**: `read_local_files(folder_path: str) -> list[tuple[str,
  str]]`. Validate `folder_path` exists and is a directory (raise
  `NotADirectoryError`/`FileNotFoundError` with a clear message if not — this
  is the "bad folder path" error case from PRD §4/§11). Recursively enumerate
  files with `Path(folder_path).rglob("*")`, filtering to
  `p.is_file()`. Skip macOS/system junk files by name up front
  (`.DS_Store`, and any dotfile — `p.name.startswith(".")`) before attempting
  extraction, so they never reach `extract_content_from_bytes()` and don't
  produce a confusing "unsupported file type" skip line. For each remaining
  file: read raw bytes (`p.read_bytes()`), call
  `vector_store.extract_content_from_bytes(raw_bytes, source=str(p))` inside
  a `try/except ContentExtractionError as e`. On success, append
  `(content, str(p))` to the results list. On `ContentExtractionError`, print
  `f"Skipped {p}: {e}"` and continue the loop (per the confirmed "print a
  skip line per file" decision) — do not let one bad file abort the run.
- **PATTERN**: `vector_store.py:20-21` for the exception type;
  `vector_store.py:166-188` for the function this wraps.
- **IMPORTS**: `from pathlib import Path`; `from vector_store import
  extract_content_from_bytes, ContentExtractionError`.
- **GOTCHA**: Do NOT use `glob("*")` (non-recursive) — real customer folders
  may have subfolders even though the current Teva test folder happens to be
  flat; `rglob` is required for correctness, not just to match the test data.
  Do NOT filter by extension before calling `extract_content_from_bytes()` —
  that function already owns the extension dispatch (line 167); duplicating
  the extension list here would create two places that need to agree on
  supported types.
- **VALIDATE**: `python -c "from read_local_files import read_local_files; results = read_local_files('/Users/maayanchen/Code/Work/Teva_Org_Streamlining_Project'); print(len(results)); print([r[1] for r in results])"`
  — expect 10 files read (11 files in folder minus `.DS_Store` skipped), each
  `source` path present, and non-empty `page_content` for each (spot-check
  the Hebrew docx/xlsx/pptx and the two PNG screenshots aren't empty strings).

### Task 2: CREATE `ingest.py` — input validation + `run_ingestion()` skeleton

- **IMPLEMENT**: `run_ingestion(customer_name: str, folder_path: str) ->
  dict`. First validate `customer_name.strip()` is non-empty — raise
  `ValueError("customer_name is required")` if not. This is the fix for the
  `set_context_tag()` silent-no-op bug: by guaranteeing `context_tag` is
  always truthy before it ever reaches `set_context_tag()`, that function's
  `if not context_tag: return chunks` branch becomes unreachable from this
  code path, without touching the reused `create_database.py` file. Do NOT
  slugify `customer_name` — the raw typed string (post-`.strip()`) IS the
  `context_tag`, verbatim, per the confirmed decision (no transformation
  step to defend in an interview).
- **PATTERN**: Fail-fast validation before any expensive work — mirrors the
  "validate folder path" step in Task 1, done here again at the
  `run_ingestion` boundary since `read_local_files` and `run_ingestion` must
  each be independently correct (defense in depth, not redundant — a future
  caller of `read_local_files()` directly still gets the folder check).
- **IMPORTS**: `from pathlib import Path`; `from read_local_files import
  read_local_files`.
- **GOTCHA**: Validate `context_tag` truthiness BEFORE calling
  `read_local_files()`, not after — no point reading/extracting an entire
  customer folder only to reject it for a missing customer name.
- **VALIDATE**: `python -c "from ingest import run_ingestion; run_ingestion('', '/tmp')"`
  should raise `ValueError` immediately (no folder walk attempted — add a
  temporary print inside `read_local_files` if needed to confirm it's never
  called, then remove the print).

### Task 3: ADD chunk/tag/save wiring to `run_ingestion()`

- **IMPLEMENT**: After validation, call `read_local_files(folder_path)` →
  build `documents = [Document(page_content=content, metadata={"source":
  source}) for content, source in results]`. Call `chunks =
  split_text(documents)`. Call `chunks = set_context_tag(chunks,
  customer_name)`. Call `save_to_pgvector(chunks,
  pre_delete_collection=False)` — **the `False` is mandatory, do not use the
  `create_database.py` default**. Return a summary dict: `{"files_read":
  len(documents), "chunks_saved": len(chunks)}`. Print a human-readable
  summary line too (e.g. `f"Ingested {len(documents)} files into
  {len(chunks)} chunks for context_tag='{customer_name}'"`) — this doubles as
  the CLI's terminal output and the return value `app.py` will use in Phase 3
  for its success message.
- **PATTERN**: `PRD.md:317-338` §7.1 steps 5-7 for the exact call order;
  `create_database.py:16-19` (`generate_data_store`) for how these three
  calls chain together today (note: that function hardcodes
  `pre_delete_collection=True` — `run_ingestion` must NOT mirror that part).
- **IMPORTS**: `from langchain.schema import Document`; `from
  create_database import split_text, set_context_tag, save_to_pgvector`.
- **GOTCHA**: `set_context_tag`'s signature takes `context_tag: str | None`
  positionally as the second arg (`create_database.py:51`) — pass
  `customer_name` (already validated non-empty in Task 2), not a derived
  slug.
- **VALIDATE**: `python -c "from ingest import run_ingestion; result = run_ingestion('Teva Org Streamlining', '/Users/maayanchen/Code/Work/Teva_Org_Streamlining_Project'); print(result)"`
  — expect a dict with `files_read: 10` and some positive `chunks_saved`
  count; no `RateLimitError` (if one occurs, see Task 5 — do not silently
  add batching yet, first confirm and report it).

### Task 4: ADD `argparse` CLI wrapper to `ingest.py`

- **IMPLEMENT**: `if __name__ == "__main__":` block:
  ```python
  parser = argparse.ArgumentParser()
  parser.add_argument("--customer", required=True, help="Customer name (used verbatim as context_tag)")
  parser.add_argument("--folder", required=True, help="Path to the customer's project folder")
  args = parser.parse_args()
  run_ingestion(args.customer, args.folder)
  ```
- **PATTERN**: `query_data.py:18-23` — same `argparse` shape, adapted for two
  required flags instead of one positional arg (matches the `python ingest.py
  --customer "<name>" --folder /path` usage already documented in
  `README.md:26`).
- **IMPORTS**: `import argparse`.
- **GOTCHA**: `--customer`/`--folder` must be `required=True` — there's no
  sensible default for either (unlike `query_data.py`'s single positional
  arg), and a missing customer name is exactly the bug Task 2 exists to
  prevent.
- **VALIDATE**: `python ingest.py --customer "Teva Org Streamlining" --folder /Users/maayanchen/Code/Work/Teva_Org_Streamlining_Project`
  run from the repo root (with `.env`/Postgres up via `docker compose up -d
  postgres`) — should print the skip line for `.DS_Store`, then the final
  summary line, with exit code 0.

### Task 5: VALIDATE end-to-end against real Postgres + observe TPM behavior

- **IMPLEMENT**: No code change — this is the Phase 2 acceptance run. Start
  Postgres (`docker compose up -d postgres`), run the Task 4 CLI command for
  real, then inspect rows via `psql` (see Validation Commands below). If a
  `RateLimitError` occurs during `save_to_pgvector`, **stop and report it**
  rather than immediately adding batching — per the agreed approach, batching
  is only justified if this real run actually trips the 40k TPM limit
  (`docs/LESSONS.md:46-58`), and if it does, that becomes a new, separately
  time-boxed task rather than speculative work folded into this plan.
- **PATTERN**: `docs/LESSONS.md:46-58` for exactly what a TPM failure looks
  like (`RateLimitError: tokens per minute (TPM): Limit 40000, Requested
  ...`) so it's recognizable if it happens.
- **VALIDATE**: See "Level 4: Manual Validation" below.

---

## TESTING STRATEGY

### Unit Tests
None — matches the project's documented scope gap (`docs/ARCHITECTURE.md`
"Gap: no automated tests"). Verification is manual, via the VALIDATE command
under each task above plus the Level 4 checks below.

### Integration Tests
None (same reason). The Task 5 end-to-end run against real Postgres +
OpenAI is the closest equivalent this project scopes for.

### Edge Cases
- Empty `customer_name` (including whitespace-only, e.g. `"   "`) →
  `ValueError`, no folder walk, no DB write. (Task 2)
- Nonexistent `folder_path` → clear error, not a stack trace surfaced
  raw to a future Streamlit UI. (Task 1)
- A folder containing only unsupported/unparseable files → `read_local_files`
  returns an empty list; `run_ingestion` should still complete without
  crashing on `split_text([])`/`save_to_pgvector([])` — verify this doesn't
  raise inside `PGVector.from_documents` on an empty list (check behavior
  during Task 3's validation; if it does raise, `run_ingestion` should catch
  and report "0 files were ingestible" rather than propagate a confusing
  library-internal error).
- `.DS_Store` / dotfiles present (confirmed present in the real Teva
  folder) → skipped before extraction is even attempted, no
  `ContentExtractionError` noise for these. (Task 1)
- Re-running `run_ingestion` twice for the same customer → both runs' chunks
  should coexist (additive, `pre_delete_collection=False`) — not required to
  test in this phase (PRD user story 5 / Phase 3 concern) but the
  `False` argument in Task 3 is what makes it possible later.

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```bash
python -m py_compile read_local_files.py ingest.py
```

### Level 2: Unit Tests
N/A — no test suite in this project (documented scope gap).

### Level 3: Integration Tests
N/A — covered by Level 4 manual validation below.

### Level 4: Manual Validation
```bash
# 1. Start Postgres only (app container not needed for CLI testing)
docker compose up -d postgres

# 2. Run ingestion against the real Teva folder
python ingest.py --customer "Teva Org Streamlining" \
  --folder /Users/maayanchen/Code/Work/Teva_Org_Streamlining_Project

# 3. Confirm rows landed with the correct context_tag
docker compose exec postgres psql -U raguser -d ragdb -c \
  "SELECT cmetadata->>'context_tag' AS tag, count(*) FROM langchain_pg_embedding GROUP BY 1;"
# Expect one row: tag = "Teva Org Streamlining", count > 0

# 4. Confirm no untagged rows ever landed (validates Task 2's fail-fast guard)
docker compose exec postgres psql -U raguser -d ragdb -c \
  "SELECT count(*) FROM langchain_pg_embedding WHERE cmetadata->>'context_tag' IS NULL;"
# Expect 0

# 5. Scoped query sanity check via existing query_data.py
python query_data.py "What is this engagement about?"
# Expect a grounded answer citing one of the real Teva filenames as a source
```

---

## ACCEPTANCE CRITERIA

- [ ] `read_local_files()` recursively finds files in nested folders (not
      just flat), correctly handling the current flat Teva folder as one
      valid case, not the only case
- [ ] Files that fail extraction are skipped with a printed reason, not
      fatal to the run
- [ ] `.DS_Store`/dotfiles never reach `extract_content_from_bytes()`
- [ ] Empty/whitespace-only `customer_name` blocks the entire run before any
      file I/O or DB write — verified no untagged rows are ever possible
- [ ] `customer_name` is used verbatim as `context_tag` — no slugify step
      anywhere in the code
- [ ] `save_to_pgvector` is called with `pre_delete_collection=False`
      (additive, never wipes other customers)
- [ ] CLI wrapper runs via `python ingest.py --customer ... --folder ...`
      and exits 0 against the real Teva folder
- [ ] `psql` confirms all inserted rows carry the typed `context_tag`, zero
      rows with a null tag
- [ ] `query_data.py` returns a grounded, sourced answer after ingestion
- [ ] No changes made to `vector_store.py` or `create_database.py`

---

## COMPLETION CHECKLIST

- [ ] Tasks 1-5 completed in order
- [ ] Each task's VALIDATE command passed before moving to the next
- [ ] Level 4 manual validation full sequence passed
- [ ] `STATE.md` updated (only if user requests it, per `CLAUDE.md`'s
      "Never update context files unless asked")

---

## NOTES

- **Deferred, not forgotten — TPM batching.** `docs/LESSONS.md` already
  documents this risk from the `alice_in_wonderland.md` test (801 chunks,
  45,575 tokens, over the 40k limit). This plan deliberately does NOT
  pre-batch `save_to_pgvector` calls; Task 5 is the real-world test of
  whether the ~10-file Teva folder (mixed docx/xlsx/pptx/pdf/2 OCR'd images)
  actually trips it. If it does, batching is a follow-up task, not part of
  this plan's scope — added only once proven necessary, consistent with
  this project's "prove the need before adding complexity" approach
  discussed with the user.
- **No customer-name normalization.** Per explicit user decision, the Ask
  tab's future customer dropdown (Phase 3) will show `context_tag` values
  exactly as typed — "Acme Retail" and "acme retail" are different
  customers. This is a Phase 3/UI concern, not something to solve here, but
  worth remembering when building the dropdown later.
- **`set_context_tag()` is intentionally left unmodified.** The bug (silent
  no-op on falsy `context_tag`) is real, but the fix lives in `ingest.py`'s
  input validation (Task 2), not in the reused `create_database.py` file —
  consistent with `CLAUDE.md`'s "don't refactor working reference code
  without a reason."
- **Why not reuse `DirectoryLoader`/`load_documents_from_path()`:** it's
  `unstructured`-backed and doesn't know about the custom OCR/docx/xlsx/pptx
  extraction logic already built and validated in
  `extract_content_from_bytes()` — using it here would silently bypass all
  of Phase 1.5's work for any non-`.md` file.
