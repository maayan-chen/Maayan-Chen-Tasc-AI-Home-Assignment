---
description: Generate implementation report for system review
---

# Execution Report

Review and deeply analyze the implementation you just completed.

## Context

You have just finished implementing a feature. Before moving on, reflect on:

- What you implemented
- How it aligns with the plan
- What challenges you encountered
- What diverged and why

This report is the input to `/validation:system-review`. Its value depends
entirely on honesty about divergence — a report claiming perfect adherence
produces a system review that improves nothing.

## Generate Report

Save to: `.agents/execution-reports/[feature-name].md`

### Meta Information

- Plan file: [path to the plan that guided this implementation]
- Files added: [list with paths]
- Files modified: [list with paths]
- Lines changed: +X -Y

### Validation Results

- Syntax & Linting: ✓/✗ [details if failed]
- Type Checking: ✓/✗ [details if failed]
- Unit Tests: ✓/✗ [X passed, Y failed]
- Integration Tests: ✓/✗ [X passed, Y failed]

### What Went Well

- [concrete examples]

### Challenges Encountered

- [what was difficult and why]

### Divergences from Plan

For each divergence:

**[Divergence Title]**
- Planned: [what the plan specified]
- Actual: [what was implemented instead]
- Reason: [why this divergence occurred]
- Type: [Better approach found | Plan assumption wrong | Security concern |
  Performance issue | Other]

### Skipped Items

- [what was skipped]
- Reason: [why]

### Recommendations

Based on this implementation, what should change for next time?

- Plan command improvements: [suggestions]
- Execute command improvements: [suggestions]
- `CLAUDE.md` additions: [suggestions]
