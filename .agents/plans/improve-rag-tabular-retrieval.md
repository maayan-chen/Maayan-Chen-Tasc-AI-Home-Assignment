# Feature: Improve RAG Retrieval Quality for Tabular (Excel) Data

The following plan should be complete, but it's important that you validate
documentation, codebase patterns, and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import
from the right files.

## Feature Description

Fix a confirmed retrieval-quality bug: `.xlsx` files ingested into the RAG
store lose their column/header context during chunking, so the LLM cannot
tell which value belongs to which field (e.g. "is `495000` a salary or an
employee level?"). The fix has three parts, in priority order: (1) preserve
column headers in every row's serialized text at extraction time, (2) chunk
spreadsheet rows as row-aligned units instead of running them through the
generic character-based splitter, (3) restructure the answer-generation
prompt to use explicit delimiters and light citation instructions, per
current OpenAI/Anthropic prompting guidance. Retrieval parameters (`k=3`,
`min_relevance=0.7`) are deliberately left unchanged — see Notes.

## User Story

As a new team member asking the Ask tab a question about tabular data
(headcount, org charts, budgets — anything sourced from a customer's Excel
files)
I want the retrieved context to preserve which column each value came from
So that the answer is actually correct instead of confidently wrong (e.g.
correctly reporting a person's salary instead of misreading their employee
ID as a salary figure)

## Problem Statement

Confirmed against real ingested data (Teva org-chart spreadsheet,
`context_tag=teva-org-streamlining-project`, table `langchain_pg_embedding`):
xlsx rows are chunked with zero header context. Example real chunk currently
in Postgres:

```
E1003 | עמית שלו | מנהל בקרה כספית | בקרה כספית | דוד כץ | D1 | 495000 | ללא שינוי
E1004 | מיכל אוזר | מנהלת כספי רכש | כספי רכש | דוד כץ | D1 | 470000 | ללא שינוי
```

Nothing in this chunk indicates that column 7 is `שכר בסיס שנתי (₪)` (annual
base salary) rather than employee level or any other numeric column. This
happens because of two independent, compounding bugs:

1. `_extract_xlsx()` (`vector_store.py:139-150`) discards the header row's
   semantic role — it joins every row's cell values with `" | "`
   (`vector_store.py:144-146`) with no column-name labeling, so header and
   data rows look identical once flattened.
2. `split_text()` (`create_database.py:32-48`) runs one shared
   `RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=100)` over
   every `Document` regardless of source type. For spreadsheet-derived text,
   this slices at arbitrary 300-character boundaries with no concept of row
   boundaries, so even if headers were preserved in the source text, most
   chunks would still land mid-table, disconnected from the one chunk that
   contains the header row.

Because `context_tag` filtering (the entire customer-isolation trust
boundary, see `docs/ARCHITECTURE.md`) is unaffected by this bug, this is
purely a retrieval-quality problem, not a correctness/security one — but it
directly undermines the tool's stated purpose (grounded, trustworthy
answers with sources).

Separately, the current answer-generation prompt (`query_rag.py:6-16`)
interpolates `{context}` with no delimiter and gives the model no
instruction for how to read multi-field chunks — both flagged by current
(2026) OpenAI/Anthropic prompting guidance as best-practice gaps, though
this alone cannot fix the header-loss bug (a prompt cannot recover
information already discarded at ingestion).

## Solution Statement

**Ingestion-side (root-cause) fix:**
`_extract_xlsx()` is changed to treat row 1 of each sheet as headers and
serialize every subsequent row as `"Header1: value1 | Header2: value2 | ..."`
instead of bare `"value1 | value2 | ..."`. A row separator marker
(`\n===ROW===\n`) is emitted between rows so a downstream row-aware splitter
can split on it without re-parsing the xlsx structure.

