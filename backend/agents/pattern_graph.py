"""
Pattern analysis graph — surfaces cross-session emotional patterns for a user.

Triggered explicitly (e.g. `python -m backend.cli --patterns`) rather than
on every session, since it requires enough history to be meaningful.

Flow:
  START → load_history → analyze_patterns → persist_insight → END
"""
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from backend.skills.pattern import analyze_patterns
from backend.services.firebase import get_history_entries, save_pattern_insight


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class PatternState(TypedDict, total=False):
    user_id: str
    history_entries: list
    insight: dict          # PatternInsight.model_dump()


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def node_load_history(state: PatternState) -> PatternState:
    user_id = state.get("user_id", "anonymous")
    entries = get_history_entries(user_id, limit=30)
    return {"history_entries": entries}


def node_analyze_patterns(state: PatternState) -> PatternState:
    user_id = state.get("user_id", "anonymous")
    insight = analyze_patterns(user_id, state.get("history_entries", []))
    return {"insight": insight.model_dump()}


def node_persist_insight(state: PatternState) -> PatternState:
    from backend.schemas import PatternInsight
    raw = state.get("insight", {})
    if raw:
        save_pattern_insight(PatternInsight(**raw))
    return {}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

workflow = StateGraph(PatternState)

workflow.add_node("load_history", node_load_history)
workflow.add_node("analyze_patterns", node_analyze_patterns)
workflow.add_node("persist_insight", node_persist_insight)

workflow.add_edge(START, "load_history")
workflow.add_edge("load_history", "analyze_patterns")
workflow.add_edge("analyze_patterns", "persist_insight")
workflow.add_edge("persist_insight", END)

pattern_graph = workflow.compile()
