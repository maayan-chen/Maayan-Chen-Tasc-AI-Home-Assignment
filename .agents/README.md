# .agents/

Working artifacts produced by the PIV loop. These are **generated output**, not
hand-maintained context.

| Directory | Produced by | Contains |
|---|---|---|
| `plans/` | `/core_piv_loop:plan-feature` | Implementation plans |
| `code-reviews/` | `/validation:code-review` | Review findings |
| `execution-reports/` | `/validation:execution-report` | What actually happened |
| `system-reviews/` | `/validation:system-review` | Process meta-analysis |
| `rca/` | `/github_bug_fix:rca` | Root-cause analyses |

`plans/_PLAN-TEMPLATE.md` is the exception: it's a hand-maintained reference
showing the shape `/core_piv_loop:plan-feature` produces, kept so the expected
structure is visible without reading the command. Leading underscore sorts it
above generated plans.

## Why these are committed

Plans and reports are the **audit trail of how the project was built**. A plan
records what was intended and why; an execution report records what actually
happened. Together they're what `/validation:system-review` reads to improve the
system — and what a future you reads to understand a decision.

## Lifecycle

Artifacts here are **historical records, not living documents**. Once a plan is
executed, don't edit it to match what got built — the divergence is the useful
part. Durable conclusions get promoted into `docs/ARCHITECTURE.md` or
`docs/LESSONS.md`; the artifact stays as-is.

If this directory gets noisy, archive old artifacts into a subdirectory rather
than deleting them.
