# EI Assistant — CLAUDE.md

Emotional Intelligence AI Agent. Analyzes text and voice input for emotional content, delivers personalized coaching, tracks patterns over time, and adapts to each user. Built with Claude (Anthropic SDK) + LangGraph.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Claude claude-sonnet-4-6 (Anthropic SDK) |
| Orchestration | LangGraph state graphs |
| Safety Screening | Google Perspective API |
| Persistence | Firebase Firestore |
| Validation | Pydantic v2 |
| Web UI | Streamlit |
| Transcription | SpeechRecognition (Google free API) |
| Voice Prosody | Hume AI (optional, requires HUME_API_KEY) |
| Runtime | Python 3.11+ |

## Quick Start

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in API keys

# Web UI (recommended)
streamlit run app.py

# CLI
python -m backend.cli         # interactive session
python -m backend.cli --patterns              # show my emotional patterns
python -m backend.cli --journal               # guided journaling mode
python -m backend.cli --profile               # show stored profile
```

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | Claude API (all LLM calls) |
| `GOOGLE_PERSPECTIVE_API_KEY` | Yes | Toxicity scoring |
| `FIREBASE_PROJECT_ID` | Yes | Session persistence |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes | Path to Firebase service account JSON |
| `HUME_API_KEY` | No | Voice emotion analysis (Phase 2) |

## Architecture

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                   ei_graph (LangGraph)                  │
│                                                         │
│  load_profile → load_memory → analyze → safety         │
│                                           │             │
│                              [critical]──▶persist─▶END │
│                              [normal]                   │
│                                    │                    │
│                                   coach                 │
│                                (with profile           │
│                                 + memory context)      │
│                                    │                    │
│                              evaluate → refine         │
│                                              │          │
│                                           journal       │
│                                              │          │
│                                          persist─▶END  │
└─────────────────────────────────────────────────────────┘

┌──────────────────────────────────────┐
│        pattern_graph (LangGraph)     │  ← triggered via CLI or API
│  load_history → analyze_patterns     │
│  → generate_insight → persist        │
└──────────────────────────────────────┘
```

### Graph Node Responsibilities

| Node | Skill(s) Called | Purpose |
|------|----------------|---------|
| `load_profile` | `personalization.get_or_create_profile` | Load user prefs/triggers/name |
| `load_memory` | `memory.build_memory_context` | Summarize last 5 sessions |
| `analyze` | `text_emotion`, `perspective.toxicity_score` | Emotion + toxicity |
| `safety` | `safety.check_safety` | Crisis detection; short-circuits if critical |
| `coach` | `coach.coach_user` | Personalized coaching with full context |
| `evaluate` | `evaluator.evaluate_coaching` | Quality gate (empathy/specificity/safety) |
| `refine` | `coach.coach_user` | Auto-improve if scores below threshold |
| `journal` | `journal.generate_journal_prompt` | Reflective question based on emotion |
| `persist` | `firebase.log_session_entry` | Save session, update user profile |

## Project Layout

```
app.py                        # Streamlit web UI entry point
backend/
├── agents/
│   ├── ei_graph.py          # Main EI workflow (9 nodes)
│   └── pattern_graph.py     # Pattern analysis graph
├── skills/
│   ├── text_emotion.py      # Emotion extraction (valence, arousal, labels)
│   ├── coach.py             # Personalized coaching response
│   ├── evaluator.py         # Coaching quality scorer
│   ├── safety.py            # Crisis / safety classifier
│   ├── memory.py            # Short-term + long-term memory context
│   ├── pattern.py           # Cross-session emotional pattern recognition
│   ├── journal.py           # Reflective journaling prompt generator
│   ├── personalization.py   # User profile CRUD
│   └── voice_emotion.py     # Audio transcription + voice prosody pipeline
├── services/
│   ├── anthropic_client.py  # Anthropic SDK singleton
│   ├── perspective.py       # Google Perspective API toxicity
│   ├── firebase.py          # Firestore: sessions + user profiles
│   └── hume_voice.py        # Hume Expression Measurement (audio prosody)
├── schemas.py               # Pydantic models
├── config.py                # Env var loading
└── cli.py                   # Interactive CLI entry point
```

## Data Schemas

