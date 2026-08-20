---
description: "Create comprehensive feature plan with deep codebase analysis and research"
---

# Plan a new task

## Feature: $ARGUMENTS

## Mission

Transform a feature request into a **comprehensive implementation plan** through
systematic codebase analysis, external research, and strategic planning.

**Core Principle**: We do NOT write code in this phase. The goal is a
context-rich implementation plan that enables one-pass implementation success.

**Key Philosophy**: Context is King. The plan must contain ALL information needed
for implementation — patterns, mandatory reading, documentation, validation
commands — so the execution agent succeeds on the first attempt.

## Planning Process

### Phase 1: Feature Understanding

**Deep Feature Analysis:**

- Extract the core problem being solved
- Identify user value and business impact
- Determine feature type: New Capability/Enhancement/Refactor/Bug Fix
- Assess complexity: Low/Medium/High
- Map affected systems and components

**Create User Story (or refine one the user provided):**

```
As a <type of user>
I want to <action/goal>
So that <benefit/value>
```

### Phase 2: Codebase Intelligence Gathering

**1. Project Structure Analysis**

- Detect primary language(s), frameworks, and runtime versions
- Map directory structure and architectural patterns
- Identify service/component boundaries and integration points
- Locate configuration files
- Find environment setup and build processes

**2. Pattern Recognition**

- Search for similar implementations in the codebase
- Identify coding conventions: naming patterns, file organization, error
  handling approaches, logging patterns
- Extract common patterns for the feature's domain
- Document anti-patterns to avoid
- Check `CLAUDE.md` for project-specific rules
- **Check `docs/LESSONS.md`** — verify the plan doesn't reintroduce a known trap
- **Check `docs/ARCHITECTURE.md`** — do not plan to "fix" a deliberate,
  documented tradeoff without flagging it as a conscious re-decision first

**3. Dependency Analysis**

- Catalog external libraries relevant to the feature
- Understand how libraries are integrated (check imports, configs)
- Find relevant documentation in `docs/`, `.claude/reference/`, or equivalent
- Note library versions and compatibility requirements

**4. Testing Patterns**

- Identify test framework and structure
- Find similar test examples for reference
- Understand test organization (unit vs integration)
- Note coverage requirements and testing standards

**5. Integration Points**

- Identify existing files that need updates
- Determine new files to create and their locations
- Map routing/registration patterns
- Understand database/model patterns if applicable
- Identify authentication/authorization patterns if relevant

**Clarify Ambiguities:**

- If requirements are unclear at this point, ask before continuing
- Get specific implementation preferences (libraries, approaches, patterns)
- Resolve architectural decisions before proceeding

### Phase 3: External Research & Documentation

**Documentation Gathering:**

- Research current library versions and best practices
- Find official documentation with specific section anchors
- Locate implementation examples
- Identify common gotchas and known issues
- Check for breaking changes and migration guides

**Compile Research References:**

```markdown
## Relevant Documentation

- [Library Official Docs](https://example.com/docs#section)
  - Specific feature implementation guide
  - Why: Needed for X functionality
```

### Phase 4: Deep Strategic Thinking

**Think harder about:**

- How does this feature fit into the existing architecture?
- What are the critical dependencies and order of operations?
- What could go wrong? (Edge cases, race conditions, partial failures)
- **What happens on partial failure?** If step 2 of 3 fails, what state is the
  system left in, and can the user tell?
- How will this be tested comprehensively?
- What performance implications exist?
- Are there security considerations?
- How maintainable is this approach?

**Design Decisions:**

- Choose between alternative approaches with clear rationale
- Design for extensibility
- Plan for backward compatibility if needed
- Consider scalability implications

### Phase 5: Plan Structure Generation

**Fill in this template for the implementation agent:**

