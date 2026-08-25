# Feature: Submission roadmap page (`Submission/roadmap.html`)

The following plan should be complete, but it's important that you validate
documentation, codebase patterns, and task sanity before you start implementing.

This is a **static HTML deliverable**, not application code — most of this
template's codebase-pattern-mining and testing-strategy sections don't apply
in their usual form. They're adapted below to fit a single self-contained
artifact page instead of forced onto a shape that doesn't fit.

## Feature Description

A single self-contained HTML page (`Submission/roadmap.html`) that visually
explains the Customer Research RAG Tool to assignment reviewers: how the repo
is laid out, how ingestion and retrieval actually work, who it's for, and
which architectural calls were made on purpose. Modeled on
`References/handoff-roadmap.html`'s visual language and interaction pattern
(condensed paper/ink theme, sticky Plain/Technical toggle, hand-coded inline
SVG diagrams, `<details class="tech">` collapsibles) but built entirely from
this project's real files, decisions, and screenshots — nothing invented.

## User Story

As an assignment reviewer (TASC AI Team),
I want a single page that shows me how this system works and why it was built
this way, without reading source code first,
So that I can evaluate the submission's design quality and defensibility in
minutes, not by reverse-engineering the repo myself.

## Problem Statement

The repo currently explains itself through `README.md`, `PRD.md`, and
`docs/ARCHITECTURE.md` — all text-only, requiring a reviewer to piece
together the pipeline and the "why" behind each choice by reading multiple
files. There's no single visual artifact that shows the system at a glance
and doubles as interview-prep material for the person defending it.

## Solution Statement

Build one static, self-contained HTML page reusing `References/handoff-roadmap.html`'s
proven visual system (already validated as effective for exactly this kind
of "explain a codebase to a reviewer" job) and fill it with this project's
actual content: real repo file map, three hand-drawn SVG diagrams (ingestion
pipeline, ask pipeline, new-advisor user journey), a "decisions that will
surprise you" section pulled from `docs/ARCHITECTURE.md`, a stack-at-a-glance
strip, a customer-isolation proof, embedded real screenshots as live-example
evidence, and a narrow, honest limitations section. Delivered as a repo file
in `Submission/` (self-contained, screenshots as base64 data URIs) and
additionally published as an Artifact for a shareable preview link.

## Feature Metadata

**Feature Type**: New Capability (documentation/deliverable, not app code)
**Estimated Complexity**: Medium (no logic risk, but three custom SVG
diagrams and careful content curation from existing docs)
**Primary Systems Affected**: None — purely additive, `Submission/` only.
Zero interaction with `app.py`/`ingest.py`/`query_rag.py`/DB.
**Dependencies**: None new. Pure HTML/CSS/inline-SVG/vanilla JS, no build
step, no external network calls (Google Fonts optional, skip if not already
proven acceptable — see Patterns to Follow).

---

## CONTEXT REFERENCES

### Relevant Codebase Files — READ THESE BEFORE IMPLEMENTING

- `References/handoff-roadmap.html` (lines 1–350, CSS shell) — Why: the
  entire visual system to reuse: CSS custom properties for light/dark theme
  (`:root`, `@media (prefers-color-scheme: dark)`, `:root[data-theme="dark"]`
  triad), condensed-font headers, `.tree`/`.pillar`/`.screen`/`.tech`
  component styles, `.toggle` button styling.
- `References/handoff-roadmap.html` (lines 417–459, `#repo` section) — Why:
  exact pattern for "Finding your way around the repository" — a
  `<div class="tree">` monospace block with inline `<span class="dir">` and
  `<span class="note"># comment</span>` annotations, plus one
  `<details class="tech">` "for developers" note below it. Mirror this
  structure with this repo's real files (see New Files / repo tree below).
- `References/handoff-roadmap.html` (lines 546–616, `#flow` section) — Why:
  the exact SVG diagram pattern to mirror for both pipeline diagrams —
  `<svg viewBox="0 0 860 300" role="img" aria-label="...">` with a full
  plain-English description in `aria-label` (do this for accessibility and
  because it doubles as alt-text for the Plain-mode reader), a single
  `<marker id="arrow">` reused via `marker-end="url(#arrow)"`, boxes as
  `<rect>` + centered `<text>` pairs, `class="diag-accent"` /
  `class="diag-warn"` for calling out the one LLM step vs. a caution note,
  dashed feedback paths (`stroke-dasharray="4 3"`), and a plain-English
  `<figcaption>` below every diagram.
