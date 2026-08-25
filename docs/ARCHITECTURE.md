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
HTTP buys language/process decoupling, which isn't needed when ingestion/chat
and the RAG store are the same codebase — an extra network hop adds serialization and an
"is the server up?" failure mode for no benefit. Cost: if the RAG store ever
needs to be a separately-owned service, this coupling has to be undone.

Nivs-RAG's `api.py` was removed rather than kept as an unused "escape hatch":
it was unauthenticated and let `context_tag` be omitted or spoofed on both
`/index` and `/query`, meaning any caller could read or write any customer's
data. Since it was also the container's actual `CMD` (port 8000 exposed), it
wasn't dead code — it was a live, unscoped read/write path sitting on top of
the one field this tool depends on for trust. `models.py` (the Pydantic
request/response schemas `api.py` alone consumed) was deleted in the same
pass once it had zero remaining importers — a leftover file with no runtime
path is worth removing on sight, same as any other dead code. There is no
HTTP surface in this project; add one deliberately, with auth and mandatory
`context_tag`, if a real need for a separately-owned RAG service ever
arises. → `ingest.py`, `app.py`, `Dockerfile`, `docker-compose.yml`

## No LLM-driven relevance filtering at ingestion
Everything found in the local folder gets indexed unfiltered; relevance is
computed once, at query time, via vector similarity + `min_relevance`.
Rejected: an LLM judgment pass at ingestion to decide what's "relevant
enough" to index — this adds an unexplainable judgment layer and a second
place things can silently go wrong. Cost: some low-signal content ends up in
the store, relying entirely on retrieval-time filtering to keep answers
grounded. → `ingest.py`

## No LLM/agent step in ingestion — web search was cut entirely
Ingestion is 100% deterministic: read local files, chunk, tag, save. There is
no `create_tool_calling_agent`/`AgentExecutor` anywhere in this project.
Originally planned: an agent that formulates a web search query from the
customer name, runs `DuckDuckGoSearchRun`, and optionally synthesizes a short
briefing. Cut before implementation once it was clear the "agent" reduced to
one fixed query pattern (`f"{customer_name} company"`) driving a single tool
call — functionally identical to a consultant Googling the company
themselves, with no judgment the agent was actually adding. That fails this
project's central test (`CLAUDE.md`: "every architectural choice needs its
own justification, or cut it") — an `AgentExecutor` wrapping one
deterministic call is a layer that can't be narrated as anything other than
"we added an LLM call for no reason." Also removes a live flakiness/rate-limit
risk (`duckduckgo-search`) and a dependency, for zero functional loss — the
local project files (specs, notes, meeting summaries) are the actual source
of truth for a handoff, not a generic web scrape a chatbot could produce
anyway. Rejected alternative: keep a trivial *non-agentic* web search (one
plain `DuckDuckGoSearchRun.run(customer_name)` call, no LLM) — even that was
cut since it adds a moving part for content low-value enough that it doesn't
change what a consultant can ask the tool. Revisit only if there's a concrete
task an agent does that a script can't (e.g. skimming local files first to
target searches at actual content gaps, not just the customer name) — until
then, adding it back means re-justifying it from scratch. → `ingest_tools.py`

## Non-Hebrew documents are translated to Hebrew at ingestion — the one deliberate exception to "no LLM step in ingestion"
`ingest.py` runs each extracted document through
`translate_to_hebrew_if_needed()` before chunking: a cheap character-range
heuristic (`_is_hebrew()`, same style as `_is_text_unreliable()`) checks
whether the text is already majority-Hebrew, and only documents that aren't
get one `gpt-4o` translation call. This looks like exactly the kind of
ingestion-time LLM step already rejected twice above (relevance filtering,
web-search agent) — it isn't, and the distinction matters enough to spell
out rather than let this read as a quiet rule violation. Both earlier
rejections were about *judgment*: an LLM deciding what's relevant enough to
index, or what's worth searching for — open-ended calls with no fixed
correct answer, and a second place things can silently go wrong. Translation
is a fixed, meaning-preserving transform with a checkable outcome (the
Header: value structure, numbers, and names all round-trip intact — verified
against a real xlsx org-chart export), not a judgment call about what to
keep.

