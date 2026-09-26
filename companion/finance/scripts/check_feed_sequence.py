#!/usr/bin/env python3
"""Check a tiny synthetic, scoped feed sequence and print its recovery trace.

This invented SIM contract counts sequenced logical messages, not transport
packets. A recovery transmission carries the original logical sequence number
and identifies that message in ``repair_of``. State is scoped to
``(feed, channel, session)``. The first observed sequence in each scope is the
local starting point; this fixture does not infer a missing prefix.

Usage:
    companion/.venv/bin/python companion/finance/scripts/check_feed_sequence.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "feed_sequence.jsonl"
REQUIRED_FIELDS = {
    "arrival_index",
    "message_id",
    "feed",
    "channel",
    "session",
    "sequence",
    "kind",
    "repair_of",
    "event_at",
    "received_at",
    "payload",
}


def logical_message_id(row: dict[str, Any]) -> str:
    """Return the stable ID for one logical message in its sequence domain."""
    return "/".join(
        (str(row["feed"]), str(row["channel"]), str(row["session"]), str(row["sequence"]))
    )


def load_fixture(path: Path = FIXTURE_PATH) -> list[dict[str, Any]]:
    """Load JSONL rows, rejecting malformed or ambiguous arrival order."""
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
        missing = REQUIRED_FIELDS - row.keys()
        if missing:
            raise ValueError(f"{path}:{line_number}: missing fields {sorted(missing)}")
        rows.append(row)

    indexes = [row["arrival_index"] for row in rows]
    if len(indexes) != len(set(indexes)):
        raise ValueError("arrival_index values must be unique")
    message_ids = [row["message_id"] for row in rows]
    if len(message_ids) != len(set(message_ids)):
        raise ValueError("message_id values must be unique transmission IDs")
    return sorted(rows, key=lambda row: row["arrival_index"])


def _validate_row(row: dict[str, Any]) -> None:
    if not isinstance(row["sequence"], int) or isinstance(row["sequence"], bool):
        raise ValueError(f"sequence must be an integer: {row['message_id']}")
    if row["sequence"] < 0:
        raise ValueError(f"sequence cannot be negative: {row['message_id']}")
    if row["kind"] not in {"data", "repair"}:
        raise ValueError(f"unsupported kind {row['kind']!r}: {row['message_id']}")
    if row["kind"] == "data" and row["repair_of"] is not None:
        raise ValueError(f"data row must have repair_of=null: {row['message_id']}")


def analyze_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a deterministic per-arrival trace for independently scoped state.

    A message ahead of ``expected`` is buffered and makes its own scope
    incomplete. A repeated applied or buffered sequence is ignored as a
    duplicate. A previously unseen sequence below ``expected`` is reported as
    out of order and ignored. An expected repair is accepted only when its
    ``repair_of`` matches the logical ID derived from its scope and sequence;
    contiguous buffered messages are released immediately after a repair fills
    a gap.
    """
    ordered = sorted(records, key=lambda row: row["arrival_index"])
    scopes: dict[tuple[str, str, str], dict[str, Any]] = {}
    trace: list[dict[str, Any]] = []

    for row in ordered:
        _validate_row(row)
        scope = (str(row["feed"]), str(row["channel"]), str(row["session"]))
        state = scopes.setdefault(
            scope,
            {"expected": None, "applied": set(), "buffered": {}},
        )
        sequence = row["sequence"]
        if state["expected"] is None:
            state["expected"] = sequence
        expected_before = state["expected"]
        action: str
        released: list[int] = []

        if sequence in state["applied"] or sequence in state["buffered"]:
            action = "duplicate"
        elif sequence < expected_before:
            action = "out_of_order"
        elif sequence > expected_before:
            state["buffered"][sequence] = row
            action = "gap_buffered"
        else:
            _apply_expected_row(row, state)
            action = "repair_applied" if row["kind"] == "repair" else "accepted"
            released.append(sequence)
            while state["expected"] in state["buffered"]:
                next_row = state["buffered"].pop(state["expected"])
                _apply_expected_row(next_row, state)
                released.append(next_row["sequence"])

        incomplete = bool(state["buffered"])
        trace.append(
            {
                "arrival_index": row["arrival_index"],
                "scope": "/".join(scope),
                "expected_sequence": expected_before,
                "received_sequence": sequence,
                "kind": row["kind"],
                "action": action,
                "next_expected": state["expected"],
                "incomplete": incomplete,
                "buffered_sequences": sorted(state["buffered"]),
                "released_sequences": released,
            }
        )

    return trace


def _apply_expected_row(row: dict[str, Any], state: dict[str, Any]) -> None:
    expected = state["expected"]
    if row["sequence"] != expected:
        raise AssertionError("only the expected sequence can be applied")
    if row["kind"] == "repair" and row["repair_of"] != logical_message_id(row):
        raise ValueError(
            f"repair {row['message_id']} must repair {logical_message_id(row)!r}, "
            f"got {row['repair_of']!r}"
        )
    state["applied"].add(row["sequence"])
    state["expected"] += 1


def render_trace(trace: list[dict[str, Any]]) -> str:
    """Format the trace as a stable compact table."""
    columns = (
        ("arrival", "arrival_index"),
        ("scope", "scope"),
        ("expected", "expected_sequence"),
        ("received", "received_sequence"),
        ("action", "action"),
        ("next", "next_expected"),
        ("state", "incomplete"),
        ("buffered", "buffered_sequences"),
        ("released", "released_sequences"),
    )
    lines = [" ".join(title.ljust(10) for title, _ in columns).rstrip()]
    for item in trace:
        cells = []
        for _, key in columns:
            value = item[key]
            if key == "incomplete":
                value = "incomplete" if value else "complete"
            elif isinstance(value, list):
                value = ",".join(str(item) for item in value) or "-"
            cells.append(str(value).ljust(10))
        lines.append(" ".join(cells).rstrip())
    return "\n".join(lines)


def main() -> int:
    rows = load_fixture()
    trace = analyze_records(rows)
    print("Sequence numbers count logical messages; state scope is feed/channel/session.")
    print("A repair transmission is accepted only for its expected sequence and matching repair_of ID.")
    print(render_trace(trace))
    final_state_by_scope: dict[str, bool] = {}
    for item in trace:
        final_state_by_scope[item["scope"]] = item["incomplete"]
    unresolved = sorted(scope for scope, incomplete in final_state_by_scope.items() if incomplete)
    print(f"\nFinal incomplete scopes: {', '.join(unresolved) if unresolved else 'none'}")
    return 0 if not unresolved else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
