"""MMR retriever from the vector store."""
from langchain_community.vectorstores import Chroma
from . import config


def get_retriever(vectorstore: Chroma):
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": config.RETRIEVER_K,
            "fetch_k": config.RETRIEVER_FETCH_K,
        },
    )
