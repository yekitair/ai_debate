import unittest

from debate.engine import DebateEngine
from debate.models import DebateState


class FakeClient:
    def __init__(self, label):
        self.label = label
        self.calls = 0

    def health_check(self):
        return {"ok": True, "model": self.label, "url": "mock://"}

    def complete(self, messages, max_tokens):
        self.calls += 1
        return {
            "text": f"{self.label} response {self.calls}",
            "finish_reason": "stop",
            "usage": None,
            "raw": {},
        }


class FakeModerator:
    def __init__(self):
        self.client = FakeClient("moderator")
        self.missions = 0
        self.updates = 0
        self.summaries = 0

    def mission(self, state):
        self.missions += 1
        return {"text": f"Mission {self.missions}", "finish_reason": "stop"}

    def update_state(self, state, mission, agent1, agent2):
        self.updates += 1
        return {"text": "[NEW]\n- New finding", "finish_reason": "stop"}

    def summarize_segment(self, state):
        self.summaries += 1
        return {"text": f"Summary for segment {state.segment_number}", "finish_reason": "stop"}


class DebateFlowTest(unittest.TestCase):
    def test_exactly_ten_rounds_and_compaction_discards_transcript(self):
        agent1 = FakeClient("agent1")
        agent2 = FakeClient("agent2")
        moderator = FakeModerator()
        engine = DebateEngine(agent1, agent2, moderator, rounds_per_segment=10, agent_max_tokens=900)
        state = DebateState(question="Test question")

        first = engine.run_segment(state)
        self.assertEqual(len(first["rounds"]), 10)
        self.assertEqual(state.round_number, 10)
        self.assertEqual(len(state.arguments), 20)
        self.assertEqual(moderator.missions, 10)
        self.assertEqual(moderator.updates, 10)
        self.assertEqual(moderator.summaries, 1)

        summary = first["summary"]["text"]
        state.compact(summary)
        self.assertEqual(state.segment_number, 2)
        self.assertEqual(state.round_number, 0)
        self.assertEqual(state.arguments, [])
        self.assertEqual(state.durable_summary, summary)

        second = engine.run_segment(state)
        self.assertEqual(len(second["rounds"]), 10)
        self.assertEqual(state.round_number, 10)
        self.assertEqual(len(state.arguments), 20)
        self.assertEqual(moderator.missions, 20)
        self.assertEqual(moderator.updates, 20)
        self.assertEqual(moderator.summaries, 2)


if __name__ == "__main__":
    unittest.main()
