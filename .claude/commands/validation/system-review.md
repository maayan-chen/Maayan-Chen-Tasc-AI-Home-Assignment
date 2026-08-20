---
description: Analyze implementation against plan for process improvements
---

# System Review

Perform a meta-level analysis of how well the implementation followed the plan
and identify process improvements.

## Purpose

**System review is NOT code review.** You're not looking for bugs in the code —
you're looking for bugs in the process.

**Your job:**

- Analyze plan adherence and divergence patterns
- Identify which divergences were justified vs problematic
- Surface process improvements that prevent future issues
- Suggest updates to standing assets (`CLAUDE.md`, plan templates, commands)

**Philosophy:**

- Good divergence reveals plan limitations → improve planning
- Bad divergence reveals unclear requirements → improve communication
- Repeated issues reveal missing automation → create commands

This is the command that makes the whole system improve over time. Everything
else executes; this one changes the machinery.

## Context & Inputs

Analyze four artifacts:

**Plan Command** — the instructions that guide plan creation:
`.claude/commands/core_piv_loop/plan-feature.md`

**Generated Plan** — what the agent was SUPPOSED to do:
Plan file: `$1`

**Execute Command** — the instructions that guide implementation:
`.claude/commands/core_piv_loop/execute.md`

**Execution Report** — what the agent ACTUALLY did, and why:
Execution report: `$2`

## Analysis Workflow

### Step 1: Understand the Planned Approach

From the plan (`$1`):
- What features were planned?
- What architecture was specified?
- What validation steps were defined?
- What patterns were referenced?

### Step 2: Understand the Actual Implementation

From the execution report (`$2`):
- What was implemented?
- What diverged from the plan?
- What challenges were encountered?
- What was skipped and why?

### Step 3: Classify Each Divergence

**Good Divergence ✅** (Justified):
- Plan assumed something that didn't exist in the codebase
- Better pattern discovered during implementation
- Performance optimization needed
- Security issue discovered requiring a different approach

**Bad Divergence ❌** (Problematic):
- Ignored explicit constraints in the plan
- Created new architecture instead of following existing patterns
- Took shortcuts that introduce tech debt
- Misunderstood requirements

### Step 4: Trace Root Causes

For each problematic divergence:
- Was the plan unclear — where, why?
- Was context missing — where, why?
- Was validation missing — where, why?
- Was a manual step repeated — where, why?

### Step 5: Generate Process Improvements

Based on patterns **across** divergences, suggest:

- **`CLAUDE.md` updates:** Universal patterns or anti-patterns to document
- **Plan command updates:** Instructions needing clarification or missing steps
- **New commands:** Manual processes that should be automated
- **Validation additions:** Checks that would catch issues earlier
- **`docs/LESSONS.md` entries:** Traps that cost real time this cycle

## Output Format

Save to: `.agents/system-reviews/[feature-name]-review.md`

#### Meta Information
- Plan reviewed: [path to `$1`]
- Execution report: [path to `$2`]
- Date: [current date]

#### Overall Alignment Score: __/10

- 10: Perfect adherence, all divergences justified
- 7-9: Minor justified divergences
- 4-6: Mix of justified and problematic divergences
- 1-3: Major problematic divergences

#### Divergence Analysis

```yaml
divergence: [what changed]
planned: [what plan specified]
actual: [what was implemented]
reason: [agent's stated reason from report]
classification: good ✅ | bad ❌
justified: yes/no
root_cause: [unclear plan | missing context | missing validation | etc]
```

#### Pattern Compliance

- [ ] Followed codebase architecture
- [ ] Used documented patterns (from `CLAUDE.md`)
- [ ] Applied testing patterns correctly
- [ ] Met validation requirements

#### System Improvement Actions

**Update `CLAUDE.md`:**
- [ ] Document [pattern X] discovered during implementation
- [ ] Add anti-pattern warning for [Y]
- [ ] Clarify [constraint Z]

**Update Plan Command:**
- [ ] Add instruction for [missing step]
- [ ] Clarify [ambiguous instruction]
- [ ] Add validation requirement for [X]

**Update Execute Command:**
- [ ] Add [validation step] to execution checklist

**Create New Command:**
- [ ] `/[command-name]` for [manual process repeated 3+ times]

**Add to `docs/LESSONS.md`:**
- [ ] [trap that cost real time and will re-set itself]

#### Key Learnings

**What worked well:** [specific things that went smoothly]

**What needs improvement:** [specific process gaps]

**For next implementation:** [concrete improvements to try]

## Important

- **Be specific:** Don't say "plan was unclear" — say "plan didn't specify which
  auth pattern to use"
- **Focus on patterns:** One-off issues aren't actionable. Look for repeated problems.
- **Action-oriented:** Every finding should have a concrete asset update suggestion
- **Suggest the actual text** to add to `CLAUDE.md` or a command — don't just
  describe the gap
