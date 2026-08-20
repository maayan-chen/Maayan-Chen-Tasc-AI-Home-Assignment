# Execution Report: Phase 2 — Ingestion Logic

## Meta Information

- Plan file: `.agents/plans/phase-2-ingestion-logic.md`
- Files added:
  - `read_local_files.py` (29 lines)
  - `ingest.py` (42 lines)
- Files modified: none (`vector_store.py`/`create_database.py` untouched, as
  required)
- Lines changed: +71 -0

## Validation Results

- Syntax & Linting: ✓ `python -m py_compile read_local_files.py ingest.py`
- Type Checking: N/A — project has no type-checking step configured
- Unit Tests: N/A — no test suite exists (documented scope gap,
  `docs/ARCHITECTURE.md` "Gap: no automated tests")
- Integration Tests: ✓ manual, via the plan's own VALIDATE commands, run for
  real against the real Teva customer folder and real Postgres (not
  simulated):
  - `read_local_files()` on the Teva folder → 11 files found, `.DS_Store`
    skipped, all 11 extracted with non-empty content (Hebrew docx/xlsx/pptx +
    2 OCR'd PNGs included)
  - `run_ingestion('', ...)` and `run_ingestion('   ', ...)` → both raise
    `ValueError` before any file I/O
  - `run_ingestion('Teva Org Streamlining', <folder>)` → 11 files → 167
    chunks saved, no `RateLimitError`
  - CLI wrapper run twice → exit code 0 both times
  - `psql`: `context_tag='Teva Org Streamlining'` count=334 (167×2, confirms
    additive `pre_delete_collection=False` — second run didn't wipe the
    first)
  - `psql`: 0 rows with null `context_tag`
  - `query_data.py "What is this engagement about?"` → grounded answer,
    sources cite real Teva filenames

## What Went Well

- The plan's task boundaries (file-discovery vs. orchestration) mapped
  cleanly onto the existing codebase's exception type
  (`ContentExtractionError`) and function signatures
  (`split_text`/`set_context_tag`/`save_to_pgvector`) — no surprises reading
  `vector_store.py`/`create_database.py` before implementing.
- Fail-fast `customer_name` validation worked exactly as designed: confirmed
  by both empty-string and whitespace-only inputs raising immediately, with
  no folder walk attempted — this was the actual fix for
  `set_context_tag()`'s silent no-op bug, without touching that reused file.
- The `pre_delete_collection=False` requirement got a real (not just
  theoretical) validation for free: running the CLI wrapper twice for the
  same customer produced 334 rows (167×2) instead of overwriting, proving
  the additive behavior end-to-end rather than just reading the code and
  trusting it.
- No `RateLimitError` on the real Teva folder (11 files, 167 chunks) — the
  TPM risk flagged in `docs/LESSONS.md` didn't materialize at this data
  size, so no speculative batching logic was needed, matching the plan's
  "prove the need before adding complexity" approach.

## Challenges Encountered

- None significant. The one friction point was a rejected multi-command Bash
  call (`cat .env.example && ls .env && docker compose ps`) — bundling a
  read of `.env` (which can hold secrets) with an unrelated status check
  triggered a permission block. Resolved by re-running just the
  `docker compose ps` portion the user approved. Not a plan or code issue —
  a reminder to keep potentially-sensitive file reads in their own isolated
  tool call rather than batched with unrelated checks.

## Divergences from Plan

**File count off by one**
- Planned: "expect 10 files read (11 files in folder minus `.DS_Store`
  skipped)"
- Actual: 11 files read (12 total in folder minus `.DS_Store`)
- Reason: the plan's file-count estimate was written before the final Teva
  folder contents were finalized; the folder actually has 11 real files, not
  10. No code change required — `read_local_files()`'s behavior (skip
  dotfiles, extract everything else, skip-with-reason on
  `ContentExtractionError`) was already correct for whatever the real count
  turned out to be.
- Type: Plan assumption wrong (stale estimate, not a logic error)

**Tasks 2 and 3 implemented as one file write**
- Planned: Task 2 creates a `run_ingestion()` skeleton with just input
  validation; Task 3 adds the chunk/tag/save wiring in a separate edit pass.
- Actual: `ingest.py` was written once, complete (validation + full
  pipeline), then each task's own VALIDATE command was still run separately
  against the finished file to confirm each concern in isolation.
- Reason: the two tasks are the same function with no meaningful
  intermediate state worth committing or testing separately — splitting the
  edit into two passes would have meant writing, testing, then immediately
  rewriting the same function body. Validating both concerns against the
  final code achieves the same confidence with less churn.
- Type: Better approach found

**Sanity-check rows kept in Postgres instead of cleaned up**
- Planned: implicitly follows the prior session's pattern (`STATE.md`:
  "Sanity-check rows cleaned from Postgres afterward" for the earlier
  RAG-base verification); this plan's Level 4 steps don't mention cleanup
  either way.
- Actual: the 334 validation rows (`context_tag='Teva Org Streamlining'`)
  were left in Postgres rather than deleted.
- Reason: explicit user instruction mid-session — Phase 3 (Streamlit Ask
  tab) is next, and having real ingested data already in place lets that be
  tested immediately without re-running ingestion. This is real,
  correctly-tagged data, not garbage, so leaving it in place doesn't
  compromise anything the plan cares about (isolation, tagging correctness).
- Type: Other (explicit user decision, not a plan or implementation issue)

## Skipped Items

- TPM batching for `save_to_pgvector` — plan explicitly deferred this
  pending proof of need (Task 5 notes). The real Teva folder (167 chunks)
  did not trip the 40k TPM limit, so batching remains unimplemented,
  correctly, per the plan's own criteria.
- Automated tests — out of scope per `docs/ARCHITECTURE.md`'s documented gap;
  not attempted.

## Recommendations

- **Plan command improvements**: when a plan's VALIDATE step predicts an
  exact count derived from live filesystem state outside the repo (e.g. "10
  files in the Teva folder"), consider phrasing it as "expect N-ish files,
  verify none are silently dropped" rather than a hard number — the count is
  environment-dependent and drifted here without indicating any actual
  problem, which could cost a future agent time double-checking a
  non-issue.
- **Execute command improvements**: none — the task-by-task validate-as-you-go
  structure worked well and caught what it needed to (e.g. confirming the
  `ValueError` fires before any I/O, not just that it fires).
- **`CLAUDE.md` additions**: none needed — existing guidance (never batch a
  sensitive file read with unrelated commands, work on a feature branch,
  don't fix reused reference code) all held up directly as written during
  this implementation.
