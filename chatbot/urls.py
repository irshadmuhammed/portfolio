from django.urls import path
from . import api

urlpatterns = [
    path("chat/", api.chat_view, name="chatbot_chat"),
    path("reset/", api.reset_view, name="chatbot_reset"),
]
