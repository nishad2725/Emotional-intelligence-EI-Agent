"""
Hume AI Expression Measurement service — audio prosody emotion analysis.

Uses Hume SDK v0.7+ (HumeClient / expression_measurement.batch API).
Requires HUME_API_KEY in .env. HUME_SECRET_KEY is optional (only needed
for EVI / streaming features, not batch prosody).

Falls back gracefully if key is missing or the hume package is not installed.

The prosody model returns per-segment emotion scores for ~50 emotions.
We aggregate by mean across all time segments and return the top-5.
"""
import logging
import time

from backend.config import HUME_API_KEY

log = logging.getLogger(__name__)


def analyze_audio_prosody(audio_path: str) -> dict:
    """
    Submit an audio file to Hume's Expression Measurement batch API and return
    aggregated prosody emotion scores.

    Returns:
        {
            "available": bool,
            "top_emotions": [{"name": str, "score": float}, ...],  # top 5
            "all_emotions": {emotion_name: avg_score, ...},
            "error": str | None
        }
    """
    if not HUME_API_KEY:
        return {
            "available": False,
            "top_emotions": [],
            "all_emotions": {},
            "error": "HUME_API_KEY not set in .env",
        }

    try:
        from hume import HumeClient
        from hume.expression_measurement.batch import Models, Prosody
    except ImportError:
        log.warning("hume package not installed. Run: pip install hume")
        return {
            "available": False,
            "top_emotions": [],
            "all_emotions": {},
            "error": "hume package not installed. Run: pip install hume",
        }

    try:
        client = HumeClient(api_key=HUME_API_KEY)

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        # Submit batch inference job
        job = client.expression_measurement.batch.start_inference_job_from_local_file(
            file=audio_bytes,
            models=Models(prosody=Prosody()),
        )

        # Poll until complete (max 90 seconds)
        for _ in range(45):
            details = client.expression_measurement.batch.get_job_details(id=job.job_id)
            status = details.state.status if details.state else None
            if status in ("COMPLETED", "FAILED"):
                break
            time.sleep(2)
        else:
            return {
                "available": False,
                "top_emotions": [],
                "all_emotions": {},
                "error": "Hume job timed out after 90 seconds",
            }

        if str(status) == "FAILED":
            return {
                "available": False,
                "top_emotions": [],
                "all_emotions": {},
                "error": "Hume inference job failed",
            }

        # Fetch predictions
        predictions_response = client.expression_measurement.batch.get_job_predictions(
            id=job.job_id
        )

        # Aggregate emotion scores across all time segments
        emotion_accumulator: dict[str, list[float]] = {}

        for file_pred in predictions_response:
            if not hasattr(file_pred, "results") or not file_pred.results:
                continue
            for prediction in file_pred.results.predictions:
                prosody_model = getattr(prediction.models, "prosody", None)
                if not prosody_model:
                    continue
                for group in prosody_model.grouped_predictions:
                    for pred in group.predictions:
                        for emotion in pred.emotions:
                            emotion_accumulator.setdefault(emotion.name, []).append(emotion.score)

        if not emotion_accumulator:
            return {
                "available": True,
                "top_emotions": [],
                "all_emotions": {},
                "error": "No prosody predictions in response",
            }

        avg_emotions = {
            name: sum(scores) / len(scores)
            for name, scores in emotion_accumulator.items()
        }
        top_5 = sorted(avg_emotions.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "available": True,
            "top_emotions": [{"name": n, "score": round(s, 4)} for n, s in top_5],
            "all_emotions": {k: round(v, 4) for k, v in avg_emotions.items()},
            "error": None,
        }

    except Exception as e:
        log.exception("Hume prosody analysis failed: %s", e)
        return {
            "available": False,
            "top_emotions": [],
            "all_emotions": {},
            "error": str(e),
        }
