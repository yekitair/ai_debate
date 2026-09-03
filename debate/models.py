from dataclasses import dataclass, field


@dataclass
class Argument:
    agent: str
    round_number: int
    text: str


@dataclass
class DebateState:
    question: str
    segment_number: int = 1
    round_number: int = 0
    arguments: list[Argument] = field(default_factory=list)
    durable_summary: str = ""

    @property
    def completed_rounds(self) -> int:
        return self.round_number

    def add_argument(self, agent: str, text: str) -> None:
        self.arguments.append(Argument(agent, self.round_number, text))

    def compact(self, summary: str) -> None:
        self.durable_summary = summary.strip()
        self.arguments.clear()
        self.round_number = 0
        self.segment_number += 1
