"""
Hume AI Expression Measurement service — audio prosody emotion analysis.

Requires HUME_API_KEY in .env. Falls back gracefully if key is missing or
the hume package is not installed.

The Hume prosody model returns per-segment emotion scores for ~50 emotions.
We aggregate them by taking the mean across all time segments and return the
top-5 emotions with their average scores.
"""
import logging

from backend.config import HUME_API_KEY

log = logging.getLogger(__name__)


def analyze_audio_prosody(audio_path: str) -> dict:
    """
    Submit an audio file to Hume's Expression Measurement API and return
    aggregated prosody emotion scores.

    Returns:
        {
            "available": True/False,
            "top_emotions": [{"name": str, "score": float}, ...],  # top 5
            "all_emotions": {emotion_name: avg_score, ...},
            "error": str or None
        }
    """
    if not HUME_API_KEY:
        return {"available": False, "top_emotions": [], "all_emotions": {}, "error": "HUME_API_KEY not set"}

    try:
        from hume import HumeBatchClient
        from hume.models.config import ProsodyConfig
    except ImportError:
        log.warning("hume package not installed. Run: pip install hume")
        return {"available": False, "top_emotions": [], "all_emotions": {}, "error": "hume package not installed"}

    try:
        client = HumeBatchClient(api_key=HUME_API_KEY)
        configs = [ProsodyConfig()]
        job = client.submit_job(urls=[], configs=configs, files=[audio_path])
        job.await_complete(timeout=60)
        predictions = job.get_predictions()

        # Aggregate emotion scores across all time segments
        emotion_accumulator: dict[str, list[float]] = {}
        for file_pred in predictions:
            for model_pred in file_pred.get("results", {}).get("predictions", []):
                for segment in model_pred.get("models", {}).get("prosody", {}).get("grouped_predictions", []):
                    for pred in segment.get("predictions", []):
                        for emotion in pred.get("emotions", []):
                            name = emotion["name"]
                            score = emotion["score"]
                            emotion_accumulator.setdefault(name, []).append(score)

        if not emotion_accumulator:
            return {"available": True, "top_emotions": [], "all_emotions": {}, "error": "No prosody predictions returned"}

        avg_emotions = {name: sum(scores) / len(scores) for name, scores in emotion_accumulator.items()}
        top_5 = sorted(avg_emotions.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "available": True,
            "top_emotions": [{"name": n, "score": round(s, 4)} for n, s in top_5],
            "all_emotions": {k: round(v, 4) for k, v in avg_emotions.items()},
            "error": None,
        }

    except Exception as e:
        log.exception("Hume prosody analysis failed: %s", e)
        return {"available": False, "top_emotions": [], "all_emotions": {}, "error": str(e)}