- `References/handoff-roadmap.html` (lines 683–702, `#throughline` /
  `.pillars`) — Why: exact pattern for a 3-card grid section
  (`.pillar` / `.num` / `h3` / `p`) — reuse for "Decisions that will
  surprise you" instead of building new card CSS from scratch.
- `References/handoff-roadmap.html` (lines 710–724, closing `<script>`) —
  Why: the exact Plain/Technical toggle JS to reuse verbatim — toggles
  `open` on every `details.tech` and swaps `aria-pressed` on the two buttons.
  No changes needed beyond confirming button IDs match.
- `docs/ARCHITECTURE.md` (all 18 `##` sections, see grep below) — Why:
  primary source for "Decisions that will surprise you" card copy and every
  `.tech` collapsible's content. Do not paraphrase loosely — these are the
  user's actual interview talking points; pull specific claims (numbers,
  rejected alternatives, measured evidence) verbatim or near-verbatim.
  Sections to draw from directly:
  - L7–13 `context_tag` sole scoping mechanism
  - L15–34 direct in-process calls, `api.py` removal (the strongest
    "decision that will surprise you" card — a live spoofing vector was
    removed, not dead code)
  - L36–43 no LLM relevance filtering at ingestion
  - L45–67 web-search agent cut before implementation
  - L69–115 translate-to-Hebrew-at-ingestion (the deliberate LLM exception
    — needed for the "only two LLM call sites" framing, see below)
  - L117–146 Markdown + language-matched answers; **the known English→Hebrew
    regression** — source for the one limitations-section item the user
    asked to keep
  - L214–230 xlsx row-aligned chunking (good second "surprise" card — a
    confirmed real bug, not a hypothetical)
  - L232–249 xlsx header-row heuristic
  - L251–268 chat history via concatenation, not LLM query-rewrite
- `STATE.md` (whole file, 61 lines) — Why: current, accurate status —
  confirms what's actually shipped vs. planned; use for the stack-at-a-glance
  strip and to avoid claiming anything not actually live.
- `README.md` (whole file) — Why: canonical stack list and command
  reference; source for the "stack at a glance" chip strip content
  (Python, Streamlit, LangChain, OpenAI, Postgres/pgvector, Docker Compose).
