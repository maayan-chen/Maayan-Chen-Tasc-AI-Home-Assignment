---
description: Execute an implementation plan
argument-hint: [path-to-plan]
---

# Execute: Implement from Plan

## Plan to Execute

Read plan file: `$ARGUMENTS`

## Execution Instructions

### 0. Create a Branch

Before making any changes, create and switch to a new branch off the current
base branch — never implement a plan directly on the main branch.

- Name it from the plan file, e.g. `plan/<plan-filename-without-extension>`
  (or ask the user for a name if the plan filename isn't descriptive)
- `git checkout -b <branch-name>`
- Confirm the branch is clean and up to date with the base branch before proceeding
- All commits for this plan go on this branch; pushing/opening a PR happens
  only when the user asks

### 1. Read and Understand

- Read the ENTIRE plan carefully
- Read every file the plan lists under "Relevant Codebase Files" before writing code
- Understand all tasks and their dependencies
- Note the validation commands to run
- Review the testing strategy

### 2. Execute Tasks in Order

For EACH task in "Step by Step Tasks":

#### a. Navigate to the task
- Identify the file and action required
- Read existing related files if modifying

#### b. Implement the task
- Follow the detailed specifications exactly
- Maintain consistency with existing code patterns
- Include proper type hints and documentation
- Add structured logging where appropriate

#### c. Verify as you go
- After each file change, check syntax
- Ensure imports are correct
- Verify types are properly defined
- Run the task's own `VALIDATE` command before moving on

### 3. Implement Testing Strategy

After completing implementation tasks:

- Create all test files specified in the plan
- Implement all test cases mentioned
- Follow the testing approach outlined
- Ensure tests cover the edge cases the plan names

**A test that passes without exercising the code proves nothing.** Where a test
guards a subtle failure, confirm it has teeth by reintroducing the bug and
watching it go red.

### 4. Run Validation Commands

Execute ALL validation commands from the plan in order.

If any command fails:
- Fix the issue
- Re-run the command
- Continue only when it passes

Never report a validation as passing without having run it.

### 5. Final Verification

Before completing:

- ✅ All tasks from plan completed
- ✅ All tests created and passing
- ✅ All validation commands pass
- ✅ Code follows project conventions
- ✅ Documentation added/updated as needed

## Output Report

### Completed Tasks
- List of all tasks completed
- Files created (with paths)
- Files modified (with paths)

### Tests Added
- Test files created
- Test cases implemented
- Test results

### Validation Results
Actual output from each validation command.

### Deviations
- Anything implemented differently from the plan, and why
- Anything skipped, and why

### Ready for Next Step
- Confirm all changes are complete
- Confirm all validations pass
- Confirm work is on the plan's feature branch, not the main branch

Next in the loop:
1. `/validation:execution-report` — record what actually happened vs. the plan,
   while it's still fresh
2. `/validation:code-review` → `/validation:code-review-fix`
3. Ask whether context needs updating (`docs/CONTEXT-PROTOCOL.md`)
4. `/commit`

## Notes

- If you encounter issues not addressed in the plan, document them
- If you need to deviate from the plan, explain why — deviations are expected
  and are the raw material for `/validation:system-review`
- If tests fail, fix the implementation until they pass
- Don't skip validation steps
- **Report honestly.** A failed test reported as failing is useful; one reported
  as passing corrupts every downstream decision.
