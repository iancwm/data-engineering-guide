#!/usr/bin/env python3
"""Offline, synthetic DuckDB demonstration of point-in-time selection.

Decision-time knowledge uses `available_at <= decision_at`. The deliberately
wrong current-value view skips that predicate only to show the look-ahead
failure. This lab is an educational data-selection exercise, not a strategy or
execution simulator.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import duckdb

ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = ROOT / "companion/finance/fixtures/pit_case.jsonl"

# Keep this ordered list in sync with the explicit union schema in pit_case.jsonl.
COLUMNS = (
    "record_id", "kind", "grain", "record_key", "instrument_id", "revision_id",
    "decision_id", "decision_at", "available_at", "received_at", "event_at",
    "effective_from", "effective_to", "period_end", "session_id", "session_date",
    "symbol", "member", "raw_close", "value", "factor", "exchange_timezone",
    "session_status", "open_at", "close_at", "adjustment_convention",
)
DDL = """
CREATE TABLE fixture (
    record_id VARCHAR,
    kind VARCHAR,
    grain VARCHAR,
    record_key VARCHAR,
    instrument_id VARCHAR,
    revision_id VARCHAR,
    decision_id VARCHAR,
    decision_at TIMESTAMPTZ,
    available_at TIMESTAMPTZ,
    received_at TIMESTAMPTZ,
    event_at TIMESTAMPTZ,
    effective_from DATE,
    effective_to DATE,
    period_end DATE,
    session_id VARCHAR,
    session_date DATE,
    symbol VARCHAR,
    member BOOLEAN,
    raw_close DOUBLE,
    value DOUBLE,
    factor DOUBLE,
    exchange_timezone VARCHAR,
    session_status VARCHAR,
    open_at TIMESTAMPTZ,
    close_at TIMESTAMPTZ,
    adjustment_convention VARCHAR
)
"""

FUNDAMENTAL_SQL = """
SELECT record_id, revision_id, period_end,
       strftime(available_at, '%Y-%m-%dT%H:%M:%S.%fZ') AS available_at, value
FROM fixture
WHERE kind = 'fundamental'
  AND instrument_id = ?
  AND period_end <= CAST(? AS DATE)
  AND available_at <= CAST(? AS TIMESTAMPTZ)
