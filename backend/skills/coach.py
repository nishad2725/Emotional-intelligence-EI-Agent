from backend.services.anthropic_client import get_client

SYSTEM = (
    "You are a warm, expert Emotional Intelligence coach. "
    "Using the provided emotion metrics, toxicity score, user profile, and emotional memory context, "
    "craft a highly personalized response that:\n"
    "1. Validates the user's emotion in 1 sentence (name what they're feeling)\n"
    "2. Offers ONE specific, actionable technique they can try right now (1-2 sentences)\n"
    "Keep the total response to 3 lines max. "
    "If memory or profile context is provided, weave in what you know about this person. "
    "Never be generic — every word should feel written for this specific person in this moment."
)


def coach_user(
    user_text: str,
    emotion_json: dict,
    toxicity: float | None,
    user_profile: dict | None = None,
    memory_context: str | None = None,
) -> str:
    client = get_client()

    context_parts = [f"User said: {user_text}", f"Emotion metrics: {emotion_json}"]
    if toxicity is not None:
        context_parts.append(f"Toxicity score: {toxicity:.2f}")
    if user_profile:
        name = user_profile.get("name", "")
        techniques = user_profile.get("preferred_techniques", [])
        triggers = user_profile.get("known_triggers", [])
        profile_str = f"User profile — Name: {name}"
        if techniques:
            profile_str += f", Preferred techniques: {techniques}"
        if triggers:
            profile_str += f", Known triggers: {triggers}"
        context_parts.append(profile_str)
    if memory_context:
        context_parts.append(f"Emotional history context:\n{memory_context}")

    user_message = "\n".join(context_parts)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        temperature=0.5,
        system=SYSTEM,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text.strip()
