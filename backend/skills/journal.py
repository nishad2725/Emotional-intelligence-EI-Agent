"""
Journal skill — generates a personalised reflective journaling prompt.

The prompt is grounded in the user's current emotion and, optionally, their
emotional history context so the question feels relevant rather than generic.
"""
import re
from backend.services.anthropic_client import get_client
from backend.schemas import JournalPrompt

_SYSTEM = (
    "You are a reflective journaling guide for an EI coaching app. "
    "Given the user's current emotional state and optional history context, "
    "generate a single open-ended journaling question that invites genuine self-exploration. "
    "The question should be specific to their feelings — never generic. "
    "Return STRICT JSON with exactly these keys:\n"
    "  prompt: string — the journaling question\n"
    "  emotion_context: string — one phrase describing the feeling this targets\n"
    "  suggested_duration_minutes: integer — 3, 5, 10, or 15\n"
    "No prose. JSON only."
)

_json_block = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(s: str) -> str:
    m = _json_block.search(s.strip())
    if not m:
        raise ValueError("Journal model did not return JSON.")
    return m.group(0)


def generate_journal_prompt(
    user_text: str,
    emotion_json: dict,
    memory_context: str | None = None,
) -> JournalPrompt:
    """
    Generate a reflective journal prompt tailored to the user's current emotion.

    Args:
        user_text: What the user just shared.
        emotion_json: EmotionMetrics dict from the analyze node.
        memory_context: Optional summary of past sessions for added context.
    """
    client = get_client()

    emotions = emotion_json.get("primary_emotions", [])
    valence = emotion_json.get("valence", 0.0)
    arousal = emotion_json.get("arousal", 0.0)

    parts = [
        f"User shared: \"{user_text}\"",
        f"Current emotions: {emotions}, valence={valence:.2f}, arousal={arousal:.2f}",
    ]
    if memory_context:
        parts.append(f"Emotional history:\n{memory_context}")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        temperature=0.6,
        system=_SYSTEM,
        messages=[{"role": "user", "content": "\n".join(parts)}],
    )
    return JournalPrompt.model_validate_json(_extract_json(response.content[0].text))
