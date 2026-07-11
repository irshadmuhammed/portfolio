"""
Data ingestion: loads PDFs and scrapes portfolio web pages.
"""
import logging
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from . import config

logger = logging.getLogger(__name__)


def load_pdfs() -> list[Document]:
    """Load all PDF files from static/files/."""
    docs: list[Document] = []
    pdf_dir = config.PDF_DIR

    if not pdf_dir.exists():
        logger.warning(f"PDF directory not found: {pdf_dir}")
        return docs

    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.info("No PDF files found.")
        return docs

    for pdf_path in pdf_files:
        try:
            loader = PyPDFLoader(str(pdf_path))
            pages = loader.load()
            for page in pages:
                page.metadata["source"] = pdf_path.name
                page.metadata["source_type"] = "pdf"
            docs.extend(pages)
            logger.info(f"Loaded {len(pages)} pages from {pdf_path.name}")
        except Exception as e:
            logger.error(f"Error loading {pdf_path}: {e}")

    return docs


def scrape_page(url: str) -> list[Document]:
    """Scrape text content from a URL using BeautifulSoup."""
    try:
        import requests
        from bs4 import BeautifulSoup

        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove noise elements
        for tag in soup(["script", "style", "nav", "footer", "aside", "header"]):
            tag.decompose()

        main = soup.find("main") or soup.find("body")
        text = main.get_text(separator="\n", strip=True) if main else ""

        # Determine source label from URL
        if "/about" in url:
            source_label = "About Page"
        elif "/projects" in url:
            source_label = "Projects Page"
        elif "/skills" in url:
            source_label = "Skills Page"
        else:
            source_label = url

        if text.strip():
            return [Document(
                page_content=text,
                metadata={"source": source_label, "source_type": "webpage", "url": url}
            )]
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")

    return []


def ingest_all() -> list[Document]:
    """Load PDFs + scrape all configured web pages."""
    documents: list[Document] = []
    documents += load_pdfs()

    for url in config.SCRAPE_URLS:
        documents += scrape_page(url)

    logger.info(f"Total documents ingested: {len(documents)}")
    return documents