```python
EmotionMetrics   – valence, arousal, primary_emotions, confidence, rationale
EvalScores       – empathy, specificity, safety, revise, critique
SafetyLabel      – is_critical, category, confidence, reason, crisis_message
UserProfile      – user_id, name, preferred_techniques, known_triggers,
                   emotion_summary, total_sessions, last_active
MemoryEntry      – user_id, session_id, primary_emotions, valence, text_preview, ts
PatternInsight   – user_id, patterns, triggers, trend, recommendation, generated_at
JournalPrompt    – prompt, emotion_context, suggested_duration_minutes
```

## Firebase Collections

```
users/{user_id}/
  profile              ← UserProfile document
  sessions/{session_id}/
    entries/{entry_id} ← per-message logs
  patterns/{pattern_id} ← PatternInsight documents
```

## Adding a New Skill

1. Create `backend/skills/your_skill.py`
2. Implement a function with typed inputs/outputs
3. Use `get_client()` from `backend.services.anthropic_client` for LLM calls
4. Add a Pydantic schema to `backend/schemas.py` if the output is structured
5. Add a node function in `backend/agents/ei_graph.py`
6. Wire the node into the graph with `workflow.add_node` + `workflow.add_edge`

Skill template:
```python
from backend.services.anthropic_client import get_client

SYSTEM = "Your system prompt."

def your_skill(input_text: str) -> str:
    client = get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=SYSTEM,
        messages=[{"role": "user", "content": input_text}]
    )
    return response.content[0].text.strip()
```

## Claude Model Usage

| Task | Model | Temperature |
|------|-------|-------------|
| Emotion analysis | claude-sonnet-4-6 | 0.2 |
| Safety classification | claude-sonnet-4-6 | 0.0 |
| Coaching response | claude-sonnet-4-6 | 0.5 |
| Coaching evaluation | claude-sonnet-4-6 | 0.0 |
| Pattern recognition | claude-sonnet-4-6 | 0.3 |
| Journal prompt | claude-sonnet-4-6 | 0.6 |
| Memory summarization | claude-haiku-4-5-20251001 | 0.1 |

Use `claude-sonnet-4-6` as default. Use `claude-haiku-4-5-20251001` for fast/cheap helper calls (memory summarization, profile updates). Reserve `claude-opus-4-6` for complex reasoning tasks if needed.

## Quality Gates

The evaluator checks every coaching response before delivery:

| Criterion | Threshold | Action if below |
|-----------|-----------|-----------------|
| Empathy | ≥ 0.75 | Trigger refinement pass |
| Specificity | ≥ 0.70 | Trigger refinement pass |
| Safety | ≥ 0.95 | Trigger refinement pass |

A single refinement pass is attempted. The refined response is used regardless of re-evaluation.

## Safety Protocol

Crisis detection runs before coaching. If `is_critical=True`:
- Coaching generation is skipped entirely
- A pre-written crisis message with hotline resources is shown
- Session is still persisted for continuity

Critical categories: self-harm/suicide, harm to others, acute medical emergency.

## Voice Analysis Pipeline

```
Audio file (WAV/MP3/M4A)
    │
    ├── SpeechRecognition  →  transcription text
    │                              │
    │                        ei_graph (full coaching pipeline)
    │
    └── Hume Prosody API   →  top-5 voice-level emotion scores
                                    (displayed alongside coaching in UI)
```

- Transcription uses Google's free Speech Recognition API (no key needed)
- Non-WAV files are auto-converted via `pydub` (requires ffmpeg installed)
- Hume prosody is **additive** — coaching always runs from transcribed text; Hume scores are extra signal shown in the UI
- If `HUME_API_KEY` is not set, voice still works (transcription only)

## Streamlit Web UI (`app.py`)

- Two input tabs: **Text** and **Voice** (file upload)
- Sidebar: user name, pattern analysis button, new session
- Each response shows: coaching, emotion metrics, voice prosody (if Hume), journal prompt, coaching quality scores
- Run: `streamlit run app.py`

## Roadmap

- **Phase 1** (done): Text EI coaching, safety guardrails, Firebase logging, quality evaluation
- **Phase 2** (done): Voice emotion analysis (transcription + Hume prosody), personalization, memory, pattern analysis, Streamlit web UI
- **Phase 3**: Mobile app, team EI features, analytics dashboard, real-time voice streaming