ORDER BY period_end DESC, available_at DESC, revision_id DESC
LIMIT 1
"""

# Ranking first chooses the revision visible at the decision. Only after that
# does the query apply its business-valid interval or report-period rule.
RESULT_SQL = """
WITH decisions AS (
    SELECT decision_id, instrument_id, decision_at,
           CAST(decision_at AS DATE) AS decision_date
    FROM fixture
    WHERE kind = 'decision'
), fundamental AS (
    SELECT d.decision_id,
           f.record_id AS fundamental_record_id,
           f.revision_id AS fundamental_revision_id,
           f.period_end AS fundamental_period_end,
           f.available_at AS fundamental_available_at,
           f.value AS fundamental_value
    FROM decisions d
    LEFT JOIN LATERAL (
        SELECT f.record_id, f.revision_id, f.period_end, f.available_at, f.value
        FROM fixture f
        WHERE f.kind = 'fundamental'
          AND f.instrument_id = d.instrument_id
          AND f.period_end <= d.decision_date
          AND f.available_at <= d.decision_at
        ORDER BY f.period_end DESC, f.available_at DESC, f.revision_id DESC
        LIMIT 1
    ) f ON TRUE
), symbol_asof AS (
    SELECT d.decision_id,
           s.symbol,
           s.revision_id AS symbol_revision_id,
           s.available_at AS symbol_available_at
    FROM decisions d
    LEFT JOIN LATERAL (
        SELECT s.symbol, s.revision_id, s.available_at
        FROM fixture s
        WHERE s.kind = 'symbol_mapping'
          AND s.instrument_id = d.instrument_id
          AND s.available_at <= d.decision_at
          AND s.effective_from <= d.decision_date
          AND (s.effective_to IS NULL OR d.decision_date < s.effective_to)
        ORDER BY s.effective_from DESC, s.available_at DESC, s.revision_id DESC
        LIMIT 1
    ) s ON TRUE
), membership_asof AS (
    SELECT d.decision_id, d.decision_date, m.instrument_id, m.member,
           m.revision_id, m.available_at, m.effective_from, m.effective_to
    FROM decisions d
    CROSS JOIN (
        SELECT DISTINCT instrument_id
        FROM fixture
        WHERE kind = 'membership'
    ) i
    LEFT JOIN LATERAL (
        SELECT m.instrument_id, m.member, m.revision_id, m.available_at,
               m.effective_from, m.effective_to
        FROM fixture m
        WHERE m.kind = 'membership'
          AND m.instrument_id = i.instrument_id
          AND m.available_at <= d.decision_at
        ORDER BY m.available_at DESC, m.revision_id DESC
        LIMIT 1
    ) m ON TRUE
), universe AS (
    SELECT decision_id,
           string_agg(
               CASE WHEN member IS TRUE
                          AND effective_from <= decision_date
                          AND (effective_to IS NULL OR decision_date < effective_to)
                    THEN instrument_id END,
               ',' ORDER BY instrument_id
           ) AS universe_instrument_ids,
           string_agg(
               CASE WHEN member IS TRUE
                          AND effective_from <= decision_date
                          AND (effective_to IS NULL OR decision_date < effective_to)
                    THEN instrument_id || ':' || revision_id END,
               ',' ORDER BY instrument_id
           ) AS universe_revision_ids,
           string_agg(instrument_id || ':' || revision_id, ',' ORDER BY instrument_id)
               AS membership_revision_ids,
           max(available_at) AS universe_max_available_at
    FROM membership_asof
    GROUP BY decision_id
), feature_ranked AS (
    SELECT d.decision_id,
           p.record_id,
           p.session_id,
           p.event_at,
           p.available_at,
           p.raw_close,
           row_number() OVER (
               PARTITION BY d.decision_id
               ORDER BY p.event_at DESC, p.record_id DESC
           ) AS close_rank
    FROM decisions d
    JOIN fixture p
      ON p.kind = 'raw_price'
     AND p.instrument_id = d.instrument_id
     AND p.event_at <= d.decision_at
     AND p.available_at <= d.decision_at
), feature AS (
    SELECT decision_id,
           max(CASE WHEN close_rank = 1 THEN record_id END) AS feature_record_id,
           max(CASE WHEN close_rank = 1 THEN session_id END) AS feature_session_id,
           max(CASE WHEN close_rank = 1 THEN event_at END) AS feature_event_at,
           max(CASE WHEN close_rank = 1 THEN available_at END) AS feature_available_at,
           max(CASE WHEN close_rank = 1 THEN raw_close END) AS feature_close_raw,
           max(CASE WHEN close_rank = 2 THEN record_id END) AS feature_previous_record_id,
           max(CASE WHEN close_rank = 2 THEN session_id END) AS feature_previous_session_id,
           max(CASE WHEN close_rank = 2 THEN raw_close END) AS feature_previous_close_raw
    FROM feature_ranked
    WHERE close_rank <= 2
    GROUP BY decision_id
), label_ranked AS (
    -- The label is deliberately calculated from the next open session and
    -- joins only after the feature selection has ended at decision_at.
    SELECT d.decision_id,
           c.session_id AS label_session_id,
           c.session_date AS label_session_date,
           p.record_id AS label_record_id,
           p.event_at AS label_event_at,
           p.available_at AS label_available_at,
           p.raw_close AS label_close_raw,
           row_number() OVER (
               PARTITION BY d.decision_id
               ORDER BY c.session_date, c.session_id
           ) AS label_rank
    FROM decisions d
    JOIN fixture c
      ON c.kind = 'calendar'
     AND c.session_status = 'open'
     AND c.session_date > d.decision_date
    JOIN fixture p
      ON p.kind = 'raw_price'
     AND p.instrument_id = d.instrument_id
     AND p.session_id = c.session_id
     AND p.event_at > d.decision_at
), label AS (
    SELECT decision_id, label_session_id, label_session_date, label_record_id, label_event_at,
           label_available_at, label_close_raw
    FROM label_ranked
    WHERE label_rank = 1
), split_asof AS (
    SELECT d.decision_id,
           s.revision_id AS split_revision_id,
           s.available_at AS split_available_at,
           s.effective_from AS split_effective_from,
           s.factor AS split_factor
    FROM decisions d
    LEFT JOIN LATERAL (
        SELECT s.revision_id, s.available_at, s.effective_from, s.factor
        FROM fixture s
        WHERE s.kind = 'split'
          AND s.instrument_id = d.instrument_id
          AND s.available_at <= d.decision_at
          AND s.effective_from <= d.decision_date
        ORDER BY s.available_at DESC, s.revision_id DESC
        LIMIT 1
    ) s ON TRUE
), split_comparison AS (
    SELECT d.decision_id,
           p.session_id AS split_pre_session_id,
           p.raw_close AS split_pre_raw_close
    FROM decisions d
    JOIN split_asof s USING (decision_id)
    LEFT JOIN LATERAL (
        SELECT p.session_id, p.raw_close
        FROM fixture p
        JOIN fixture c
          ON c.kind = 'calendar'
         AND c.session_id = p.session_id
        WHERE p.kind = 'raw_price'
          AND p.instrument_id = d.instrument_id
          AND c.session_date < s.split_effective_from
          AND p.event_at <= d.decision_at
          AND p.available_at <= d.decision_at
        ORDER BY c.session_date DESC, p.event_at DESC
        LIMIT 1
    ) p ON TRUE
)
SELECT d.decision_id,
       d.instrument_id,
       strftime(d.decision_at, '%Y-%m-%dT%H:%M:%S.%fZ') AS decision_at,
       f.fundamental_period_end,
       f.fundamental_record_id,
       f.fundamental_revision_id,
       strftime(f.fundamental_available_at, '%Y-%m-%dT%H:%M:%S.%fZ') AS fundamental_available_at,
       f.fundamental_value,
       n.value AS naive_current_fundamental_value,
       n.revision_id AS naive_current_fundamental_revision_id,
       s.symbol,
       s.symbol_revision_id,
       strftime(s.symbol_available_at, '%Y-%m-%dT%H:%M:%S.%fZ') AS symbol_available_at,
       u.universe_instrument_ids,
       u.universe_revision_ids,
       u.membership_revision_ids,
       strftime(u.universe_max_available_at, '%Y-%m-%dT%H:%M:%S.%fZ') AS universe_max_available_at,
       x.feature_record_id,
       x.feature_session_id,
       strftime(x.feature_event_at, '%Y-%m-%dT%H:%M:%S.%fZ') AS feature_event_at,
       strftime(x.feature_available_at, '%Y-%m-%dT%H:%M:%S.%fZ') AS feature_available_at,
       x.feature_close_raw,
       x.feature_previous_record_id,
       x.feature_previous_session_id,
       x.feature_previous_close_raw,
       CASE WHEN x.feature_previous_close_raw IS NULL OR x.feature_previous_close_raw = 0
            THEN NULL
            ELSE x.feature_close_raw / x.feature_previous_close_raw - 1 END AS feature_return,
       l.label_session_id,
       l.label_session_date,
       l.label_record_id,
       strftime(l.label_event_at, '%Y-%m-%dT%H:%M:%S.%fZ') AS label_event_at,
       strftime(l.label_available_at, '%Y-%m-%dT%H:%M:%S.%fZ') AS label_available_at,
       l.label_close_raw,
       CASE WHEN x.feature_close_raw IS NULL OR x.feature_close_raw = 0 OR l.label_close_raw IS NULL
            THEN NULL
            ELSE l.label_close_raw / x.feature_close_raw - 1 END AS label_return,
       a.split_revision_id,
       strftime(a.split_available_at, '%Y-%m-%dT%H:%M:%S.%fZ') AS split_available_at,
       a.split_effective_from,
       a.split_factor,
       q.split_pre_session_id,
       q.split_pre_raw_close,
       CASE WHEN a.split_factor IS NULL OR q.split_pre_raw_close IS NULL
            THEN NULL ELSE q.split_pre_raw_close * a.split_factor END
            AS split_pre_close_post_split_units
