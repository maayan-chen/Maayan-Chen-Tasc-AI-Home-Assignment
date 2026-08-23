# Code Review: Phase 3 — Streamlit App (`streamlit-ui` vs `main`)

**Stats:**
- Files Modified: 5 (`CLAUDE.md`, `docs/ARCHITECTURE.md`, `ingest.py`, `read_local_files.py`)
- Files Added: 5 (`app.py`, `query_rag.py`, `.streamlit/config.toml`, `.agents/plans/phase-3-streamlit-app.md`, `.agents/execution-reports/phase-3-streamlit-app.md`)
- New lines: 1098 / Deleted lines: 15

## Issues

```
status: FIXED
severity: high
file: ingest.py
line: 28-69
issue: Per-file delete is committed before the replacement chunks exist, with no rollback
detail: `_delete_indexed_file()` (lines 28-36) opens its own connection and
  calls `conn.commit()` immediately, inside the per-file loop (line 58),
  for every file whose content changed. The actual re-insert of new chunks
  for the whole batch happens once, later, in a single `save_to_pgvector()`
  call (line 69) — a completely separate connection with no transaction
  spanning both steps. If that call fails for any reason after one or more
  deletes already committed — including the OpenAI embeddings TPM
  `RateLimitError` this exact codebase has already hit once
  (`docs/LESSONS.md`: "A single `save_to_pgvector()` call can exceed the
  OpenAI embeddings TPM limit") — the deleted files' old content is gone
  from Postgres with nothing to replace it. This is a genuine partial-failure
  state: previously (pre-PR) ingestion was purely additive
  (`pre_delete_collection=False`, no deletes existed at all), so a failed
  run just meant nothing new got written; this PR introduces the first
  delete path in the codebase, unguarded.
suggestion: Defer the deletes until after `save_to_pgvector()` succeeds —
  collect the list of `(context_tag, source)` pairs to delete during the
  loop, call `save_to_pgvector()` first, and only run the deletes once the
  insert has succeeded. This flips the failure mode from "data loss" to
  "harmless duplicate rows that a retry/re-ingest will clean up," matching
  the existing additive-safe default.
fix: `run_ingestion()` now collects changed sources into `files_to_replace`
  during the loop instead of deleting immediately; `save_to_pgvector()` runs
  first, and the deletes for `files_to_replace` only happen afterward, once
  the new chunks are safely saved.
```

```
status: FIXED
severity: medium
file: app.py
line: 144-163
issue: No error handling around answer_question() in the Ask chat flow
detail: The Ingest tab (lines 90-96) explicitly wraps `run_ingestion()` in
  `try/except` for both expected errors (`FileNotFoundError`,
  `NotADirectoryError`, `ValueError`) and a generic fallback, rendering
  `st.error(...)`. The Ask tab's `answer_question()` call (line 148) has no
  such handling. If it raises (OpenAI rate limit, network error, Postgres
  connection drop — all realistic failure modes for a live API call), the
  user's message was already appended to `st.session_state["messages"]`
  (line 145) before the call, so the failure leaves an unanswered user
  question in the chat history with no assistant reply and no scoped error
  message — just Streamlit's default traceback box. This also leaks
  internals to the user, which the project's own success criteria
  (`.agents/plans/phase-3-streamlit-app.md`, referencing PRD §4) call out:
  "never let a raw traceback reach the Streamlit UI."
suggestion: Wrap the `answer_question()` call in a `try/except Exception as
  e:` that appends an assistant message like
  `f"Something went wrong answering that: {e}"` (or a generic
  "Ask failed, try again" message) to `st.session_state["messages"]` instead
  of letting the exception propagate, mirroring the Ingest tab's existing
  pattern.
fix: `answer_question()` is now wrapped in `try/except Exception as e:`;
  on failure an assistant message ("Something went wrong answering that:
  {e}") is appended to `st.session_state["messages"]` instead of letting
  the exception reach Streamlit's default traceback box.
```

```
severity: medium
file: ingest.py
line: 40
issue: context_tag derivation change silently orphans data ingested under the old (pre-slugify) tag
detail: `context_tag = slugify(customer_name)` (line 40) replaces the prior
  verbatim `customer_name.strip()`. Any customer already ingested before
  this change lands is tagged with the raw typed name (e.g. `"Teva"`), not
  its slug (`"teva"`). Re-ingesting that same folder under this PR's code
  calls `_get_indexed_file_hashes("teva")` (line 49), which finds zero rows
  under the new tag, treats every file as new, and inserts a full duplicate
  set under `context_tag="teva"` — while the original `"Teva"`-tagged rows
  remain in Postgres, permanently orphaned and invisible to `list_customers()`
  or any query scoped to the new tag. `CLAUDE.md` states `context_tag` is
  "the *only* mechanism that scopes data to a customer," and
  `docs/ARCHITECTURE.md` calls it "the entire trust boundary" — this is a
  one-time migration hazard against that exact field, not a hypothetical.
  (Also already flagged and posted to PR #1 in a separate review pass.)
suggestion: Either (a) run a one-time migration that re-tags existing rows
  from their raw customer-name value to `slugify(value)` before this PR
  merges, or (b) document the hazard explicitly in `STATE.md`/a release
  note so whoever re-ingests an existing customer folder post-merge knows
  to expect a duplicate under the new slug and can manually clean up the
  old tag afterward. Silent duplication either way is worse than a
  documented one-time cost.
```

```
severity: low
file: ingest.py
line: 81
issue: CLI --customer help text is stale relative to the code
detail: The `argparse` help string still reads
  `"Customer name (used verbatim as context_tag)"`, but line 40 now
  slugifies the name before using it as `context_tag`. This is misleading
  `--help` output for the one CLI entrypoint into this pipeline, in a
  project whose central constraint is that every part must be explainable.
suggestion: Update to `"Customer name (slugified into context_tag)"` or
  similar.
```

## Verified non-issues

- All raw SQL in `ingest.py`/`app.py` (3 `cur.execute()` call sites) uses
  `%s` parameterized queries with tuple params — no injection risk.
- `docs/LESSONS.md`'s documented `PGVector.from_documents([])` crash (empty
  list throws `NotNullViolation`) is correctly guarded twice: once for zero
  files found (`ingest.py:45-47`, pre-existing) and once for the new
  "all files unchanged" case where `documents` ends up empty after the
  hash-skip loop (`ingest.py:63-65`, new in this PR). `save_to_pgvector` is
  never reached with an empty list on either path.
- `context_tag` remains the sole scoping mechanism throughout — no
  `display_name` field, no second lookup table, dropdown/pill render the
  raw slug directly (`app.py:124`, `129`).
- No LLM/agent call added anywhere in the ingestion path — the new
  dedup logic (`_get_indexed_file_hashes`, `_delete_indexed_file`) is plain
  deterministic SQL.
- `html.escape()` is correctly applied before interpolating the customer
  tag into `unsafe_allow_html=True` markup (`app.py:124`) — no XSS risk
  from a customer name containing HTML-special characters.
