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

    @staticmethod
    def _remove_exact(values: list[str], items: list[str]) -> None:
        for item in items:
            if item in values:
                values.remove(item)

    def _merge_markers(self, state: DebateState, text: str) -> None:
        consensus = self._section(text, "[CONSENSUS]")
        disagreements = self._section(text, "[DISAGREEMENTS]")
        new_items = self._section(text, "[NEW]")
        risks = self._section(text, "[RISKS]")
        resolved = self._section(text, "[RESOLVED]")
        open_items = self._section(text, "[OPEN]")
        next_items = self._section(text, "[NEXT]")

        for item in consensus:
            if item not in state.consensus:
                state.consensus.append(item)
        for item in disagreements:
            if item not in state.disagreements:
                state.disagreements.append(item)
        for item in new_items:
            if item not in state.proposals:
                state.proposals.append(item)
        for item in risks:
            if item not in state.risks:
                state.risks.append(item)
        for item in resolved:
            if item not in state.decisions:
                state.decisions.append(item)
            self._remove_exact(state.disagreements, [item])
            self._remove_exact(state.open_questions, [item])
        for item in open_items:
            if item not in state.open_questions:
                state.open_questions.append(item)

        # NEXT is a current-round directive, not historical state.
        state.next_focus = next_items[:2]
        state.discussed_topics.extend(item for item in next_items if item not in state.discussed_topics)
