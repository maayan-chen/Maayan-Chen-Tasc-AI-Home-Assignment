from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from vector_store import create_vector_store

PROMPT_TEMPLATE = """
Answer the question based only on the following context. If the context does
not contain enough information to answer the question, say you don't know —
do not guess or use information outside the context.

{context}

---

Answer the question based on the above context: {question}
"""


def answer_question(question: str, context_tag: str, k: int = 3, min_relevance: float = 0.7) -> dict:
    embedding_function = OpenAIEmbeddings()
    db = create_vector_store(embedding_function)

    results = db.similarity_search_with_relevance_scores(
        question, k=k, filter={"context_tag": context_tag}
    )
    if len(results) == 0 or results[0][1] < min_relevance:
        return {"answer": None, "sources": []}

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=question)

    model = ChatOpenAI()
    response_text = model.predict(prompt)

    sources = [
        {"source": doc.metadata.get("source"), "content": doc.page_content}
        for doc, _score in results
    ]
    return {"answer": response_text, "sources": sources}
