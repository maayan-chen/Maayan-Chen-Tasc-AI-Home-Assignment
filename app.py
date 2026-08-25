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


def format_source_label(source: str) -> str:
    path = Path(source)
    return f"{path.name} ({path.parent.name})" if path.parent.name else path.name


def list_customers() -> list[str]:
    with psycopg.connect(get_psycopg_connection()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT cmetadata->>'context_tag' FROM langchain_pg_embedding "
                "WHERE cmetadata->>'context_tag' IS NOT NULL ORDER BY 1"
            )
            return [row[0] for row in cur.fetchall()]


st.set_page_config(page_title="כלי RAG למסירת לקוחות", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        direction: rtl;
    }
    [data-testid="stChatInput"] textarea {
        text-align: right;
    }
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
    .source-chunk-text {
        font-family: 'Segoe UI', 'Assistant', 'Arial', sans-serif;
        font-size: 0.95rem;
        line-height: 1.6;
        white-space: pre-wrap;
        direction: rtl;
        text-align: right;
    }
    [data-testid="stPopover"] button {
        justify-content: flex-end;
        gap: 0.5rem;
    }
    [data-testid="stPopover"] button p {
        text-align: right;
    }
    </style>
    <div class="header-bar">
        <h1>צ׳אט חקירת לקוחות</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("קליטת לקוח")
    last_ingest = load_last_ingest()
    folder_path = st.text_input("נתיב תיקיית הפרויקט של הלקוח", value=last_ingest["folder_path"])

    if folder_path:
        folder = Path(folder_path)
        if not folder.exists():
            st.error(f"התיקייה לא נמצאה: {folder_path}")
        elif not folder.is_dir():
            st.error(f"זו אינה תיקייה: {folder_path}")
        else:
            file_count = sum(1 for p in folder.rglob("*") if p.is_file() and not p.name.startswith("."))
            st.success(f"נמצאו {file_count} קבצים בתיקייה זו.")

    customer_name = st.text_input("שם הלקוח", value=last_ingest["customer_name"])

    if st.button("הרץ קליטה"):
        save_last_ingest(folder_path, customer_name)
        try:
            with st.spinner("קולט..."):
                result = run_ingestion(customer_name, folder_path)
        except (FileNotFoundError, NotADirectoryError, ValueError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"הקליטה נכשלה: {e}")
        else:
            skipped = result.get("files_skipped", 0)
            skipped_note = f" ({skipped} קבצים ללא שינוי דולגו)" if skipped else ""
            if result["chunks_saved"] == 0:
                if skipped:
                    st.info(f"כל {skipped} הקבצים כבר נקלטו וללא שינוי — אין מה לעשות.")
                else:
                    st.warning("לא נמצאו קבצים ניתנים לקליטה בתיקייה זו.")
            else:
                st.success(
                    f"נקראו {result['files_read']} קבצים, נשמרו {result['chunks_saved']} מקטעים.{skipped_note}"
                )

customers = list_customers()

if not customers:
    st.info("עדיין לא נקלטו לקוחות — השתמשו בסרגל הצד כדי לקלוט לקוח.")
else:
    if st.session_state.get("context_tag") not in customers:
        st.session_state["context_tag"] = customers[0]
        st.session_state["messages"] = []

    selected_customer = st.session_state["context_tag"]

    pill_col, change_col = st.columns([4, 1])
    with pill_col:
        st.markdown(
            f'<div class="pill-label">שאלות על: {html.escape(selected_customer)}</div>',
            unsafe_allow_html=True,
        )
    with change_col:
        with st.popover("החלף לקוח"):
            new_customer = st.selectbox("לקוח", customers, index=customers.index(selected_customer))
            if new_customer != selected_customer:
                st.session_state["context_tag"] = new_customer
                st.session_state["messages"] = []
                st.rerun()

    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander("מקורות"):
                    for source in message["sources"]:
                        with st.popover(format_source_label(source["source"])):
                            st.markdown(
                                f'<div class="source-chunk-text">{html.escape(source["content"])}</div>',
                                unsafe_allow_html=True,
                            )

    if user_input := st.chat_input("שאלו שאלה על הלקוח"):
        history = [
            {"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]
        ]
        st.session_state["messages"].append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        try:
            with st.chat_message("assistant"), st.spinner("חושב..."):
                result = answer_question(user_input, selected_customer, history=history)
        except Exception as e:
            st.session_state["messages"].append(
                {"role": "assistant", "content": f"משהו השתבש בעת מענה לשאלה: {e}", "sources": []}
            )
        else:
            if result["answer"] is None:
                answer_content = "אין לי מספיק מידע כדי לענות על כך."
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