- `ingest.py` (whole file, 116 lines) — Why: ground-truth for the ingestion
  diagram's exact step order: `read_local_files()` → hash-based skip/replace
  decision → `translate_to_hebrew_if_needed()` (L73) → xlsx-vs-other branch
  (L82–84, `_chunk_xlsx_documents()` vs `split_text()`) →
  `set_context_tag()` (L85) → `save_to_pgvector()` (L86) → deferred delete
  of replaced files (L92–93, only after save succeeds — worth a diagram
  callout, mirrors the reference's "never blocks the write" callout style).
- `vector_store.py` (whole file, 232 lines) — Why: ground-truth for the
  per-file-type extraction branch in the ingestion diagram —
  `extract_content_from_bytes()` (L183–205) dispatches to `_extract_pdf`
  (OCR fallback on unreliable text, L96–118), `_extract_image` (always OCR,
  L121–127), `_extract_docx` (L130–136), `_extract_xlsx` (header-heuristic +
  row pairs, L139–167), `_extract_pptx` (L170–180). Also
  `translate_to_hebrew_if_needed()` (L217–231) and `_is_hebrew()` (L208–214)
  for the translation diagram step.
- `query_rag.py` (whole file, 85 lines) — Why: ground-truth for the ask-flow
  diagram — `answer_question()` (L44–84): embed question (L51),
  `_recent_history_text()` fold-in (L54, L32–41), similarity search filtered
  by `context_tag` (L57–59), `min_relevance` threshold gate (L60–61,
  worth a diagram callout — this is the "I don't know" branch), prompt
  assembly with XML-tagged documents (L63–75), `ChatOpenAI(model="gpt-4o")`
  call (L77–78), sources returned alongside the answer (L80–83).
- `app.py` (whole file, 204 lines) — Why: source for the "new advisor" user
  journey diagram — sidebar ingest form → customer selector gate
  (L136–159, no chat until a customer exists) → persistent
  "שאלות על: X" pill (L145–152) → chat loop with sources shown via
  click-to-reveal popovers (L161–171). Confirms the actual UI shape so the
  journey diagram doesn't invent screens that don't exist.
- `Submission/CleanShot 2026-08-24 at 10.47.32@2x.png` (2284×1362 PNG,
  281KB) — Why: live-example screenshot #1 — real Hebrew Q&A ("How should I
  approach Ronit? What tone fits her role?") with the `teva` context pill
  and a "מקורות" (sources) expander visible. Embed as base64 data URI.
- `Submission/CleanShot 2026-08-25 at 09.47.16@2x.png` (2256×1364 PNG,
  290KB) — Why: live-example screenshot #2 — a different real question
  ("Tell me about the projects we worked on with Teva") with a structured,
  numbered-list answer citing sources. Embed as base64 data URI.
- `Tasc-logo.png` (6.7KB) — Why: header logo, per user's explicit choice
  (2026-08-25 conversation) to match the reference page's own-logo-in-header
  pattern. Embed as base64 data URI.

### New Files to Create

- `Submission/roadmap.html` — the complete self-contained deliverable page.
  No other files. Screenshots and logo are embedded inline (base64 data
  URIs), not shipped as sibling files, per explicit user instruction
  ("self-contained, embed the screenshots as data URIs").

### Relevant Documentation — READ THESE BEFORE IMPLEMENTING

None external. This page has zero runtime dependencies — no CDN, no
framework, no build step. (If publishing via the `Artifact` tool: the
`artifact-design` skill must be loaded before writing the file, and the CSP
rules on external fonts/assets from that tool apply — see Gotchas below.)

### Patterns to Follow

**Theming (CSS custom properties, light/dark, matches this codebase's own
`artifact-design`/`Artifact`-tool conventions as well as the reference):**
```css
:root { --ink:#17170f; --paper:#f6f3ea; /* ...full light palette... */ }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { --ink:#f2f1e8; --paper:#121210; /* ... */ }
}
:root[data-theme="dark"] { --ink:#f2f1e8; --paper:#121210; /* ... */ }
```
Reuse the reference's exact token names and values — no need to invent a new
palette; this project has no existing brand palette of its own beyond the
Streamlit UI's dark-purple/pink accents (`#1A1230`, `#D6006E` in `app.py`
L54, L66), which is a reasonable **accent substitution** if a "this looks
like the actual app" tie-in is wanted (optional, not required — the
reference's lime works fine standalone).

**Repo tree block** — mirror lines 421–458 exactly in structure:
```html
<div class="tree">
<span class="dir">app.py</span>                    <span class="note"># Streamlit entrypoint — sidebar Ingest + main-page Ask</span>
<span class="dir">ingest.py</span>                 <span class="note"># run_ingestion() orchestration + CLI wrapper</span>
<span class="dir">read_local_files.py</span>        <span class="note"># walks a folder, hashes + reads each file</span>
<span class="dir">vector_store.py</span>            <span class="note"># REUSED — file parsing, OCR, translation, pgvector connection</span>
<span class="dir">create_database.py</span>         <span class="note"># REUSED — split_text(), save_to_pgvector(), set_context_tag()</span>
<span class="dir">query_rag.py</span>               <span class="note"># answer_question() — retrieval + prompt + gpt-4o call</span>
<span class="dir">docker-compose.yml</span>, <span class="dir">Dockerfile</span>, <span class="dir">init.sql</span>  <span class="note"># REUSED — Postgres+pgvector, unchanged</span>

<span class="dir">docs/</span>                     <span class="note"># the why, not the what</span>
  ARCHITECTURE.md              <span class="note">→ every non-obvious design decision, with reasoning</span>
  LESSONS.md                    <span class="note">→ real bugs hit during the build, and how they were caught</span>
STATE.md                          <span class="note">→ project status as of the last working session</span>
PRD.md                              <span class="note">→ full requirements &amp; success criteria</span>
</div>
```
(Fill in remaining rows — `data/`, `.agents/plans/`, `CLAUDE.md` — using
`git ls-files` output already captured in this conversation; do not invent
paths.)

**SVG diagram box:**
```html
<rect x="16" y="120" width="140" height="60" rx="8" fill="none" stroke="currentColor" stroke-width="1.5"/>
<text x="86" y="145" text-anchor="middle" font-size="13" font-weight="700" fill="currentColor">Label</text>
```
Arrows always via the single shared `<marker id="arrow">` def, reused per
diagram (each `<svg>` needs its own `<defs>`/marker since diagrams are
separate `<svg>` elements). Use `class="diag-accent"` (define as
`.diag-accent{color:var(--lime)}` or similar, matching reference's approach
where the SVG uses `currentColor` and a class only changes the color scope)
on the box/step that represents the one LLM call in that diagram, so the
"where's the AI" question is visually self-answering — this is the strongest
diagram opportunity for the "only two LLM call sites" framing the user
confirmed.

