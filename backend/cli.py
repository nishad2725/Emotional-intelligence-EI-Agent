from backend.agents.ei_graph import ei_graph, EIState

BANNER = """
=========================
 EI Assistant (Phase 1)
=========================
(type 'quit' to exit)
"""

def run_once(user_text: str) -> dict:
    initial: EIState = {"user_text": user_text}
    final = ei_graph.invoke(initial)
    return final

def main():
    print(BANNER)
    while True:
        try:
            txt = input("How are you feeling today? ")
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not txt or txt.strip().lower() in {"quit", "exit"}:
            print("Bye!")
            break

        result = run_once(txt.strip())
        coaching = result.get("coaching", "(no coaching)")
        print("\n— Coach —")
        print(coaching)
        print()

if __name__ == "__main__":
    main()