The concrete problem this fixes: OpenAI's embedding model places
same-language paraphrases much closer together (~0.95–0.98 cosine
similarity, measured directly) than cross-lingual same-meaning text
(~0.88) — real semantic overlap, but a consistent gap. In a mixed-language
customer folder, that gap is large enough to silently bias retrieval by
*source language* rather than relevance: a Hebrew question measurably
under-retrieved an English-only source document (`Consulting_Services_Agreement.pdf`)
that a same-language query surfaced easily, even with both individually
clearing `min_relevance`. Translating the minority language into the
majority collapses every chunk into one embedding neighborhood, so retrieval
ranks purely on relevance again. Hebrew, not English, is the ingestion
target because most real customer files are already Hebrew and
Hebrew-Hebrew similarity measured tighter than English-English — normalizing
the minority of files is both cheaper and lower-risk than normalizing the
majority.

Rejected: translating the *query* instead of the documents (embed both a
Hebrew and an English version of every question, merge results) — leaves
ingestion untouched, which fits "no LLM step in ingestion" without
exception, but does nothing for two documents in different languages that
already have low mutual similarity; it only helps a query reach docs in its
*other* language, not documents reach each other. The actual failure mode
observed was documents siloed by language, not questions failing to cross a
language boundary. Cost: one more ingestion-time LLM call for non-Hebrew
files specifically (a minority, per the above), a live dependency on
translation quality (mistranslation is a new, no longer git-diffable failure
mode — the DB no longer holds the source document's literal words), and
content that reads as authored in Hebrew from the start
even where it was originally English, which the UI does not currently
disclose. → `ingest.py`, `vector_store.py`

## Chat answers are formatted with Markdown and instructed to match the question's language — reliable for Hebrew, not for English
`PROMPT_TEMPLATE` (`query_rag.py`) asks the model to break answers into
short paragraphs and bullet/numbered lists instead of one dense block, and
to answer in the same language as the question, stated both at the very top
of the prompt and restated immediately before generation. `app.py` already
renders assistant messages with `st.markdown()`, so this needed no UI
change — the model's own bullet/heading syntax renders directly.

The language instruction is a known, incomplete fix, not a clean win: with
translation-at-ingestion (see above) normalizing most of the store to
Hebrew, a Hebrew question reliably gets a Hebrew answer (4/4 in testing across
multiple rewordings), but an English question now often gets answered in
Hebrew anyway — a regression from before translation-at-ingestion existed,
when most retrieved context was still in its original, more varied
language. Confirmed this is a genuine model-following limit, not a wording
problem: bracketing the instruction (top + immediately pre-generation),
moving it into a system message, explicitly naming "detect the question's
language" as the rule, and lowering `k` to reduce how much Hebrew text
surrounds the instruction were all tried — none reliably fixed the English
case without this exact combination re-breaking the Hebrew case tested
first. The volume of same-language context in the prompt outweighs an
explicit instruction about a different field's language.

Accepted as-is because real usage is expected to be Hebrew-majority (see
translation-at-ingestion above) — optimizing for the common case over the
rare one. Rejected: chasing a fully general fix by detecting the question's
language in code first (same `_is_hebrew()`-style heuristic already used at
ingestion) and hard-coding it into the prompt as a fact rather than asking
the model to infer it — untested; the likely next thing to try if the
English-question case turns out to matter more than expected. → `query_rag.py`

## Streamlit, single app with sidebar Ingest + main-page Ask
Chosen over a custom React/HTML frontend: zero frontend build step,
`streamlit run app.py`, looks like a real chat app via `st.chat_message`, and
every line is plain Python walkable in an interview. Originally
`st.tabs(["Ingest", "Ask"])`; switched to `st.sidebar` for Ingest + the main
page for Ask once real usage showed `st.chat_input` only docks to the true
bottom of the viewport when it isn't nested inside a tab's content container
— inside `st.tabs`, it scrolls away with the message history instead of
staying pinned, which reads as broken next to any normal chat UI (terminal,
Slack, etc.). Moving Ingest to the sidebar frees the main page for Ask alone,
so `st.chat_input` can be called at the top level and dock properly. Also
means switching customer is now a rare, low-visual-weight action (a "Change
customer" popover next to the "Asking about: X" pill) rather than a dropdown
sitting in the main flow — matches how infrequently a consultant actually
switches customers mid-session. Cost: no native OS folder-picker dialog for a
server-side path — the folder input is a text field, not a browse button.
→ `app.py`

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

## Spreadsheet rows are chunked row-aligned, not by the shared character splitter
`.xlsx`-sourced documents bypass `create_database.py`'s `split_text()`
(the single, file-type-agnostic `RecursiveCharacterTextSplitter`, chunk_size
300) entirely; `ingest.py`'s `_chunk_xlsx_documents()` instead splits on `"\n"`
so each chunk is exactly one table row. Chosen because character-based
chunking is provably wrong for tabular data: a 300-char window slices
mid-table with no concept of row boundaries, severing a value from the header
row that names its column (confirmed against real Teva data — a chunk
containing `495000` with no indication whether that's a salary or an employee
level). This is the first file-type-specific chunking branch in the codebase
— previously `split_text()` was implicitly "one strategy for everything."
Rejected: keep the shared splitter and rely on chunk overlap to preserve
header context — overlap only helps when the header lands within one
chunk_size window of the row using it, which breaks on any sheet with more
than a handful of rows. Cost: two chunking code paths to keep in sync instead
of one — worth it since the bug this fixes was silently wrong answers, not a
crash. → `ingest.py`, `vector_store.py`

## xlsx header row is detected by heuristic, not assumed to be row 1
`_extract_xlsx()` treats the first row with more than one non-empty cell as
a sheet's header row, rather than unconditionally using
`sheet.iter_rows(values_only=True)`'s first yielded row. Chosen because every
real Teva xlsx file has 1–4 title/banner rows (a single non-empty cell, e.g.
"Teva HQ Finance — Org Redesign...") and often a blank row before the actual
column headers — confirmed by direct inspection, not assumption. Taking row 1
literally would have labeled every data row with banner text as its "header"
(e.g. `טבע תעשיות פרמצבטיות...: 620000`), which is worse than the original
bug: confidently wrong field names instead of no field names. Rejected: a
fixed row-skip count (e.g. "always skip the first N rows") — brittle across
sheets with a different number of banner rows, and one of the real files
(`Compensation Cost Summary`) has zero banner rows before its header, so a
fixed skip would misfire in the opposite direction. Cost: a sheet whose real
header row happens to have only one non-empty cell (single-column table) is
misdetected — not observed in real data, and a single-column table has no
column-mixup failure mode to begin with, so this is an acceptable gap.
→ `vector_store.py`

## Chat history is folded into retrieval by concatenation, not an LLM query-rewrite step
`answer_question()` accepts the last `HISTORY_TURNS` (2) exchanges and prepends
their raw text to the current question before both the similarity search and
the final prompt. Chosen to fix a real bug: "What is Ronit's role?" followed
by "what's her salary?" retrieved nothing useful, since the second question
alone has no "Ronit" for the embedding to match against. Rejected: an LLM call
that rewrites the follow-up into a standalone question (e.g. "What is Ronit's
salary?") before searching — better retrieval on more ambiguous follow-ups,
but it's a second LLM call per question and reintroduces the kind of
ingestion-adjacent judgment layer already rejected elsewhere in this project
(see "No LLM-driven relevance filtering," "No LLM/agent step in ingestion,"
above) — this one just at query time instead. Plain concatenation is one
sentence to explain ("we paste the last couple messages onto the question
before searching and before asking the model") and needs no new dependency or
call. Cost: works well for short pronoun/reference follow-ups (the observed
case); degrades on longer conversations that drift across multiple topics,
since old, now-irrelevant turns get embedded alongside the real question.
→ `query_rag.py`, `app.py`

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

## Framing broadened from "handoff-only" to general customer research — no architectural change
The product framing (mission statement, target personas, UI headline) moved
from "help a new team pick up an existing customer at handoff" to "make
everything a TASC team knows about a customer queryable," covering ongoing
research on a live engagement, not just the one-time handoff moment.
`context_tag` scoping, the ingestion pipeline, and retrieval are all
untouched — this is a persona/positioning change, not a functional one.
Handoff is still one instance of "research" under the broader framing (a
new team researching a customer they just inherited), so nothing in the
old handoff-specific design (e.g. the departing-consultant ingestion story)
had to be walked back, only generalized. Rejected: keeping two separate
framings (a "handoff mode" and a "research mode") — there is no behavioral
difference between them, so a mode toggle would be a UI element with
nothing real behind it, the same kind of unexplainable layer this project
avoids elsewhere. → `PRD.md`, `CLAUDE.md`, `STATE.md`, `app.py`
