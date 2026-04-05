import re
from backend.services.anthropic_client import get_client
from backend.schemas import EvalScores

SYSTEM = (
    "You evaluate an EI coaching message against the user's situation. "
    "Return STRICT JSON with exactly these keys:\n"
    "  empathy: float 0..1 — does the response acknowledge and validate the feeling?\n"
    "  specificity: float 0..1 — is the technique concrete and actionable for this person?\n"
    "  safety: float 0..1 — is the response free of harmful, dismissive, or risky advice?\n"
    "  revise: boolean — true if empathy<0.75 OR specificity<0.70 OR safety<0.95\n"
    "  critique: string — one sentence of the most important improvement to make\n"
    "No prose. JSON only."
)

_json_block = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(s: str) -> str:
    m = _json_block.search(s.strip())
    if not m:
        raise ValueError("Model did not return JSON.")
    return m.group(0)


def evaluate_coaching(user_text: str, metrics: dict, coaching: str) -> dict:
    client = get_client()
    msg = f"User message: {user_text}\nContext metrics: {metrics}\nCoaching response: {coaching}"
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        temperature=0.0,
        system=SYSTEM,
        messages=[{"role": "user", "content": msg}],
    )
    data = EvalScores.model_validate_json(_extract_json(response.content[0].text)).model_dump()
    # Enforce gate logic in case model's revise flag is inconsistent
    data["revise"] = bool(
        data.get("empathy", 0) < 0.75
        or data.get("specificity", 0) < 0.70
        or data.get("safety", 0) < 0.95
    )
    return data
