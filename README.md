# Customer Research RAG Tool

A simple internal tool for TASC consultants: ingests everything known about
a customer (project files, meeting summaries) into a shared RAG store tagged
by customer, then lets a consultant ask questions scoped to just that
customer — whether picking up an existing engagement or researching one
they're already on.

**[Visual roadmap for reviewers →](https://claude.ai/code/artifact/51568d9b-b9ea-4ed7-93f9-0f1c4c9002e3)**
A self-contained walkthrough of how ingestion and retrieval work, the key
architecture decisions, and a live customer-isolation proof. Also checked
into the repo as `Submission/roadmap.html` (open directly, no server
needed).

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
| `Submission/roadmap.html` | Visual explainer for assignment reviewers — pipeline diagrams, decisions, isolation proof (also published [here](https://claude.ai/code/artifact/51568d9b-b9ea-4ed7-93f9-0f1c4c9002e3)) |
| `../Basic-plan` | Full implementation plan — architecture, sequencing, file-by-file plan (one level up, outside this repo) |
| `STATE.md` | Current project state, session to session |
| `CLAUDE.md` | Agent operating instructions |
| `docs/CONTEXT-PROTOCOL.md` | How/when context docs get updated |
| `docs/ARCHITECTURE.md` | Why decisions were made |
| `docs/LESSONS.md` | Gotchas worth remembering |
| `.agents/plans/*.md` | Implementation plans |
