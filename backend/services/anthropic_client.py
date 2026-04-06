"""
OpenAI client — singleton wrapper.
Named anthropic_client.py for backward compatibility with existing skill imports.
All LLM calls use the OpenAI API (gpt-4o-mini by default).
"""
from openai import OpenAI

_client: OpenAI | None = None

# Default models — change here to upgrade globally
MODEL_MAIN = "gpt-4o-mini"    # used by all skills
MODEL_FAST = "gpt-4o-mini"    # used for quick helper calls (memory, profile)


def get_client() -> OpenAI:
    """Lazy-loaded OpenAI client singleton."""
    global _client
    if _client is None:
        from backend.config import OPENAI_API_KEY
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client
