import json, re
from typing import Dict, Any
from backend.services.openai_client import get_client

SYSTEM = (
    "You analyze emotional tone in a user's text. "
    "Return STRICT JSON with keys: "
    "valence (float -1..1), arousal (float 0..1), "
    "primary_emotions (array of up to 3 strings), confidence (0..1), "
    "rationale (string ~20 words). No prose. JSON only."
)

_json_block = re.compile(r"\{.*\}", re.DOTALL)

def _safe_json_extract(s: str) -> str:
    m = _json_block.search(s.strip())
    if not m:
        raise ValueError("Model did not return JSON.")
    return m.group(0)

def analyze_text_emotion(text: str) -> Dict[str, Any]:
    client = get_client()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": text}]
    )
    content = resp.choices[0].message.content
    return json.loads(_safe_json_extract(content))
