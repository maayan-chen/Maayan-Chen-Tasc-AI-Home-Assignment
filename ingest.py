import argparse

from langchain.schema import Document
from create_database import save_to_pgvector, set_context_tag, split_text
from read_local_files import read_local_files


def run_ingestion(customer_name: str, folder_path: str) -> dict:
    context_tag = customer_name.strip()
    if not context_tag:
        raise ValueError("customer_name is required")

    results = read_local_files(folder_path)
    if not results:
        print(f"No ingestible files found in {folder_path}.")
        return {"files_read": 0, "chunks_saved": 0}

    documents = [
        Document(page_content=content, metadata={"source": source})
        for content, source in results
    ]
    chunks = split_text(documents)
    chunks = set_context_tag(chunks, context_tag)
    save_to_pgvector(chunks, pre_delete_collection=False)

    print(
        f"Ingested {len(documents)} files into {len(chunks)} chunks "
        f"for context_tag='{context_tag}'"
    )
    return {"files_read": len(documents), "chunks_saved": len(chunks)}


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
