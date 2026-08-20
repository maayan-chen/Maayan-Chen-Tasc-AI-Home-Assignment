---
description: Create a new commit for all of our uncommitted changes
---

Create a new commit for all of our uncommitted changes.

Run `git status && git diff HEAD && git status --porcelain` to see what files
are uncommitted.

Add the untracked and changed files.

Write an atomic commit message with an appropriate description, prefixed with a
conventional tag that reflects the work: `feat`, `fix`, `docs`, `refactor`,
`test`, `chore`.

## Before Committing

**Ask whether context needs updating**, unless it was already handled this
session. Evaluate against `docs/CONTEXT-PROTOCOL.md` and present the result as
a checklist:

```
Context updates:
- [ ] STATE.md: Update current task to "..."
- [ ] docs/ARCHITECTURE.md: Add decision about [X]
- [ ] No other changes needed
```

Wait for approval before editing any context file, then include the approved
changes in this commit. Code and the context describing it should land
together — deferred, `STATE.md` drifts and the next session starts from a false
picture.

If nothing qualifies, say so in one line and proceed.

## Guardrails

- **Confirm you are not on the main branch** before committing. If you are,
  stop and ask — work belongs on a feature branch.
- If the changes span several unrelated concerns, propose splitting them into
  separate commits rather than bundling them into one.
- Do not push or open a PR unless explicitly asked.
