from .context_manager import compact_state
from .models import DebateState

AGENT_PROFILES = {
    "Agent 1": {
        "role": "Systems Analyst / Constructive Strategist",
        "position": "Build the strongest technically coherent solution. Prioritize feasibility, systems thinking, evidence, and concrete proposals.",
    },
    "Agent 2": {
        "role": "Adversarial Critic / Red-Team Analyst",
        "position": "Stress-test Agent 1. Challenge assumptions, identify failure modes and trade-offs, and propose better alternatives when criticism reveals a weakness.",
    },
}


def agent_prompt(name: str, state: DebateState, mission: str, opponent_argument: str) -> list[dict[str, str]]:
    profile = AGENT_PROFILES[name]
    return [
        {"role": "system", "content": (
            f"You are {name}, role: {profile['role']}.\n"
            f"Your fixed debate position: {profile['position']}\n"
            "You are a participant, not the moderator. Address the current mission, directly engage the opponent's latest point, "
            "avoid repeating old ideas, and add at least one useful advancement when possible. Be concise but finish completely."
        )},
        {"role": "user", "content": (
            f"Question:\n{state.question}\n\nCurrent mission:\n{mission}\n\n"
            f"Durable debate state:\n{compact_state(state)}\n\n"
            f"Opponent's latest argument:\n{opponent_argument or '(no opponent argument yet)'}\n\n"
            "Produce one complete debate contribution."
        )},
    ]


def moderator_mission_prompt(state: DebateState) -> list[dict[str, str]]:
    recent = state.arguments[-2:]
    recent_text = "\n\n".join(f"{a.agent}: {a.text}" for a in recent) or "(no previous round arguments)"
    return [
        {"role": "system", "content": (
            "You are the Moderator and protocol controller. You are not a contestant. "
            "Choose the single most valuable question or angle for this round based on durable state and the latest exchange. "
            "Force progress rather than repetition. Return only a short mission in Persian."
        )},
        {"role": "user", "content": (
            f"Question:\n{state.question}\n\nCurrent round: {state.round_number}\n\n"
            f"Durable state:\n{compact_state(state)}\n\nLatest exchange:\n{recent_text}"
        )},
    ]


def moderator_round_update_prompt(state: DebateState, mission: str, agent1: str, agent2: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": (
            "You are the Moderator. Evaluate this round impartially. Identify what actually changed: agreements, disagreements, "
            "new proposals, risks, resolved issues, open questions, and the best next direction. Do not merely restate arguments. "
            "Use exactly these markers:\n[CONSENSUS]\n[DISAGREEMENTS]\n[NEW]\n[RISKS]\n[RESOLVED]\n[OPEN]\n[NEXT]"
        )},
        {"role": "user", "content": (
            f"Question:\n{state.question}\n\nMission:\n{mission}\n\nAgent 1:\n{agent1}\n\nAgent 2:\n{agent2}\n\n"
            f"Existing durable state:\n{compact_state(state)}"
        )},
    ]


def moderator_summary_prompt(state: DebateState) -> list[dict[str, str]]:
    transcript = "\n\n".join(f"Round {a.round_number} — {a.agent}:\n{a.text}" for a in state.arguments)
    return [
        {"role": "system", "content": (
            "You are the final Moderator for a completed 10-round segment. Produce a decision-useful master summary in Persian. "
            "Distinguish established consensus from unresolved disagreement. Preserve concrete proposals, risks, trade-offs, "
            "resolved issues, and open questions needed for the next segment. Do not invent facts."
        )},
        {"role": "user", "content": (
            f"Question:\n{state.question}\n\nDurable state before this segment:\n{state.durable_summary or '(none)'}\n\n"
            f"Current segment transcript:\n{transcript}\n\n"
            "Write a compact master summary with: consensus, disagreements, strongest proposals, risks/trade-offs, resolved issues, "
            "open questions, and recommended next investigations."
        )},
    ]
