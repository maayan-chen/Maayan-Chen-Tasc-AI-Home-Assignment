from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from vector_store import create_vector_store

PROMPT_TEMPLATE = """
Answer the question using only the documents below. Each document may
contain table rows formatted as "Header: value | Header: value" — treat
each Header: value pair as a distinct field, not continuous prose.

<documents>
{context}
</documents>

If the documents do not contain enough information to answer the question,
say you don't know — do not guess or use information outside the documents.

Question: {question}

Answer using only the documents above:
"""


def answer_question(question: str, context_tag: str, k: int = 3, min_relevance: float = 0.7) -> dict:
    embedding_function = OpenAIEmbeddings()
    db = create_vector_store(embedding_function)

    results = db.similarity_search_with_relevance_scores(
        question, k=k, filter={"context_tag": context_tag}
    )
    if len(results) == 0 or results[0][1] < min_relevance:
        return {"answer": None, "sources": []}

    context_text = "\n\n".join(
        f'<document source="{doc.metadata.get("source", "unknown")}">\n{doc.page_content}\n</document>'
        for doc, _score in results
    )
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=question)

    model = ChatOpenAI()
    response_text = model.predict(prompt)

    sources = [
        {"source": doc.metadata.get("source"), "content": doc.page_content}
        for doc, _score in results
    ]
    return {"answer": response_text, "sources": sources}
