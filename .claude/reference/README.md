# Reference Docs

Deep reference material loaded **on demand**, not into every session.

## The distinction that matters

| | `CLAUDE.md` | `.claude/reference/*.md` |
|---|---|---|
| Loaded | Every session, always | Only when relevant |
| Length | Under ~60 lines | As long as it needs to be |
| Content | Rules that change behavior | Procedures, patterns, commands, examples |

If something is needed in **every** session, it belongs in `CLAUDE.md`. If it's
needed when working on a **specific area**, it belongs here — and gets a pointer
from `CLAUDE.md`'s Pointer Index so the agent knows to come find it.

This split is what keeps `CLAUDE.md` short enough to actually be followed.

## Suggested files

Create only the ones your project needs. An unused reference doc is a file that
drifts out of date and misleads later.

| File | Covers |
|---|---|
| `deployment-best-practices.md` | Local dev via Docker Compose, environment/config, deployment gotchas |

No `testing-and-logging.md` — this project has no automated test suite (see
`docs/ARCHITECTURE.md` → "Gap: no automated tests"), so there's nothing to
document there yet.

## Writing a good reference doc

- **Start with a table of contents** if it's over ~50 lines
- **Show real commands from this project**, not generic illustrations
- **Document what's non-obvious**, not what the official docs already cover well
- **Include the traps** — a third-party API reference is most valuable for its
  "this endpoint's response shape isn't what the docs say" notes
- **Date claims about scope.** "Testing stops here because of X budget" is true
  when written and false later. Either keep it current or don't write it — a
  stale scope claim actively misleads an agent into skipping needed work.
