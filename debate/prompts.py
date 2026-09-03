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

SUMMARY_HEADINGS = {
    "fa": "نتیجه و موضع غالب\nتوافق‌ها\nاختلاف‌های حل‌نشده\nپیشنهادهای کلیدی\nریسک‌ها و بده‌بستان‌ها\nموارد حل‌شده\nپرسش‌های باز\nگام بعدی",
    "en": "Dominant conclusion and position\nAgreements\nUnresolved disagreements\nKey proposals\nRisks and trade-offs\nResolved issues\nOpen questions\nNext step",
    "de": "Vorherrschendes Ergebnis und Position\nÜbereinstimmungen\nUngelöste Meinungsverschiedenheiten\nWichtige Vorschläge\nRisiken und Zielkonflikte\nGelöste Punkte\nOffene Fragen\nNächster Schritt",
    "fr": "Conclusion et position dominante\nAccords\nDésaccords non résolus\nPropositions clés\nRisques et compromis\nPoints résolus\nQuestions ouvertes\nProchaine étape",
    "zh": "主要结论与立场\n共识\n未解决的分歧\n关键建议\n风险与权衡\n已解决的问题\n开放问题\n下一步",
}


def _language_rule(state: DebateState) -> str:
    return (
        f"Required human-facing language: {state.language_name} ({state.language}). "
        "Write ALL natural-language output in this language. Do not switch languages unless the user explicitly requests it. "
        "Technical names, product names, code identifiers, and established scientific terms may remain in their conventional form."
    )


def agent_prompt(name: str, state: DebateState, mission: str, opponent_argument: str) -> list[dict[str, str]]:
    profile = AGENT_PROFILES[name]
    return [
        {"role": "system", "content": (
            f"You are {name}, role: {profile['role']}.\n"
            f"Your fixed debate position: {profile['position']}\n"
            "You are a participant, not the moderator. Address the current mission, directly engage the opponent's latest point, "
            "avoid repeating old ideas, and add at least one useful advancement when possible. "
            f"{_language_rule(state)} Be concise, concrete, and finish your response completely."
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
            "Choose ONE precise, answerable question or investigation target for this round. "
            "The mission must be a neutral directive, not an answer, conclusion, proposal, or copied sentence from an agent. "
            "Force progress rather than repetition. Base the mission on the durable state and latest exchange. "
            "A user note is a direct instruction/observation from the human operator; consider it explicitly. "
            f"{_language_rule(state)} Return only the short mission, with no heading or explanation."
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
            "You are the Moderator. Evaluate ONLY the current round and produce a durable state delta. "
            "Do not copy old state items unless this round provides new evidence that materially changes them. "
            "Every non-none item must be supported by Agent 1 or Agent 2 in THIS round. "
            "If an existing disagreement was resolved this round, report it under [RESOLVED] and do not repeat it under [DISAGREEMENTS]. "
            "Use exactly these protocol markers; keep the markers in English but write all content under them in the required language:\n"
            "[CONSENSUS]\n[DISAGREEMENTS]\n[NEW]\n[RISKS]\n[RESOLVED]\n[OPEN]\n[NEXT]\n"
            "For [NEXT], provide only 1–2 concrete investigation targets for the next round. "
            "Do not use [NEXT] for summaries or conclusions. If a section has no genuinely new item, write '- none'. "
            "Do not invent facts. "
            f"{_language_rule(state)}"
        )},
        {"role": "user", "content": (
            f"Question:\n{state.question}\n\nCurrent round mission:\n{mission}\n\n"
            f"Agent 1 current argument:\n{agent1}\n\nAgent 2 current argument:\n{agent2}\n\n"
            f"Existing durable state (reference only; do not blindly copy):\n{compact_state(state)}"
        )},
    ]


def moderator_summary_prompt(state: DebateState) -> list[dict[str, str]]:
    headings = SUMMARY_HEADINGS.get(state.language, SUMMARY_HEADINGS["en"])
    return [
        {"role": "system", "content": (
            "You are the final Moderator for a completed debate segment. Produce a decision-useful master summary. "
            "Distinguish consensus from unresolved disagreement. Preserve concrete proposals, risks, trade-offs, resolved issues, "
            "and open questions. Do not invent facts. Do not claim consensus where the agents actually disagree. "
            f"{_language_rule(state)}"
        )},
        {"role": "user", "content": (
            f"Question:\n{state.question}\n\nDurable state accumulated during this segment:\n{compact_state(state)}\n\n"
            f"Write a compact master summary using these headings in this exact order:\n{headings}"
        )},
    ]
