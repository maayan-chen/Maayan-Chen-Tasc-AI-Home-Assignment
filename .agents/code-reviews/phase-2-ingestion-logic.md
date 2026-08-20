# Code Review: Phase 2 — Ingestion Logic

**Stats:**
- Files Modified: 0
- Files Added: 2 (`read_local_files.py`, `ingest.py`) + 2 process files
  (`.agents/plans/phase-2-ingestion-logic.md`,
  `.agents/execution-reports/phase-2-ingestion-logic.md`)
- New lines: 71 (code) — `read_local_files.py` 29, `ingest.py` 42
- Deleted lines: 0

---

## Issues

```
severity: high
file: ingest.py
line: 13-20
issue: A folder with zero ingestible files crashes with a raw IntegrityError instead of a clean result.
detail: When read_local_files() returns an empty list (empty folder, or a
  folder containing only files that all fail extraction), `documents` and
  `chunks` are both `[]`. `save_to_pgvector([], pre_delete_collection=False)`
  → `PGVector.from_documents([], ...)` does not short-circuit on an empty
  list — it still issues an INSERT, which fails with
  `psycopg.errors.NotNullViolation: null value in column "id"` (verified by
  reproduction below). This is exactly the edge case the plan called out
  ("Edge Cases" section: "A folder containing only unsupported/unparseable
  files... verify this doesn't raise inside PGVector.from_documents on an
  empty list... run_ingestion should catch and report '0 files were
  ingestible' rather than propagate a confusing library-internal error") but
  the guard was never implemented. A future caller (the Phase 3 Streamlit UI)
  would surface this SQL/library exception directly to a non-technical
  consultant instead of a message like "no ingestible files found."
  Reproduced directly:
    mkdir /tmp/empty_test_folder
    python -c "from ingest import run_ingestion; run_ingestion('X', '/tmp/empty_test_folder')"
    # -> IntegrityError (psycopg.errors.NotNullViolation) null value in column "id"
suggestion: In run_ingestion(), after computing `documents` (or `chunks`),
  check `if not documents: return {"files_read": 0, "chunks_saved": 0}` (with
  a printed message, e.g. "No ingestible files found in <folder_path>.")
  before calling split_text/save_to_pgvector. This matches the plan's
  specified behavior exactly and requires no changes to
  vector_store.py/create_database.py.
```

No other issues found. Everything else checked out:

- **`context_tag` scoping**: `run_ingestion()` validates `customer_name`
  truthiness *before* calling `read_local_files()` (fail-fast, no wasted I/O
  on an invalid tag) and passes it verbatim to `set_context_tag()` — no
  slugify step, matching `docs/ARCHITECTURE.md`'s "Customer name is always
  explicit user input, never inferred" and the plan's explicit requirement.
  Verified live: empty and whitespace-only `customer_name` both raise
  `ValueError` before any folder walk; a real ingestion run left 0 rows with
  a null `context_tag` in Postgres.
- **Additive writes**: `save_to_pgvector(chunks, pre_delete_collection=False)`
  is hardcoded, not left at `create_database.py`'s default (`True`) — matches
  `PRD.md` §4 "Ingestion is additive/incremental." Verified live: running the
  CLI twice for the same customer produced 334 rows (167×2), not an
  overwrite.
- **Extraction dispatch not duplicated**: `read_local_files()` correctly
  delegates all extension handling to `extract_content_from_bytes()`
  (`vector_store.py`) rather than re-implementing a file-type check, avoiding
  the two-places-to-agree problem the plan warned against.
- **`ContentExtractionError` handling**: caught narrowly, not a bare
  `except Exception` — a bug inside `extract_content_from_bytes` (e.g. a
  typo) would still propagate and fail loudly rather than being silently
  treated as "unsupported file," matching the plan's stated intent.
- **Recursive walk**: uses `rglob("*")`, not `glob("*")` — correct for
  folders with subfolders, not just the flat Teva test case.
- **Dotfile handling**: `p.name.startswith(".")` correctly filters
  `.DS_Store` and other dotfiles before they ever reach
  `extract_content_from_bytes()`, avoiding confusing "unsupported file type"
  skip lines for junk files. Verified: no skip line was printed for
  `.DS_Store` during the real Teva folder run.
- **No LLM/relevance judgment in ingestion**: no LLM calls anywhere in either
  file — matches `docs/ARCHITECTURE.md`'s "No LLM-driven relevance filtering
  at ingestion" and "No LLM/agent step in ingestion."
- **`vector_store.py`/`create_database.py` unchanged**: confirmed via `git
  diff` — no modifications to reused reference code, matching `CLAUDE.md`'s
  "don't refactor working reference code without a reason" and the plan's
  explicit "do NOT fix `set_context_tag()`" instruction (its silent no-op on
  falsy `context_tag` is correctly made unreachable by validating in
  `ingest.py` instead).
- **No security issues**: no SQL/command construction from user input in
  either file (all DB writes go through existing parameterized
  `PGVector`/LangChain calls); `customer_name`/`folder_path` are used as
  plain string values, not interpolated into any query or shell command.
- **No swallowed errors**: the one `except` (`ContentExtractionError`) prints
  the file path and the original exception's message before continuing — the
  diagnostic isn't discarded.
- **Type hints**: present and consistent with the rest of the codebase
  (`create_database.py`, `vector_store.py`, `query_data.py` all use similar
  partial type-hinting, no stricter standard to match here).
