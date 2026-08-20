# Customer Handoff RAG Tool

A simple internal tool for TASC consultants: when a new team picks up an
existing customer, this app ingests everything known about that customer
(project files, meeting summaries, public web info) into a shared RAG store,
then lets the new team ask questions scoped to just that customer.

## Stack

Python · Streamlit · LangChain · OpenAI (embeddings + chat) · Postgres/pgvector · Docker Compose

## Getting Started

```bash
docker compose up --build
streamlit run app.py
```

See `.claude/commands/init-project.md` for full local setup.

## Scripts

| Command | Purpose |
|---|---|
| `streamlit run app.py` | Start the app (Ingest + Ask tabs) |
| `python ingest.py --customer "<name>" --folder /path` | Run ingestion from the CLI, without the UI |
| `python query_data.py "<question>"` | Query via CLI (reference script from Nivs-RAG) |
| `docker compose up --build` | Start Postgres+pgvector and the app |

## Documentation

| Doc | Purpose |
|---|---|
| `../Basic-plan` | Full implementation plan — architecture, sequencing, file-by-file plan (one level up, outside this repo) |
| `STATE.md` | Current project state, session to session |
| `CLAUDE.md` | Agent operating instructions |
| `docs/CONTEXT-PROTOCOL.md` | How/when context docs get updated |
| `docs/ARCHITECTURE.md` | Why decisions were made |
| `docs/LESSONS.md` | Gotchas worth remembering |
| `.agents/plans/*.md` | Implementation plans |
