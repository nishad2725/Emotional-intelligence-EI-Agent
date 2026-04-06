"""
Personalization skill — manages user profiles stored in Firebase.

A profile holds the user's name, preferred coaching techniques, known emotional
triggers, and a running summary of their emotional journey.
"""
from __future__ import annotations
from datetime import datetime, timezone

from backend.schemas import UserProfile


def get_or_create_profile(user_id: str, name: str = "") -> UserProfile:
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
    coaching: str,  # reserved for future preference learning
) -> UserProfile:
    from backend.services.firebase import save_user_profile

    profile.total_sessions += 1
    profile.last_active = _now_iso()

    new_emotions: list[str] = emotion_json.get("primary_emotions", [])
    for emotion in new_emotions:
        if emotion not in profile.known_triggers and len(profile.known_triggers) < 10:
            profile.known_triggers.append(emotion)

    if profile.total_sessions % 5 == 0:
        profile.emotion_summary = _refresh_summary(profile)

    save_user_profile(profile)
    return profile


def _refresh_summary(profile: UserProfile) -> str:
    from backend.services.anthropic_client import get_client, MODEL_FAST

    if not profile.known_triggers:
        return profile.emotion_summary

    client = get_client()
    prompt = (
        f"User {profile.name} has completed {profile.total_sessions} EI coaching sessions. "
        f"Their common emotions/triggers include: {profile.known_triggers}. "
        f"Previous summary: {profile.emotion_summary or 'none'}. "
        "Write a single updated sentence summarising their emotional journey so far."
    )
    response = client.chat.completions.create(
        model=MODEL_FAST,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
