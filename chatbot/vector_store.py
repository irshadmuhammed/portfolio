"""ChromaDB vector store â€” build and load."""
import logging
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from .embeddings import get_embeddings
from . import config

logger = logging.getLogger(__name__)


def build_vectorstore(documents: list[Document]) -> Chroma:
    """Create and persist a ChromaDB from documents."""
    logger.info(f"Building vector store with {len(documents)} chunksâ€¦")
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=get_embeddings(),
        persist_directory=config.CHROMA_DB_PATH,
        collection_name=config.CHROMA_COLLECTION,
    )
    logger.info("Vector store built and persisted.")
    return vectorstore


def load_vectorstore() -> Chroma:
    """Load existing ChromaDB from disk."""
    return Chroma(
        persist_directory=config.CHROMA_DB_PATH,
        embedding_function=get_embeddings(),
        collection_name=config.CHROMA_COLLECTION,
    )


def vectorstore_exists() -> bool:
    """Check if a vector store has been built."""
    import os
    db_path = config.CHROMA_DB_PATH
    return os.path.isdir(db_path) and len(os.listdir(db_path)) > 0
