from dataclasses import dataclass
import os


LANGUAGE_OPTIONS = {
    "auto": "خودکار — تشخیص از پرسش",
    "fa": "فارسی",
    "en": "English",
    "de": "Deutsch",
    "fr": "Français",
    "zh": "中文",
}


@dataclass(frozen=True)
class ModelConfig:
    role: str
    name: str
    base_url: str
    temperature: float = 0.4
    timeout: float = 300.0
    health_timeout: float = 5.0


@dataclass(frozen=True)
class DebateConfig:
    default_rounds_per_segment: int = 10
    default_agent_max_tokens: int = 1200
    default_moderator_max_tokens: int = 800
    default_summary_max_tokens: int = 1600
    min_rounds: int = 1
    max_rounds: int = 100
    min_output_tokens: int = 128
    max_output_tokens: int = 4096


MODERATOR = ModelConfig(
    role="moderator",
    name=os.getenv("MODERATOR_MODEL", "gemma4Coding-12B-Q4_K_M"),
    base_url=os.getenv("MODERATOR_URL", "http://127.0.0.1:8081/v1"),
    temperature=float(os.getenv("MODERATOR_TEMPERATURE", "0.2")),
)

AGENT_1 = ModelConfig(
    role="agent_1",
    name=os.getenv("AGENT1_MODEL", "Qwen3-8B-Q5_K_M"),
    base_url=os.getenv("AGENT1_URL", "http://127.0.0.1:8080/v1"),
    temperature=float(os.getenv("AGENT1_TEMPERATURE", "0.5")),
)

AGENT_2 = ModelConfig(
    role="agent_2",
    name=os.getenv("AGENT2_MODEL", "qwen2.5-coder-7b-instruct-q6_k"),
    base_url=os.getenv("AGENT2_URL", "http://127.0.0.1:8082/v1"),
    temperature=float(os.getenv("AGENT2_TEMPERATURE", "0.5")),
)

DEBATE = DebateConfig(
    default_rounds_per_segment=int(os.getenv("DEFAULT_ROUNDS", "10")),
    default_agent_max_tokens=int(os.getenv("DEFAULT_AGENT_MAX_TOKENS", "1200")),
    default_moderator_max_tokens=int(os.getenv("DEFAULT_MODERATOR_MAX_TOKENS", "800")),
    default_summary_max_tokens=int(os.getenv("DEFAULT_SUMMARY_MAX_TOKENS", "1600")),
)