```markdown
# Feature: <feature-name>

The following plan should be complete, but it's important that you validate
documentation, codebase patterns, and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import
from the right files.

## Feature Description

<Detailed description of the feature, its purpose, and value>

## User Story

As a <type of user>
I want to <action/goal>
So that <benefit/value>

## Problem Statement

<The specific problem or opportunity this addresses>

## Solution Statement

<The proposed approach and how it solves the problem>

## Feature Metadata

**Feature Type**: [New Capability/Enhancement/Refactor/Bug Fix]
**Estimated Complexity**: [Low/Medium/High]
**Primary Systems Affected**: [List]
**Dependencies**: [External libraries or services required]

---

## CONTEXT REFERENCES

### Relevant Codebase Files — READ THESE BEFORE IMPLEMENTING

<List files with line numbers AND a specific reason each matters>

- `path/to/file` (lines 15-45) — Why: Contains the pattern for X that we'll mirror
- `path/to/model` (lines 100-120) — Why: Data model structure to follow
- `path/to/test` — Why: Test pattern example

### New Files to Create

- `path/to/new_service` — Service implementation for X
- `path/to/test_new_service` — Unit tests for the new service

### Relevant Documentation — READ THESE BEFORE IMPLEMENTING

- [Documentation Link](https://example.com/doc#section)
  - Specific section: <name>
  - Why: <what it's needed for>

### Patterns to Follow

<Actual code examples from THIS project — not generic illustrations>

**Naming Conventions:**
**Error Handling:**
**Logging Pattern:**
**Other Relevant Patterns:**

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation
<Foundational work needed before main implementation>

### Phase 2: Core Implementation
<The main implementation work>

### Phase 3: Integration
<How the feature connects to existing functionality>

### Phase 4: Testing & Validation
<Testing approach>

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and
independently testable.

### Task Format Keywords

- **CREATE**: New files or components
- **UPDATE**: Modify existing files
- **ADD**: Insert new functionality into existing code
- **REMOVE**: Delete deprecated code
- **REFACTOR**: Restructure without changing behavior
- **MIRROR**: Copy pattern from elsewhere in codebase

### {ACTION} {target_file}

- **IMPLEMENT**: {Specific implementation detail}
- **PATTERN**: {Reference to existing pattern — file:line}
- **IMPORTS**: {Required imports and dependencies}
- **GOTCHA**: {Known issues or constraints to avoid}
- **VALIDATE**: `{executable validation command}`

<Continue with all tasks in dependency order...>

---

## TESTING STRATEGY

### Unit Tests
<Scope and requirements based on project standards>

### Integration Tests
<Scope and requirements>

### Edge Cases
<Specific edge cases that must be tested>

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and feature correctness.

### Level 1: Syntax & Style
### Level 2: Unit Tests
### Level 3: Integration Tests
### Level 4: Manual Validation
<Feature-specific manual steps — API calls, UI walkthrough>

---

## ACCEPTANCE CRITERIA

- [ ] Feature implements all specified functionality
- [ ] All validation commands pass with zero errors
- [ ] Test coverage meets project requirements
- [ ] Integration tests verify end-to-end workflows
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

<Additional context, design decisions, trade-offs, explicitly deferred scope>
```

## Output Format

**Filename**: `.agents/plans/{kebab-case-descriptive-name}.md`

Examples: `add-user-authentication.md`, `implement-search-api.md`,
`refactor-database-layer.md`

**Directory**: Create `.agents/plans/` if it doesn't exist

## Quality Criteria

### Context Completeness ✓
- [ ] All necessary patterns identified and documented
- [ ] External library usage documented with links
- [ ] Integration points clearly mapped
- [ ] Gotchas and anti-patterns captured
- [ ] Every task has an executable validation command

### Implementation Ready ✓
- [ ] Another developer could execute without additional context
- [ ] Tasks ordered by dependency (executable top-to-bottom)
- [ ] Each task is atomic and independently testable
- [ ] Pattern references include specific file:line numbers

### Pattern Consistency ✓
- [ ] Tasks follow existing codebase conventions
- [ ] New patterns justified with clear rationale
- [ ] No reinvention of existing utils or patterns
- [ ] Testing approach matches project standards

### Information Density ✓
- [ ] No generic references (all specific and actionable)
- [ ] URLs include section anchors where applicable
- [ ] Task descriptions use codebase-specific names
- [ ] Validation commands are non-interactive and executable

## Success Metrics

**One-Pass Implementation**: The execution agent completes the feature without
additional research or clarification.

**Validation Complete**: Every task has at least one working validation command.

**Context Rich**: The plan passes the **"No Prior Knowledge Test"** — someone
unfamiliar with the codebase can implement using only the plan's content.

**Confidence Score**: #/10 that execution succeeds on the first attempt.

## Report

After creating the plan, provide:

- Summary of the feature and approach
- Full path to the created plan file
- Complexity assessment
- Key implementation risks or considerations
- Estimated confidence score for one-pass success
