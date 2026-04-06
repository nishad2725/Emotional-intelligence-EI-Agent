import re
from typing import Dict, Any

from backend.services.anthropic_client import get_client, MODEL_MAIN
from backend.schemas import EmotionMetrics

SYSTEM = (
    "You analyze the emotional tone of a user's text for an EI coaching app. "
    "Return STRICT JSON with exactly these keys:\n"
    "  valence: float -1.0 to 1.0 (negative = unpleasant, positive = pleasant)\n"
    "  arousal: float 0.0 to 1.0 (low = calm, high = activated)\n"
    "  primary_emotions: array of up to 3 emotion label strings\n"
    "  confidence: float 0.0 to 1.0\n"
    "  rationale: string, ~20 words explaining the reading\n"
    "No prose. JSON only."
)

_json_block = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(s: str) -> str:
    m = _json_block.search(s.strip())
    if not m:
        raise ValueError("Model did not return JSON.")
    return m.group(0)


def analyze_text_emotion(text: str) -> Dict[str, Any]:
    client = get_client()
    response = client.chat.completions.create(
        model=MODEL_MAIN,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": text},
        ],
    )
    content = response.choices[0].message.content
    metrics = EmotionMetrics.model_validate_json(_extract_json(content))
    return metrics.model_dump()
