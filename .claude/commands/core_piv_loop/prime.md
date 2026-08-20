---
description: Prime agent with codebase understanding
---

# Prime: Load Project Context

## Objective

Build comprehensive understanding of the codebase by analyzing structure,
documentation, and key files. Run this at the start of a session.

<!--
OPTIONAL: if a semantic code-search tool (e.g. Serena MCP) is configured for
this project, prefer it over raw grep for symbol lookup. If it errors, fall
back to the standard search tools rather than retrying indefinitely.
-->

## Process

### 1. Analyze Project Structure

List tracked files and show the directory tree:

```bash
git ls-files
```

```bash
# macOS/Linux with tree installed:
tree -L 3 -I 'node_modules|__pycache__|.git|dist|build|venv|target'
# Fallback:
git ls-files | cut -d/ -f1-2 | sort -u
```

### 2. Read Core Documentation

- `CLAUDE.md` — standing rules (highest priority)
- `STATE.md` — where the project is right now
- `docs/ARCHITECTURE.md` — why decisions were made
- `docs/LESSONS.md` — known gotchas
- `README.md` at root and in major directories

### 3. Identify Key Files

Based on the structure, read:
- Main entry points ({{main.py, index.ts, app.tsx, main.go — adapt to stack}})
- Core configuration ({{package.json, pyproject.toml, go.mod, Cargo.toml}})
- Key model/schema definitions
- Important service, controller, or handler files
- Authorization/security boundary files, if the project has them

Read these in parallel where possible rather than one at a time.

### 4. Understand Current State

```bash
git log --oneline -10
git status
git branch --show-current
```

## Output Report

Provide a concise, scannable summary:

### Project Overview
- Purpose and type of application
- Primary technologies and frameworks
- Current phase/state

### Architecture
- Overall structure and organization
- Key architectural patterns identified
- Important directories and their purposes

### Tech Stack
- Languages and versions
- Frameworks and major libraries
- Build tools and package managers
- Testing frameworks and how to run them

### Core Principles
- Code style and conventions observed
- The project's central design constraint (from `CLAUDE.md`)
- Testing approach

### Current State
- Active branch and working-tree status
- Recent development focus
- Immediate observations or concerns worth flagging

**Use bullet points and clear headers. Optimize for scanning, not completeness.**

Close by asking what the user wants to work on — don't assume and start.
