"""
Main EI agent graph — 9-node LangGraph state machine.

Flow:
  START
    → load_profile   (personalisation)
    → load_memory    (emotional history context)
    → analyze        (emotion extraction + toxicity)
    → safety         (crisis detection)
        ├─ [critical] → persist → END
        └─ [normal]  → coach
                          → evaluate
                          → refine
                          → journal
                          → persist → END
"""
import uuid
from typing import Optional
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from backend.skills.text_emotion import analyze_text_emotion
from backend.skills.coach import coach_user
from backend.skills.evaluator import evaluate_coaching
from backend.skills.safety import check_safety
from backend.skills.memory import build_memory_context
from backend.skills.journal import generate_journal_prompt
from backend.skills.personalization import get_or_create_profile, update_after_session
from backend.services.perspective import toxicity_score
from backend.services.firebase import log_session_entry, get_recent_entries


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class EIState(TypedDict, total=False):
    # ── inputs ──────────────────────────────────────────────────────────────
    user_id: str
    user_name: str
    user_text: str
    session_id: str

    # ── loaded context ───────────────────────────────────────────────────────
    user_profile: dict
    memory_context: str

    # ── analysis ─────────────────────────────────────────────────────────────
    emotion: dict
    toxicity: Optional[float]
    safety: dict
    is_critical: bool

    # ── coaching pipeline ────────────────────────────────────────────────────
    coaching: str
    eval: dict
    journal_prompt: Optional[dict]   # JournalPrompt.model_dump()


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def node_load_profile(state: EIState) -> EIState:
    profile = get_or_create_profile(
        user_id=state.get("user_id", "anonymous"),
        name=state.get("user_name", ""),
    )
    return {"user_profile": profile.model_dump()}


def node_load_memory(state: EIState) -> EIState:
    user_id = state.get("user_id", "anonymous")
    recent = get_recent_entries(user_id, limit=5)
    ctx = build_memory_context(user_id, recent)
    return {"memory_context": ctx}


def node_analyze(state: EIState) -> EIState:
    text = state["user_text"]
    emotion = analyze_text_emotion(text)
    tox = toxicity_score(text)
    # Stamp user_id into emotion dict for downstream Firebase queries
    return {"emotion": emotion, "toxicity": tox}


def node_safety(state: EIState) -> EIState:
    label = check_safety(state["user_text"])
    out: EIState = {"safety": label.model_dump(), "is_critical": label.is_critical}
    if label.is_critical and label.crisis_message:
        out["coaching"] = label.crisis_message
    return out


def node_coach(state: EIState) -> EIState:
    coaching = coach_user(
        user_text=state["user_text"],
        emotion_json=state["emotion"],
        toxicity=state.get("toxicity"),
        user_profile=state.get("user_profile"),
        memory_context=state.get("memory_context"),
    )
    return {"coaching": coaching}


def node_evaluate(state: EIState) -> EIState:
    ev = evaluate_coaching(
        user_text=state["user_text"],
        metrics={"emotion": state["emotion"], "toxicity": state.get("toxicity")},
        coaching=state["coaching"],
    )
    return {"eval": ev}


def node_refine(state: EIState) -> EIState:
    if state.get("eval", {}).get("revise"):
        refined = coach_user(
            user_text=state["user_text"],
            emotion_json=state["emotion"],
            toxicity=state.get("toxicity"),
            user_profile=state.get("user_profile"),
            memory_context=state.get("memory_context"),
        )
        return {"coaching": refined}
    return {}


def node_journal(state: EIState) -> EIState:
    jp = generate_journal_prompt(
        user_text=state["user_text"],
        emotion_json=state["emotion"],
        memory_context=state.get("memory_context"),
    )
    return {"journal_prompt": jp.model_dump()}


def node_persist(state: EIState) -> EIState:
    user_id = state.get("user_id", "anonymous")
    session_id = state.get("session_id", str(uuid.uuid4()))
    entry = {
        "user_id": user_id,
        "user_text": state["user_text"],
        "emotion": state.get("emotion"),
        "toxicity": state.get("toxicity"),
        "safety": state.get("safety"),
        "coaching": state.get("coaching"),
        "eval": state.get("eval"),
        "journal_prompt": state.get("journal_prompt"),
    }
    log_session_entry(user_id, session_id, entry)

    # Update user profile stats (non-blocking; ignore errors)
    try:
        from backend.schemas import UserProfile
        profile_data = state.get("user_profile") or {}
        if profile_data:
            profile = UserProfile(**profile_data)
            update_after_session(profile, state.get("emotion", {}), state.get("coaching", ""))
    except Exception:
        pass

    return {}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def _route_after_safety(state: EIState) -> str:
    return "critical" if state.get("is_critical") else "normal"


workflow = StateGraph(EIState)

workflow.add_node("load_profile", node_load_profile)
workflow.add_node("load_memory", node_load_memory)
workflow.add_node("analyze", node_analyze)
workflow.add_node("safety", node_safety)
workflow.add_node("coach", node_coach)
workflow.add_node("evaluate", node_evaluate)
workflow.add_node("refine", node_refine)
workflow.add_node("journal", node_journal)
workflow.add_node("persist", node_persist)

workflow.add_edge(START, "load_profile")
workflow.add_edge("load_profile", "load_memory")
workflow.add_edge("load_memory", "analyze")
workflow.add_edge("analyze", "safety")

workflow.add_conditional_edges(
    "safety",
    _route_after_safety,
    {"critical": "persist", "normal": "coach"},
)

workflow.add_edge("coach", "evaluate")
workflow.add_edge("evaluate", "refine")
workflow.add_edge("refine", "journal")
workflow.add_edge("journal", "persist")
workflow.add_edge("persist", END)

ei_graph = workflow.compile()
