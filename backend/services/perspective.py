# backend/services/perspective.py
import logging
from typing import Optional
from googleapiclient.discovery import build
from google.oauth2 import service_account
from backend.config import GOOGLE_APPLICATION_CREDENTIALS

log = logging.getLogger(__name__)

# Scope for Cloud APIs
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
API_NAME = "commentanalyzer"
API_VERSION = "v1alpha1"

def _get_service():
    """
    Construct a googleapiclient service object using a service account JSON.
    Returns None if credentials file is missing or invalid.
    """
    if not GOOGLE_APPLICATION_CREDENTIALS:
        log.debug("GOOGLE_APPLICATION_CREDENTIALS not set; skipping Perspective calls.")
        return None
    try:
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_APPLICATION_CREDENTIALS,
            scopes=SCOPES
        )
        service = build(API_NAME, API_VERSION, credentials=creds, cache_discovery=False)
        return service
    except Exception as e:
        log.exception("Failed to build Perspective service client: %s", e)
        return None

def toxicity_score(text: str) -> Optional[float]:
    """
    Returns toxicity score 0..1 or None on failure.
    """
    svc = _get_service()
    if svc is None:
        return None

    body = {
        "comment": {"text": text},
        "requestedAttributes": {"TOXICITY": {}},
        "doNotStore": True,
        "languages": ["en"]
    }
    try:
        resp = svc.comments().analyze(body=body).execute()
        attr = resp.get("attributeScores", {}).get("TOXICITY")
        if not attr:
            log.warning("Perspective response missing TOXICITY: %s", resp)
            return None
        summary = attr.get("summaryScore", {})
        value = summary.get("value")
        if value is None:
            log.warning("Perspective toxicity value missing: %s", summary)
            return None
        return float(value)
    except Exception as e:
        log.exception("Perspective analyze failed: %s", e)
        return None

    
