from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from backend.skills.text_emotion import analyze_text_emotion
from backend.services.perspective import toxicity_score
from backend.skills.coach import coach_user
from backend.skills.evaluator import evaluate_coaching
from backend.skills.safety import check_safety
from backend.services.firebase import log_session_entry

class EIState(TypedDict, total=False):
    user_text: str
    emotion: dict
    toxicity: Optional[float]
    safety: dict
    coaching: str
    eval: dict
    is_critical: bool

def node_analyze(state: EIState) -> EIState:
    text = state["user_text"]
    emo = analyze_text_emotion(text)
    tox = toxicity_score(text)
    return {"emotion": emo, "toxicity": tox}

def node_safety(state: EIState) -> EIState:
    s = check_safety(state["user_text"]).model_dump()
    out: EIState = {"safety": s, "is_critical": s["is_critical"]}
    # If critical, pre-fill coaching with crisis message to short-circuit
    if s["is_critical"] and s.get("crisis_message"):
        out["coaching"] = s["crisis_message"]
    return out

def node_coach(state: EIState) -> EIState:
    coaching = coach_user(state["user_text"], state["emotion"], state.get("toxicity"))
    return {"coaching": coaching}

def node_evaluate(state: EIState) -> EIState:
    ev = evaluate_coaching(
        state["user_text"],
        {"emotion": state["emotion"], "toxicity": state.get("toxicity")},
        state["coaching"]
    )
    return {"eval": ev}

def node_refine_if_needed(state: EIState) -> EIState:
    ev = state["eval"]
    if ev.get("revise"):
        refined = coach_user(state["user_text"], state["emotion"], state.get("toxicity"))
        return {"coaching": refined}
    return {}

def node_persist(state: EIState) -> EIState:
    log_session_entry({
        "user_text": state["user_text"],
        "emotion": state["emotion"],
        "toxicity": state.get("toxicity"),
        "coaching": state["coaching"],
        "eval": state.get("eval")
    })
    return {}

# Build the graph
workflow = StateGraph(EIState)
workflow.add_node("analyze", node_analyze)
workflow.add_node("safety", node_safety)
workflow.add_node("coach", node_coach)
workflow.add_node("evaluate", node_evaluate)
workflow.add_node("refine", node_refine_if_needed)
workflow.add_node("persist", node_persist)

workflow.add_edge(START, "analyze")
workflow.add_edge("analyze", "safety")

# critical branch: safety → persist (skip coaching)
def route_after_safety(state: EIState):
    return "critical" if state.get("is_critical") else "normal"

workflow.add_conditional_edges(
    "safety",
    route_after_safety,
    {
        "critical": "persist",
        "normal": "coach",
    },
)
workflow.add_edge("coach", "evaluate")
workflow.add_edge("evaluate", "refine")
workflow.add_edge("refine", "persist")
workflow.add_edge("evaluate", "persist")  # if no refinement needed
workflow.add_edge("persist", END)

ei_graph = workflow.compile()
