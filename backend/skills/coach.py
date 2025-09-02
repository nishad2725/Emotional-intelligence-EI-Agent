from backend.services.openai_client import get_client

COACH_SYSTEM = (
    "You are an EI coach. Using the provided metrics (valence, arousal, emotions, toxicity), "
    "respond with ONE concise, practical exercise the user can try NOW. 3 lines max. "
    "Start with a validating reflection (1 line), then a specific technique (1-2 lines)."
)

def coach_user(user_text: str, emotion_json: dict, toxicity: float | None) -> str:
    client = get_client()
    metrics_line = f"metrics={emotion_json}, toxicity={toxicity}"
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.5,
        messages=[
            {"role": "system", "content": COACH_SYSTEM},
            {"role": "user", "content": f"User said: {user_text}\n{metrics_line}"}
        ]
    )
    return resp.choices[0].message.content.strip()
