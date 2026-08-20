---
description: Process to fix bugs found in manual/AI code review
---

I ran/performed a code review and found these issues:

Code-review (file or description of issues): $1

Please fix these issues one by one. If the code-review argument is a file, read
the entire file first to understand all of the issues presented there.

Scope: $2

For each fix:
1. Explain what was wrong
2. Show the fix
3. Create and run relevant tests to verify

If a finding is **not** a real defect — a deliberate tradeoff documented in
`docs/ARCHITECTURE.md`, or a misreading of the code — say so and explain why,
rather than changing working code to satisfy an incorrect review.

After all fixes, run `/validation:validate` to finalize.
