from typing import Iterable

import requests

from config import ModelConfig


class LLMClient:
    """Minimal client for local OpenAI-compatible inference servers."""

    def __init__(self, config: ModelConfig):
        self.config = config

    def complete(self, messages: Iterable[dict[str, str]], max_tokens: int) -> str:
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.name,
            "messages": list(messages),
            "temperature": self.config.temperature,
            "max_tokens": max_tokens,
        }
        response = requests.post(url, json=payload, timeout=self.config.timeout)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
