---
description: Initialize Project
---

# Initialize Project

Set up and start the project locally.

Single-root Python project — no backend/frontend split. `app.py` is the
Streamlit entrypoint; Postgres+pgvector runs via `docker-compose.yml`.

## 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure Environment

Copy `.env.example` to `.env` and fill in real values (`OPENAI_API_KEY`,
`PGVECTOR_*` / `PGVECTOR_CONNECTION` — see `README.md` for the full key list,
same as `References/Nivs-RAG/.env`). `.env` is gitignored.

`OPENAI_API_KEY` is used server-side only (ingestion agent, query flow) — it
is never read by anything the Streamlit frontend sends to the browser.

## 3. Start Supporting Services

```bash
docker compose up --build
```

Starts Postgres+pgvector (and, per `docker-compose.yml`, optionally the app
container too — see that file for whether `app.py`/`api.py` runs in Docker or
locally for this project).

## 4. Start the Dev Server

```bash
streamlit run app.py
```

## 5. Validate Setup

```bash
python ingest_agent.py --customer "Test Customer" --folder ./References/Nivs-RAG/data
```

No linter/typechecker/build step is configured for this 2-day assignment —
manual verification only (see `../Basic-plan` Verification section).

## Access Points

- **Streamlit app**: http://localhost:8501
- **Postgres+pgvector**: localhost:5432 (see `docker-compose.yml` for actual port/creds)
- **FastAPI (optional, unused by the app)**: http://localhost:8000

## Notes

Requires an OpenAI API key (embeddings + chat). The ingestion agent also runs
a live DuckDuckGo web search per customer — no API key needed for that, but it
does require outbound internet access.
