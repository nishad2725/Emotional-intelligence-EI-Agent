import firebase_admin
from firebase_admin import credentials, firestore
from backend.config import GOOGLE_APPLICATION_CREDENTIALS, FIREBASE_PROJECT_ID

_app = None
_db = None

def db():
    global _app, _db
    if _db:
        return _db
    cred = credentials.Certificate(GOOGLE_APPLICATION_CREDENTIALS)
    _app = firebase_admin.initialize_app(cred, {"projectId": FIREBASE_PROJECT_ID})
    _db = firestore.client(_app)
    return _db

def log_session_entry(entry: dict):
    ref = db().collection("sessions").document()
    ref.set({"created_at": firestore.SERVER_TIMESTAMP})
    ref.collection("entries").add(entry)
