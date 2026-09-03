from .models import DebateState

MAX_ITEMS_PER_FIELD = 12
MAX_TEXT_CHARS = 18000


def transcript(state: DebateState) -> str:
    return "\n\n".join(
        f"Round {arg.round_number} — {arg.agent}:\n{arg.text}"
        for arg in state.arguments
    )


def _bounded(values: list[str]) -> list[str]:
    return values[-MAX_ITEMS_PER_FIELD:]


def compact_state(state: DebateState) -> str:
    sections = [
        f"Segment: {state.segment_number}",
        f"Question: {state.question}",
        f"Durable summary:\n{state.durable_summary or '(none)'}",
    ]
    for title, values in (
        ("Consensus", state.consensus),
        ("Disagreements", state.disagreements),
        ("Open questions", state.open_questions),
        ("Decisions", state.decisions),
        ("Proposals", state.proposals),
        ("Risks", state.risks),
        ("Discussed topics", state.discussed_topics),
    ):
        items = _bounded(values)
        if items:
            sections.append(title + ":\n- " + "\n- ".join(items))
    return "\n\n".join(sections)[:MAX_TEXT_CHARS]


def continuation_package(state: DebateState) -> dict[str, str | int]:
    # Deliberately excludes DebateState.arguments: the next segment gets only durable state.
    return {
        "question": state.question,
        "segment": state.segment_number,
        "state": compact_state(state),
    }
