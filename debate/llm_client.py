from typing import Iterable
from urllib.parse import urlsplit

import requests

from config import ModelConfig


class LLMError(RuntimeError):
    pass


class LLMClient:
    """OpenAI-compatible client for local llama-server instances."""

    def __init__(self, config: ModelConfig):
        self.config = config

    def health_check(self) -> dict[str, object]:
        base = self.config.base_url.rstrip("/")
        parsed = urlsplit(base)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        candidates = (f"{origin}/health", f"{base}/models", f"{base}/health")
        last_error = "unknown error"
        for url in candidates:
            try:
                response = requests.get(url, timeout=self.config.health_timeout)
                if response.ok:
                    try:
                        data = response.json() if response.content else {}
                    except ValueError:
                        data = {"text": response.text[:200]}
                    return {"ok": True, "url": url, "model": self.config.name, "data": data}
                last_error = f"HTTP {response.status_code}"
            except requests.RequestException as exc:
                last_error = str(exc)
        return {"ok": False, "url": base, "model": self.config.name, "error": last_error}

    def complete(self, messages: Iterable[dict[str, str]], max_tokens: int) -> dict[str, object]:
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.name,
            "messages": list(messages),
            "temperature": self.config.temperature,
            "max_tokens": max_tokens,
        }
        try:
            response = requests.post(url, json=payload, timeout=self.config.timeout)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise LLMError(f"{self.config.role} request failed: {exc}") from exc

        try:
            choice = data["choices"][0]
            message = choice.get("message") or {}
            content = (message.get("content") or "").strip()
            finish_reason = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"{self.config.role} returned an invalid response: {data!r}") from exc

        return {
            "text": content,
            "finish_reason": finish_reason,
            "usage": data.get("usage"),
            "raw": data,
        }