FROM decisions d
LEFT JOIN fundamental f USING (decision_id)
LEFT JOIN LATERAL (
    SELECT n.value, n.revision_id
    FROM fixture n
    WHERE n.kind = 'fundamental'
      AND n.instrument_id = d.instrument_id
      AND n.period_end <= d.decision_date
    ORDER BY n.period_end DESC, n.available_at DESC, n.revision_id DESC
    LIMIT 1
) n ON TRUE
LEFT JOIN symbol_asof s USING (decision_id)
LEFT JOIN universe u USING (decision_id)
LEFT JOIN feature x USING (decision_id)
LEFT JOIN label l USING (decision_id)
LEFT JOIN split_asof a USING (decision_id)
LEFT JOIN split_comparison q USING (decision_id)
ORDER BY d.decision_at, d.decision_id
"""


def read_fixture(path: Path = FIXTURE_PATH) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def _fixture_hash(records: Iterable[dict[str, Any]]) -> str:
    canonical = json.dumps(list(records), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        if isinstance(value, datetime):
            value = value.astimezone(timezone.utc)
            return value.isoformat(timespec="microseconds").replace("+00:00", "Z")
        return value.isoformat()
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def _normalized_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return round(value, 10)
    return value


def _connect(records: Iterable[dict[str, Any]]) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(database=":memory:")
    conn.execute("SET TimeZone='UTC'")
    conn.execute(DDL)
    record_list = list(records)
    values = [tuple(row.get(column) for column in COLUMNS) for row in record_list]
    placeholders = ", ".join("?" for _ in COLUMNS)
    conn.executemany(f"INSERT INTO fixture VALUES ({placeholders})", values)
    return conn


def select_fundamental(
    conn: duckdb.DuckDBPyConnection,
    instrument_id: str,
    decision_at: str,
) -> dict[str, Any] | None:
    """Return the latest eligible period and revision using the frozen tie rule."""
    decision = datetime.fromisoformat(decision_at.replace("Z", "+00:00"))
    row = conn.execute(
        FUNDAMENTAL_SQL,
        [instrument_id, decision.date().isoformat(), decision_at],
    ).fetchone()
    if row is None:
        return None
    return dict(zip(("record_id", "revision_id", "period_end", "available_at", "value"), row))


def _all_decision_rows(conn: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    columns = [item[0] for item in conn.execute(RESULT_SQL).description]
    raw_rows = conn.fetchall()
    return [
        {column: _normalized_value(value) for column, value in zip(columns, row)}
        for row in raw_rows
    ]


def run_lab(records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Run all PIT views in memory and return deterministic rows and manifest."""
    records = read_fixture() if records is None else records
    conn = _connect(records)
    try:
        rows = _all_decision_rows(conn)
    finally:
        conn.close()

    rows_bytes = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    query_bundle = FUNDAMENTAL_SQL + "\n" + RESULT_SQL
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    decisions = [
        {
            "decision_id": row["decision_id"],
            "decision_at": row["decision_at"],
            "fundamental_record_id": row["fundamental_record_id"],
            "fundamental_revision_id": row["fundamental_revision_id"],
            "symbol": row["symbol"],
            "symbol_revision_id": row["symbol_revision_id"],
            "universe_instrument_ids": row["universe_instrument_ids"],
            "universe_revision_ids": row["universe_revision_ids"],
            "membership_revision_ids": row["membership_revision_ids"],
            "split_revision_id": row["split_revision_id"],
            "feature_record_id": row["feature_record_id"],
            "feature_previous_record_id": row["feature_previous_record_id"],
            "label_record_id": row["label_record_id"],
        }
        for row in rows
    ]
    manifest = {
        "manifest_version": 1,
        "fixture_sha256": _fixture_hash(records),
        "code_sha256": code_hash,
        "query_sha256": hashlib.sha256(query_bundle.encode("utf-8")).hexdigest(),
        "parameters": {
            "availability_predicate": "available_at <= decision_at",
            "fundamental_order": "period_end DESC, available_at DESC, revision_id DESC",
            "revision_tie_breaker": "lexicographically greatest revision_id",
            "business_interval": "[effective_from, effective_to)",
            "calendar_timezone": "America/New_York",
            "feature_boundary": "event_at <= decision_at and available_at <= decision_at",
            "label_boundary": "next open session, event_at > decision_at; evaluation only",
        },
        "decisions": decisions,
        "output_sha256": hashlib.sha256(rows_bytes.encode("utf-8")).hexdigest(),
    }
    return {"rows": rows, "manifest": manifest}


