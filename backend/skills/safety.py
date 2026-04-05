import json
import re
from backend.services.anthropic_client import get_client
from backend.schemas import SafetyLabel

SYSTEM = (
    "You are a safety classifier for an EI coaching app. "
    "Determine whether the user's text contains crisis or unsafe content requiring immediate escalation. "
    "Return STRICT JSON with exactly these keys:\n"
    "  is_critical: boolean\n"
    "  category: string or null — one of: self-harm, suicide, harm-to-others, violence, medical-emergency, null\n"
    "  confidence: float 0..1\n"
    "  reason: string — brief explanation\n"
    "  crisis_message: string or null — if critical, a short warm message with resource info\n"
    "No prose. JSON only."
)

_DEFAULT_CRISIS = (
    "I'm concerned about your safety and I'm here with you. "
    "If you're in immediate danger, please call emergency services (911 in the US). "
    "You can also text HOME to 741741 to reach a Crisis Text Line counselor anytime."
)

_json_block = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(s: str) -> str:
    m = _json_block.search(s.strip())
    if not m:
        raise ValueError("Safety model did not return JSON.")
    return m.group(0)


def check_safety(user_text: str) -> SafetyLabel:
    client = get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        temperature=0.0,
        system=SYSTEM,
        messages=[{"role": "user", "content": user_text}],
    )
    data = json.loads(_extract_json(response.content[0].text))
    if data.get("is_critical") and not data.get("crisis_message"):
        data["crisis_message"] = _DEFAULT_CRISIS
    return SafetyLabel(**data)