**Toggle JS — copy verbatim, no changes needed:**
```js
(function () {
  var btnPlain = document.getElementById('btn-plain');
  var btnTech = document.getElementById('btn-tech');
  var detailsEls = Array.prototype.slice.call(document.querySelectorAll('details.tech'));
  function setMode(tech) {
    detailsEls.forEach(function (d) { d.open = tech; });
    btnPlain.setAttribute('aria-pressed', String(!tech));
    btnTech.setAttribute('aria-pressed', String(tech));
  }
  btnPlain.addEventListener('click', function () { setMode(false); });
  btnTech.addEventListener('click', function () { setMode(true); });
})();
```

**Embedding local images as data URIs (base64):**
```bash
base64 -i "Submission/CleanShot 2026-08-24 at 10.47.32@2x.png" | tr -d '\n'
```
Use in `<img src="data:image/png;base64,{output}" alt="...">`. Do this via a
one-off shell step during implementation, not by hand-typing base64.

---

## IMPLEMENTATION PLAN

### Phase 1: Shell & content skeleton
Copy the reference's CSS shell (theme tokens, typography, `.top`/`.nav`/
`.toggle` header, section spacing rules) into the new file. Build the empty
section skeleton with real headings and nav anchors: repo map, ingestion
diagram, ask diagram, new-advisor journey, decisions-that-surprise, stack
strip, isolation proof, live example, limitations.

### Phase 2: Repo map + text sections
Fill in the "Finding your way around the repository" tree from real
`git ls-files` output. Write the stack-at-a-glance chip strip. Write the
"Decisions that will surprise you" 3–4 card grid, sourced from
`docs/ARCHITECTURE.md` per the file list above — must include the `api.py`
removal, the two-LLM-call-sites framing (translation + answer synthesis,
everything else deterministic), and the xlsx row-chunking bug/fix. Write the
narrow limitations section (English→Hebrew regression + missing per-customer
access control — both per explicit user instruction, nothing else).

### Phase 3: Diagrams
Build the three inline SVGs: (1) ingestion pipeline — folder → per-type
branch (text as-is / image+unreadable-PDF→OCR / xlsx→header-tagged rows) →
Hebrew translation-if-needed (accent-marked as the LLM step) →
`context_tag` stamp → chunk → embed → pgvector; (2) ask pipeline — question
→ embed → `context_tag`-filtered similarity search → `min_relevance` gate →
top-k chunks + folded-in chat history → prompt → gpt-4o (accent-marked) →
answer + sources; (3) new-advisor journey — a simpler horizontal
persona-flow (advisor joins → "what do I need to know?" → asks the system →
gets sourced answer → is oriented), styled more like a journey strip than
the two technical box-diagrams. Each gets a plain-English `aria-label` and a
`<figcaption>`.

