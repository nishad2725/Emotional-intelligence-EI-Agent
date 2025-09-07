import json, re
from backend.services.openai_client import get_client
from backend.schemas import SafetyLabel

SYSTEM = (
    "You are a safety classifier for an EI coaching app. "
    "Determine whether the text contains crisis or unsafe content that requires immediate escalation. "
    "Return STRICT JSON: {"
    "\"is_critical\": boolean, "
    "\"category\": string | null, "
    "\"confidence\": 0..1, "
    "\"reason\": string, "
    "\"crisis_message\": string | null "
    "}."
    "Critical categories include: self-harm/suicide, harm to others/violence, acute medical emergency."
    "If critical, craft a short supportive crisis_message (non-clinical, resource-oriented)."
)

_json_block = re.compile(r"\{.*\}", re.DOTALL)

def _safe_json_extract(s: str) -> str:
    m = _json_block.search(s.strip())
    if not m:
        raise ValueError("Safety model did not return JSON.")
    return m.group(0)

def check_safety(user_text: str) -> SafetyLabel:
    client = get_client()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.0,
        messages=[
            {"role":"system", "content": SYSTEM},
            {"role":"user", "content": user_text}
        ]
    )
    content = resp.choices[0].message.content
    data = json.loads(_safe_json_extract(content))
    # default crisis message if missing but critical
    if data.get("is_critical") and not data.get("crisis_message"):
        data["crisis_message"] = (
            "I’m concerned about your safety. If you’re in immediate danger, call local emergency services. "
            "You can also text HOME to 741741 (US) to reach a Crisis Counselor."
        )
    return SafetyLabel(**data)
