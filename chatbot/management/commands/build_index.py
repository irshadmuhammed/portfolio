"""
Management command to build the RAG vector index.
Usage: python manage.py build_index
"""
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Build the RAG vector index from PDFs and portfolio web pages."

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO("Starting data ingestion..."))

        try:
            from chatbot.ingestion import ingest_all
            from chatbot.splitter import split_documents
            from chatbot.vector_store import build_vectorstore

            self.stdout.write("Loading documents (PDFs + web pages)...")
            documents = ingest_all()
            self.stdout.write(f"-> {len(documents)} raw documents loaded.")

            self.stdout.write("Splitting into chunks...")
            chunks = split_documents(documents)
            self.stdout.write(f"-> {len(chunks)} chunks created.")

            self.stdout.write("Building embeddings and ChromaDB vector store...")
            build_vectorstore(chunks)

            self.stdout.write(self.style.SUCCESS("Index built successfully! The chatbot is ready."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error building index: {e}"))
            raise
