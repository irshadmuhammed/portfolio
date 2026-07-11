"""
Session-based conversation memory.
Stores chat history as (human, ai) tuples in Django session.
"""
from . import config

SESSION_KEY = "chatbot_history"


def get_history(request):
    """Return conversation history from session."""
    return request.session.get(SESSION_KEY, [])


def save_history(request, history: list):
    """Persist conversation history to session, keeping last N turns."""
    trimmed = history[-config.MEMORY_WINDOW:]
    request.session[SESSION_KEY] = trimmed
    request.session.modified = True


def clear_history(request):
    """Clear conversation history from session."""
    request.session[SESSION_KEY] = []
    request.session.modified = True
