from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PERSPECTIVE_API_KEY = os.getenv("GOOGLE_PERSPECTIVE_API_KEY")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
HUME_API_KEY = os.getenv("HUME_API_KEY")  # optional (Phase 2+)

REQUIRED = {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "GOOGLE_PERSPECTIVE_API_KEY": PERSPECTIVE_API_KEY,
    "FIREBASE_PROJECT_ID": FIREBASE_PROJECT_ID,
    "GOOGLE_APPLICATION_CREDENTIALS": GOOGLE_APPLICATION_CREDENTIALS,
}
missing = [k for k, v in REQUIRED.items() if not v]
if missing:
    print(f"[warn] Missing env vars: {missing}. Some features will not work.")
