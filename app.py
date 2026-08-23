import html
import json
from pathlib import Path

import psycopg
import streamlit as st

from ingest import run_ingestion
from query_rag import answer_question
from vector_store import get_psycopg_connection

LAST_INGEST_PATH = Path(".last_ingest.json")


def load_last_ingest() -> dict:
    if LAST_INGEST_PATH.exists():
        return json.loads(LAST_INGEST_PATH.read_text())
    return {"folder_path": "", "customer_name": ""}


def save_last_ingest(folder_path: str, customer_name: str) -> None:
    LAST_INGEST_PATH.write_text(
        json.dumps({"folder_path": folder_path, "customer_name": customer_name})
    )


def list_customers() -> list[str]:
    with psycopg.connect(get_psycopg_connection()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT cmetadata->>'context_tag' FROM langchain_pg_embedding "
                "WHERE cmetadata->>'context_tag' IS NOT NULL ORDER BY 1"
            )
            return [row[0] for row in cur.fetchall()]


st.set_page_config(page_title="Customer Handoff RAG Tool", layout="wide")

st.markdown(
    """
    <style>
    .header-bar {
        background-color: #1A1230;
        padding: 1.25rem 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
    }
    .header-bar h1 {
        color: #FFFFFF;
        font-size: 1.5rem;
        margin: 0;
    }
    .pill-label {
        display: inline-block;
        background-color: #D6006E;
        color: #FFFFFF;
        padding: 0.25rem 0.9rem;
        border-radius: 999px;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    </style>
    <div class="header-bar">
        <h1>Customer Handoff RAG Tool</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Ingest a customer")
    last_ingest = load_last_ingest()
    folder_path = st.text_input("Customer project folder path", value=last_ingest["folder_path"])

    if folder_path:
        folder = Path(folder_path)
        if not folder.exists():
            st.error(f"Folder not found: {folder_path}")
        elif not folder.is_dir():
            st.error(f"Not a directory: {folder_path}")
        else:
            file_count = sum(1 for p in folder.rglob("*") if p.is_file() and not p.name.startswith("."))
            st.success(f"Found {file_count} files in this folder.")

    customer_name = st.text_input("Customer name", value=last_ingest["customer_name"])

    if st.button("Run Ingestion"):
        save_last_ingest(folder_path, customer_name)
        try:
            with st.spinner("Ingesting..."):
                result = run_ingestion(customer_name, folder_path)
        except (FileNotFoundError, NotADirectoryError, ValueError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Ingestion failed: {e}")
        else:
            skipped = result.get("files_skipped", 0)
            skipped_note = f" ({skipped} unchanged files skipped)" if skipped else ""
            if result["chunks_saved"] == 0:
                if skipped:
                    st.info(f"All {skipped} files already ingested and unchanged — nothing to do.")
                else:
                    st.warning("No ingestible files found in that folder.")
            else:
                st.success(
                    f"{result['files_read']} files read, {result['chunks_saved']} chunks saved.{skipped_note}"
                )

customers = list_customers()

if not customers:
    st.info("No customers ingested yet — use the sidebar to ingest one.")
else:
    if st.session_state.get("context_tag") not in customers:
        st.session_state["context_tag"] = customers[0]
        st.session_state["messages"] = []

    selected_customer = st.session_state["context_tag"]

    pill_col, change_col = st.columns([4, 1])
    with pill_col:
        st.markdown(
            f'<div class="pill-label">Asking about: {html.escape(selected_customer)}</div>',
            unsafe_allow_html=True,
        )
    with change_col:
        with st.popover("Change customer"):
            new_customer = st.selectbox("Customer", customers, index=customers.index(selected_customer))
            if new_customer != selected_customer:
                st.session_state["context_tag"] = new_customer
                st.session_state["messages"] = []
                st.rerun()

    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander("Sources"):
                    for source in message["sources"]:
                        st.markdown(f"**{source['source']}**")
                        st.text(source["content"])

    if user_input := st.chat_input("Ask a question about this customer"):
        st.session_state["messages"].append({"role": "user", "content": user_input})

        try:
            with st.spinner("Thinking..."):
                result = answer_question(user_input, selected_customer)
        except Exception as e:
            st.session_state["messages"].append(
                {"role": "assistant", "content": f"Something went wrong answering that: {e}", "sources": []}
            )
        else:
            if result["answer"] is None:
                answer_content = "I don't have enough information to answer that."
                st.session_state["messages"].append(
                    {"role": "assistant", "content": answer_content, "sources": []}
                )
            else:
                st.session_state["messages"].append(
                    {
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result["sources"],
                    }
                )
        st.rerun()
