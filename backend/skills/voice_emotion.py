"""
Voice emotion skill — two-step pipeline for audio input.

Step 1 — Transcription:
    Uses SpeechRecognition (Google free API) to convert audio → text.
    Supports WAV natively. MP3/M4A/OGG require pydub + ffmpeg.

Step 2 — Prosody (optional, enhanced):
    If HUME_API_KEY is set and the hume package is installed, runs the audio
    through Hume's Expression Measurement API for voice-level emotion scores.
    These are additive — the text transcription still flows through the main
    EI graph for coaching.

Returns:
    {
        "transcription": str,          # text to pass into ei_graph
        "voice_emotions": dict,        # Hume prosody result (or empty)
        "transcription_error": str | None
    }
"""
import os
import logging
import tempfile

log = logging.getLogger(__name__)


def _convert_to_wav(audio_path: str) -> str:
    """Convert non-WAV audio to a temporary WAV file using pydub."""
    try:
        from pydub import AudioSegment
    except ImportError:
        raise RuntimeError("pydub is required to process non-WAV files. Run: pip install pydub")

    ext = os.path.splitext(audio_path)[1].lower().lstrip(".")
    audio = AudioSegment.from_file(audio_path, format=ext)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    audio.export(tmp.name, format="wav")
    return tmp.name


def transcribe_audio(audio_path: str) -> tuple[str, str | None]:
    """
    Transcribe an audio file to text.

    Returns (transcription, error_message).
    """
    try:
        import speech_recognition as sr
    except ImportError:
        return "", "SpeechRecognition package not installed. Run: pip install SpeechRecognition"

    wav_path = audio_path
    tmp_wav = None

    try:
        ext = os.path.splitext(audio_path)[1].lower()
        if ext != ".wav":
            wav_path = _convert_to_wav(audio_path)
            tmp_wav = wav_path

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            # Adjust for ambient noise for better accuracy
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data)
        return text, None

    except Exception as e:
        log.exception("Transcription failed: %s", e)
        return "", str(e)

    finally:
        if tmp_wav and os.path.exists(tmp_wav):
            os.unlink(tmp_wav)


def analyze_voice(audio_path: str) -> dict:
    """
    Full voice emotion analysis pipeline.

    1. Transcribes audio to text.
    2. Optionally runs Hume prosody analysis in parallel.

    Args:
        audio_path: Path to audio file (WAV preferred; MP3/M4A need pydub+ffmpeg).

    Returns:
        {
            "transcription": str,
            "voice_emotions": {           # Hume prosody result
                "available": bool,
                "top_emotions": [...],
                "all_emotions": {...},
                "error": str | None
            },
            "transcription_error": str | None
        }
    """
    transcription, transcription_error = transcribe_audio(audio_path)

    # Run Hume prosody analysis (non-blocking failure)
    from backend.services.hume_voice import analyze_audio_prosody
    voice_emotions = analyze_audio_prosody(audio_path)

    return {
        "transcription": transcription,
        "voice_emotions": voice_emotions,
        "transcription_error": transcription_error,
    }
