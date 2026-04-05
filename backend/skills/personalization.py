"""
Personalization skill — manages user profiles stored in Firebase.

A profile holds the user's name, preferred coaching techniques, known emotional
triggers, and a running summary of their emotional journey. It is loaded at the
start of each session and updated after each interaction.
"""
from __future__ import annotations
from datetime import datetime, timezone

from backend.schemas import UserProfile


def get_or_create_profile(user_id: str, name: str = "") -> UserProfile:
    """
    Load the user profile from Firebase. Creates one if it doesn't exist yet.

    Args:
        user_id: Unique identifier for the user.
        name: Display name — only used when creating a new profile.
    """
    from backend.services.firebase import get_user_profile, save_user_profile

    existing = get_user_profile(user_id)
    if existing:
        return UserProfile(**existing)

    profile = UserProfile(
        user_id=user_id,
        name=name,
        last_active=_now_iso(),
    )
    save_user_profile(profile)
    return profile


def update_after_session(
    profile: UserProfile,
    emotion_json: dict,
    coaching: str,
) -> UserProfile:
    """
    Increment session count, refresh last_active, and optionally update the
    emotion summary using Claude Haiku if enough sessions have accumulated.

    Args:
        profile: The current UserProfile.
        emotion_json: EmotionMetrics from this session.
        coaching: The final coaching response delivered.
    """
    from backend.services.firebase import save_user_profile

    profile.total_sessions += 1
    profile.last_active = _now_iso()

    # Refresh known triggers from emotion labels every 5 sessions
    new_emotions: list[str] = emotion_json.get("primary_emotions", [])
    for emotion in new_emotions:
        if emotion not in profile.known_triggers and len(profile.known_triggers) < 10:
            profile.known_triggers.append(emotion)

    # Refresh emotion summary every 5 sessions using Claude Haiku
    if profile.total_sessions % 5 == 0:
        profile.emotion_summary = _refresh_summary(profile)

    save_user_profile(profile)
    return profile


def _refresh_summary(profile: UserProfile) -> str:
    """Ask Claude Haiku to write a fresh 1-sentence summary of the user's journey."""
    from backend.services.anthropic_client import get_client

    if not profile.known_triggers:
        return profile.emotion_summary

    client = get_client()
    prompt = (
        f"User {profile.name} has completed {profile.total_sessions} EI coaching sessions. "
        f"Their common emotions/triggers include: {profile.known_triggers}. "
        f"Previous summary: {profile.emotion_summary or 'none'}. "
        "Write a single updated sentence summarising their emotional journey so far."
    )
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
