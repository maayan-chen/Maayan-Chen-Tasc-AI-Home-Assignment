# Code Review: Improve RAG Tabular Retrieval

**Stats:**
- Files Modified: 3 (`vector_store.py`, `ingest.py`, `query_rag.py`)
- Files Added: 0
- New lines: 51 / Deleted lines: 11

## Summary

Reviewed against `CLAUDE.md`, `docs/ARCHITECTURE.md`, and `docs/LESSONS.md`.
Read all three changed files in full (not just the diff). Verified the
following concretely rather than by inspection alone:

- Ragged/short rows and `None` cell values against the new `_extract_xlsx()`
  header-detection logic (constructed a synthetic workbook with a title
  banner row, blank row, real header, a ragged extra cell, and a `None`
  value) — all handled correctly, no `IndexError`, no crash.
- Curly braces (`{`/`}`) inside `context_text` do not break
  `ChatPromptTemplate.from_template(...).format(...)` — LangChain's
  `.format()` only substitutes the outer template's named placeholders, it
  does not re-parse the substituted value, so no template-injection risk
  from spreadsheet content that happens to contain braces.
- `source` is always a real file path string set unconditionally in
  `ingest.py:74` (`Document(metadata={"source": source, ...})`), so
  `.lower().endswith(".xlsx")` in the new partition logic
  (`ingest.py:81-82`) can never hit a missing-key or `None` case.
- `split_text([])` (empty `other_documents` list) returns `[]` safely — does
  not reproduce the `PGVector.from_documents([])` empty-list crash documented
  in `docs/LESSONS.md`.
- The new `<document source="...">` XML tagging in `query_rag.py` only
  reaches `st.markdown`/`st.text` in `app.py` (no `unsafe_allow_html`) — no
  XSS surface introduced.
- `start_index` metadata (added by `split_text()` via `add_start_index=True`)
  is absent on row-chunked `.xlsx` documents — confirmed via `grep` that
  nothing in the codebase reads `start_index`, so this asymmetry is inert,
  not a bug.

No violations of the `context_tag`-as-sole-scoping-mechanism rule, no new
HTTP surface, no LLM judgment introduced at ingestion (row-splitting on `"\n"`
is deterministic string splitting, consistent with `docs/ARCHITECTURE.md`'s
"No LLM-driven relevance filtering at ingestion").

## Issues

Code review passed. No technical issues detected.

## Notes (non-blocking, for awareness only)

- `ingest.py:81-82` computes `.lower().endswith(".xlsx")` twice (once per
  list comprehension) instead of partitioning in one pass. Not a real
  performance concern at realistic file-list sizes (dozens of files, not
  thousands), and splitting into two comprehensions is more readable than a
  single-pass partition here — not flagged as an issue.
- `query_rag.py`'s `context_text` f-string embeds `doc.metadata.get("source")`
  directly into an XML attribute value with no escaping (e.g. a source path
  containing `"` would break the attribute). This only affects prompt text
  sent to the LLM, not any rendered HTML/SQL, and file paths come from the
  local filesystem the user explicitly points ingestion at (not attacker
  -controlled remote input), so this is a correctness edge case at most, not
  a security issue. Not worth guarding given this project's "don't add
  validation for scenarios that can't happen" standard (`CLAUDE.md`) — real
  customer folder paths don't contain quote characters in practice.
