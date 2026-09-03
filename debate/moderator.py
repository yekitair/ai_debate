from .context_manager import transcript
from .llm_client import LLMClient
from .models import DebateState
from .prompts import moderator_prompt


class Moderator:
    def __init__(self, client: LLMClient, max_tokens: int):
        self.client = client
        self.max_tokens = max_tokens

    def summarize_segment(self, state: DebateState) -> str:
        return self.client.complete(
            moderator_prompt(state.question, transcript(state), state.durable_summary),
            self.max_tokens,
        )
