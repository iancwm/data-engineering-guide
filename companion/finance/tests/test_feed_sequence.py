from __future__ import annotations

import copy
import unittest
from pathlib import Path

from companion.finance.scripts.check_feed_sequence import (
    analyze_records,
    load_fixture,
    render_trace,
)


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "feed_sequence.jsonl"


class FeedSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_fixture(FIXTURE)

    def test_gap_duplicate_and_repair_trace(self) -> None:
        trace = analyze_records(self.rows)
        channel_a = [row for row in trace if row["scope"] == "SIM/A/2026-01-07"]

        self.assertEqual([row["received_sequence"] for row in channel_a], [10, 11, 13, 13, 12])
        self.assertEqual(channel_a[2]["action"], "gap_buffered")
        self.assertEqual(channel_a[2]["expected_sequence"], 12)
        self.assertTrue(channel_a[2]["incomplete"])
        self.assertEqual(channel_a[2]["buffered_sequences"], [13])
        self.assertEqual(channel_a[3]["action"], "duplicate")
        self.assertTrue(channel_a[3]["incomplete"])
        self.assertEqual(channel_a[4]["action"], "repair_applied")
        self.assertEqual(channel_a[4]["released_sequences"], [12, 13])
        self.assertEqual(channel_a[4]["next_expected"], 14)
        self.assertFalse(channel_a[4]["incomplete"])

    def test_channel_and_session_state_are_independent_during_gap(self) -> None:
        trace = analyze_records(self.rows)
        while_a_is_incomplete = [row for row in trace if row["arrival_index"] in {4, 5, 7, 8}]

        self.assertEqual(
            [(row["scope"], row["action"], row["incomplete"], row["next_expected"]) for row in while_a_is_incomplete],
            [
                ("SIM/B/2026-01-07", "accepted", False, 2),
                ("SIM/A/2026-01-08", "accepted", False, 2),
                ("SIM/B/2026-01-07", "accepted", False, 3),
                ("SIM/A/2026-01-08", "accepted", False, 3),
            ],
        )

    def test_missing_repair_leaves_affected_scope_incomplete(self) -> None:
        rows_without_repair = [row for row in self.rows if row["kind"] != "repair"]
        trace = analyze_records(rows_without_repair)
        channel_a = [row for row in trace if row["scope"] == "SIM/A/2026-01-07"]

        self.assertTrue(channel_a[-1]["incomplete"])
        self.assertEqual(channel_a[-1]["next_expected"], 12)
        self.assertEqual(channel_a[-1]["buffered_sequences"], [13])
        self.assertFalse([row for row in trace if row["scope"] != "SIM/A/2026-01-07" and row["incomplete"]])

    def test_unseen_lower_sequence_is_reported_as_out_of_order(self) -> None:
        rows = copy.deepcopy(self.rows)
        rows.append(
            {
                "arrival_index": 10,
                "message_id": "rx-010",
                "feed": "SIM",
                "channel": "A",
                "session": "2026-01-07",
                "sequence": 9,
                "kind": "data",
                "repair_of": None,
                "event_at": "2026-01-07T21:04:58.000000Z",
                "received_at": "2026-01-08T21:05:00.400000Z",
                "payload": "late-trade-9",
            }
        )

        trace = analyze_records(rows)
        late = trace[-1]
        self.assertEqual(late["action"], "out_of_order")
        self.assertEqual(late["expected_sequence"], 14)
        self.assertFalse(late["incomplete"])

    def test_repair_must_match_expected_logical_message(self) -> None:
        rows = copy.deepcopy(self.rows)
        repair = next(row for row in rows if row["kind"] == "repair")
        repair["repair_of"] = "SIM/A/2026-01-07/99"

        with self.assertRaisesRegex(ValueError, "must repair"):
            analyze_records(rows)

    def test_repeated_run_has_identical_trace_and_rendering(self) -> None:
        first = analyze_records(self.rows)
        second = analyze_records(self.rows)
        self.assertEqual(first, second)
        self.assertEqual(render_trace(first), render_trace(second))


if __name__ == "__main__":
    unittest.main()
