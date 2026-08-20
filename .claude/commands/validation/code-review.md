---
description: Technical code review for quality and bugs that runs pre-commit
---

Perform a technical code review on recently changed files.

## Core Principles

- Simplicity is the ultimate sophistication — every line should justify its existence
- Code is read far more often than it's written — optimize for readability
- The best code is often the code you don't write
- Elegance emerges from clarity of intent and economy of expression

## What to Review

Start by gathering codebase context to understand standards and patterns:

- `CLAUDE.md`
- `README.md`
- `docs/ARCHITECTURE.md` — so a deliberate tradeoff isn't flagged as a defect
- `docs/LESSONS.md` — check the changes don't reintroduce a known trap
- Key files in the core module(s)

Then run:

```bash
git status
git diff HEAD
git diff --stat HEAD
git ls-files --others --exclude-standard
```

Read each new file in its entirety. Read each changed file in its entirety
(not just the diff) to understand full context.

For each changed or new file, analyze for:

1. **Logic Errors**
   - Off-by-one errors
   - Incorrect conditionals
   - Missing error handling
   - Race conditions
   - Partial-failure states — if step 2 of 3 fails, what's left behind?

2. **Security Issues**
   - Injection vulnerabilities (SQL, command, template)
   - XSS and output-encoding gaps
   - Insecure data handling
   - Exposed secrets or API keys
   - **Authorization enforced only client-side**
   - Errors that leak internals to the user

3. **Performance Problems**
   - N+1 queries
   - Inefficient algorithms
   - Memory leaks
   - Unnecessary computations

4. **Code Quality**
   - Violations of DRY
   - Overly complex functions
   - Poor naming
   - Missing type hints/annotations
   - **Swallowed errors** — any catch that discards the error before throwing a
     generic one. The user-facing message and the diagnostic log are two
     separate obligations; satisfying one does not satisfy the other.

5. **Adherence to Codebase Standards**
   - Standards documented in `CLAUDE.md` and `docs/`
   - Linting, typing, and formatting standards
   - Logging standards
   - Testing standards

## Verify Issues Are Real

Before reporting:
- Run specific tests for issues found
- Confirm type errors are legitimate
- Validate security concerns in context

**Do not report a finding you haven't verified.** A review padded with
speculative findings costs more time than it saves.

## Output Format

Save to `.agents/code-reviews/[appropriate-name].md`

**Stats:**
- Files Modified / Added / Deleted
- New lines / Deleted lines

**For each issue:**

```
severity: critical|high|medium|low
file: path/to/file
line: 42
issue: [one-line description]
detail: [why this is a problem]
suggestion: [how to fix it]
```

If no issues: "Code review passed. No technical issues detected."

## Important

- Be specific (line numbers, not vague complaints)
- Focus on real bugs, not style — style is the linter's job
- Suggest fixes, don't just complain
- Flag security issues as CRITICAL
