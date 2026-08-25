---
description: Initialize Project
---

# Initialize Project

Set up and start the project locally.

Single-root Python project — no backend/frontend split, no HTTP API layer.
`app.py` is the Streamlit entrypoint; Postgres+pgvector runs via
`docker-compose.yml`.

## 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure Environment

Copy `.env.example` to `.env` and fill in real values (`OPENAI_API_KEY`,
`PGVECTOR_*` / `PGVECTOR_CONNECTION` — see `.env.example` for the full key
list). `.env` is gitignored.

`OPENAI_API_KEY` is used server-side only (ingestion translation step, chat
query flow) — it is never read by anything sent to the browser.

## 3. Start Everything via Docker Compose

```bash
docker compose up --build
```

Starts Postgres+pgvector, then the `app` container: it initializes the
vector store and runs `streamlit run app.py` bound to `0.0.0.0:8501`, mapped
to the host at `localhost:8501` (see `docker-compose.yml`). This is the
normal way to run the whole app.

## 4. (Alternative) Start the Dev Server Directly on the Host

Skip this if you already used step 3. Only needed for local iteration
against a Postgres you're running separately:

```bash
streamlit run app.py
```

## 5. Validate Setup

Ingest a real customer project folder (see `CLAUDE.md`: never fabricate a
demo customer folder — use one supplied by the user):

```bash
python ingest.py --customer "Test Customer" --folder /path/to/customer/folder
```

No linter/typechecker/build step is configured for this 5-day assignment —
manual verification only (see `docs/ARCHITECTURE.md`'s "Gap: no automated
tests" section).

## Access Points

- **Streamlit app**: http://localhost:8501
- **Postgres+pgvector**: localhost:5432 (see `docker-compose.yml` for actual port/creds)

## Notes

Requires an OpenAI API key (embeddings + chat, and the non-Hebrew-document
translation step at ingestion — see `docs/ARCHITECTURE.md`). There is no
HTTP API in this project.
