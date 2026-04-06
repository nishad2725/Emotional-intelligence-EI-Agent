"""
Pattern skill — identifies cross-session emotional patterns for a user.

Loads a longer history window (up to 30 sessions) and asks the model to surface:
  - recurring emotion clusters
  - apparent triggers
  - valence trend (improving / stable / declining)
  - one long-term recommendation
"""
import re
from backend.services.anthropic_client import get_client, MODEL_MAIN
from backend.schemas import PatternInsight

_SYSTEM = (
    "You are an emotional intelligence analyst. "
    "Given a user's emotional check-in history, identify meaningful patterns. "
    "Return STRICT JSON with exactly these keys:\n"
    "  patterns: array of strings — e.g. [\"Sunday evening anxiety\", \"post-meeting exhaustion\"]\n"
    "  triggers: array of strings — apparent situational triggers\n"
    "  trend: string — one of: improving, stable, declining\n"
    "  recommendation: string — one actionable long-term suggestion (1-2 sentences)\n"
    "No prose. JSON only."
)

_json_block = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(s: str) -> str:
    m = _json_block.search(s.strip())
    if not m:
        raise ValueError("Pattern model did not return JSON.")
    return m.group(0)


def _format_history(entries: list[dict]) -> str:
    lines = []
    for i, e in enumerate(entries, 1):
        emotions = e.get("emotion", {}).get("primary_emotions", [])
        valence = e.get("emotion", {}).get("valence", 0.0)
        arousal = e.get("emotion", {}).get("arousal", 0.0)
        preview = (e.get("user_text") or "")[:100]
        coaching = (e.get("coaching") or "")[:60]
        lines.append(
            f"{i}. \"{preview}\" | emotions={emotions} | valence={valence:.2f} | arousal={arousal:.2f}"
            + (f" | coaching: \"{coaching}\"" if coaching else "")
        )
    return "\n".join(lines)


def analyze_patterns(user_id: str, history_entries: list[dict]) -> PatternInsight:
    if not history_entries:
        return PatternInsight(
            user_id=user_id,
            patterns=[],
            triggers=[],
            trend="stable",
            recommendation="Keep checking in — more sessions will reveal your patterns.",
        )

    client = get_client()
    response = client.chat.completions.create(
        model=MODEL_MAIN,
        temperature=0.3,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": _format_history(history_entries)},
        ],
    )
    data = PatternInsight.model_validate_json(_extract_json(response.choices[0].message.content))
    data.user_id = user_id
    return data
