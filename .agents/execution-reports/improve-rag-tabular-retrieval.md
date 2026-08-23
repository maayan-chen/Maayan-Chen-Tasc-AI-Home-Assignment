# Execution Report: Improve RAG Tabular Retrieval

## Meta Information

- Plan file: `.agents/plans/improve-rag-tabular-retrieval.md`
- Files added: none
- Files modified:
  - `vector_store.py`
  - `ingest.py`
  - `query_rag.py`
- Lines changed: +51 -11 (`ingest.py` +17/-1, `query_rag.py` +20/-6, `vector_store.py` +25/-4... actual diffstat: 51 insertions(+), 11 deletions(-) across the three files)

## Validation Results

- Syntax & Linting: ✓ (`python3 -c "import vector_store, ingest, query_rag"` passed clean)
- Type Checking: N/A — project has no type-checking step configured
- Unit Tests: N/A — project has no automated test suite (deliberate scope gap, see `docs/ARCHITECTURE.md`)
- Integration Tests: ✓ (manual, against real data)
  - `_extract_xlsx()` validated against all 3 real Teva xlsx files — correct `Header: value` output
  - `run_ingestion()` against test `context_tag` — 12 files → 239 chunks (168 char-split + 71 row-split), inspected directly via `psql`
  - `answer_question()` against test `context_tag` — correct, sourced answer for a real salary question
  - `answer_question()` against pre-existing real `teva` data — no regression (prompt restructuring alone)
  - `context_tag` isolation spot-check — mismatched tag returns empty result, unchanged
  - Real `teva` data re-ingested end-to-end (old xlsx rows deleted, re-ingested, dedup correctly skipped 9 unchanged non-xlsx files) — live query returned correct, sourced salary answer

## What Went Well

- The plan's file-by-file task breakdown mapped cleanly onto the actual code — `_extract_xlsx()`, `run_ingestion()`, and `PROMPT_TEMPLATE`/context-formatting were exactly where the plan said, with the exact shapes described (e.g. `Document(page_content=..., metadata={"source":..., "file_hash":...})`).
- The plan's GOTCHA notes were accurate and pre-empted real issues: `split_text([])` was confirmed safe (empty list doesn't throw, unlike `PGVector.from_documents([])`), and the `dict(doc.metadata)` copy (not reference) in `_chunk_xlsx_documents` correctly prevents cross-contamination between row-chunks from the same source document.
- `answer_question()`'s return shape (`{"answer": ..., "sources": [...]}`) was preserved exactly as required — `app.py` needed zero changes, confirmed by not touching it and having the full UI-adjacent contract (dict shape) still hold in manual query tests.
- The plan's own validation script explicitly flagged the dedup-hash gotcha in advance ("re-running ingestion will NOT re-chunk the xlsx file because its hash is unchanged") — this was exactly correct and let the real-data re-ingestion step go smoothly once flagged to the user rather than being discovered as a surprise mid-validation.
- End-to-end validation against real, messy production data (bilingual Hebrew/English spreadsheets with merged-looking title rows) caught a real bug the plan's own author acknowledged wasn't the confirmed path — validating against synthetic/simple data would have missed this entirely.

## Challenges Encountered

- The plan's Task 1 `VALIDATE` command output wasn't eyeballed for correctness in the plan itself — it specified the command to run but not what "correct" output looks like beyond "shows `Header: value` pairs, not bare values." Running it against the real file immediately surfaced that the *labels themselves* were wrong (title-row text used as headers), not just "are there labels at all." This shows the value of actually running validation commands rather than trusting the plan's code sample would work as-is.
- Distinguishing "the fix is wrong" from "the test data is unusual" required inspecting raw `openpyxl` row output directly (`sheet.iter_rows(values_only=True)` printed row-by-row) rather than trusting either the plan's assumption or my first instinct — this added one extra investigation step but was necessary to root-cause correctly rather than patch around a symptom.

## Divergences from Plan

