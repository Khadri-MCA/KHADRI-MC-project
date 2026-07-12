"""
LLM access layer for the LangGraph HCP agent.

Per task spec: LLMs are served via Groq (https://console.groq.com/docs/models).
- Primary reasoning / tool-calling model: gemma2-9b-it
- Larger context fallback (long voice-note transcripts, multi-turn chat memory): llama-3.3-70b-versatile
"""
from langchain_groq import ChatGroq

from app.config import settings


from langchain_groq import ChatGroq
from app.config import settings

from langchain_groq import ChatGroq

from app.config import settings

def get_primary_llm(temperature: float = 0):
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_primary_model,
        temperature=temperature,
        timeout=25,
        max_retries=1,
    )


def get_context_llm(temperature: float = 0):
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_context_model,
        temperature=temperature,
        timeout=25,
        max_retries=1,
    )
