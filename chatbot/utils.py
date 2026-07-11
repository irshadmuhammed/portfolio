"""Utility helpers for the chatbot."""
from langchain_core.documents import Document


SOURCE_ICONS = {
    "pdf": "ðŸ“„",
    "webpage": "ðŸŒ",
}


def extract_sources(source_docs: list[Document]) -> list[dict]:
    """
    Extract unique source references from retrieved documents.
    Returns list of {icon, label} dicts for frontend chips.
    """
    seen = set()
    sources = []

    for doc in source_docs:
        meta = doc.metadata or {}
        source = meta.get("source", "Unknown")
        source_type = meta.get("source_type", "webpage")

        if source not in seen:
            seen.add(source)
            sources.append({
                "icon": SOURCE_ICONS.get(source_type, "ðŸŒ"),
                "label": source,
            })

    return sources
