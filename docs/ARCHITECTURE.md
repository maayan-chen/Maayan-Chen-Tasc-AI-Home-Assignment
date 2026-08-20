# Architecture Decisions

Pointers to decisions and their rationale — not a description of the code.
Read the code for how; read this for why. These are also the interview
talking points for this assignment (see `PRD.md`).

## `context_tag` is the sole customer-scoping mechanism
One indexed JSONB metadata field on each chunk, filtered on at query time.
Chosen because customer isolation only needs to be logical, not physical — no
per-customer tables or pgvector collections. Rejected: separate collections
per customer, which would need dynamic collection creation/lookup for no real
isolation benefit at this scale. Cost: a bug in the filter leaks across
customers, so this one field is the entire trust boundary. → `vector_store.py`, `create_database.py`

## Direct in-process Python calls instead of HTTP hops within the same codebase
Both ingestion→RAG and chat→RAG import and call `vector_store.py` /
`create_database.py` functions directly, rather than exposing an HTTP API.
HTTP buys language/process decoupling, which isn't needed when agent and RAG
store are the same codebase — an extra network hop adds serialization and an
"is the server up?" failure mode for no benefit. Cost: if the RAG store ever
needs to be a separately-owned service, this coupling has to be undone.

Nivs-RAG's `api.py` was removed rather than kept as an unused "escape hatch":
it was unauthenticated and let `context_tag` be omitted or spoofed on both
`/index` and `/query`, meaning any caller could read or write any customer's
data. Since it was also the container's actual `CMD` (port 8000 exposed), it
wasn't dead code — it was a live, unscoped read/write path sitting on top of
the one field this tool depends on for trust. There is no HTTP surface in
this project; add one deliberately, with auth and mandatory `context_tag`, if
a real need for a separately-owned RAG service ever arises.
→ `ingest_agent.py`, `app.py`, `Dockerfile`, `docker-compose.yml`

## No LLM-driven relevance filtering at ingestion
Everything found (local files + web search result) gets indexed unfiltered;
relevance is computed once, at query time, via vector similarity +
`min_relevance`. Rejected: an LLM judgment pass at ingestion to decide what's
"relevant enough" to index — this adds an unexplainable judgment layer and a
second place things can silently go wrong. Cost: some low-signal content ends
up in the store, relying entirely on retrieval-time filtering to keep answers
grounded. → `ingest_agent.py`

## Agent scope is deliberately narrow
The LLM/tool-calling agent (`create_tool_calling_agent` + `AgentExecutor`)
only formulates a web search query from the customer name/local file skim and
optionally synthesizes a short briefing paragraph. File reading and the
write-to-pgvector path are plain deterministic Python, not agent tool calls.
Rejected: giving the agent tools for file reading and indexing too — harder
to debug, harder to narrate step-by-step in an interview. Cost: less
"impressive" as an agent demo, but every step is inspectable. → `ingest_agent.py`, `ingest_tools.py`

## Streamlit, single app with two tabs
Chosen over a custom React/HTML frontend: zero frontend build step,
`streamlit run app.py`, looks like a real chat app via `st.chat_message`, and
every line is plain Python walkable in an interview. One app with
`st.tabs(["Ingest", "Ask"])` means no separate ingestion tool to install or
run. Cost: no native OS folder-picker dialog for a server-side path — the
folder input is a text field, not a browse button. → `app.py`

## Customer name is always explicit user input, never inferred
Both the folder path and typed customer name persist across runs (written to
`.last_ingest.json`), but the name itself is never guessed from the
folder/project name. Rejected: inferring customer identity from the folder
name — a project folder is normally named after the project, not the
customer, and a wrong guess would silently mis-scope data between customers,
which is the one thing this tool depends on for trust. Cost: one extra typed
field on first run per customer; free on every re-run after. → `app.py`

## Meeting notes and web search are the only external context sources
No calendar/notes-tool integration, no email integration. Meeting summaries
are just files a consultant drops in the folder, treated identically to
project files. Rejected: building real OAuth integrations for calendar/email
— would burn the entire 2-day budget on plumbing unrelated to the core
RAG/agent skill being demonstrated. Cost: the tool only knows what's already
been written down in the folder or is publicly findable on the web. → `ingest_tools.py`

---

## Gap: no automated tests
This is a 2-day take-home assignment: verification is manual (see `PRD.md`
§11 Success Criteria — CLI wrapper run, `psql` check, UI walkthrough), not a
pytest suite.

**This is a scope gap, not an oversight.** Deliberate call given the time
budget; a real production version of this tool would need tests around
`context_tag` scoping specifically, since that's the trust boundary.

1. Ship as-is with manual verification steps documented in `PRD.md` — chosen, matches the assignment's actual time budget.
2. Add a minimal pytest for `context_tag` isolation only — costs an hour+ Day 2 doesn't have to spare.

→ `PRD.md`

## Images are always OCR'd, no LLM pre-classification
`.png`/`.jpg`/`.jpeg` files found in a customer folder are always routed
through `pytesseract` — no vision-model step decides first whether an image
"looks like text" (a slide/screenshot) versus a photo or diagram. Rejected:
an LLM vision call to classify each image before deciding whether to OCR it.
That would reintroduce the same ingestion-time LLM judgment layer already
rejected for relevance filtering (see above), and it doesn't prevent a real
failure mode — OCR on a non-text image just yields empty/garbled text, which
is harmless and gets filtered out at query time by `min_relevance` like any
other low-signal chunk, the same way a low-quality OCR'd PDF page is handled.
A misclassified image (real slide marked "not text" and skipped) would be a
worse, silent failure than always-OCR's worst case. Cost: OCR runs on some
images that turn out to have no useful text — cheap and local, not worth
avoiding. → `vector_store.py`

## Image OCR uses `lang="heb+eng"`; PDF OCR fallback uses `lang="heb"`
The two OCR call sites use different Tesseract language settings, and this is
deliberate, not an inconsistency. PDF OCR only fires when a PDF's existing
text layer is untrustworthy (see `context_tag`-adjacent note above on
detection) — by the time OCR runs, the document's language is already known
(Hebrew, per the validated real-world case), so `lang="heb"` is correct and
`lang="heb+eng"` was already shown to introduce extra misreads on pure-Hebrew
text. A dropped-in image (chat/email screenshot, slide export) has no such
prior — it's whatever a consultant happened to paste into the folder, and can
be pure English, pure Hebrew, or a mix in the same image. Confirmed against
two real screenshots: `lang="heb"` badly garbled an all-English email
screenshot (readable text turned into near-random Hebrew-like glyphs), while
`lang="heb+eng"` correctly read both an all-English screenshot and an
all-Hebrew one. Rejected: a single shared `lang` setting for both call sites
— whichever choice is picked, one of the two real cases already observed in
testing degrades badly. Cost: two hardcoded language strings to keep straight
instead of one — worth it since guessing wrong on either path produces
unusable text, not just marginally worse text. → `vector_store.py`
