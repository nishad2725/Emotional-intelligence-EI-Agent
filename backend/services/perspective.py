import requests
from typing import Optional
from backend.config import PERSPECTIVE_API_KEY

PERSPECTIVE_URL = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"

def toxicity_score(text: str) -> Optional[float]:
    if not PERSPECTIVE_API_KEY:
        return None
    payload = {
        "comment": {"text": text},
        "requestedAttributes": {"TOXICITY": {}},
        "doNotStore": True,
        "languages": ["en"]
    }
    r = requests.post(f"{PERSPECTIVE_URL}?key={PERSPECTIVE_API_KEY}", json=payload, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
