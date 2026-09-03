from config import AGENT_1, AGENT_2, DEBATE, MODERATOR
from debate.engine import DebateEngine
from debate.llm_client import LLMClient
from debate.models import DebateState
from debate.moderator import Moderator


def main() -> None:
    question = input("Debate question: ").strip()
    if not question:
        raise SystemExit("A debate question is required.")

    engine = DebateEngine(
        LLMClient(AGENT_1),
        LLMClient(AGENT_2),
        Moderator(LLMClient(MODERATOR), DEBATE.max_tokens),
        DEBATE.rounds_per_segment,
        DEBATE.max_tokens,
    )
    state = DebateState(question=question)

    while True:
        print(f"\n=== Segment {state.segment_number}: {DEBATE.rounds_per_segment} rounds ===")
        summary = engine.run_segment(state)
        print("\n=== Moderator summary ===\n")
        print(summary)
        state.durable_summary = summary

        choice = input("\nContinue for another segment? [y/N]: ").strip().lower()
        if choice != "y":
            break
        state.compact(summary)


if __name__ == "__main__":
    main()
