# Feature: {{feature-name}}

<!--
This is the artifact `/core_piv_loop:plan-feature` produces. Kept here as a
standalone reference so the expected shape is visible without reading the
command.

THE BAR: the "No Prior Knowledge Test" — someone unfamiliar with this codebase
should be able to implement from this document alone.

The two sections that decide whether that's true are "Relevant Codebase Files"
(with line numbers and a specific WHY for each) and the per-task VALIDATE
commands. A plan without those is a description, not a plan.
-->

The following plan should be complete, but it's important that you validate
documentation, codebase patterns, and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import
from the right files.

## Feature Description

{{What this is, its purpose, and its value.}}

## User Story

As a {{type of user}}
I want to {{action/goal}}
So that {{benefit/value}}

## Problem Statement

{{The specific problem or opportunity this addresses.}}

## Solution Statement

{{The proposed approach and how it solves the problem.}}

## Feature Metadata

**Feature Type**: {{New Capability/Enhancement/Refactor/Bug Fix}}
**Estimated Complexity**: {{Low/Medium/High}}
**Primary Systems Affected**: {{list}}
**Dependencies**: {{external libraries or services}}

---

## CONTEXT REFERENCES

### Relevant Codebase Files — READ THESE BEFORE IMPLEMENTING

<!-- Line numbers and a specific reason each file matters. "Why: relevant
     context" is not a reason. -->

- `{{path}}` (lines {{X-Y}}) — Why: {{what pattern this shows or what constraint it sets}}
- `{{path}}` (full file) — Why: {{...}}

### New Files to Create

- `{{path}}` — {{purpose}}
- `{{test path}}` — {{tests for the above}}

### Relevant Documentation — READ THESE BEFORE IMPLEMENTING

- [{{Title}}]({{url#section-anchor}})
  - Specific section: {{name}}
  - Why: {{what it's needed for}}

### Patterns to Follow

{{Real code excerpts from THIS project, not generic illustrations.}}

**Naming Conventions:**
**Error Handling:**
**Logging Pattern:**

### Known Traps

{{Relevant entries from `docs/LESSONS.md` this feature could reintroduce.}}
{{Relevant entries from `docs/ARCHITECTURE.md` — deliberate tradeoffs that must
NOT be "fixed" as part of this work without a conscious re-decision.}}

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation
{{Foundational work needed first}}

### Phase 2: Core Implementation
{{Main implementation}}

### Phase 3: Integration
{{Connecting to existing functionality}}

### Phase 4: Testing & Validation
{{Testing approach}}

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and
independently testable.

Keywords: **CREATE** / **UPDATE** / **ADD** / **REMOVE** / **REFACTOR** / **MIRROR**

### {{ACTION}} `{{target_file}}`

- **IMPLEMENT**: {{specific detail}}
- **PATTERN**: {{file:line reference}}
- **IMPORTS**: {{required imports}}
- **GOTCHA**: {{known constraint to avoid}}
- **VALIDATE**: `{{executable command}}`

### {{ACTION}} `{{target_file}}`

- **IMPLEMENT**:
- **PATTERN**:
- **IMPORTS**:
- **GOTCHA**:
- **VALIDATE**:

---

## TESTING STRATEGY

### Unit Tests
{{scope}}

### Integration Tests
{{scope}}

### Edge Cases
{{Specific cases that must be tested — including partial-failure states}}

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```bash
{{command}}
```

### Level 2: Unit Tests
```bash
{{command}}
```

### Level 3: Integration Tests
```bash
{{command}}
```

### Level 4: Manual Validation
{{Concrete steps — API calls, UI walkthrough}}

---

## ACCEPTANCE CRITERIA

- [ ] Feature implements all specified functionality
- [ ] All validation commands pass with zero errors
- [ ] Test coverage meets project requirements
- [ ] Code follows project conventions and patterns
- [ ] No regressions in existing functionality
- [ ] Documentation updated (if applicable)
- [ ] Security considerations addressed (if applicable)

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed immediately
- [ ] All validation commands executed successfully
- [ ] Full test suite passes
- [ ] No linting or type checking errors
- [ ] Manual testing confirms the feature works
- [ ] Acceptance criteria all met

---

## NOTES

{{Design decisions, trade-offs, and explicitly deferred scope. Stating what is
deliberately NOT in this plan prevents scope creep during execution.}}
