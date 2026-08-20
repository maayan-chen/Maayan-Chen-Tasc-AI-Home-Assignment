# Deployment Best Practices Reference

A concise reference for running Customer Handoff RAG Tool locally: Python +
Streamlit + LangChain + Postgres/pgvector via Docker Compose. There is no
production deployment target for this 2-day assignment — "deployment" here
means local Docker Compose only.

---

## Table of Contents

1. [Local Development](#1-local-development)
2. [Environment & Configuration](#2-environment--configuration)
3. [Security](#3-security)
4. [Gotchas](#4-gotchas)

---

## 1. Local Development

Single Python root, no frontend build step.

```bash
docker compose up --build   # Postgres+pgvector (+ app, per docker-compose.yml)
streamlit run app.py        # if the app isn't run inside Docker
```

## 2. Environment & Configuration

| Variable | Where it lives | Client-visible? |
|---|---|---|
| `OPENAI_API_KEY` | `.env`, server-side only | No |
| `PGVECTOR_CONNECTION` | `.env` (Docker Compose sets it for the app service) | No |
| `POSTGRES_HOST` / `PORT` / `DB` / `USER` / `PASSWORD` | `.env` | No |
| `PGVECTOR_COLLECTION` | `.env` | No |

Streamlit has no client/server bundle split like a JS framework — everything
in `app.py` runs server-side, so there is no "accidentally shipped to the
browser" secrets risk the way there would be with `NEXT_PUBLIC_`-style
prefixes. Still: never `st.write()` or log a secret value to the UI.

## 3. Security

- Secrets never printed to the Streamlit UI or committed to `.last_ingest.json`
  (that file only ever holds a folder path + customer name).
- `context_tag` filtering is the only customer-isolation boundary — see
  `../../docs/ARCHITECTURE.md`. It is enforced in the retrieval query, not in
  the UI layer.
- No auth on the Streamlit app itself — out of scope for this assignment; it's
  assumed to run on a trusted local/internal network only.

## 4. Gotchas

**If `PGVECTOR_CONNECTION` is set, it wins over the individual `POSTGRES_*`
vars.** Per `References/Nivs-RAG/README.md`. Docker Compose sets it
automatically for the app service — don't be confused if changing
`POSTGRES_PASSWORD` alone has no effect inside the container.

**Ingestion never resets the collection** (`pre_delete_collection=False`).
Re-running against stale test data will accumulate duplicate chunks under the
same `context_tag` rather than replacing them — expected for the "run
anytime, incrementally" design, but confusing if you're expecting a clean
slate each time.

**`Add project-specific gotchas here as they're discovered.`**
