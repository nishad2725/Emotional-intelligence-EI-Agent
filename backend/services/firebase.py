"""
Firebase Firestore service — user-scoped data persistence.

Collection layout:
  users/{user_id}/profile            ← UserProfile document
  users/{user_id}/sessions/{sid}/entries/{eid}  ← session entries
  users/{user_id}/patterns/{pid}     ← PatternInsight documents
"""
import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from backend.config import GOOGLE_APPLICATION_CREDENTIALS, FIREBASE_PROJECT_ID

log = logging.getLogger(__name__)

_app = None
_db = None


def _get_db():
    global _app, _db
    if _db:
        return _db
    if not GOOGLE_APPLICATION_CREDENTIALS or not FIREBASE_PROJECT_ID:
        return None
    if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        log.warning("Firebase credentials file not found: %s", GOOGLE_APPLICATION_CREDENTIALS)
        return None
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(GOOGLE_APPLICATION_CREDENTIALS)
            _app = firebase_admin.initialize_app(cred, {"projectId": FIREBASE_PROJECT_ID})
        _db = firestore.client()
        return _db
    except Exception:
        log.exception("Failed to initialise Firebase client.")
        return None


# ---------------------------------------------------------------------------
# User Profiles
# ---------------------------------------------------------------------------

def get_user_profile(user_id: str) -> dict | None:
    db = _get_db()
    if not db:
        return None
    try:
        doc = db.collection("users").document(user_id).collection("profile").document("data").get()
        return doc.to_dict() if doc.exists else None
    except Exception:
        log.exception("Failed to get user profile for %s", user_id)
        return None


def save_user_profile(profile) -> None:
    """Accepts a UserProfile Pydantic model or a plain dict."""
    db = _get_db()
    if not db:
        return
    try:
        data = profile.model_dump() if hasattr(profile, "model_dump") else profile
        db.collection("users").document(data["user_id"]).collection("profile").document("data").set(data)
    except Exception:
        log.exception("Failed to save user profile.")


# ---------------------------------------------------------------------------
# Session Entries
# ---------------------------------------------------------------------------

def log_session_entry(user_id: str, session_id: str, entry: dict) -> None:
    db = _get_db()
    if not db:
        return
    try:
        entry_with_ts = {**entry, "created_at": firestore.SERVER_TIMESTAMP}
        (
            db.collection("users").document(user_id)
            .collection("sessions").document(session_id)
            .collection("entries").add(entry_with_ts)
        )
    except Exception:
        log.exception("Failed to log session entry.")


def get_recent_entries(user_id: str, limit: int = 5) -> list[dict]:
    """Load the most recent `limit` session entries across all sessions for this user."""
    db = _get_db()
    if not db:
        return []
    try:
        # Flatten across all sessions via a collection group query
        entries_ref = (
            db.collection_group("entries")
            .where("user_id", "==", user_id)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        return [doc.to_dict() for doc in entries_ref.stream()]
    except Exception:
        log.exception("Failed to fetch recent entries for %s", user_id)
        return []


def get_history_entries(user_id: str, limit: int = 30) -> list[dict]:
    """Load up to `limit` entries for pattern analysis."""
    return get_recent_entries(user_id, limit=limit)


# ---------------------------------------------------------------------------
# Pattern Insights
# ---------------------------------------------------------------------------

def save_pattern_insight(insight) -> None:
    """Accepts a PatternInsight Pydantic model."""
    db = _get_db()
    if not db:
        return
    try:
        data = insight.model_dump() if hasattr(insight, "model_dump") else insight
        user_id = data["user_id"]
        db.collection("users").document(user_id).collection("patterns").add(
            {**data, "created_at": firestore.SERVER_TIMESTAMP}
        )
    except Exception:
        log.exception("Failed to save pattern insight.")
