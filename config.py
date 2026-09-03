from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ModelConfig:
    name: str
    base_url: str
    temperature: float = 0.4
    timeout: float = 300.0


@dataclass(frozen=True)
class DebateConfig:
    rounds_per_segment: int = 10
    max_tokens: int = 2048


MODERATOR = ModelConfig(
    name=os.getenv("MODERATOR_MODEL", "StupidModel-6b"),
    base_url=os.getenv("MODERATOR_URL", "http://127.0.0.1:8081/v1"),
    temperature=float(os.getenv("MODERATOR_TEMPERATURE", "0.2")),
)

AGENT_1 = ModelConfig(
    name=os.getenv("AGENT1_MODEL", "Qwen3-8B"),
    base_url=os.getenv("AGENT1_URL", "http://127.0.0.1:8080/v1"),
    temperature=float(os.getenv("AGENT1_TEMPERATURE", "0.5")),
)

AGENT_2 = ModelConfig(
    name=os.getenv("AGENT2_MODEL", "gemma4Coding-12B"),
    base_url=os.getenv("AGENT2_URL", "http://127.0.0.1:8082/v1"),
    temperature=float(os.getenv("AGENT2_TEMPERATURE", "0.5")),
)

DEBATE = DebateConfig(
    rounds_per_segment=int(os.getenv("ROUNDS_PER_SEGMENT", "10")),
    max_tokens=int(os.getenv("MAX_TOKENS", "2048")),
)
