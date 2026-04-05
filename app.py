"""
EI Assistant — Streamlit Web UI

Run:
    streamlit run app.py
"""
import uuid
import tempfile
import os
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EI Assistant",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _valence_label(v: float) -> str:
    if v < -0.6:   return "very low 😔"
    if v < -0.2:   return "low 😟"
    if v < 0.2:    return "neutral 😐"
    if v < 0.6:    return "positive 🙂"
    return "very positive 😄"


def _arousal_label(a: float) -> str:
    if a < 0.33:  return "calm"
    if a < 0.66:  return "moderate"
    return "activated"


def _run_text(user_text: str, user_id: str, user_name: str, session_id: str) -> dict:
    from backend.agents.ei_graph import ei_graph, EIState
    return ei_graph.invoke(EIState(
        user_id=user_id,
        user_name=user_name,
        user_text=user_text,
        session_id=session_id,
    ))


def _run_voice(audio_bytes: bytes, audio_ext: str, user_id: str, user_name: str, session_id: str) -> dict:
    from backend.skills.voice_emotion import analyze_voice
    from backend.agents.ei_graph import ei_graph, EIState

    with tempfile.NamedTemporaryFile(suffix=f".{audio_ext}", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        voice_result = analyze_voice(tmp_path)
        transcription = voice_result.get("transcription", "")
        voice_emotions = voice_result.get("voice_emotions", {})
        transcription_error = voice_result.get("transcription_error")

        if not transcription:
            return {
                "_voice_only": True,
                "_transcription_error": transcription_error or "Could not transcribe audio.",
                "_voice_emotions": voice_emotions,
            }

        result = ei_graph.invoke(EIState(
            user_id=user_id,
            user_name=user_name,
            user_text=transcription,
            session_id=session_id,
        ))
        result["_transcription"] = transcription
        result["_voice_emotions"] = voice_emotions
        return result
    finally:
        os.unlink(tmp_path)


def _run_patterns(user_id: str) -> dict:
    from backend.agents.pattern_graph import pattern_graph, PatternState
    return pattern_graph.invoke(PatternState(user_id=user_id))


# ── Session state init ────────────────────────────────────────────────────────

if "user_id" not in st.session_state:
    st.session_state.user_id = "anonymous"
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "history" not in st.session_state:
    st.session_state.history = []   # list of (user_text, result_dict)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🧠 EI Assistant")
    st.caption("Powered by Claude claude-sonnet-4-6")
    st.divider()

    name_input = st.text_input("Your name", value=st.session_state.user_name, placeholder="Optional")
    if name_input != st.session_state.user_name:
        st.session_state.user_name = name_input
        st.session_state.user_id = name_input.lower().replace(" ", "_") if name_input else "anonymous"
        st.session_state.session_id = str(uuid.uuid4())

    st.divider()

    if st.button("🔍 Analyse My Patterns", use_container_width=True):
        with st.spinner("Analysing your emotional patterns…"):
            try:
                result = _run_patterns(st.session_state.user_id)
                insight = result.get("insight", {})
                st.session_state._last_insight = insight
            except Exception as e:
                st.error(f"Pattern analysis failed: {e}")

    if hasattr(st.session_state, "_last_insight") and st.session_state._last_insight:
        ins = st.session_state._last_insight
        st.markdown("**Your patterns**")
        for p in ins.get("patterns", []):
            st.markdown(f"- {p}")
        st.markdown(f"**Trend:** {ins.get('trend', '—')}")
        st.markdown(f"**Long-term tip:** {ins.get('recommendation', '—')}")

    st.divider()
    if st.button("🔄 New Session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.history = []
        if hasattr(st.session_state, "_last_insight"):
            del st.session_state._last_insight
        st.rerun()

# ── Main area ─────────────────────────────────────────────────────────────────

st.header("How are you feeling?")
st.caption("Share in text or upload a voice recording — your EI coach responds personally.")

tab_text, tab_voice = st.tabs(["💬 Text", "🎙️ Voice"])

# ── Text tab ──────────────────────────────────────────────────────────────────

with tab_text:
    with st.form("text_form", clear_on_submit=True):
        user_text = st.text_area(
            "What's on your mind?",
            placeholder="e.g. I'm feeling overwhelmed with work deadlines…",
            height=100,
        )
        submitted = st.form_submit_button("Send", use_container_width=True)

    if submitted and user_text.strip():
        with st.spinner("Thinking…"):
            try:
                result = _run_text(
                    user_text.strip(),
                    st.session_state.user_id,
                    st.session_state.user_name,
                    st.session_state.session_id,
                )
                st.session_state.history.append((user_text.strip(), result))
            except Exception as e:
                st.error(f"Error: {e}")

# ── Voice tab ─────────────────────────────────────────────────────────────────

with tab_voice:
    st.markdown(
        "Upload a WAV, MP3, or M4A recording. The audio will be transcribed, "
        "then analysed exactly like text. If you have a Hume API key, voice-level "
        "prosody scores are shown too."
    )
    audio_file = st.file_uploader(
        "Upload audio", type=["wav", "mp3", "m4a", "ogg"], label_visibility="collapsed"
    )
    if audio_file and st.button("Analyse Voice", use_container_width=True):
        ext = audio_file.name.rsplit(".", 1)[-1].lower()
        with st.spinner("Transcribing and analysing…"):
            try:
                result = _run_voice(
                    audio_file.read(),
                    ext,
                    st.session_state.user_id,
                    st.session_state.user_name,
                    st.session_state.session_id,
                )
                if result.get("_voice_only"):
                    st.warning(f"Transcription failed: {result.get('_transcription_error')}")
                    voice_emo = result.get("_voice_emotions", {})
                    if voice_emo.get("available") and voice_emo.get("top_emotions"):
                        st.subheader("Voice Prosody (Hume)")
                        for e in voice_emo["top_emotions"]:
                            st.progress(e["score"], text=f"{e['name']}: {e['score']:.0%}")
                else:
                    transcription = result.get("_transcription", "")
                    if transcription:
                        st.info(f"Transcription: *\"{transcription}\"*")
                    st.session_state.history.append((transcription or "[voice]", result))
            except Exception as e:
                st.error(f"Voice analysis error: {e}")

# ── Conversation history ───────────────────────────────────────────────────────

if st.session_state.history:
    st.divider()
    st.subheader("Session")

    for user_text, result in reversed(st.session_state.history):
        # User bubble
        with st.chat_message("user"):
            st.write(user_text)

        # Coach bubble
        with st.chat_message("assistant", avatar="🧠"):
            is_critical = result.get("is_critical", False)

            if is_critical:
                st.error(result.get("coaching", ""))
            else:
                st.write(result.get("coaching", ""))

            # Emotion metrics
            emotion = result.get("emotion", {})
            if emotion:
                emotions = emotion.get("primary_emotions", [])
                valence = emotion.get("valence", 0.0)
                arousal = emotion.get("arousal", 0.0)
                tox = result.get("toxicity")

                with st.expander("Emotion analysis", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Mood", _valence_label(valence), f"{valence:+.2f}")
                        st.metric("Energy", _arousal_label(arousal), f"{arousal:.2f}")
                    with col2:
                        st.markdown("**Detected emotions**")
                        for emo in emotions:
                            st.markdown(f"- {emo}")
                        if tox is not None:
                            color = "red" if tox > 0.6 else "orange" if tox > 0.3 else "green"
                            st.markdown(f"**Toxicity:** :{color}[{tox:.0%}]")

            # Voice prosody (Hume)
            voice_emo = result.get("_voice_emotions", {})
            if voice_emo.get("available") and voice_emo.get("top_emotions"):
                with st.expander("Voice prosody (Hume)", expanded=False):
                    for e in voice_emo["top_emotions"]:
                        st.progress(e["score"], text=f"{e['name']}: {e['score']:.0%}")

            # Journal prompt
            jp = result.get("journal_prompt")
            if jp:
                with st.expander("✦ Journaling prompt", expanded=False):
                    st.info(jp.get("prompt", ""))
                    st.caption(f"Suggested: {jp.get('suggested_duration_minutes', 5)} minutes")

            # Eval scores (collapsed by default)
            ev = result.get("eval", {})
            if ev:
                with st.expander("Coaching quality scores", expanded=False):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Empathy", f"{ev.get('empathy', 0):.0%}")
                    c2.metric("Specificity", f"{ev.get('specificity', 0):.0%}")
                    c3.metric("Safety", f"{ev.get('safety', 0):.0%}")
                    if ev.get("critique"):
                        st.caption(f"Note: {ev['critique']}")
