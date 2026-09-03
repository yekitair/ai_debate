from .models import DebateState


def transcript(state: DebateState) -> str:
    return "\n\n".join(
        f"Round {arg.round_number} — {arg.agent}:\n{arg.text}"
        for arg in state.arguments
    )


def continuation_package(state: DebateState) -> dict[str, str | int]:
    return {
        "question": state.question,
        "segment": state.segment_number,
        "previous_summary": state.durable_summary,
    }
