import anthropic

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    """Lazy-loaded Anthropic client singleton."""
    global _client
    if _client is None:
        from backend.config import ANTHROPIC_API_KEY
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client
