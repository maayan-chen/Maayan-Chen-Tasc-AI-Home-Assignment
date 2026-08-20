---
description: Run comprehensive validation of the project.
---

Run comprehensive validation of the project.

This is a 2-day take-home assignment with no automated lint/typecheck/test/build
tooling configured (see `docs/ARCHITECTURE.md` → "Gap: no automated tests" —
deliberate scope call given the time budget). Validation here is manual.

Execute the following in sequence and report results.

## 1. Services Start Cleanly

```bash
docker compose up --build
```

**Expected:** Postgres+pgvector starts with no errors; `init.sql` runs cleanly.

## 2. Ingestion — CLI Wrapper

```bash
python ingest_agent.py --customer "<real customer name>" --folder /path/to/real/folder
```

**Expected:** Completes without error, reports files read + chunks saved.
**Cannot be run bare without services up** — step 1 must succeed first.

## 3. Ingestion — Data Landed Correctly

```bash
psql "$PGVECTOR_CONNECTION" -c "SELECT DISTINCT cmetadata->>'context_tag' FROM langchain_pg_embedding;"
```

**Expected:** The customer's `context_tag` (slugified name) appears.

## 4. Streamlit App

```bash
streamlit run app.py
```

**Expected:** Opens at http://localhost:8501. Ingest tab: folder path +
customer name inputs prefilled from `.last_ingest.json` after the first run.
Ask tab: customer dropdown lists the ingested customer; a real question
returns a grounded, sourced answer.

## 5. Summary Report

Provide a summary with:

- Docker services status (up/errors)
- CLI ingestion result (chunks saved count)
- `context_tag` presence in Postgres
- Streamlit manual walkthrough result (Ingest + Ask)
- Any errors or warnings encountered
- Overall health assessment (PASS/FAIL)

**Report actual output, not a claim about it.** If a step was skipped, say it
was skipped and why.
