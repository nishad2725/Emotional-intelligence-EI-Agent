"""
EI Assistant — Streamlit Web UI
Run:  streamlit run app.py
"""
import uuid
import tempfile
import os
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EI Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide Streamlit default header/footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Coach response card */
    .coach-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-left: 4px solid #e94560;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 12px 0;
        color: #eaeaea;
        font-size: 1.05rem;
        line-height: 1.7;
    }
    .crisis-card {
        background: #2d0000;
        border-left: 4px solid #ff4444;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 12px 0;
        color: #ffcccc;
        font-size: 1.05rem;
        line-height: 1.7;
    }
    .emotion-badge {
        display: inline-block;
        background: #e94560;
        color: white;
        border-radius: 20px;
        padding: 3px 12px;
        margin: 2px 4px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .section-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #888;
        margin-bottom: 4px;
    }
    .journal-box {
        background: #f0f7ff;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid #4a90d9;
        font-size: 1rem;
        color: #1a3a5c;
        font-style: italic;
    }
    .stForm button[kind="primaryFormSubmit"] {
        background-color: #e94560 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _valence_emoji(v: float) -> str:
    if v < -0.6:  return "😔"
    if v < -0.2:  return "😟"
    if v < 0.2:   return "😐"
    if v < 0.6:   return "🙂"
    return "😄"

def _valence_color(v: float) -> str:
    if v < -0.4: return "red"
    if v < 0.2:  return "orange"
    return "green"

def _trend_emoji(trend: str) -> str:
    return {"improving": "📈", "declining": "📉", "stable": "➡️"}.get(trend, "➡️")

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
    st.session_state.history: list[tuple[str, dict]] = []
if "insight" not in st.session_state:
    st.session_state.insight = None


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🧠 EI Assistant")
    st.caption("Emotional Intelligence Coaching · GPT-4o-mini")
    st.divider()

    name_input = st.text_input(
        "Your name",
        value=st.session_state.user_name,
        placeholder="Optional — helps personalise coaching",
    )
    if name_input != st.session_state.user_name:
        st.session_state.user_name = name_input
        st.session_state.user_id = name_input.lower().replace(" ", "_") if name_input else "anonymous"
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.insight = None

    st.divider()
    st.markdown("### Your Patterns")

    if st.button("🔍 Analyse My Patterns", use_container_width=True):
        with st.spinner("Analysing your emotional history…"):
            try:
                result = _run_patterns(st.session_state.user_id)
                st.session_state.insight = result.get("insight")
            except Exception as e:
                st.error(f"Could not load patterns: {e}")

    if st.session_state.insight:
        ins = st.session_state.insight
        trend = ins.get("trend", "stable")
        st.markdown(f"**Overall trend:** {_trend_emoji(trend)} {trend.capitalize()}")

        patterns = ins.get("patterns", [])
        if patterns:
            st.markdown("**Recurring patterns:**")
            for p in patterns:
                st.markdown(f"- {p}")

        triggers = ins.get("triggers", [])
        if triggers:
            st.markdown("**Common triggers:**")
            for t in triggers:
                st.markdown(f"- {t}")

        rec = ins.get("recommendation", "")
        if rec:
            st.info(f"💡 {rec}")
    else:
        st.caption("Share a few check-ins first, then tap the button above.")

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔄 New Session", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.history = []
            st.rerun()
    with col_b:
        session_count = len(st.session_state.history)
        st.metric("Messages", session_count)


# ── Main area ─────────────────────────────────────────────────────────────────

# Header
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    greeting = f"Hey {st.session_state.user_name}! " if st.session_state.user_name else ""
    st.markdown(f"## {greeting}How are you feeling?")
    st.caption("Type a message or upload a voice recording — your EI coach responds personally.")

st.divider()

# Input tabs
tab_text, tab_voice = st.tabs(["💬 Text", "🎙️ Voice"])

with tab_text:
    with st.form("text_form", clear_on_submit=True):
        user_text = st.text_area(
            "What's on your mind?",
            placeholder="e.g. I've been feeling really anxious about a presentation at work…",
            height=110,
            label_visibility="collapsed",
        )
        col_btn1, col_btn2 = st.columns([4, 1])
        with col_btn1:
            submitted = st.form_submit_button("✉️ Send to Coach", use_container_width=True, type="primary")
        with col_btn2:
            st.form_submit_button("Clear", use_container_width=True)

    if submitted and user_text.strip():
        with st.spinner("Your coach is thinking…"):
            try:
                result = _run_text(
                    user_text.strip(),
                    st.session_state.user_id,
                    st.session_state.user_name,
                    st.session_state.session_id,
                )
                st.session_state.history.append((user_text.strip(), result))
                st.rerun()
            except Exception as e:
                st.error(f"Something went wrong: {e}")

with tab_voice:
    st.markdown(
        "Upload a **WAV, MP3, or M4A** recording. It will be transcribed then "
        "analysed exactly like text. Voice prosody scores appear if Hume AI is configured."
    )
    audio_file = st.file_uploader(
        "Audio file", type=["wav", "mp3", "m4a", "ogg"], label_visibility="collapsed"
    )
    if audio_file:
        st.audio(audio_file)
        if st.button("🎙️ Analyse Voice", use_container_width=True, type="primary"):
            ext = audio_file.name.rsplit(".", 1)[-1].lower()
            with st.spinner("Transcribing and analysing…"):
                try:
                    result = _run_voice(
                        audio_file.getvalue(),
                        ext,
                        st.session_state.user_id,
                        st.session_state.user_name,
                        st.session_state.session_id,
                    )
                    if result.get("_voice_only"):
                        st.warning(f"⚠️ Transcription failed: {result.get('_transcription_error')}")
                        voice_emo = result.get("_voice_emotions", {})
                        if voice_emo.get("available") and voice_emo.get("top_emotions"):
                            st.subheader("Voice Prosody (Hume)")
                            for e in voice_emo["top_emotions"]:
                                st.progress(e["score"], text=f"{e['name']}: {e['score']:.0%}")
                    else:
                        transcription = result.get("_transcription", "")
                        if transcription:
                            st.info(f"🗣️ Transcription: *\"{transcription}\"*")
                        st.session_state.history.append((transcription or "[voice]", result))
                        st.rerun()
                except Exception as e:
                    st.error(f"Voice analysis error: {e}")


# ── Conversation feed ─────────────────────────────────────────────────────────

if st.session_state.history:
    st.divider()
    st.markdown("### Session")

    for user_text, result in reversed(st.session_state.history):
        # User message
        with st.chat_message("user"):
            st.write(user_text)

        # Coach response
        with st.chat_message("assistant", avatar="🧠"):
            is_critical = result.get("is_critical", False)
            coaching_text = result.get("coaching", "")

            if is_critical:
                st.markdown(f'<div class="crisis-card">🚨 {coaching_text}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="coach-card">{coaching_text}</div>', unsafe_allow_html=True)

            # ── Emotion row ──────────────────────────────────────────────────
            emotion = result.get("emotion", {})
            if emotion:
                emotions = emotion.get("primary_emotions", [])
                valence = emotion.get("valence", 0.0)
                arousal = emotion.get("arousal", 0.0)
                tox = result.get("toxicity")

                badges = "".join(
                    f'<span class="emotion-badge">{e}</span>' for e in emotions
                )
                mood_emoji = _valence_emoji(valence)
                mood_color = _valence_color(valence)

                st.markdown(
                    f'<p class="section-label">Detected emotions</p>'
                    f'{badges}&nbsp;&nbsp;'
                    f'<span style="color:{mood_color};font-weight:600">'
                    f'{mood_emoji} Mood {valence:+.2f}</span>'
                    f'&nbsp;&nbsp;⚡ Energy {arousal:.0%}',
                    unsafe_allow_html=True,
                )

                if tox is not None and tox > 0.3:
                    st.caption(f"⚠️ Toxicity flag: {tox:.0%}")

            # ── Details expanders ────────────────────────────────────────────
            expander_cols = st.columns(3)

            # Journal prompt
            jp = result.get("journal_prompt")
            if jp:
                with expander_cols[0]:
                    with st.expander("✦ Journal prompt"):
                        st.markdown(
                            f'<div class="journal-box">{jp.get("prompt", "")}</div>',
                            unsafe_allow_html=True,
                        )
                        st.caption(f"⏱ Suggested: {jp.get('suggested_duration_minutes', 5)} min")

            # Voice prosody
            voice_emo = result.get("_voice_emotions", {})
            if voice_emo and voice_emo.get("available") and voice_emo.get("top_emotions"):
                with expander_cols[1]:
                    with st.expander("🎙️ Voice prosody"):
                        for e in voice_emo["top_emotions"]:
                            st.progress(e["score"], text=f"{e['name']}: {e['score']:.0%}")

            # Coaching quality
            ev = result.get("eval", {})
            if ev:
                with expander_cols[2]:
                    with st.expander("📊 Quality scores"):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Empathy", f"{ev.get('empathy', 0):.0%}")
                        c2.metric("Specificity", f"{ev.get('specificity', 0):.0%}")
                        c3.metric("Safety", f"{ev.get('safety', 0):.0%}")
                        if ev.get("critique"):
                            st.caption(ev["critique"])

else:
    # Empty state illustration
    st.markdown("""
    <div style="text-align:center; padding: 60px 0; color: #888;">
        <p style="font-size:3rem">🧠</p>
        <p style="font-size:1.2rem; font-weight:600">Your EI Coach is ready</p>
        <p>Share what's on your mind — text or voice — and receive personalised coaching.</p>
    </div>
    """, unsafe_allow_html=True)
