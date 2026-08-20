# Context Update Protocol

When the user asks "should we update context?", evaluate using these triggers:

| Trigger | Action |
|---------|--------|
| Current task changed | Update STATE.md → Current Task |
| Feature shipped or broke | Update STATE.md → System Status |
| Architectural decision made | Update docs/ARCHITECTURE.md |
| System-critical lesson learned | Update docs/LESSONS.md |
| Info in STATE.md is outdated | Remove it |
| New domain became complex enough | Create docs/[DOMAIN].md |
| Persistent memory has system-critical info | Move to docs/LESSONS.md |

## Rules

- Never update context files without user request.
- Every entry must be a pointer or a decision, not a description.
- Never summarize code that can be read from file paths.
- When suggesting updates, be specific: quote what to add/remove/change.
- STATE.md must stay under 80 lines. If growing, prune or move to docs/.

## What Makes a Good Entry

Bad pointer: `Payment → /src/payments/`
Good pointer: `Payment (Stripe webhooks, LemonSqueezy checkout) → /src/payments/`

Bad entry: `We use Firebase for authentication and it handles user sessions`
Good entry: `Auth: Firebase (chose over Supabase, needed phone auth) → /src/auth/`

The difference in both cases is **information that isn't recoverable from the
code**. The file path is recoverable. Which alternatives were rejected, and why,
is not.

## Which File Does This Go In?

The three context files answer different questions. Putting an entry in the
wrong one makes both files harder to search.

| The entry is... | It goes in | Test |
|---|---|---|
| Where the project is right now | `STATE.md` | Will it be false in a month? |
| Why we chose X over Y | `docs/ARCHITECTURE.md` | Would a new dev ask "why is this like this?" |
| Something that behaved unexpectedly | `docs/LESSONS.md` | Did it cost real debugging time? |

If an entry fits two files, it usually belongs in the deeper one with a
one-line pointer left in the shallower one.

## After Evaluation

Present changes as a checklist:
```
Context updates:
- [ ] STATE.md: Update current task to "..."
- [ ] STATE.md: Mark [feature] as ✅ Live
- [ ] docs/ARCHITECTURE.md: Add decision about [X]
- [ ] No other changes needed
```

Wait for user approval before making any changes.
