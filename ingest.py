import argparse
import re

import psycopg
from langchain.schema import Document
from create_database import save_to_pgvector, set_context_tag, split_text
from read_local_files import read_local_files
from vector_store import get_psycopg_connection


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def _get_indexed_file_hashes(context_tag: str) -> dict[str, str]:
    """Map of source path -> file_hash for every file already indexed under
    this context_tag."""
    with psycopg.connect(get_psycopg_connection()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT cmetadata->>'source', cmetadata->>'file_hash' "
                "FROM langchain_pg_embedding WHERE cmetadata->>'context_tag' = %s",
                (context_tag,),
            )
            return {source: file_hash for source, file_hash in cur.fetchall()}


def _delete_indexed_file(context_tag: str, source: str) -> None:
    with psycopg.connect(get_psycopg_connection()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM langchain_pg_embedding "
                "WHERE cmetadata->>'context_tag' = %s AND cmetadata->>'source' = %s",
                (context_tag, source),
            )
        conn.commit()


def _chunk_xlsx_documents(documents: list[Document]) -> list[Document]:
    """Chunk spreadsheet-derived documents one row per chunk, instead of
    running them through the shared character splitter — see
    docs/ARCHITECTURE.md for why xlsx ingestion diverges from split_text()."""
    chunks = []
    for doc in documents:
        for row_text in doc.page_content.split("\n"):
            row_text = row_text.strip()
            if row_text:
                chunks.append(Document(page_content=row_text, metadata=dict(doc.metadata)))
    return chunks


def run_ingestion(customer_name: str, folder_path: str) -> dict:
    context_tag = slugify(customer_name)
    if not context_tag:
        raise ValueError("customer_name is required")

    results = read_local_files(folder_path)
    if not results:
        print(f"No ingestible files found in {folder_path}.")
        return {"files_read": 0, "chunks_saved": 0, "files_skipped": 0}

    indexed = _get_indexed_file_hashes(context_tag)

    documents = []
    files_to_replace = []
    files_skipped = 0
    for content, source, file_hash in results:
        if indexed.get(source) == file_hash:
            files_skipped += 1
            continue
        if source in indexed:
            files_to_replace.append(source)
        documents.append(
            Document(page_content=content, metadata={"source": source, "file_hash": file_hash})
        )

    if not documents:
        print(f"No new or changed files in {folder_path}; {files_skipped} unchanged file(s) skipped.")
        return {"files_read": 0, "chunks_saved": 0, "files_skipped": files_skipped}

    xlsx_documents = [d for d in documents if d.metadata["source"].lower().endswith(".xlsx")]
    other_documents = [d for d in documents if not d.metadata["source"].lower().endswith(".xlsx")]
    chunks = split_text(other_documents) + _chunk_xlsx_documents(xlsx_documents)
    chunks = set_context_tag(chunks, context_tag)
    save_to_pgvector(chunks, pre_delete_collection=False)

    # Only delete a changed file's old chunks after its replacement chunks
    # are safely saved — deleting first would lose that file's content for
    # good if save_to_pgvector then failed (e.g. an OpenAI TPM rate limit,
    # see docs/LESSONS.md).
    for source in files_to_replace:
        _delete_indexed_file(context_tag, source)

    print(
        f"Ingested {len(documents)} files into {len(chunks)} chunks "
        f"for context_tag='{context_tag}' ({files_skipped} unchanged file(s) skipped)"
    )
    return {"files_read": len(documents), "chunks_saved": len(chunks), "files_skipped": files_skipped}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--customer", required=True, help="Customer name (used verbatim as context_tag)"
    )
    parser.add_argument(
        "--folder", required=True, help="Path to the customer's project folder"
    )
    args = parser.parse_args()
    run_ingestion(args.customer, args.folder)


if __name__ == "__main__":
    main()
