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
            "avoid repeating old ideas, and add at least one useful advancement when possible. "
            "Use Persian. Be concise, concrete, and finish your response completely."
        )},
        {"role": "user", "content": (
            f"Question:\n{state.question}\n\nCurrent mission:\n{mission}\n\n"
            f"Durable debate state:\n{compact_state(state)}\n\n"
            f"Opponent's latest argument:\n{opponent_argument or '(no opponent argument yet)'}\n\n"
            "Produce one complete debate contribution."
        )},
    ]


def moderator_mission_prompt(state: DebateState, user_note: str = "") -> list[dict[str, str]]:
    recent = state.arguments[-2:]
    recent_text = "\n\n".join(f"{a.agent}: {a.text}" for a in recent) or "(no previous round arguments)"
    note_text = user_note.strip() or "(no user note)"
    return [
        {"role": "system", "content": (
            "You are the Moderator and protocol controller. You are not a contestant. "
            "Choose the single most valuable question or angle for this round based on durable state and the latest exchange. "
            "Force progress rather than repetition. A user note is a direct instruction/observation from the human operator; "
            "consider it explicitly when deciding the mission. Return only a short mission in Persian."
        )},
        {"role": "user", "content": (
            f"Question:\n{state.question}\n\nCurrent round: {state.round_number}\n\n"
            f"Durable state:\n{compact_state(state)}\n\nLatest exchange:\n{recent_text}\n\n"
            f"USER NOTE:\n{note_text}"
        )},
    ]


def moderator_round_update_prompt(state: DebateState, mission: str, agent1: str, agent2: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": (
            "You are the Moderator. Evaluate this round impartially. Identify only what actually changed. "
            "Use exactly these markers, one item per line under each marker:\n"
            "[CONSENSUS]\n[DISAGREEMENTS]\n[NEW]\n[RISKS]\n[RESOLVED]\n[OPEN]\n[NEXT]\n"
            "If a section has no new item, write '- none'. Do not invent facts."
        )},
        {"role": "user", "content": (
            f"Question:\n{state.question}\n\nMission:\n{mission}\n\nAgent 1:\n{agent1}\n\nAgent 2:\n{agent2}\n\n"
            f"Existing durable state:\n{compact_state(state)}"
        )},
    ]


def moderator_summary_prompt(state: DebateState) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": (
            "You are the final Moderator for a completed debate segment. Produce a decision-useful master summary in Persian. "
            "Distinguish consensus from unresolved disagreement. Preserve concrete proposals, risks, trade-offs, resolved issues, "
            "and open questions. Do not invent facts."
        )},
        {"role": "user", "content": (
            f"Question:\n{state.question}\n\nDurable state accumulated during this segment:\n{compact_state(state)}\n\n"
            "Write a compact master summary with these headings:\n"
            "نتیجه و موضع غالب\nتوافق‌ها\nاختلاف‌های حل‌نشده\nپیشنهادهای کلیدی\nریسک‌ها و بده‌بستان‌ها\nموارد حل‌شده\nپرسش‌های باز\nگام بعدی"
        )},
    ]
