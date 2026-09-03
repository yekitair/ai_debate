from .llm_client import LLMClient
from .models import DebateState
from .moderator import Moderator
from .prompts import agent_prompt


class DebateEngine:
    def __init__(self, agent1: LLMClient, agent2: LLMClient, moderator: Moderator, rounds_per_segment: int, max_tokens: int):
        self.agents = [("Agent 1", agent1), ("Agent 2", agent2)]
        self.moderator = moderator
        self.rounds_per_segment = rounds_per_segment
        self.max_tokens = max_tokens

    def run_segment(self, state: DebateState) -> str:
        for round_number in range(1, self.rounds_per_segment + 1):
            state.round_number = round_number
            previous = ""
            for name, client in self.agents:
                reply = client.complete(
                    agent_prompt(name, state.question, state.durable_summary, previous),
                    self.max_tokens,
                )
                state.add_argument(name, reply)
                previous = reply

        return self.moderator.summarize_segment(state)

    def continue_debate(self, state: DebateState) -> None:
        summary = self.run_segment(state)
        state.compact(summary)