`run_ingestion()` (`ingest.py`) gains a branch: `Document`s whose `source`
ends in `.xlsx` are split on the row marker (one row = one chunk, small
row-groups if a single row is large) instead of being passed through
`create_database.py`'s shared `split_text()`. This is additive — `.xlsx`
documents are pulled out of the batch that goes to `split_text()`, chunked
separately, and both chunk lists are concatenated before
`set_context_tag()`/`save_to_pgvector()`. `create_database.py` itself is
**not modified** (stays "reused as-is" per `CLAUDE.md`); the branching lives
in `ingest.py`, which already owns file-type-agnostic orchestration.

**Prompt-side fix:**
`query_rag.py`'s `PROMPT_TEMPLATE` is rewritten to wrap `{context}` in
`<documents>` tags, tag each retrieved chunk with its source filename inline
(so citation/debugging is possible), and keep the existing "don't guess"
instruction at both the start and end of the prompt (confirmed
best-practice: later-positioned instructions are weighted more heavily by
GPT-4.1-family models). `answer_question()`'s chunk-formatting loop
(`query_rag.py:29`) is updated to interpolate each chunk's source into the
per-document tag.

**Left unchanged:** `k=3` and `min_relevance=0.7` in `answer_question()`
(`query_rag.py:19`). See Notes for why.

## Feature Metadata

**Feature Type**: Bug Fix / Enhancement (retrieval quality)
**Estimated Complexity**: Low
**Primary Systems Affected**: Ingestion (`vector_store.py`, `ingest.py`),
retrieval/answer generation (`query_rag.py`)
**Dependencies**: None new — uses `openpyxl` (already a dependency, see
`requirements.txt`) and stdlib only.

---

## CONTEXT REFERENCES

### Relevant Codebase Files — READ THESE BEFORE IMPLEMENTING

- `vector_store.py` (lines 139-150) — `_extract_xlsx()`: the function being
  changed. Currently joins `openpyxl` row values with `" | "`, no header
  labeling. `workbook.worksheets` iteration and `values_only=True` usage
  must be preserved (used to detect the header row as `sheet.iter_rows()`'s
  first yielded row).
- `vector_store.py` (lines 166-188) — `extract_content_from_bytes()`: the
  dispatcher that calls `_extract_xlsx()` by file extension. No change
  needed here, but confirms `.xlsx` routing and that `ContentExtractionError`
  is the established pattern for "nothing usable" (empty workbook after the
  fix should still raise this, matching `_extract_docx`/`_extract_pptx`'s
  existing `if not content: raise ContentExtractionError(...)` pattern at
  lines 135-136 and 161-163).
- `read_local_files.py` (lines 7-31) — `read_local_files()`: calls
  `extract_content_from_bytes()` per file and returns
  `(content, source, file_hash)` tuples. No change needed — `source` (the
  full file path, extension included) already flows through unchanged,
  which is what the new `ingest.py` branch will key off of.
- `create_database.py` (lines 32-48) — `split_text()`: the shared character
  splitter. **Do not modify this file** — it's a "reuse as-is" file per
  `CLAUDE.md`. Read it to confirm the `Document` shape (`page_content`,
  `metadata`) the new row-splitting logic in `ingest.py` must also produce,
  so chunks from both paths are structurally identical before
  `set_context_tag()`.
- `create_database.py` (lines 51-56) — `set_context_tag()`: called on the
  full combined chunk list (character-split + row-split) after both are
  concatenated. Confirms it just mutates `chunk.metadata["context_tag"]` in
  place — works identically regardless of chunk origin.
- `ingest.py` (lines 39-83) — `run_ingestion()`: the orchestration function
  being extended. Currently: read files → dedup by hash
  (`indexed.get(source) == file_hash`, lines 54-62) → build `Document` list
  → `split_text(documents)` (line 68, **single call, all documents**) →
  `set_context_tag()` → `save_to_pgvector()`. The new branch splits the
  `documents` list by `.xlsx` vs. non-`.xlsx` source **before** line 68,
  chunks each subset with its own method, then concatenates before line 69.
  The existing dedup logic (lines 54-62) and delete-after-save-succeeds
  ordering (lines 72-77, see `docs/LESSONS.md`-adjacent comment) must be
  preserved unchanged — this task only touches the chunking step between
  document-building and `set_context_tag()`.
