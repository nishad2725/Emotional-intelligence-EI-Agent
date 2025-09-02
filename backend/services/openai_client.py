from openai import OpenAI
from backend.config import OPENAI_API_KEY

_client = None

def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client
