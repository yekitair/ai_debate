from __future__ import annotations

import threading
from typing import Callable

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
        return {
            "Moderator": self.moderator.client.health_check(),
            "Agent 1": self.agents[0][1].health_check(),
            "Agent 2": self.agents[1][1].health_check(),
        }

    def run_segment(
        self,
        state: DebateState,
        stop_event: threading.Event | None = None,
        on_event: Callable[..., None] | None = None,
    ) -> dict[str, object]:
        rounds = []
        for round_number in range(1, self.rounds_per_segment + 1):
            self._check_stop(stop_event)
            state.round_number = round_number
            self._emit(on_event, "round_start", segment=state.segment_number, round=round_number)

            mission_result = self.moderator.mission(state)
            mission = str(mission_result["text"]).strip()
            self._emit(
                on_event,
                "moderator_mission",
                round=round_number,
                text=mission,
                finish_reason=mission_result.get("finish_reason"),
            )

            previous = ""
            round_data = {"round": round_number, "mission": mission, "agents": []}
            for name, client in self.agents:
                self._check_stop(stop_event)
                result = client.complete(agent_prompt(name, state, mission, previous), self.agent_max_tokens)
                reply = str(result["text"]).strip()
                if not reply:
                    raise LLMError(f"{name} returned an empty response in round {round_number}")
                state.add_argument(name, reply)
                previous = reply
                agent_data = {"name": name, **result, "text": reply}
                round_data["agents"].append(agent_data)
                self._emit(
                    on_event,
                    "agent_response",
                    round=round_number,
                    agent=name,
                    text=reply,
                    finish_reason=result.get("finish_reason"),
                    truncated=result.get("finish_reason") == "length",
                )

            self._check_stop(stop_event)
            update = self.moderator.update_state(
                state, mission, round_data["agents"][0]["text"], round_data["agents"][1]["text"]
            )
            round_data["moderator_update"] = update
            self._emit(
                on_event,
                "moderator_update",
                round=round_number,
                text=str(update["text"]),
                finish_reason=update.get("finish_reason"),
                state=self._state_snapshot(state),
            )
            rounds.append(round_data)

        self._check_stop(stop_event)
        summary = self.moderator.summarize_segment(state)
        self._emit(
            on_event,
            "moderator_summary",
            segment=state.segment_number,
            text=str(summary["text"]),
            finish_reason=summary.get("finish_reason"),
        )
        return {"segment": state.segment_number, "rounds": rounds, "summary": summary, "state": state}

    @staticmethod
    def _check_stop(stop_event: threading.Event | None) -> None:
        if stop_event is not None and stop_event.is_set():
            raise LLMError("Debate stopped by user.")

    @staticmethod
    def _emit(callback: Callable[..., None] | None, event_type: str, **payload: object) -> None:
        if callback:
            callback(event_type, **payload)

    @staticmethod
    def _state_snapshot(state: DebateState) -> dict[str, object]:
        return {
            "segment": state.segment_number,
            "round": state.round_number,
            "consensus": state.consensus,
            "disagreements": state.disagreements,
            "open_questions": state.open_questions,
            "decisions": state.decisions,
            "proposals": state.proposals,
            "risks": state.risks,
            "discussed_topics": state.discussed_topics,
        }
