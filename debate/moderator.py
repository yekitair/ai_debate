from .llm_client import LLMClient, LLMError
from .models import DebateState
from .prompts import moderator_mission_prompt, moderator_round_update_prompt, moderator_summary_prompt

MARKERS = ("[CONSENSUS]", "[DISAGREEMENTS]", "[NEW]", "[RISKS]", "[RESOLVED]", "[OPEN]", "[NEXT]")


class Moderator:
    def __init__(self, client: LLMClient, max_tokens: int, summary_max_tokens: int):
        self.client = client
        self.max_tokens = max_tokens
        self.summary_max_tokens = summary_max_tokens

    def mission(self, state: DebateState, user_note: str = "") -> dict[str, object]:
        result = self.client.complete(moderator_mission_prompt(state, user_note), self.max_tokens)
        text = str(result["text"]).strip()
        if not text:
            raise LLMError("Moderator returned an empty mission")
        return result | {"text": text}

    def update_state(self, state: DebateState, mission: str, agent1: str, agent2: str) -> dict[str, object]:
        result = self.client.complete(moderator_round_update_prompt(state, mission, agent1, agent2), self.max_tokens)
        text = str(result["text"]).strip()
        if not text:
            raise LLMError("Moderator returned an empty state update")
        self._merge_markers(state, text)
        return result | {"text": text}

    def summarize_segment(self, state: DebateState) -> dict[str, object]:
        result = self.client.complete(moderator_summary_prompt(state), self.summary_max_tokens)
        text = str(result["text"]).strip()
        if not text:
            raise LLMError("Moderator returned an empty segment summary")
        return result | {"text": text}

    @staticmethod
    def _section(text: str, marker: str) -> list[str]:
        start = text.find(marker)
        if start < 0:
            return []
        start += len(marker)
        end = len(text)
        for other in MARKERS:
            if other != marker:
                pos = text.find(other, start)
                if pos >= 0:
                    end = min(end, pos)
        items = [line.strip(" -•\t") for line in text[start:end].splitlines()]
        return [item for item in items if item and item.lower() not in {"none", "هیچ", "موردی نیست", "ندارد"}]

    def _merge_markers(self, state: DebateState, text: str) -> None:
        mapping = {
            "[CONSENSUS]": state.consensus,
            "[DISAGREEMENTS]": state.disagreements,
            "[NEW]": state.proposals,
            "[RISKS]": state.risks,
            "[RESOLVED]": state.decisions,
            "[OPEN]": state.open_questions,
            "[NEXT]": state.discussed_topics,
        }
        for marker, target in mapping.items():
            for item in self._section(text, marker):
                if item not in target:
                    target.append(item)
