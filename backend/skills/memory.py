"""
Memory skill — builds a concise emotional-history context string from past sessions.

Short-term: current session conversation turns (passed in by the graph).
Long-term:  last N Firestore session entries for this user, summarised by Claude Haiku
            to keep the prompt lean.
"""
from backend.services.anthropic_client import get_client

_SUMMARISE_SYSTEM = (
    "You are a memory assistant for an EI coaching app. "
    "Given a list of a user's recent emotional check-ins, write 2-3 sentences "
    "that capture recurring emotions, apparent triggers, and any notable trends. "
    "Be concise and factual. No advice. Plain text only."
)


def _format_entries(entries: list[dict]) -> str:
    lines = []
    for e in entries:
        emotions = e.get("emotion", {}).get("primary_emotions", [])
        valence = e.get("emotion", {}).get("valence", 0.0)
        preview = (e.get("user_text") or "")[:80]
        lines.append(f"- \"{preview}\" → emotions: {emotions}, valence: {valence:.2f}")
    return "\n".join(lines)


def build_memory_context(user_id: str, recent_entries: list[dict]) -> str:
    """
    Returns a brief natural-language summary of the user's emotional history.
    Falls back to a formatted list if no entries are available.

    Args:
        user_id: Not used for the LLM call but kept for future caching/logging.
        recent_entries: List of session entry dicts loaded from Firebase.
    """
    if not recent_entries:
        return ""

    formatted = _format_entries(recent_entries)

    client = get_client()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        temperature=0.1,
        system=_SUMMARISE_SYSTEM,
        messages=[{"role": "user", "content": formatted}],
    )
    return response.content[0].text.strip()
