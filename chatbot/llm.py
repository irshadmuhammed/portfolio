"""OpenRouter LLM via langchain-openai ChatOpenAI wrapper."""
import os
from langchain_openai import ChatOpenAI
from . import config


def get_llm(streaming: bool = False) -> ChatOpenAI:
    api_key = config.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY", "")
    return ChatOpenAI(
        model=config.OPENROUTER_MODEL,
        openai_api_key=api_key,
        openai_api_base=config.OPENROUTER_BASE_URL,
        streaming=streaming,
        temperature=0.3,
        max_tokens=1024,
        default_headers={
            "HTTP-Referer": "https://irshadmuhammed.github.io/portfolio",
            "X-Title": "IrshadGPT Portfolio Assistant",
        },
    )
