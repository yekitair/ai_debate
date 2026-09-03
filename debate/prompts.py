def agent_prompt(role: str, question: str, durable_summary: str, opponent_argument: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                f"You are Debate Agent {role}. Defend your assigned position rigorously. "
                "Use explicit reasoning, challenge unsupported claims, and avoid personal attacks."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Debate question: {question}\n\n"
                f"Durable state from earlier segments:\n{durable_summary or '(none)'}\n\n"
                f"Opponent's latest argument:\n{opponent_argument or '(opening argument)'}\n\n"
                "Respond with your strongest concise argument."
            ),
        },
    ]


def moderator_prompt(question: str, transcript: str, durable_summary: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are the debate moderator. Do not act as a contestant. "
                "Evaluate claims impartially, identify unresolved issues and contradictions, "
                "and produce a durable continuation state."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"Previous durable state:\n{durable_summary or '(none)'}\n\n"
                f"Current 10-round segment:\n{transcript}\n\n"
                "Return a compact summary containing: strongest claims from each side, "
                "important evidence/assumptions, unresolved issues, concessions, and "
                "what the next segment should investigate."
            ),
        },
    ]
