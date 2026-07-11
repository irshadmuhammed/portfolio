"""
RAG chain builder.
Combines retriever + system prompt + LLM into a conversational chain.
"""
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from .llm import get_llm
from .retriever import get_retriever
from .vector_store import load_vectorstore
from .prompts import SYSTEM_PROMPT


def build_rag_chain(streaming: bool = False):
    """Build and return the RAG chain."""
    vectorstore = load_vectorstore()
    retriever = get_retriever(vectorstore)
    llm = get_llm(streaming=streaming)

    prompt = PromptTemplate(
        input_variables=["context", "chat_history", "question"],
        template=SYSTEM_PROMPT,
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True,
        verbose=False,
    )
    return chain
