# Lessons

System-critical gotchas worth remembering — not a changelog.

<!--
THE TEST FOR AN ENTRY
Would reading this six months from now have prevented the bug?
If no → it's a changelog entry. Delete it. Git history already has it.

WHAT EARNS A PLACE
- Something that passed every automated check and still didn't work
- A fix that looks like an improvement but is a silent regression
- A failure whose symptom pointed somewhere unrelated to its cause
- A trap that will re-set itself for the next person

ENTRY SHAPE
## <The lesson stated as a claim>
<What happened. Why the intuitive reading is wrong. What the real signal is.
What to do instead — and, if the wrong fix is tempting, why it's wrong.>
→ `path/to/file`

The most valuable entries carry a WARNING AGAINST THE OBVIOUS FIX. A lesson
that only says "X was broken, we fixed it" doesn't stop the next person from
un-fixing it.

Where a lesson is worth enforcing, pin it with a test and say so in the entry.
Prose degrades; a red test does not.
-->

## `unstructured`'s markdown/HTML loader silently needs extra NLTK data not bundled with pip
`DirectoryLoader(glob="*.md")` (used by `create_database.py`'s
`load_documents()`) worked fine at container build/import time, then failed
at first actual use with `LookupError: Resource 'punkt_tab' not found`. The
error only surfaces when a real `.md`/`.html` file is partitioned — nothing
in `requirements.txt` or the import graph signals this dependency exists.
Fixing it one resource at a time is a trap: after downloading `punkt_tab`,
the very next run failed again on a *different* missing resource
(`averaged_perceptron_tagger_eng`), because `unstructured`'s sentence
tokenizer and POS tagger are each looked up lazily on first use, not
validated upfront. Don't chase these one at a time in the running container —
download both in the `Dockerfile` (`python -m nltk.downloader punkt_tab
averaged_perceptron_tagger_eng`) so it's part of the image and survives
rebuilds; a container-only `nltk.download()` fix disappears on the next
`docker compose up --build`. → `Dockerfile`

## A single `save_to_pgvector()` call can exceed the OpenAI embeddings TPM limit
Indexing `alice_in_wonderland.md` (170KB, 801 chunks) whole in one
`PGVector.from_documents()` call failed with `RateLimitError: tokens per
minute (TPM): Limit 40000, Requested 45575` — not an auth or quota problem
(credits were confirmed present), and not obvious from the error alone that
it's a *batch size* issue rather than an account-level block. `save_to_pgvector`
→ `create_vector_store_from_documents` → `PGVector.from_documents` embeds
every chunk's text in one request with no batching. A full customer folder
could plausibly exceed this the same way a full book did. Workaround used
for the sanity check: index a small text slice instead of the whole file.
Real fix, not yet implemented: batch `save_to_pgvector` calls (e.g. embed in
groups of chunks under the account's TPM limit) if real customer folders turn
out to be large enough to trip this. → `vector_store.py`, `create_database.py`

## `PGVector.from_documents([])` doesn't no-op on an empty list — it throws
Calling `save_to_pgvector([])` (empty chunk list — e.g. a customer folder
with zero ingestible files) doesn't skip the write like an empty loop would
suggest. It still issues one INSERT with no row data and fails with
`psycopg.errors.NotNullViolation: null value in column "id"` — a raw
library/SQL error, not anything that names "empty input" as the cause.
Nothing upstream (`split_text([])`, `set_context_tag([], ...)`) raises first,
so the failure only surfaces at the DB call, several functions removed from
where the empty list originated. Don't chase this by looking for a bug in
`split_text`/`set_context_tag` — both correctly return `[]` unchanged;
`PGVector.from_documents` is the one that assumes a non-empty batch.
`ingest.py`'s `run_ingestion()` now guards against this by checking
`if not results:` right after `read_local_files()` and returning early with a
clean "no ingestible files" message — any other caller of
`save_to_pgvector`/`PGVector.from_documents` needs the same guard, since the
library itself doesn't provide one. → `ingest.py`

## Re-running ingestion does not retroactively fix already-ingested files
Fixing a chunking/extraction bug (e.g. the header-loss bug fixed for `.xlsx`,
see `docs/ARCHITECTURE.md`) does not automatically repair a customer's
already-indexed data — the natural assumption "ship the fix, click Ingest
again" silently does nothing for unchanged files. `ingest.py`'s dedup logic
(`_get_indexed_file_hashes`, `indexed.get(source) == file_hash`) skips any
file whose content hash already matches what's indexed, and a code change
doesn't touch the file's bytes, so the hash is identical and the file is
skipped every time — the stale, buggy chunks stay in Postgres indefinitely,
mixed in with correctly-chunked data from any newly-ingested file. This
surfaced when re-ingesting the real Teva folder after the `.xlsx` header fix:
the CLI reported "3 unchanged files skipped," confirming the fix had not
actually reached the live data despite the code being correct and deployed.
The old chunks must be explicitly deleted (`DELETE FROM
langchain_pg_embedding WHERE cmetadata->>'context_tag' = ... AND
cmetadata->>'source' = ...`) before re-running ingestion, for every file
whose *processing logic* changed even though its *bytes* didn't. Don't chase
this by looking for a bug in the new extraction/chunking code — it's correct;
the bug is that old rows were never told they're stale. → `ingest.py`