**Header-row detection heuristic**
- Planned: "Treat the first row yielded by `sheet.iter_rows(values_only=True)` as the header tuple for that sheet" — i.e., row 1 is always the header.
- Actual: Skip rows with ≤1 non-empty cell (title/banner rows, blank rows); the first row with 2+ non-empty cells is treated as the header.
- Reason: All 3 real Teva xlsx files have 1–4 title/banner rows and often a blank row before the true header row (confirmed by direct inspection: e.g. the org-chart sheet's real header is row index 5, not row 0). Implementing the plan literally would have mislabeled every data row with banner text as the "header" (e.g. `טבע תעשיות פרמצבטיות...: 620000`), which is arguably worse than the original bug — confidently wrong labels instead of no labels. This was a plan assumption that didn't hold against the actual confirmed test data the plan itself cited (the plan's own Problem Statement quotes a real chunk from this same file).
- Type: **Plan assumption wrong.** Flagged to the user via `AskUserQuestion` before implementing (not a unilateral judgment call), user selected the heuristic fix and confirmed it should be the recommended path.

No other divergences — the row-based xlsx chunking (Task 2) and prompt restructuring (Task 3) were implemented as specified, including the `dict(doc.metadata)` copy, the `xlsx_documents`/`other_documents` partition, the `<documents>`/`<document source="...">` XML tagging, and leaving `k=3`/`min_relevance=0.7` untouched.

## Skipped Items

- **Re-chunking already-ingested spreadsheet data automatically**: explicitly out of scope per the plan's Notes section. However, unlike the plan's default assumption (leave old chunks as inert relics, decide with user later), the user was asked mid-execution and chose to have the real `teva` context_tag's stale xlsx rows deleted and re-ingested immediately, so this was actually completed rather than deferred — see plan's Notes "Explicitly deferred" list, first bullet, which anticipated this decision point correctly.
- **`docs/ARCHITECTURE.md` update**: the plan's Notes section and Completion Checklist both flag this as a real architectural decision worth recording but explicitly leave it to the user to request (per `docs/CONTEXT-PROTOCOL.md`, only the user triggers context updates). Not done in this pass — pending user request. Two entries now warranted: the originally-anticipated "why xlsx diverges from `split_text()`" decision, plus a new one for the header-row-detection heuristic (not anticipated by the plan, since the plan didn't know its own row-1 assumption would fail).
- **`.docx`/`.pptx` embedded tables**: explicitly out of scope per plan Notes, not attempted.
- **Retrieval parameter tuning (`k`, `min_relevance`)**: explicitly left unchanged per plan Notes' reasoning (context-rot research), not revisited.

## Recommendations

- **Plan command improvements**: When a plan's `VALIDATE` step includes a literal code sample (like Task 1's `_extract_xlsx()` rewrite), the plan should be explicit that the sample is a *starting point*, not a drop-in-and-done answer — and validation commands should specify what "correct output" looks like in more concrete terms (e.g. "the labels should be actual column names like 'שכר בסיס שנתי', not sentence fragments") rather than a shape-only check ("shows `Header: value` pairs"). A shape check alone can pass while the semantic content is still wrong.
- **Plan command improvements**: For any plan whose Problem Statement quotes a real data sample (as this one did — the exact headerless chunk from Postgres), the planning step should include actually opening that source file and inspecting its raw row structure before finalizing the extraction algorithm, not just the already-corrupted downstream chunk. This would have caught the banner-row issue at plan-writing time instead of execution time.
- **Execute command improvements**: None — the existing instruction to "verify as you go" and run each task's `VALIDATE` command before moving on is exactly what surfaced this divergence early (after Task 1, before Task 2/3 were built on top of a wrong assumption). No change needed here.
- **`CLAUDE.md` additions**: Consider adding a line under Code Standards for this project specifically: "When writing extraction/parsing logic against real customer files, inspect actual raw structure (not just a previously-flagged bad chunk) before finalizing the algorithm — real files have messier structure (title rows, blank rows, merged cells) than the happy-path case." This generalizes beyond xlsx to any future extractor changes (`.docx` tables, `.pptx` structured content) this codebase might touch later.
