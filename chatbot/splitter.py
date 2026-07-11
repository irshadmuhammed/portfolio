"""Text splitting for RAG chunks."""
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from . import config


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = splitter.split_documents(documents)
    return chunks
