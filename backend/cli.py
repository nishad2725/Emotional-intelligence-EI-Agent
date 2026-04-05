"""
EI Assistant CLI entry point.

Usage:
  python -m backend.cli                  # interactive EI coaching session
  python -m backend.cli --patterns       # show your emotional pattern analysis
  python -m backend.cli --journal        # guided journaling mode (no coaching)
  python -m backend.cli --profile        # show your stored profile
"""
import argparse
import uuid
import sys

from backend.agents.ei_graph import ei_graph, EIState

BANNER = """
╔══════════════════════════════════════╗
║       EI Assistant  ✦  Powered by   ║
║           Claude claude-sonnet-4-6            ║
╚══════════════════════════════════════╝
"""

HELP_TEXT = """
Commands during a session:
  journal   — get a reflective journaling prompt for your last message
  patterns  — analyse your emotional patterns across all sessions
  profile   — show your stored profile
  quit      — exit
"""


def _get_user_id() -> tuple[str, str]:
    """Prompt for a name and derive a stable user_id from it."""
    try:
        name = input("Your name (or press Enter for anonymous): ").strip()
    except (EOFError, KeyboardInterrupt):
        name = ""
    if not name:
        return "anonymous", "Anonymous"
    # Simple deterministic ID from name (not a hash — just for dev convenience)
    user_id = name.lower().replace(" ", "_")
    return user_id, name


def _print_result(result: dict, show_journal: bool = False) -> None:
    coaching = result.get("coaching", "(no response)")
    emotion = result.get("emotion", {})
    emotions = emotion.get("primary_emotions", [])
    valence = emotion.get("valence", 0.0)

    mood_bar = _valence_bar(valence)
    print(f"\n  Emotions detected: {', '.join(emotions) or 'unknown'}  {mood_bar}")
    print("\n┌─ Coach ─────────────────────────────────────────")
    for line in coaching.split("\n"):
        print(f"│  {line}")
    print("└─────────────────────────────────────────────────")

    if show_journal:
        jp = result.get("journal_prompt")
        if jp:
            print(f"\n  ✦ Journal prompt ({jp.get('suggested_duration_minutes', 5)} min):")
            print(f"    {jp.get('prompt', '')}")

    print()


def _valence_bar(valence: float) -> str:
    """ASCII mood indicator from -1 (very negative) to +1 (very positive)."""
    idx = int((valence + 1) / 2 * 4)   # 0..4
    bars = ["▁▁▁▁▁", "▂▂▂▂▂", "▃▃▃▃▃", "▄▄▄▄▄", "█████"]
    labels = ["very low", "low", "neutral", "positive", "very positive"]
    idx = max(0, min(4, idx))
    return f"{bars[idx]} ({labels[idx]})"


def _show_patterns(user_id: str) -> None:
    from backend.agents.pattern_graph import pattern_graph, PatternState
    print("\n  Analysing your emotional patterns across all sessions…\n")
    result = pattern_graph.invoke(PatternState(user_id=user_id))
    insight = result.get("insight", {})
    if not insight:
        print("  Not enough data yet. Keep checking in!\n")
        return
    print(f"  Patterns:       {', '.join(insight.get('patterns', [])) or 'none detected'}")
    print(f"  Triggers:       {', '.join(insight.get('triggers', [])) or 'none detected'}")
    print(f"  Overall trend:  {insight.get('trend', 'unknown')}")
    print(f"\n  Long-term tip:  {insight.get('recommendation', '')}\n")


def _show_profile(user_id: str, name: str) -> None:
    from backend.skills.personalization import get_or_create_profile
    profile = get_or_create_profile(user_id, name)
    print(f"\n  Name:            {profile.name or 'Anonymous'}")
    print(f"  Sessions:        {profile.total_sessions}")
    print(f"  Last active:     {profile.last_active or 'never'}")
    print(f"  Common emotions: {', '.join(profile.known_triggers) or 'none yet'}")
    print(f"  Journey:         {profile.emotion_summary or 'building up…'}\n")


def run_session(user_id: str, user_name: str, user_text: str, session_id: str) -> dict:
    initial: EIState = {
        "user_id": user_id,
        "user_name": user_name,
        "user_text": user_text,
        "session_id": session_id,
    }
    return ei_graph.invoke(initial)


def main() -> None:
    parser = argparse.ArgumentParser(description="EI Assistant CLI")
    parser.add_argument("--patterns", action="store_true", help="Show emotional pattern analysis")
    parser.add_argument("--journal", action="store_true", help="Journaling mode")
    parser.add_argument("--profile", action="store_true", help="Show your profile")
    args = parser.parse_args()

    print(BANNER)
    user_id, user_name = _get_user_id()
    session_id = str(uuid.uuid4())

    greeting = f"  Welcome{', ' + user_name if user_name != 'Anonymous' else ''}."
    print(greeting)
    print(HELP_TEXT)

    # One-shot modes
    if args.patterns:
        _show_patterns(user_id)
        return
    if args.profile:
        _show_profile(user_id, user_name)
        return

    # Interactive loop
    prompt = "  [journal mode] How are you feeling? " if args.journal else "  How are you feeling? "
    last_result: dict = {}

    while True:
        try:
            user_input = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Take care!\n")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in {"quit", "exit", "q"}:
            print("\n  Take care!\n")
            break
        if cmd == "patterns":
            _show_patterns(user_id)
            continue
        if cmd == "profile":
            _show_profile(user_id, user_name)
            continue
        if cmd == "journal" and last_result:
            jp = last_result.get("journal_prompt")
            if jp:
                print(f"\n  ✦ Journal prompt ({jp.get('suggested_duration_minutes', 5)} min):")
                print(f"    {jp.get('prompt', '')}\n")
            else:
                print("  No journal prompt yet — share how you're feeling first.\n")
            continue

        print("  …\n")
        try:
            result = run_session(user_id, user_name, user_input, session_id)
            last_result = result
            _print_result(result, show_journal=args.journal)
        except Exception as e:
            print(f"  [error] {e}\n")
            if "--debug" in sys.argv:
                raise


if __name__ == "__main__":
    main()
