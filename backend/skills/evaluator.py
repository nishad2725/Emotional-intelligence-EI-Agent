import json, re
from backend.services.openai_client import get_client

SYSTEM = (
  "You evaluate the coaching message for empathy, specificity, and safety. "
  "Return STRICT JSON: {\"empathy\":0..1, \"specificity\":0..1, \"safety\":0..1, \"revise\":boolean, \"critique\":string}."
)

_json_block = re.compile(r"\{.*\}", re.DOTALL)

def _safe_json_extract(s: str) -> str:
    m = _json_block.search(s.strip())
    if not m:
        raise ValueError("Model did not return JSON.")
    return m.group(0)

def evaluate_coaching(user_text: str, metrics: dict, coaching: str) -> dict:
    client = get_client()
    msg = f"User: {user_text}\nMetrics: {metrics}\nCoaching: {coaching}"
    out = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.0,
        messages=[{"role":"system", "content": SYSTEM},
                  {"role":"user", "content": msg}]
    ).choices[0].message.content
    data = json.loads(_safe_json_extract(out))

    # gate: refine if quality is low
    data["revise"] = bool(
        (data.get("empathy",0) < 0.75) or
        (data.get("specificity",0) < 0.70) or
        (data.get("safety",0) < 0.95)
    )
    return data
