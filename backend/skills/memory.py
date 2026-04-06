"""
Memory skill — builds a concise emotional-history context string from past sessions.

Uses gpt-4o-mini to summarise the last N session entries into a 2-3 sentence
context that gets passed to the coach for personalised responses.
"""
from backend.services.anthropic_client import get_client, MODEL_FAST

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


def build_memory_context(_user_id: str, recent_entries: list[dict]) -> str:
    if not recent_entries:
        return ""

    formatted = _format_entries(recent_entries)
    client = get_client()
    response = client.chat.completions.create(
        model=MODEL_FAST,
        temperature=0.1,
        messages=[
            {"role": "system", "content": _SUMMARISE_SYSTEM},
            {"role": "user", "content": formatted},
        ],
    )
    return response.choices[0].message.content.strip()