def _pct(value: Any) -> str:
    return "—" if value is None else f"{value * 100:.2f}%"


def print_report(report: dict[str, Any]) -> None:
    rows = report["rows"]
    print("PIT result (synthetic; raw closes unchanged)")
    print("decision | fundamental | value | symbol | universe | feature session/close | label session/close | split comparison")
    for row in rows:
        split_text = "no factor known" if row["split_factor"] is None else (
            f"{row['split_pre_session_id']} raw {row['split_pre_raw_close']:.2f} x "
            f"{row['split_factor']:.2f} = {row['split_pre_close_post_split_units']:.2f} post-split units"
        )
        print(
            f"{row['decision_id']} | {row['fundamental_revision_id']} | {row['fundamental_value']} | "
            f"{row['symbol']} | {row['universe_instrument_ids']} | "
            f"{row['feature_session_id']} {row['feature_close_raw']:.2f} ({_pct(row['feature_return'])}) | "
            f"{row['label_session_id']} {row['label_close_raw']:.2f} ({_pct(row['label_return'])}) | {split_text}"
        )
    print("\nDeliberately wrong latest-value view (ignores decision availability):")
    for row in rows:
        print(f"{row['decision_id']} -> {row['naive_current_fundamental_revision_id']} = {row['naive_current_fundamental_value']}")
    print("\nDeterministic manifest:")
    print(json.dumps(report["manifest"], indent=2, sort_keys=True))


def main() -> None:
    print_report(run_lab())


if __name__ == "__main__":
    main()
