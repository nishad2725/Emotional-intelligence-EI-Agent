from backend.config import HUME_API_KEY

def analyze_voice_stub(path_to_wav: str) -> dict:
    if not HUME_API_KEY:
        return {"note": "Hume API key not set; skipping voice analysis."}
    return {"note": "Voice analysis stub (implement Hume EVI v3 in Phase 2)."}
