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
    consensus: list[str] = field(default_factory=list)
    disagreements: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    proposals: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    discussed_topics: list[str] = field(default_factory=list)

    @property
    def completed_rounds(self) -> int:
        return self.round_number

    def add_argument(self, agent: str, text: str) -> None:
        self.arguments.append(Argument(agent, self.round_number, text))

    def compact(self, summary: str) -> None:
        # The next segment must never inherit the previous live transcript.
        self.durable_summary = summary.strip()
        self.arguments.clear()
        self.round_number = 0
        self.segment_number += 1
