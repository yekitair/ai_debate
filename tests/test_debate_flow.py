import unittest

from debate.context_manager import compact_state, continuation_package
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
        return {"text": f"{self.label} response {self.calls}", "finish_reason": "stop", "usage": None, "raw": {}}


class FakeModerator:
    def __init__(self):
        self.client = FakeClient("moderator")
        self.missions = 0
        self.updates = 0
        self.summaries = 0
        self.notes = []

    def mission(self, state, user_note=""):
        self.missions += 1
        self.notes.append(user_note)
        return {"text": f"Mission {self.missions}", "finish_reason": "stop"}

    def update_state(self, state, mission, agent1, agent2):
        self.updates += 1
        state.proposals.append(f"Finding {self.updates}")
        return {"text": "[NEW]\n- New finding", "finish_reason": "stop"}

    def summarize_segment(self, state):
        self.summaries += 1
        return {"text": f"Summary for segment {state.segment_number}", "finish_reason": "stop"}


class DebateFlowTest(unittest.TestCase):
    def test_runtime_rounds_compaction_and_human_note_consumption(self):
        agent1 = FakeClient("agent1")
        agent2 = FakeClient("agent2")
        moderator = FakeModerator()
        engine = DebateEngine(agent1, agent2, moderator, rounds_per_segment=3, agent_max_tokens=500)
        state = DebateState(question="Test question")
        notes = iter(["Human note: consider cost.", "", ""])

        first = engine.run_segment(state, user_note_provider=lambda: next(notes))
        self.assertEqual(len(first["rounds"]), 3)
        self.assertEqual(state.round_number, 3)
        self.assertEqual(len(state.arguments), 6)
        self.assertEqual(moderator.missions, 3)
        self.assertEqual(moderator.updates, 3)
        self.assertEqual(moderator.summaries, 1)
        self.assertEqual(moderator.notes[0], "Human note: consider cost.")
        self.assertEqual(moderator.notes[1], "")

        package_before = continuation_package(state)
        self.assertNotIn("arguments", package_before)
        self.assertNotIn("agent1 response 1", compact_state(state))

        summary = first["summary"]["text"]
        state.compact(summary)
        self.assertEqual(state.segment_number, 2)
        self.assertEqual(state.round_number, 0)
        self.assertEqual(state.arguments, [])
        self.assertEqual(state.durable_summary, summary)
        self.assertIn("Finding 3", compact_state(state))

        second = engine.run_segment(state, user_note_provider=lambda: "")
        self.assertEqual(len(second["rounds"]), 3)
        self.assertEqual(state.round_number, 3)
        self.assertEqual(len(state.arguments), 6)
        self.assertEqual(moderator.missions, 6)
        self.assertEqual(moderator.updates, 6)
        self.assertEqual(moderator.summaries, 2)


if __name__ == "__main__":
    unittest.main()
