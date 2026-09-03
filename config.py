from dataclasses import dataclass
import os


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
    rounds_per_segment: int = 10
    agent_max_tokens: int = 900
    moderator_max_tokens: int = 650
    summary_max_tokens: int = 1400


# Model identity is deliberately separate from role logic. Any model can be
# assigned to any role without changing the debate engine.
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
    rounds_per_segment=int(os.getenv("ROUNDS_PER_SEGMENT", "10")),
    agent_max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "900")),
    moderator_max_tokens=int(os.getenv("MODERATOR_MAX_TOKENS", "650")),
    summary_max_tokens=int(os.getenv("SUMMARY_MAX_TOKENS", "1400")),
)
