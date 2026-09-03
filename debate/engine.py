from .llm_client import LLMClient, LLMError
from .models import DebateState
from .moderator import Moderator
from .prompts import agent_prompt


class DebateEngine:
    def __init__(self, agent1: LLMClient, agent2: LLMClient, moderator: Moderator, rounds_per_segment: int, agent_max_tokens: int):
        self.agents = [("Agent 1", agent1), ("Agent 2", agent2)]
        self.moderator = moderator
        self.rounds_per_segment = rounds_per_segment
        self.agent_max_tokens = agent_max_tokens

    def health_check(self) -> dict[str, dict[str, object]]:
        return {name: client.health_check() for name, client in [
            ("Moderator", self.moderator.client),
            ("Agent 1", self.agents[0][1]),
            ("Agent 2", self.agents[1][1]),
        ]}

    def run_segment(self, state: DebateState) -> dict[str, object]:
        rounds = []
        for round_number in range(1, self.rounds_per_segment + 1):
            state.round_number = round_number
            mission_result = self.moderator.mission(state)
            mission = str(mission_result["text"])
            previous = ""
            round_data = {"round": round_number, "mission": mission, "agents": []}

            for name, client in self.agents:
                result = client.complete(
                    agent_prompt(name, state, mission, previous),
                    self.agent_max_tokens,
                )
                reply = str(result["text"]).strip()
                if not reply:
                    raise LLMError(f"{name} returned an empty response in round {round_number}")
                state.add_argument(name, reply)
                previous = reply
                round_data["agents"].append({"name": name, **result, "text": reply})

            update = self.moderator.update_state(
                state, mission, round_data["agents"][0]["text"], round_data["agents"][1]["text"]
            )
            round_data["moderator_update"] = update
            rounds.append(round_data)

        summary = self.moderator.summarize_segment(state)
        return {"segment": state.segment_number, "rounds": rounds, "summary": summary, "state": state}

    def continue_debate(self, state: DebateState) -> dict[str, object]:
        result = self.run_segment(state)
        summary_text = str(result["summary"]["text"])
        state.compact(summary_text)
        return result
