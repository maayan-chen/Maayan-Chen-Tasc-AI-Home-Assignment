# Execution Report: Phase 3 — Streamlit App

## Meta Information

- Plan file: `.agents/plans/phase-3-streamlit-app.md`
- Files added:
  - `app.py` (163 lines)
  - `query_rag.py` (40 lines)
  - `.streamlit/config.toml` (6 lines)
- Files modified:
  - `ingest.py` (+52/-3 net, incl. `slugify()` from the plan plus an
    unplanned per-file dedup layer)
  - `read_local_files.py` (+4/-2, extended to also return a per-file content
    hash)
  - `docs/ARCHITECTURE.md` (+20/-5, documents the Ask-tab layout reversal and
    the sidebar switch)
- Lines changed: +911 -15 (includes the 630-line plan file itself, committed
  alongside the code per this repo's convention of keeping `.agents/plans/`
  in git)

## Validation Results

- Syntax & Linting: ✓ `python -m py_compile app.py query_rag.py ingest.py
  read_local_files.py` — clean at every edit pass.
- Type Checking: N/A — no type-checking step configured for this project.
- Unit Tests: ✓ `slugify()` assertions from the plan's Level 2
  (`'Acme Retail'` → `'acme-retail'`, `'  Ac--me!! Co '` → `'ac-me-co'`,
  `'---'` → `''`) — all passed. No pytest suite (documented scope gap).
- Integration Tests: **partial** — see Challenges below. `list_customers()`
  verified live against real Postgres (`['teva']` before cleanup, `[]` after).
  The plan's Level 3 (`python ingest.py --customer ... --folder ...` against
  the real Teva folder) was never run in this session — blocked by the
  environment's permission classifier (writes to Postgres/OpenAI). Level 4
  (manual browser walkthrough) was not completed by the agent either —
  Chrome browser automation was unavailable (extension not connected), so
  the actual click-through was handed to the user rather than verified
  directly.

## What Went Well

- The plan's four-file shape (`app.py`, `query_rag.py`,
  `.streamlit/config.toml`, `ingest.py` slugify) was implemented essentially
  as specified on the first pass — priming the session against the plan
  before touching code meant zero rework on the core retrieval/UI logic.
- `query_rag.py`'s mirror-not-refactor relationship to `query_data.py` held
  up exactly as planned: same retrieval shape, added `filter` kwarg and
  richer `sources`, `query_data.py` left untouched.
- The `context_tag`-as-sole-scoping-mechanism constraint was respected
  throughout every later change (dedup, UI restructure) without needing a
  correction — new fields added (`file_hash`) were justified as per-file
  bookkeeping, not scoping, and no second lookup table or `display_name`
  field was introduced despite several UI reshuffles that could have
  tempted one.
- Read-only DB inspection (`psql` checks on `cmetadata`) caught a stale
  assumption in both the plan and `STATE.md` before it caused any bug: the
  plan predicted Phase 2's existing rows might carry a non-slugified raw
  customer-name tag; the real data was already `context_tag='teva'`,
  simplifying the migration story for the later dedup work instead of
  complicating it.

## Challenges Encountered

- **No live write access in this session.** Both `python ingest.py --customer
  ... --folder ...` (real ingestion) and the Chrome browser tools were
  unavailable — the former blocked by the permission classifier (writes
  real data to Postgres/OpenAI), the latter because the extension wasn't
  connected. This meant Level 3 and Level 4 of the plan's own validation
  strategy could only be partially substituted with read-only Postgres
  queries and `py_compile`/unit-test checks, not the real end-to-end
  ingest-then-ask flow the plan calls for. The user ended up doing the
  actual UI verification and dedup logic exercising outside this
  conversation.
- **`st.chat_input` inside `st.tabs` silently breaks bottom-docking.** This
  wasn't visible from reading the plan or the code — it only surfaces as a
  live behavioral difference (input scrolls with messages instead of
  pinning to the viewport bottom) once actually run in a browser. Caught
  because the user reported it, not because any of the available
  validation tooling (`py_compile`, unit tests, read-only SQL) could have
  caught it — a real gap in what this session could verify unassisted.

## Divergences from Plan

**Ask tab replaced with sidebar Ingest + main-page Ask**
- Planned: `st.tabs(["Ingest", "Ask"])`, both tabs as originally scaffolded
  and validated in the Phase 3 plan.
- Actual: Ingest moved into `st.sidebar`; Ask now owns the full main page,
  with `st.chat_input` called at the top level (outside any container).
- Reason: `st.chat_input` only docks to the true bottom of the viewport when
  it isn't nested inside a tab's content container — inside `st.tabs` it
  scrolls away with the message history, which the user flagged as broken
  next to any normal chat UI. There is no way to keep both `st.tabs` and a
  properly page-docked `chat_input` in current Streamlit. `docs/ARCHITECTURE.md`
  was updated in the same pass to record this as a deliberate reversal, not
  an oversight.
