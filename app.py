from config import AGENT_1, AGENT_2, DEBATE, MODERATOR
from debate.engine import DebateEngine
from debate.llm_client import LLMClient, LLMError
from debate.models import DebateState
from debate.moderator import Moderator


def build_engine() -> DebateEngine:
    return DebateEngine(
        LLMClient(AGENT_1),
        LLMClient(AGENT_2),
        Moderator(LLMClient(MODERATOR), DEBATE.moderator_max_tokens, DEBATE.summary_max_tokens),
        DEBATE.rounds_per_segment,
        DEBATE.agent_max_tokens,
    )


def print_health(engine: DebateEngine) -> bool:
    print("\n=== Local LLM health check ===")
    health = engine.health_check()
    all_ok = True
    for name, result in health.items():
        ok = bool(result.get("ok"))
        all_ok &= ok
        status = "OK" if ok else "FAILED"
        print(f"{name}: {status} | {result.get('model')} | {result.get('url')}")
        if not ok:
            print(f"  Error: {result.get('error')}")
    return all_ok


def main() -> None:
    question = input("Debate question: ").strip()
    if not question:
        raise SystemExit("A debate question is required.")

    engine = build_engine()
    if not print_health(engine):
        raise SystemExit("One or more local LLM servers are unavailable. Start all three servers first.")

    state = DebateState(question=question)

    while True:
        print(f"\n=== Segment {state.segment_number}: {DEBATE.rounds_per_segment} rounds ===")
        try:
            result = engine.run_segment(state)
        except LLMError as exc:
            raise SystemExit(f"Debate stopped safely: {exc}") from exc

        print(f"\n=== Segment {result['segment']} complete: {len(result['rounds'])} rounds ===")
        print("\n=== Moderator master summary ===\n")
        print(result["summary"]["text"])

        choice = input("\nContinue with a fresh compact context? [y/N]: ").strip().lower()
        if choice != "y":
            print("Debate stopped.")
            break

        state.compact(str(result["summary"]["text"]))
        print(f"\nContext compacted. Starting fresh Segment {state.segment_number}; previous transcript discarded.")


if __name__ == "__main__":
    main()
