# 🧠 EI Assistant — Emotional Intelligence AI Agent

A personalized AI coach that analyzes your emotional state from text or voice, delivers tailored coaching, remembers your history, and surfaces patterns over time. Powered by GPT-4o-mini + LangGraph.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎭 **Emotion Analysis** | Extracts valence, arousal, and emotion labels from text |
| 🎙️ **Voice Input** | Upload audio → auto-transcription → full coaching pipeline |
| 🧑‍🏫 **Personalized Coaching** | Responses adapt to your profile and emotional history |
| 🔁 **Quality Loop** | Every response is scored (empathy/specificity/safety) and auto-refined |
| 📓 **Journal Prompts** | Reflective question tailored to your current emotion |
| 📈 **Pattern Analysis** | Cross-session trends, triggers, and long-term recommendations |
| 🚨 **Crisis Detection** | Immediate escalation with crisis resources if needed |
| 🔒 **Toxicity Screening** | Google Perspective API flags harmful content |
| 💾 **Firebase Persistence** | Every session stored per-user in Firestore |

---

## 🏗️ Architecture

```
User (Text or Voice)
        │
        ▼
┌───────────────────────────────────────────┐
│             ei_graph (LangGraph)          │
│                                           │
│  load_profile → load_memory → analyze    │
│                                  │        │
│                               safety      │
│                           ┌─────┴──────┐  │
│                      [critical]    [normal]│
│                           │            │  │
│                        persist      coach │
│                           │         eval  │
│                          END        refine│
│                                    journal│
│                                    persist│
│                                      END  │
└───────────────────────────────────────────┘

pattern_graph (on demand) → load_history → analyze_patterns → persist
```

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/nishad2725/Emotional-intelligence-EI-Agent.git
cd Emotional-intelligence-EI-Agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-...
GOOGLE_PERSPECTIVE_API_KEY=...
FIREBASE_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json
HUME_API_KEY=          # optional — for voice prosody
```

Place your Firebase service account JSON at `./serviceAccountKey.json`.

### 3. Run the Web UI

```bash
streamlit run app.py
```

Opens at **http://localhost:8501**

### 4. Or use the CLI

```bash
python -m backend.cli                 # interactive coaching session
python -m backend.cli --patterns      # view your emotional patterns
python -m backend.cli --journal       # journaling mode
python -m backend.cli --profile       # view your profile
```

---

## 🗂️ Project Structure

```
app.py                        # Streamlit web UI
backend/
├── agents/
│   ├── ei_graph.py           # Main 9-node LangGraph workflow
│   └── pattern_graph.py      # Pattern analysis sub-graph
├── skills/
│   ├── text_emotion.py       # Emotion extraction
│   ├── coach.py              # Personalized coaching
│   ├── evaluator.py          # Quality scoring + refinement gate
│   ├── safety.py             # Crisis detection
│   ├── memory.py             # Session history summarization
│   ├── pattern.py            # Cross-session pattern recognition
│   ├── journal.py            # Reflective journal prompts
│   ├── personalization.py    # User profile management
│   └── voice_emotion.py      # Audio transcription + Hume prosody
├── services/
│   ├── anthropic_client.py   # OpenAI client singleton
│   ├── perspective.py        # Google Perspective API
│   ├── firebase.py           # Firestore persistence
│   └── hume_voice.py         # Hume prosody API
├── schemas.py                # Pydantic data models
├── config.py                 # Env var loading
└── cli.py                    # CLI entry point
```

---

## 🔌 Integrations

| Service | Purpose | Required |
|---------|---------|----------|
| OpenAI GPT-4o-mini | All LLM reasoning (emotion, coaching, safety, patterns) | Yes |
| Google Perspective API | Toxicity detection | Yes |
| Firebase Firestore | User profiles + session history | Yes |
| SpeechRecognition | Audio → text transcription | Auto (no key needed) |
| Hume AI | Voice-level prosody emotion scores | Optional |

---

## 📊 What You See Per Response

```
User message
    │
    ├── Detected emotions  (e.g. anxiety · overwhelm)
    ├── Mood bar           (valence -1.0 → +1.0)
    ├── Energy level       (arousal 0 → 1)
    │
    ├── Coach response     (personalised 3-line coaching)
    │
    ├── ✦ Journal prompt   (open-ended reflection question)
    ├── 🎙️ Voice prosody   (Hume top-5 emotions, if available)
    └── 📊 Quality scores  (Empathy · Specificity · Safety)
```

---

## 🛡️ Safety

- Crisis content (self-harm, violence, medical emergency) triggers immediate escalation
- Coaching is skipped and a crisis message with hotline resources is shown
- All sessions are still logged for continuity

---

## 🗺️ Roadmap

| Phase | Status | Features |
|-------|--------|---------|
| Phase 1 | ✅ Done | Text coaching, safety guardrails, quality evaluation, Firebase |
| Phase 2 | ✅ Done | Voice input, personalization, memory, pattern analysis, Streamlit UI |
| Phase 3 | 🔜 Planned | Mobile app, real-time voice streaming, team EI, analytics dashboard |

---

## 🤝 Contributing

```bash
git checkout -b feature/your-feature
# make changes
git commit -m "Add your feature"
git push origin feature/your-feature
# open a Pull Request
```

---

**Built with ❤️ for emotional intelligence and mental wellness**
