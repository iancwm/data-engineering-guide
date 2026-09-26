"""Focused acceptance tests for the synthetic point-in-time DuckDB lab."""
from __future__ import annotations

import copy
import sys
import unittest
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import run_pit_case as pit  # noqa: E402


class PitCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = pit.read_fixture()
        cls.report = pit.run_lab(cls.records)
        cls.by_id = {row["decision_id"]: row for row in cls.report["rows"]}

    def test_golden_decisions_select_original_then_correction(self) -> None:
        d1, d2 = self.by_id["D1"], self.by_id["D2"]
        self.assertEqual((d1["fundamental_revision_id"], d1["fundamental_value"]), ("F1", 100.0))
        self.assertEqual((d2["fundamental_revision_id"], d2["fundamental_value"]), ("F2", 95.0))
        self.assertEqual(d1["naive_current_fundamental_revision_id"], "F2")
        self.assertEqual(d1["naive_current_fundamental_value"], 95.0)
        self.assertNotEqual(d1["naive_current_fundamental_value"], d1["fundamental_value"])

    def test_boundary_is_inclusive_and_one_microsecond_before_excludes_revision(self) -> None:
        conn = pit._connect(self.records)
        try:
            exact = pit.select_fundamental(conn, "EQ1", "2026-01-10T14:00:00Z")
            before = pit.select_fundamental(conn, "EQ1", "2026-01-10T13:59:59.999999Z")
        finally:
            conn.close()
        self.assertEqual(exact["revision_id"], "F2")
        self.assertEqual(before["revision_id"], "F1")

    def test_unavailable_revision_is_not_selected(self) -> None:
        records = copy.deepcopy(self.records)
        future = next(row for row in records if row["revision_id"] == "F2")
        future["available_at"] = "2026-01-14T14:00:00Z"
        conn = pit._connect(records)
        try:
            selected = pit.select_fundamental(conn, "EQ1", "2026-01-13T21:05:00Z")
        finally:
            conn.close()
        self.assertEqual(selected["revision_id"], "F1")

    def test_same_availability_uses_lexicographically_greatest_revision_id(self) -> None:
        records = copy.deepcopy(self.records)
        base = next(row for row in records if row["revision_id"] == "F2")
        tied = copy.deepcopy(base)
        tied.update(record_id="FUND-F2Z", revision_id="F2Z", value=96.0)
        records.append(tied)
        conn = pit._connect(records)
        try:
            selected = pit.select_fundamental(conn, "EQ1", "2026-01-10T14:00:00Z")
        finally:
            conn.close()
        self.assertEqual(selected["revision_id"], "F2Z")
        self.assertEqual(selected["value"], 96.0)

    def test_historical_symbol_mapping_and_membership_are_preserved(self) -> None:
        d1, d2 = self.by_id["D1"], self.by_id["D2"]
        self.assertEqual((d1["symbol"], d2["symbol"]), ("AAA", "AAB"))
        self.assertEqual(d1["universe_instrument_ids"], "EQ1,EQ2")
        self.assertEqual(d2["universe_instrument_ids"], "EQ1")
        self.assertEqual(d1["universe_revision_ids"], "EQ1:M1,EQ2:M1")
        self.assertEqual(d2["universe_revision_ids"], "EQ1:M1")
        self.assertEqual(d2["membership_revision_ids"], "EQ1:M1,EQ2:M2")

    def test_decision_rows_remain_unique_and_missing_fundamental_is_visible(self) -> None:
        self.assertEqual(len(self.report["rows"]), 2)
        self.assertEqual(len({row["decision_id"] for row in self.report["rows"]}), 2)
        records = copy.deepcopy(self.records)
        d3 = copy.deepcopy(next(row for row in records if row["decision_id"] == "D2"))
        d3.update(record_id="DEC-D3-EQ2", decision_id="D3", instrument_id="EQ2")
        records.append(d3)
        result = pit.run_lab(records)
        row = next(row for row in result["rows"] if row["decision_id"] == "D3")
        self.assertIsNone(row["fundamental_revision_id"])
        self.assertEqual(row["symbol"], "CCC")
        self.assertEqual(len(result["rows"]), 3)

    def test_features_end_at_decision_and_labels_begin_on_next_open_session(self) -> None:
        for row in self.report["rows"]:
            decision_at = datetime.fromisoformat(row["decision_at"].replace("Z", "+00:00"))
            self.assertLessEqual(datetime.fromisoformat(row["feature_event_at"].replace("Z", "+00:00")), decision_at)
            self.assertLessEqual(datetime.fromisoformat(row["feature_available_at"].replace("Z", "+00:00")), decision_at)
            self.assertGreater(datetime.fromisoformat(row["label_event_at"].replace("Z", "+00:00")), decision_at)
            self.assertGreater(datetime.fromisoformat(row["label_available_at"].replace("Z", "+00:00")), decision_at)
        self.assertEqual(self.by_id["D1"]["label_session_id"], "S20260108")
        self.assertEqual(self.by_id["D2"]["label_session_id"], "S20260114")

    def test_closed_calendar_date_is_skipped_for_next_open_label(self) -> None:
        records = copy.deepcopy(self.records)
        d3 = copy.deepcopy(next(row for row in records if row["decision_id"] == "D1"))
        d3.update(
            record_id="DEC-D3",
            decision_id="D3",
            decision_at="2026-01-09T21:05:00Z",
        )
        records.append(d3)
        result = pit.run_lab(records)
        row = next(row for row in result["rows"] if row["decision_id"] == "D3")
        self.assertEqual(row["label_session_id"], "S20260112")
        self.assertNotEqual(row["label_session_id"], "S20260111")

    def test_every_selected_input_is_available_by_its_decision(self) -> None:
        for row in self.report["rows"]:
            decision = datetime.fromisoformat(row["decision_at"].replace("Z", "+00:00"))
            for field in (
                "fundamental_available_at", "symbol_available_at", "universe_max_available_at",
                "feature_available_at", "split_available_at",
            ):
                if row[field] is not None:
                    available = datetime.fromisoformat(row[field].replace("Z", "+00:00"))
                    self.assertLessEqual(available, decision, (row["decision_id"], field))

    def test_split_factor_is_decision_time_eligible_and_raw_prices_stay_unchanged(self) -> None:
        d1, d2 = self.by_id["D1"], self.by_id["D2"]
        self.assertIsNone(d1["split_factor"])
        self.assertIsNone(d1["split_pre_close_post_split_units"])
        self.assertEqual(d2["split_factor"], 0.5)
        self.assertEqual(d2["split_pre_session_id"], "S20260108")
        self.assertEqual(d2["split_pre_raw_close"], 102.0)
        self.assertEqual(d2["split_pre_close_post_split_units"], 51.0)
        raw_pre_split = next(row["raw_close"] for row in self.records if row["record_id"] == "PX-EQ1-2026-01-08")
        self.assertEqual(raw_pre_split, 102.0)

        records = copy.deepcopy(self.records)
        d3 = copy.deepcopy(next(row for row in records if row["decision_id"] == "D1"))
        d3.update(record_id="DEC-D3", decision_id="D3", decision_at="2026-01-08T21:05:00Z")
        records.append(d3)
        after_announcement_before_effective = next(
            row for row in pit.run_lab(records)["rows"] if row["decision_id"] == "D3"
        )
        self.assertIsNone(after_announcement_before_effective["split_revision_id"])
        self.assertIsNone(after_announcement_before_effective["split_factor"])

    def test_manifest_and_outputs_repeat_exactly(self) -> None:
        repeated = pit.run_lab(self.records)
        self.assertEqual(self.report, repeated)
        self.assertEqual(len(self.report["manifest"]["fixture_sha256"]), 64)
        self.assertEqual(len(self.report["manifest"]["code_sha256"]), 64)
        self.assertEqual(len(self.report["manifest"]["query_sha256"]), 64)
        self.assertEqual(len(self.report["manifest"]["output_sha256"]), 64)
        self.assertNotIn("run_at", self.report["manifest"])
        self.assertNotIn(str(Path.cwd()), str(self.report["manifest"]))
        d1 = self.report["manifest"]["decisions"][0]
        self.assertEqual(d1["fundamental_record_id"], "FUND-F1")
        self.assertEqual(d1["fundamental_revision_id"], "F1")
        self.assertEqual(d1["symbol_revision_id"], "SYM1")
        self.assertEqual(d1["universe_revision_ids"], "EQ1:M1,EQ2:M1")
        self.assertEqual(d1["feature_record_id"], "PX-EQ1-2026-01-07")
        self.assertEqual(d1["label_record_id"], "PX-EQ1-2026-01-08")


if __name__ == "__main__":
    unittest.main()
