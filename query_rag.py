from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from vector_store import create_vector_store

PROMPT_TEMPLATE = """
IMPORTANT: Regardless of what language the documents below are written in,
you must write your entire answer in the same language as the Question at
the bottom of this prompt.

Answer the question using only the documents below. Each document may
contain table rows formatted as "Header: value | Header: value" — treat
each Header: value pair as a distinct field, not continuous prose.

<documents>
{context}
</documents>

{history_block}
If the documents do not contain enough information to answer the question,
say you don't know — do not guess or use information outside the documents.

Break the answer into short paragraphs, and use bullet points or numbered
lists when covering multiple items, people, or steps. Avoid a single dense
block of text.

Question: {question}

Remember: answer in the same language as the Question above, using only the
documents above.
"""

HISTORY_TURNS = 2  # number of prior user/assistant exchanges to carry forward


def _recent_history_text(history: list[dict] | None) -> str:
    """Flatten the last HISTORY_TURNS exchanges into plain text, so a
    follow-up like "what's her salary?" carries the "Ronit" from the prior
    turn — both into the retrieval query and the prompt. Simple
    concatenation, no LLM query-rewrite: keeps this one deterministic call,
    no extra judgment layer (see CLAUDE.md)."""
    if not history:
        return ""
    turns = history[-(HISTORY_TURNS * 2):]
    return "\n".join(f"{turn['role']}: {turn['content']}" for turn in turns)


def answer_question(
    question: str,
    context_tag: str,
    history: list[dict] | None = None,
    k: int = 8,
    min_relevance: float = 0.7,
) -> dict:
    embedding_function = OpenAIEmbeddings()
    db = create_vector_store(embedding_function)

    history_text = _recent_history_text(history)
    search_query = f"{history_text}\n{question}" if history_text else question

    results = db.similarity_search_with_relevance_scores(
        search_query, k=k, filter={"context_tag": context_tag}
    )
    if len(results) == 0 or results[0][1] < min_relevance:
        return {"answer": None, "sources": []}

    context_text = "\n\n".join(
        f'<document source="{doc.metadata.get("source", "unknown")}">\n{doc.page_content}\n</document>'
        for doc, _score in results
    )
    history_block = (
        f"Recent conversation (for resolving references like pronouns):\n{history_text}\n"
        if history_text
        else ""
    )
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(
        context=context_text, question=question, history_block=history_block
    )

    model = ChatOpenAI(model="gpt-4o")
    response_text = model.predict(prompt)

    sources = [
        {"source": doc.metadata.get("source"), "content": doc.page_content}
        for doc, _score in results
    ]
    return {"answer": response_text, "sources": sources}