- Type: Plan assumption wrong (the plan assumed tabs + chat_input would
  compose cleanly; they don't) — surfaced only through actual browser use,
  not code review.

**Customer selection changed from a plain dropdown to a pill + popover**
- Planned: `st.selectbox` for customer choice, always visible above the chat,
  gating chat visibility.
- Actual: "Asking about: X" pill is the default state; a "Change customer"
  `st.popover` next to it reveals the dropdown only when opened.
- Reason: explicit user framing — switching customers is a rare action ("once
  in a few months"), so a dropdown with constant visual weight in the main
  flow overstates how often it's used. This is a UX judgment call from the
  user, not a bug or plan error.
- Type: Other (explicit user preference, discovered only through
  conversation, not derivable from the plan or codebase).

**Per-file content-hash dedup added to ingestion — not in the plan at all**
- Planned: the Phase 3 plan does not mention re-ingestion behavior; Phase 2's
  `run_ingestion()` had no duplicate-detection, and nothing in Phase 3's scope
  called for adding it.
- Actual: `read_local_files()` now also returns a `sha256` hash per file;
  `run_ingestion()` looks up each file's previously-indexed hash
  (`cmetadata->>'file_hash'`, scoped by `context_tag`) and skips unchanged
  files, deletes+replaces changed ones, and adds new ones — a full three-way
  branch that didn't exist in any prior phase.
- Reason: user-identified gap — re-running ingestion on an unchanged folder
  (a realistic action with no "already done" guard in the UI) silently
  duplicated every chunk, which would corrupt retrieval ranking over time.
  Confirmed as a real, not hypothetical, risk: Phase 2's own `STATE.md`
  already recorded two ingestion runs of the same folder producing 334 rows
  (167×2) as "deliberate," which is exactly the failure mode this closes.
- Type: Plan assumption wrong at the phase-boundary level — Phase 2's
  omission was implicitly carried into Phase 3's scope as "not our problem,"
  but the new Ingest UI (a clickable button, not a one-shot CLI invocation)
  makes accidental re-ingestion far more likely than the original CLI
  workflow did, which the plan didn't account for.

**Reverted: Ingest form wrapped in `st.form` with a submit button**
- Planned: not in the plan (an in-session request, not a plan item) — noted
  here because it was implemented, then explicitly reverted at the user's
  request ("revert, its worse").
- Actual: reverted back to the original plain `st.text_input`/`st.button`
  pattern with live per-keystroke folder validation.
- Reason: wrapping the fields in a form removed the live-as-you-type folder
  validation (forms only report values on submit), which the user judged a
  worse tradeoff than the form's benefit (suppressing the "Press Enter to
  submit" caption). Reverted in the same session, no residual form code left
  behind.
- Type: Other (tried, judged worse by the user, reverted — a real example of
  an in-session dead end, not a plan divergence).

## Skipped Items

- **Plan's Level 3 integration test** (re-running `ingest.py` CLI against the
  real Teva folder) — skipped because the permission classifier blocked the
  write. Not re-attempted after the block; no alternative write path was
  tried (e.g. asking the user to grant the permission explicitly).
- **Plan's Level 4 manual UI walkthrough** — skipped by the agent (Chrome
  automation unavailable); handed to the user instead, whose subsequent
  feedback (chat_input docking, customer-picker weight, form revert) shows
  the walkthrough did happen, just not through this session's own tooling.
- **Slug-collision detection, per-format source locations, `display_name`
  field, automated tests** — all explicitly out-of-scope per the plan's own
  "Deliberately deferred" section; none were revisited or accidentally
  reintroduced.

## Recommendations

- **Plan command improvements**: a plan that specifies a Streamlit layout
  (tabs, columns, sidebar) should flag layout/widget interactions that are
  known Streamlit gotchas — e.g. `st.chat_input` + `st.tabs` — if a "confirm
  this composes correctly in a live browser before treating the Level 4 step
  as a checkbox" note had been in the plan, this would have been caught
  before commit instead of after, in a follow-up correction round.
- **Execute command improvements**: when a plan's own validation levels
  (Level 3/4 here) can't actually be run in the current session (permission
  blocks, missing tool connections), the execution report should say so
  explicitly *before* declaring the feature done, not just note it
  retrospectively in this report. In this session the Phase 3 work was
  effectively handed to the user to validate live, which worked out, but
  the gap wasn't flagged loudly enough in the moment.
- **`CLAUDE.md` additions**: consider adding "re-ingestion of an unchanged
  folder must not duplicate data" as an explicit standing requirement (like
  the existing `context_tag`-scoping rule), since it was discovered
  reactively here rather than being a known constraint going in — future
  ingestion-adjacent phases would benefit from it being stated up front
  rather than rediscovered.
