"""
Chatbot API views.
POST /chatbot/chat/  -> streaming SSE response
POST /chatbot/reset/ -> clear session memory
"""
import json
import logging
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .memory import get_history, save_history, clear_history
from .utils import extract_sources

logger = logging.getLogger(__name__)

# Lazy load the RAG chain to avoid heavy imports at startup
_rag_chain = None

def get_rag_chain():
    global _rag_chain
    if _rag_chain is None:
        from .rag_chain import build_rag_chain
        from .vector_store import vectorstore_exists
        if vectorstore_exists():
            _rag_chain = build_rag_chain(streaming=True)
        else:
            logger.warning("Vector store not found. RAG chain will not be built.")
    return _rag_chain


def _format_history(history):
    # LangChain expects a list of (human, ai) tuples
    return history


@csrf_exempt
@require_POST
def chat_view(request):
    try:
        body = json.loads(request.body)
        question = body.get("question", "").strip()
        if not question:
            return JsonResponse({"error": "No question provided."}, status=400)

        history = get_history(request)
        chain = get_rag_chain()

        if not chain:
            # Fallback if no index
            return JsonResponse({"error": "Chatbot is not initialized. Please build the RAG index first."}, status=500)

        def stream_response():
            full_response = ""
            sources = []
            try:
                # We use the standard ConversationalRetrievalChain or similar
                # However, with streaming=True in ChatOpenAI, we can iterate over the stream
                # wait, LangChain's ConversationalRetrievalChain doesn't directly yield tokens in .stream() unless we use an async iterator or callbacks.
                # A simpler approach using LangChain Core runnables is better, but since we are in Django sync views,
                # let's just use regular chain and a CallbackHandler to stream, or fallback to the previous HTTP direct approach if we want to stream manually.
                # Actually, wait, my previous direct HTTP approach worked beautifully with SSE streaming!
                pass
            except Exception as e:
                pass
        
        # Let's write the LangChain streaming manually or just use direct HTTP approach with LangChain retriever!
        pass
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

