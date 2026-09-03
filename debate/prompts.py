from .context_manager import compact_state
from .models import DebateState


AGENT_PROFILES = {
    "Agent 1": {
        "role": "Systems Analyst / Constructive Strategist",
        "position": "Build the strongest technically coherent solution to the question. Prioritize feasibility, systems thinking, evidence, and concrete proposals.",
    },
    "Agent 2": {
        "role": "Adversarial Critic / Red-Team Analyst",
        "position": "Stress-test Agent 1. Challenge assumptions, identify failure modes and trade-offs, and propose better alternatives when criticism reveals a weakness.",
    },
}


def agent_prompt(name: str, state: DebateState, mission: str, opponent_argument: str) -> list[dict[str, str]]:
    profile = AGENT_PROFILES[name]
    return [
        {
            "role": "system",
            "content": (
                f"You are {name}, role: {profile['role']}.\n"
                f"Your fixed debate position: {profile['position']}\n"
                "You are one participant, not the moderator. Do not summarize the whole debate. "
                "Address the current mission, directly engage the opponent's latest point, avoid repeating old ideas, "
                "and add at least one useful advancement when possible. Be concise but finish your argument completely."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question:\n{state.question}\n\n"
                f"Current mission:\n{mission}\n\n"
                f"Durable debate state from earlier segments:\n{compact_state(state)}\n\n"
                f"Opponent's latest argument:\n{opponent_argument or '(no opponent argument yet in this round)'}\n\n"
                "Produce one complete debate contribution."
            ),
        },
    ]


def moderator_mission_prompt(state: DebateState) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are the Moderator and protocol controller. You are not a contestant. "
                "Choose the single most valuable question or angle for this round based on the durable state. "
                "Do not write a summary. Return only a short mission in Persian."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question:\n{state.question}\n\n"
                f"Current round: {state.round_number}\n"
                f"Durable state:\n{compact_state(state)}\n\n"
                "Mission must force progress rather than repetition."
            ),
        },
    ]


def moderator_round_update_prompt(
    state: DebateState, mission: str, agent1: str, agent2: str
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are the Moderator. Evaluate this round impartially. "
                "Identify what actually changed in the debate: agreements, disagreements, new proposals, risks, "
                "resolved/open questions, and the best next direction. Do not merely restate the arguments. "
                "Use exactly these markers and keep each section concise:\n"
                "[CONSENSUS]\n[DISAGREEMENTS]\n[NEW]\n[RISKS]\n[RESOLVED]\n[OPEN]\n[NEXT]"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question:\n{state.question}\n\nMission:\n{mission}\n\n"
                f"Agent 1:\n{agent1}\n\nAgent 2:\n{agent2}\n\n"
                f"Existing durable state:\n{compact_state(state)}"
            ),
        },
    ]


def moderator_summary_prompt(state: DebateState) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are the final Moderator for a completed 10-round segment. Produce a decision-useful master summary in Persian. "
                "Distinguish established consensus from unresolved disagreement. Preserve concrete proposals, risks, trade-offs, "
                "and open questions needed for the next segment. Do not invent facts."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question:\n{state.question}\n\n"
                f"Durable state before this segment:\n{state.durable_summary or '(none)'}\n\n"
                f"Current segment transcript:\n"
                + "\n\n".join(f"Round {a.round_number} — {a.agent}:\n{a.text}" for a in state.arguments)
                + "\n\nWrite a compact master summary with: consensus, disagreements, strongest proposals, risks/trade-offs, resolved issues, "
                  "open questions, and recommended next investigations."
            ),
        },
    ]