- `query_rag.py` (all, 41 lines) — `PROMPT_TEMPLATE` and `answer_question()`:
  the prompt and retrieval function being updated. `results` is a list of
  `(Document, score)` tuples from `similarity_search_with_relevance_scores`
  (line 23-25); the per-chunk formatting happens at line 29
  (`context_text = "\n\n---\n\n".join(...)`) and must be changed to include
  `doc.metadata.get("source")` per chunk, and the `sources` list
  construction at lines 36-39 already extracts `source` — reuse that same
  metadata key.
- `app.py` (lines 144-168) — chat loop calling `answer_question()`: **no
  change needed**, but read to confirm the `result["answer"]`/
  `result["sources"]` dict shape returned by `answer_question()` must stay
  identical (UI already renders `source["source"]` and `source["content"]`
  per source at lines 140-142) — the prompt/citation change must not alter
  this return shape, only its internal prompt construction.
- `docs/ARCHITECTURE.md` (lines 36-43, "No LLM-driven relevance filtering at
  ingestion") — confirms row-based spreadsheet chunking is still
  deterministic Python, not an LLM judgment call, consistent with this
  documented constraint. No architectural exception needed.
- `docs/LESSONS.md` (lines 46-58) — "A single `save_to_pgvector()` call can
  exceed the OpenAI embeddings TPM limit". Relevant because row-based
  spreadsheet chunking will very likely *increase* total chunk count for
  large sheets (many small chunks instead of few large ones) — worth a
  sanity check against a real large sheet during manual validation (Task 4
  below), though no code change is anticipated since `save_to_pgvector()`
  itself is untouched.

### New Files to Create

None. All changes are edits to existing files.

### Relevant Documentation — READ THESE BEFORE IMPLEMENTING

- [openpyxl `iter_rows` docs](https://openpyxl.readthedocs.io/en/stable/tutorial.html#reading-a-cell-s-value)
  — confirms `values_only=True` yields plain tuples; the header row is
  simply the first tuple yielded per sheet (no separate "is this a header"
  API — must be tracked by position, first row of each sheet's iteration).
  Why: needed to correctly pair each subsequent row's values with the
  header tuple's values by index.
- OpenAI Prompting Best Practices (via CandleKeep library,
  id `cmnx9xcub04cvqo0zh7vrdgdz`, pp. 3, 8) — source of the
  `ID: 1 | TITLE: X | CONTENT: Y` labeled-pipe-delimiting pattern this plan
  applies to xlsx rows, and the "place instructions before AND after
  context" guidance for GPT-4.1-family models. Why: both the row
  serialization format and the prompt restructuring in this plan are
  directly sourced from this reference, not invented.
- Anthropic Prompting Best Practices (via CandleKeep library,
  id `cmnx9xcsz048oqo0zz4tpb5ny`, p. 2) — source of the `<documents>`/
  `<document><source>...</source><content>...</content></document>` XML
  tagging pattern used for the prompt rewrite. Why: this plan's
  `<documents>` wrapper and per-chunk source tagging in `query_rag.py`
  mirror this pattern.

### Patterns to Follow

**Extraction function error handling** (mirror `_extract_docx`,
`vector_store.py:130-136`):
```python
def _extract_docx(raw_bytes: bytes) -> str:
    document = docx.Document(BytesIO(raw_bytes))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    content = "\n".join(paragraphs).strip()
    if not content:
        raise ContentExtractionError("DOCX has no extractable text.")
    return content
```
The rewritten `_extract_xlsx()` must keep this same
"build content, raise `ContentExtractionError` if empty" shape.

**Document construction** (mirror `ingest.py:60-62`):
```python
documents.append(
    Document(page_content=content, metadata={"source": source, "file_hash": file_hash})
)
```
Any row-split `Document`s must carry the same `metadata` keys
(`source`, `file_hash`) as the character-split path — `source` is what the
new `.xlsx`-detection branch keys off of, and both `context_tag` isolation
(via `set_context_tag()`) and per-file dedup/replace (via
`_get_indexed_file_hashes`/`_delete_indexed_file`, `ingest.py:15-36`)
depend on `source`/`file_hash` being present and correct regardless of which
chunking path produced the chunk.

**Naming Conventions:** `snake_case` functions, leading-underscore for
module-private helpers (`_extract_xlsx`, `_is_text_unreliable` in
`vector_store.py`; `_get_indexed_file_hashes`, `_delete_indexed_file` in
`ingest.py`) — the new row-chunking helper in `ingest.py` should follow this
same `_leading_underscore` convention, e.g. `_chunk_xlsx_documents`.

**Error Handling:** Custom exceptions only where an existing one fits
(`ContentExtractionError`); otherwise let stdlib/library exceptions
propagate — `CLAUDE.md` explicitly says not to add error handling for
scenarios that can't happen.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation — header-aware xlsx extraction
Rewrite `_extract_xlsx()` to label every cell with its column header, with a
row-separator marker so the row structure survives into a plain string.

### Phase 2: Core Implementation — row-based spreadsheet chunking
Add a row-aware chunking path in `ingest.py` for `.xlsx`-sourced documents,
routed around the generic `split_text()` character splitter, then
concatenated with the normal character-split chunks from all other file
types before saving.

### Phase 3: Integration — prompt restructuring
Update `query_rag.py`'s `PROMPT_TEMPLATE` and `answer_question()`'s
context-formatting to use XML-style document tags with per-chunk source
attribution.

### Phase 4: Testing & Validation
Re-ingest the real Teva xlsx data (additive — dedup will skip unchanged
files, so this validates the *new* code path only if the file's hash
changed or the collection is queried against fresh test data) and manually
confirm a tabular question now returns a correctly-attributed answer.

---

## STEP-BY-STEP TASKS

### UPDATE `vector_store.py` — `_extract_xlsx()` (lines 139-150)

- **IMPLEMENT**: Treat the first row yielded by `sheet.iter_rows(values_only=True)`
  as the header tuple for that sheet. For every subsequent row, zip header
  values with row values and build `"Header: value"` pairs, joined by `" | "`,
  skipping pairs where the cell value is `None`. Join rows within a sheet
  with `"\n"` as before. If a sheet has fewer than 2 rows (no data rows,
  only a header or empty), skip it (matches existing "skip empty" behavior
  implicitly — no explicit empty-sheet check exists today, don't add
  scaffolding for a case the loop already handles naturally by producing no
  lines for that sheet).
  ```python
  def _extract_xlsx(raw_bytes: bytes) -> str:
      workbook = openpyxl.load_workbook(BytesIO(raw_bytes), data_only=True)
      lines = []
      for sheet in workbook.worksheets:
          rows = sheet.iter_rows(values_only=True)
          header = next(rows, None)
          if header is None:
              continue
          header = [str(h) if h is not None else "" for h in header]
          for row in rows:
              pairs = [
                  f"{header[i]}: {cell}"
                  for i, cell in enumerate(row)
                  if cell is not None and i < len(header) and header[i]
              ]
              if pairs:
                  lines.append(" | ".join(pairs))
      content = "\n".join(lines).strip()
      if not content:
          raise ContentExtractionError("XLSX has no extractable text.")
      return content
  ```
- **PATTERN**: `_extract_docx` (`vector_store.py:130-136`) for the
  "build content, raise `ContentExtractionError` if empty" shape.
- **GOTCHA**: `header[i]` can raise `IndexError` if a data row has more
  cells than the header row (ragged sheet) — the `i < len(header)` guard in
  the list comprehension above handles this; don't drop it. Also: a header
  cell that's an empty string (blank header cell in the source sheet) would
  otherwise produce `": value"` with no field name — the `and header[i]`
  clause in the guard drops those pairs rather than emitting a
  meaningless label.
- **GOTCHA**: Do not add a row-separator marker in this function — that
  belongs in Phase 2's chunking logic, not extraction, to keep this function
  a pure "bytes → labeled text" concern. (Originally considered emitting a
  `\n===ROW===\n` marker here, but decided against it: `ingest.py`'s new
  chunking helper already receives the `Document` with one row per `\n`-
  joined line per sheet, and splitting on `"\n"` per sheet is sufficient —
  no separate marker syntax needed. Confirm this is still true when
  implementing Task 2; if sheets need multi-line cell values preserved
  within a row, revisit.)
- **VALIDATE**: `python3 -c "from vector_store import _extract_xlsx; import pathlib; print(_extract_xlsx(pathlib.Path('/Users/maayanchen/Code/Work/Teva_Org_Streamlining_Project/תרשים_ארגוני_מצב_עתידי.xlsx').read_bytes())[:500])"`
  — confirm output shows `Header: value | Header: value` pairs, not bare
  values.

### UPDATE `ingest.py` — add row-aware chunking for `.xlsx` documents

- **IMPLEMENT**: Add a private helper `_chunk_xlsx_documents(documents)`
  that takes a list of `.xlsx`-sourced `Document`s and returns one `Document`
  chunk per row (splitting `page_content` on `"\n"`), preserving each
  original document's `metadata` (`source`, `file_hash`) on every resulting
  chunk. In `run_ingestion()` (after building the `documents` list, before
  the `split_text(documents)` call at current line 68), partition
  `documents` into `xlsx_documents` (source ends with `.xlsx`) and
  `other_documents`. Call `split_text(other_documents)` for the latter
  (existing behavior, unchanged for all non-spreadsheet files) and
  `_chunk_xlsx_documents(xlsx_documents)` for the former; concatenate both
  chunk lists before the existing `set_context_tag()` call.
  ```python
  def _chunk_xlsx_documents(documents: list[Document]) -> list[Document]:
      chunks = []
      for doc in documents:
          for row_text in doc.page_content.split("\n"):
              row_text = row_text.strip()
              if row_text:
                  chunks.append(Document(page_content=row_text, metadata=dict(doc.metadata)))
      return chunks
  ```
  And in `run_ingestion()`, replace:
  ```python
  chunks = split_text(documents)
  ```
  with:
  ```python
  xlsx_documents = [d for d in documents if d.metadata["source"].lower().endswith(".xlsx")]
  other_documents = [d for d in documents if not d.metadata["source"].lower().endswith(".xlsx")]
  chunks = split_text(other_documents) + _chunk_xlsx_documents(xlsx_documents)
  ```
- **PATTERN**: `ingest.py:60-62` for `Document` construction with
  `metadata={"source": ..., "file_hash": ...}` — `_chunk_xlsx_documents`
  must preserve these same two keys via `dict(doc.metadata)` (copy, not
  reference, so `set_context_tag()`'s later per-chunk mutation doesn't
  cross-contaminate rows from the same source document).
- **IMPORTS**: `Document` is already imported (`ingest.py:5`,
  `from langchain.schema import Document`) — no new import needed.
- **GOTCHA**: `split_text(other_documents)` must never be called with an
  empty list if `other_documents` is empty — check
  `create_database.py:32-48`'s `split_text()`: `RecursiveCharacterTextSplitter.split_documents([])`
  returns `[]` safely (unlike `PGVector.from_documents([])`, see
  `docs/LESSONS.md:60-75` — that failure is at the *save* step, not the
  *split* step, so this is fine, but confirm empirically in Task validation
  rather than assuming).
- **GOTCHA**: The existing `if not documents: ...` early return
  (`ingest.py:64-66`) happens *before* this new partition logic — no change
  needed there, it already guards the case where nothing was read at all.
- **VALIDATE**: `python3 -c "
from ingest import run_ingestion
result = run_ingestion('Test XLSX Chunking', '/Users/maayanchen/Code/Work/Teva_Org_Streamlining_Project')
print(result)
"` — then inspect chunk count sanity: row-based chunking of the org-chart
  sheet should produce roughly one chunk per employee row instead of a few
  300-char chunks; confirm `chunks_saved` increased relative to a prior run
  against the same folder (check via `psql`/the query in Task 4 below)
  rather than assuming a specific number.

### UPDATE `query_rag.py` — prompt restructuring and per-chunk source tagging

- **IMPLEMENT**: Replace `PROMPT_TEMPLATE` with an XML-delimited version
  that repeats the "don't guess" instruction before and after the context,
  and update the context-formatting loop (line 29) to tag each chunk with
  its source filename.
  ```python
  PROMPT_TEMPLATE = """
  Answer the question using only the documents below. Each document may
  contain table rows formatted as "Header: value | Header: value" — treat
  each Header: value pair as a distinct field, not continuous prose.

  <documents>
  {context}
  </documents>

  If the documents do not contain enough information to answer the question,
  say you don't know — do not guess or use information outside the documents.

  Question: {question}

  Answer using only the documents above:
  """
  ```
  And update the context-building loop:
  ```python
  context_text = "\n\n".join(
      f'<document source="{doc.metadata.get("source", "unknown")}">\n{doc.page_content}\n</document>'
      for doc, _score in results
  )
  ```
- **PATTERN**: `query_rag.py:36-39` (`sources` list construction) already
  extracts `doc.metadata.get("source")` — reuse the identical accessor in
  the new context-formatting loop for consistency.
- **GOTCHA**: `answer_question()`'s return shape
  (`{"answer": ..., "sources": [...]}`, lines 27 and 40) **must not
  change** — `app.py:161-166` destructures this exact shape. Only the
  internal `PROMPT_TEMPLATE` string and `context_text` construction change.
- **GOTCHA**: `doc.metadata.get("source")` could theoretically be `None` if
  a chunk somehow lacks the key — the `"unknown"` fallback in the f-string
  above prevents an XML tag like `source="None"`; this is defensive only
  for chunks that predate this change (already-ingested data from before
  this fix) which may not have every field the new pipeline expects — but
  since `source` has always been a required metadata key
  (`ingest.py:60-62`, unconditional), this fallback should never actually
  trigger on real data; keep it only because it's a one-line no-cost guard,
  not because a real gap was found.
- **VALIDATE**: `python3 -c "
from query_rag import answer_question
result = answer_question('What is דוד כץ salary?', 'teva-org-streamlining-project')
print(result['answer'])
print([s['source'] for s in result['sources']])
"` (adjust `context_tag` to match whatever the real ingested Teva data's
  slug is — check via the `list_customers()` query in `app.py:27-34` or a
  direct `psql` `SELECT DISTINCT cmetadata->>'context_tag' FROM langchain_pg_embedding;`
  if unsure) — confirm the answer correctly identifies the salary figure,
  not a different column's value.

---

## TESTING STRATEGY

Per `docs/ARCHITECTURE.md`'s documented scope gap ("Gap: no automated
tests"), this project has no pytest suite by deliberate 2-day-budget
decision — manual verification only, consistent with existing practice
(`docs/ARCHITECTURE.md:106-118`). This plan follows the same pattern: no new
test files are created; each task's `VALIDATE` command is a standalone
manual script run via `python3 -c`.

### Unit Tests
None (matches project convention — see above).

### Integration Tests
None (matches project convention — see above).

### Edge Cases
Covered inline via GOTCHA notes on each task:
- Ragged sheets (data row longer than header row) — Task 1's `i < len(header)` guard.
- Blank header cells — Task 1's `and header[i]` guard.
- Empty `other_documents` or `xlsx_documents` list after partitioning — Task 2's GOTCHA, verified empirically since `docs/LESSONS.md` documents a related-but-distinct empty-list failure mode at the *save* step (not split step).
- Chunk missing `source` metadata — Task 3's defensive fallback (should not trigger on real data, included as a no-cost guard only).

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and feature correctness.

### Level 1: Syntax & Style
```bash
python3 -c "import vector_store, ingest, query_rag"  # confirms no syntax/import errors
```

### Level 2: Unit Tests
N/A — no test suite (see Testing Strategy above).

### Level 3: Integration Tests
N/A — no test suite (see Testing Strategy above).

### Level 4: Manual Validation
1. Confirm Postgres is up: `docker ps --format "{{.Names}}: {{.Status}}"` should show `rag_pgvector: Up ... (healthy)`.
2. Run Task 1's VALIDATE command — confirm `_extract_xlsx()` output shows labeled `Header: value` pairs against the real Teva org-chart file.
3. Run Task 2's VALIDATE command — run `run_ingestion()` against the real Teva folder under a **new** test `context_tag` (e.g. `"Test XLSX Chunking"`, not the real `"Teva Org Streamlining Project"` tag) so this doesn't collide with or dirty the existing real customer data already in Postgres.
4. Query the new `context_tag`'s chunks directly to eyeball the row-chunking result:
   ```bash
   python3 -c "
   import psycopg
   from vector_store import get_psycopg_connection
   with psycopg.connect(get_psycopg_connection()) as conn:
       with conn.cursor() as cur:
           cur.execute(\"SELECT document FROM langchain_pg_embedding WHERE cmetadata->>'context_tag' = 'test-xlsx-chunking' AND document LIKE '%שכר%' LIMIT 3\")
           for (doc,) in cur.fetchall():
               print(doc)
               print('---')
   "
   ```
   Confirm each returned chunk is a single row with header labels (e.g.
   `שכר בסיס שנתי (₪): 495000`), not a headerless multi-row blob.
5. Run Task 3's VALIDATE command against the **real** existing
   `teva-org-streamlining-project` context_tag (not the new test tag, since
   that data hasn't been re-ingested with the header fix) to confirm the
   prompt restructuring alone doesn't break the existing answer flow — then
   re-run against `test-xlsx-chunking` once step 3-4 confirm the new
   ingestion path works, to see the full fix (header-labeled chunks +
   restructured prompt) working together.
6. Clean up the test `context_tag` rows from Postgres afterward (per
   `CLAUDE.md`'s established pattern of not leaving sanity-check rows
   behind — see `STATE.md`'s Phase 1 validation note about cleaning up
   after a similar sanity check):
   ```bash
   python3 -c "
   import psycopg
   from vector_store import get_psycopg_connection
   with psycopg.connect(get_psycopg_connection()) as conn:
       with conn.cursor() as cur:
           cur.execute(\"DELETE FROM langchain_pg_embedding WHERE cmetadata->>'context_tag' = 'test-xlsx-chunking'\")
       conn.commit()
   "
   ```
7. Full UI walkthrough: `streamlit run app.py`, select the real
   `teva-org-streamlining-project` customer, ask a tabular question (e.g.
   "What is [employee]'s salary?" or "who reports to [manager]?"), confirm
   the answer and its Sources expander look correct. Note: this uses the
   **old** (pre-fix) ingested chunks unless step 3's re-ingestion is also
   pointed at the real tag — decide with the user whether to re-ingest the
   real Teva data under its real tag (which is safe/additive per
   `pre_delete_collection=False`, but will produce a mix of old headerless
   and new header-labeled chunks for unchanged files, since the dedup
   hash-check in `ingest.py:54-62` will *skip* files whose content hasn't
   changed — the xlsx file's bytes are unchanged, so its hash is unchanged,
   so re-running ingestion will NOT re-chunk it with the new logic). **This
   is a real gotcha to flag to the user before Task 4**: the dedup-by-hash
   mechanism means simply re-running `streamlit run app.py`'s "Run
   Ingestion" button will silently skip re-processing the xlsx file even
   after this fix ships, because the file's bytes (and thus hash) haven't
   changed. The real Teva xlsx data must be explicitly deleted from
   Postgres and re-ingested from scratch to benefit from this fix — decide
   with the user whether to do this as part of validation.

---

## ACCEPTANCE CRITERIA

- [ ] `_extract_xlsx()` produces `Header: value` labeled output, not bare pipe-delimited values
- [ ] `.xlsx`-sourced documents are chunked one-row-per-chunk (or small row-groups), bypassing `RecursiveCharacterTextSplitter`
- [ ] Non-`.xlsx` documents still go through `split_text()` unchanged (no regression to existing `.txt`/`.md`/`.pdf`/`.docx`/`.pptx`/image ingestion)
- [ ] `query_rag.py`'s prompt wraps context in `<documents>` tags with per-chunk source attribution
- [ ] `answer_question()`'s return shape (`{"answer": ..., "sources": [...]}`) is unchanged — `app.py` requires no edits
- [ ] A real query against re-ingested Teva salary data returns a correctly-attributed answer (manually verified per Validation Commands step 7)
- [ ] No regressions in existing `context_tag` isolation (spot-check: query still filters correctly by `context_tag`)
- [ ] Test `context_tag` rows created during validation are cleaned up from Postgres

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task's VALIDATE command run and passed
- [ ] Manual UI walkthrough (Validation Commands step 7) confirms the fix visibly changes answer quality on a real tabular question
- [ ] User informed of the dedup-hash gotcha (Validation Commands step 7) and has decided whether/how to re-ingest real Teva data to actually benefit from this fix
- [ ] `docs/ARCHITECTURE.md` updated if the user wants the row-chunking-for-spreadsheets decision recorded (see Notes — this is a real architectural decision: "why does xlsx ingestion diverge from the shared `split_text()` path")

---

## NOTES

**Why `k=3`/`min_relevance=0.7` are NOT changed by this plan:** Researched
via CandleKeep (Anthropic's "Effective Context Engineering for AI Agents")
and confirmed by current web research — no source gives a numeric ideal for
either parameter, and the "context rot" principle (larger retrieved context
measurably *degrades* recall accuracy, not just costs tokens) argues for
keeping k small and the threshold strict rather than loosening them
speculatively. If the header/chunking fix in this plan does not fully
resolve observed answer-quality problems, revisit these parameters *next*,
informed by the specific remaining failure mode — not preemptively.

**Why this is a real architectural decision worth recording:** Prior to
this plan, `create_database.py`'s `split_text()` was the single,
file-type-agnostic chunking path — a "one chunking strategy for everything"
design implicit in the codebase (not explicitly stated as a decision in
`docs/ARCHITECTURE.md`, but observably true of the code). This plan
introduces the first file-type-specific chunking branch. This is a
deliberate divergence, not a regression of the "keep it simple" principle:
`CLAUDE.md` says every architectural choice needs its own one-sentence
justification, and this one has it ("character-based chunking is provably
wrong for tabular data — it severs rows from their headers"), but per
`docs/CONTEXT-PROTOCOL.md`, this plan does not update `docs/ARCHITECTURE.md`
itself (only the user can request context updates) — flagging it here so
the user can decide whether to add an entry after this ships.

**Explicitly deferred / out of scope for this plan:**
- Re-chunking already-ingested spreadsheet data automatically — the dedup
  hash-check means old xlsx chunks are inert relics until the source file
  is explicitly re-ingested from a cleared state. No auto-migration is
  proposed; see Validation Commands step 7's gotcha.
- `.docx`/`.pptx` tabular content (e.g. a table embedded inside a Word doc)
  — out of scope; this plan only addresses `.xlsx` files, since that's the
  confirmed real-world failure mode. `_extract_docx`/`_extract_pptx`
  (`vector_store.py:130-136`, `153-163`) are unchanged.
- Semantic/embedding-based chunking, reranking, or hybrid search — flagged
  by web research as viable further improvements but explicitly out of
  scope here per `CLAUDE.md`'s "cut scope rather than add a layer that
  needs its own justification"; this plan fixes the confirmed root cause
  only.
