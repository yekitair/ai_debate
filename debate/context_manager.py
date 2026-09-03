from .models import DebateState


def transcript(state: DebateState) -> str:
    return "\n\n".join(
        f"Round {arg.round_number} — {arg.agent}:\n{arg.text}"
        for arg in state.arguments
    )


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
        if values:
            sections.append(title + ":\n- " + "\n- ".join(values))
    return "\n\n".join(sections)


def continuation_package(state: DebateState) -> dict[str, str | int]:
    return {
        "question": state.question,
        "segment": state.segment_number,
        "previous_summary": state.durable_summary,
        "state": compact_state(state),
    }