### Phase 4: Live evidence
Convert both `Submission/*.png` screenshots and `Tasc-logo.png` to base64,
embed as data URIs — logo in the header, screenshots in the "live example"
section with captions naming the real question asked and the `teva`
context. **Add the customer-isolation proof section once the user supplies
the isolation-proof screenshot/example** (not yet present in `Submission/`
as of this plan — see Notes/Open Items). If still missing when this phase
starts, implement the section with the stated claim in prose
("the same question against two different customers returns two different,
correctly-scoped answers — verified via the two real Teva project folders
ingested under one `context_tag` plus a second test customer") and flag it
to the user as pending the actual screenshot swap-in, rather than blocking
the rest of the page.

### Phase 5: Polish, toggle wiring, validation
Wire the Plain/Technical toggle JS (verbatim from reference). Add
`<details class="tech">` blocks under each major section with the specific
file:line references and the rejected-alternative reasoning from
`ARCHITECTURE.md` (this is what "Technical" mode reveals). Validate in
browser (see Validation Commands). Publish as an Artifact.

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic
and independently testable.

### CREATE `Submission/roadmap.html` — shell
- **IMPLEMENT**: `<title>Customer Research RAG Tool</title>`, full CSS
  shell (theme tokens + typography + `.top`/`.nav`/`.toggle` + section
  spacing), sticky nav with anchor links to every section, Plain/Technical
  toggle buttons (`#btn-plain`, `#btn-tech`).
- **PATTERN**: `References/handoff-roadmap.html` lines 1–116 (CSS `:root`
  triad + base typography) and lines 380–416 (`.top`/`.nav` markup).
- **GOTCHA**: don't hardcode `data-theme` via the reference's
  `<script>document.documentElement.setAttribute('data-theme','light')</script>`
  line 2 — that line forces light-only and defeats dark-mode support; the
  reference does this deliberately for a fixed brand look, but this page has
  no such constraint, so omit it and let `prefers-color-scheme` drive dark
  mode naturally, consistent with `artifact-design` skill conventions for
  Artifact publishing.
- **VALIDATE**: Open the raw file in a browser (`open Submission/roadmap.html`)
  — page renders with header, empty section anchors scroll correctly, no
  console errors.

### ADD "Finding your way around the repository" section
- **IMPLEMENT**: `<div class="tree">` block per Patterns to Follow above,
  using real files from `git ls-files` (already captured this session) —
  do not invent files or paths not present in the repo.
- **PATTERN**: `References/handoff-roadmap.html` lines 417–459.
- **GOTCHA**: the reference's tree separates "what runs" from "planning
  history" (`dev-content/`). This repo's equivalent split is
  `app.py`/`ingest.py`/`vector_store.py`/etc. (runtime) vs. `docs/`,
  `STATE.md`, `PRD.md`, `.agents/plans/` (planning/rationale) — mirror that
  same two-tree framing since it's accurate here too, not just copied for
  its own sake.
- **VALIDATE**: every path listed in the tree exists in `git ls-files`
  output — spot-check with `git ls-files | grep -F "<path>"` for each row.

### ADD stack-at-a-glance chip strip
- **IMPLEMENT**: small horizontal row of chips under the header —
  Python, Streamlit, LangChain, OpenAI (gpt-4o + embeddings),
  Postgres/pgvector, Docker Compose.
- **PATTERN**: reference's `.role-chip` styling (lines ~275–290 in the CSS)
  repurposed for a stack strip (new class, e.g. `.stack-chip`, same visual
  language: pill, small caps, subtle background).
- **VALIDATE**: matches `README.md`'s "## Stack" line exactly — no
  invented/extra technologies.

### ADD "Decisions that will surprise you" section
- **IMPLEMENT**: 3–4 card grid (`.pillars`/`.pillar` pattern), each card:
  a short surprising claim as the heading, 1–2 sentence explanation as body.
  Required cards: (1) `api.py` removal — "we deleted the reused reference
  API, not kept it as a safety net" — because it let `context_tag` be
  spoofed; (2) two LLM call sites, named — translation-at-ingestion +
  answer-synthesis-at-query — "everything else, including which chunks get
  retrieved, is deterministic Python and vector math"; (3) xlsx row-chunking
  bug — a real confirmed bug (salary value with no header context) fixed by
  chunking spreadsheet rows differently from every other file type.
  Optional 4th: `context_tag` as the sole scoping mechanism (one indexed
  metadata field is the entire trust boundary).
- **PATTERN**: `References/handoff-roadmap.html` lines 683–701 (`.pillars`).
- **GOTCHA**: do not soften or generalize the `api.py` claim — the specific,
  surprising fact is that it was a **live, exploitable, unauthenticated
  read/write path** at the time of removal (container's actual `CMD`), not
  routine cleanup. That specificity is what makes it a "surprise" card
  instead of a boring one.
- **VALIDATE**: every claim traces to a specific `docs/ARCHITECTURE.md`
  section (cite mentally against the line ranges in Context References
  above) — no card should state something not actually written there.

### ADD ingestion pipeline diagram
- **IMPLEMENT**: inline SVG per Phase 3 description — folder icon/box →
  three parallel extraction branches (text-as-is / OCR / xlsx-header-tagged)
  merging into → translate-if-needed (accent box) → context_tag stamp →
  chunk → embed → pgvector cylinder/box.
- **PATTERN**: `References/handoff-roadmap.html` lines 549–598 (full SVG
  structure, marker def, box/arrow/label conventions).
- **GOTCHA**: get the actual step order right per `ingest.py` — hash-based
  skip check happens *before* translation (L67–73), and the xlsx/other
  chunking split (L82–84) happens *after* translation, not before — don't
  simplify this into a wrong order for visual tidiness.
- **VALIDATE**: `aria-label` on the `<svg>` reads as a complete, accurate
  one-paragraph description of the real pipeline — read it aloud and check
  it matches `ingest.py`'s actual control flow.

### ADD ask pipeline diagram
- **IMPLEMENT**: inline SVG — question box → embed → context_tag-filtered
  similarity search → min_relevance gate (branch: below threshold → "I don't
  know" path) → top-k chunks + chat history fold-in → prompt assembly →
  gpt-4o (accent box) → answer + sources box.
- **PATTERN**: same SVG conventions as above; the reference's branching
  pattern (lines 573–588, the Sumit best-effort branch) is the closest
  existing example of a diagram with a conditional path — mirror that
  structure for the `min_relevance` gate branch.
- **GOTCHA**: don't omit the `min_relevance` gate — it's a real, deliberate
  design decision (`query_rag.py` L60–61) that explains why the system says
  "I don't know" instead of hallucinating, and is worth showing visually.
- **VALIDATE**: `aria-label` matches `query_rag.py`'s `answer_question()`
  control flow exactly, including the history fold-in and the gate.

### ADD new-advisor user journey diagram
- **IMPLEMENT**: simpler horizontal flow (not a technical box-diagram) —
  advisor joins engagement → asks "what do I need to know about this
  customer?" → system retrieves + answers with sources → advisor is
  oriented, can verify via sources. Persona-journey framing per user's
  explicit request.
- **PATTERN**: adapt the reference's diagram SVG conventions but simplify —
  fewer boxes, more narrative labels, closer to a "steps" strip than a
  system diagram. No existing exact reference-page equivalent; use
  `.screen`-card visual language (lines ~230–275 CSS) as an alternative if a
  card-sequence reads better than an SVG for this one — implementer's
  judgment, but keep it visually distinct from the two technical diagrams
  so a reviewer immediately reads it as "the human story," not "more
  system internals."
- **VALIDATE**: a non-technical reader (the actual TASC consultant persona
  from `PRD.md` §3) could follow this diagram with zero code knowledge.

### ADD live example section
- **IMPLEMENT**: embed both screenshots as base64 `<img>` data URIs, each
  with a caption naming the real question asked (readable from the
  screenshots' Hebrew text — already viewed this session) and noting these
  are real answers against real ingested Teva data, not mockups.
- **PATTERN**: simple `.screen`-style bordered card per image, or a
  side-by-side two-up grid at wider viewports (match reference's
  responsive card patterns).
- **GOTCHA**: convert to base64 via `base64 -i <file> | tr -d '\n'` — do
  not attempt to hand-type or approximate base64 data.
- **VALIDATE**: `Submission/roadmap.html` opens standalone (no other files
  needed) and both screenshots render — test by copying just this one file
  to a different directory and opening it.

### ADD customer-isolation proof section
- **IMPLEMENT**: state the isolation claim plainly — "the same question
  asked against two different customers returns two different,
  correctly-scoped answers; `context_tag` is the only thing that makes
  this true." Embed the user's isolation-proof screenshot when provided
  (was not yet present in `Submission/` as of this plan's creation — see
  Notes).
- **GOTCHA — BLOCKING SUB-ITEM**: do not fabricate a second screenshot or a
  fake side-by-side comparison. If the user's promised example isn't in
  `Submission/` yet when this task is reached, implement the section with
  the prose claim only and a visible placeholder/TODO comment in the HTML
  source (not visible to a page viewer, but easy for the next editing pass
  to find), and explicitly tell the user this section needs the real
  asset before final submission.
- **VALIDATE**: check `ls Submission/*.png` at implementation time for a
  third image beyond the two already present; confirm with the user which
  file is the isolation proof before wiring it in.

### ADD limitations section
- **IMPLEMENT**: exactly two items, stated confidently (not apologetically)
  — (1) English questions are sometimes answered in Hebrew, a known
  regression from translation-at-ingestion normalizing most retrieved
  context to Hebrew (cite `docs/ARCHITECTURE.md` L117–146); (2) no
  per-customer access control — `context_tag` prevents data *mixing*
  between customers but does not prevent an advisor with app access from
  querying *any* ingested customer; a real deployment needs
  auth/authorization so advisors only reach customers they're assigned to.
- **GOTCHA**: per explicit user instruction, do **not** add the TPM
  rate-limit gap or a "what we cut and why" list to this section — those
  were explicitly declined. Keep this section to exactly these two items.
- **VALIDATE**: re-read the two items against the user's own wording in
  this conversation to confirm nothing was added or dropped.

### ADD Technical-mode `<details>` blocks
- **IMPLEMENT**: under the repo-map, both pipeline diagrams, and the
  decisions-that-surprise section, add one `<details class="tech">` each
  with file:line references and the specific rejected-alternative reasoning
  from `docs/ARCHITECTURE.md` (e.g., under the ingestion diagram: why
  translate documents rather than translate the query — L102–113).
- **PATTERN**: `References/handoff-roadmap.html` lines 460 (`.tech`
  usage after the repo tree) and lines 610–615 (`.tech` after the flow
  diagram, with a `.filelist` of exact file paths).
- **VALIDATE**: clicking "Technical" in the toggle opens every `.tech`
  block simultaneously (test in browser); clicking "Plain" closes them all.

### WIRE toggle JS
- **IMPLEMENT**: paste the reference's closing `<script>` verbatim (see
  Patterns to Follow) just before `</body>`-equivalent end of file (no
  `<body>` tag needed if publishing via `Artifact` tool — content-only file;
  include the `<script>` tag directly if writing as a plain standalone
  HTML file for `Submission/`, which needs full `<!doctype>`/`<html>`/
  `<head>`/`<body>` structure since it's not going through the Artifact
  wrapper).
- **GOTCHA**: the `Submission/roadmap.html` file is a real, standalone repo
  deliverable — it must be full valid HTML (`<!doctype html>`, `<html>`,
  `<head>`, `<body>`) since nothing wraps it. This differs from the
  `Artifact` tool's publish format (page-content-only, tool adds the
  skeleton) — if using the Artifact tool to also publish this page, that
  call needs a page-content-only version; do not publish the full-document
  version through `Artifact` (it would double-wrap `<html>`/`<head>`/`<body>`).
  Two near-identical file bodies are fine here since they share ~everything
  except the outer wrapper tags.
- **VALIDATE**: `open Submission/roadmap.html` in a real browser, click
  both toggle buttons, confirm all `.tech` blocks open/close together and
  `aria-pressed` states swap correctly (inspect via browser devtools).

### PUBLISH as Artifact
- **IMPLEMENT**: load the `artifact-design` skill (required before writing
  any artifact per that tool's rules), then call `Artifact` with the
  content-only version of the page (no `<!doctype>`/`<html>`/`<head>`/
  `<body>` — those are added by the publish wrapper), a distinctive
  `favicon` emoji, and a `title`/`description`.
- **GOTCHA**: the Artifact tool's strict CSP blocks external fonts except
  Google Fonts and blocks all other external asset/script loading — this
  page already has zero external dependencies by design (Patterns to
  Follow), so no adjustment should be needed, but verify no accidental
  `<link>`/`<script src>` to an external host slipped in during Phase 1–5.
- **VALIDATE**: Artifact publish call succeeds; open the returned URL,
  re-run the same toggle/rendering checks as the standalone-file validation.

---

## TESTING STRATEGY

No automated test suite applies — this is a static content page with no
application logic, consistent with this project's own documented stance on
testing (`docs/ARCHITECTURE.md` "Gap: no automated tests" — manual
verification is the deliberate, already-accepted approach here too).

### Manual Validation (replaces Unit/Integration Tests)
- Open `Submission/roadmap.html` directly in a browser (file:// URL) —
  must render fully with zero external network requests (check devtools
  Network tab: only the `data:` URIs and, if any, `fonts.googleapis.com`
  should appear — nothing else).
- Toggle Plain/Technical — every `.tech` block opens/closes in sync.
- Resize to a narrow viewport (~375px) — no horizontal scroll on the page
  body; wide elements (the repo tree, diagrams) scroll within their own
  container if needed.
- Copy just the single file to a fresh empty directory and open it there —
  confirms true self-containment (no missing sibling image files).
- Read every diagram's `aria-label` aloud against the corresponding real
  code path (`ingest.py`, `query_rag.py`) — must match exactly.
- Read every "Decisions that will surprise you" card against
  `docs/ARCHITECTURE.md` — no unsupported claims.
- Confirm the limitations section has exactly the two agreed items, no more.

### Edge Cases
- Dark mode (`prefers-color-scheme: dark` in OS/browser) — full page must
  remain legible, all diagram `currentColor` strokes/text must still
  contrast against `var(--paper)`.
- Missing isolation-proof screenshot at implementation time — handled via
  the blocking sub-item in that task; must not silently ship a fabricated
  or misleading placeholder image.

---

## VALIDATION COMMANDS

### Level 1: File integrity
```bash
# Confirm the file is valid, well-formed HTML (no unclosed tags) —
# quick sanity check, not a full validator
python3 -c "import re,sys; s=open('Submission/roadmap.html').read(); print('OK' if s.strip().startswith('<!doctype') and '</html>' in s else 'MISSING WRAPPER')"
```

### Level 2: Self-containment check
```bash
# Must show zero external asset references beyond optional Google Fonts
grep -Eo 'src="https?://[^"]+"|href="https?://[^"]+"' Submission/roadmap.html | grep -v 'fonts.googleapis.com\|fonts.gstatic.com' || echo "OK: no unexpected external refs"
```

### Level 3: Repo-path accuracy check
```bash
# Every path mentioned inside the .tree block should exist in git ls-files
git ls-files > /tmp/real-files.txt
# Manually cross-check each row of the rendered <div class="tree"> against this list
```

### Level 4: Manual browser walkthrough
- `open Submission/roadmap.html`
- Click through nav anchors, toggle Plain/Technical, resize window,
  check dark mode, verify both screenshots render, verify logo renders.

---

## ACCEPTANCE CRITERIA

- [ ] Page opens standalone from `Submission/roadmap.html` with zero
      external file dependencies (screenshots + logo embedded as data URIs)
- [ ] "Finding your way around the repository" section lists only real
      files from this repo, correctly annotated
- [ ] Three diagrams present: ingestion pipeline, ask pipeline, new-advisor
      journey — each with accurate `aria-label` and `<figcaption>`
- [ ] "Decisions that will surprise you" section present with the `api.py`
      removal, two-LLM-call-sites framing, and xlsx-chunking-bug cards,
      all traceable to `docs/ARCHITECTURE.md`
- [ ] Stack-at-a-glance chip strip present, matching `README.md`'s stack
- [ ] Customer-isolation proof section present (prose claim at minimum;
      real screenshot swapped in once user supplies it)
- [ ] Live-example section shows both real screenshots with accurate
      captions
- [ ] Limitations section present with exactly two items (English→Hebrew
      regression, missing per-customer access control) — nothing more
- [ ] Plain/Technical toggle works, matches reference's interaction exactly
- [ ] Light and dark mode both legible
- [ ] Published as an Artifact with a working shareable link

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task's validation passed immediately after that task
- [ ] All four validation command levels executed
- [ ] Manual browser walkthrough confirms toggle, responsiveness, dark mode
- [ ] No fabricated content — every factual claim traces to a real file in
      this repo
- [ ] Acceptance criteria all met
- [ ] User has reviewed and approved before this is treated as final for
      submission

---

## NOTES

**Open item — blocking one section only:** as of this plan's creation, the
user said the customer-isolation-proof example "will be provided in a
moment" in the `Submission/` folder, but only the two original screenshots
are present there. This does not block starting implementation — build
everything else first, and either wait for the asset or implement that one
section with the prose claim + explicit flag to the user, per the task's
gotcha above.

**Design decision — accent palette:** the plan defaults to reusing the
reference page's lime/paper palette as-is (zero new design risk, already
proven to work for this exact kind of page). Swapping to the app's own
purple/pink accents (`#1A1230`/`#D6006E` from `app.py`) is a reasonable
optional enhancement for brand tie-in, but not required — flagged as an
implementer/user judgment call, not a task.

**Explicitly out of scope (per conversation):**
- TPM rate-limit gap (declined by user)
- "What we cut and why" list as a standalone section (declined by user —
  though the web-search-cut and no-relevance-filtering decisions may still
  surface briefly inside `.tech` details under other sections if natural)
- Any live/interactive demo — this is a static reference page only, matching
  the reference's own explicit footer disclaimer ("This page is a static
  reference; it holds no live data")
- Automated tests of any kind

**Confidence score: 8/10** for one-pass implementation success. The two
points of friction most likely to need a follow-up pass: (1) hand-coding
three SVG diagrams with correct proportions/no overlapping labels on the
first try is inherently iterative, even with a strong reference pattern to
mirror; (2) the isolation-proof asset is genuinely not available yet, so
that one section cannot be fully finished until the user supplies it.
