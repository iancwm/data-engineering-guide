"""Fixture -> normalized raw envelope -> partitioned Parquet.

Reads the bounded JSONL fixture (companion/fixtures/trades_sample.jsonl),
assigns each row a monotonically-increasing synthetic `ingested_at` based on
its position in the file (standing in for real arrival order, since a static
fixture has no live clock), normalizes it into the capstone's raw event
envelope shape (matching manuscript/02-ingestion.md's
`lst:sec02-raw-event-envelope` field names: exchange_name, asset_symbol,
source_trade_id, event_timestamp, ingested_at, price, quantity), derives an
`event_date` partition column from `event_timestamp` in UTC, and writes the
result as Hive-partitioned Parquet under `companion/output/raw/`.

No credentials, network, or external services -- everything reads and
writes local files via DuckDB's Python API.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = REPO_ROOT / "companion" / "fixtures" / "trades_sample.jsonl"
RAW_OUTPUT_DIR = REPO_ROOT / "companion" / "output" / "raw"

# Synthetic arrival clock: each fixture row "arrives" 100ms after the previous
# one, in file order. This is what makes the duplicate-redelivery and
# late-arriving rows near the end of the fixture actually land last.
ARRIVAL_EPOCH = datetime(2026, 9, 7, 2, 0, 0, tzinfo=timezone.utc)
ARRIVAL_STEP = timedelta(milliseconds=100)


def load_fixture_rows() -> list[dict]:
    rows = []
    with FIXTURE_PATH.open() as f:
        for line_number, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            ingested_at = ARRIVAL_EPOCH + ARRIVAL_STEP * line_number
            event_dt = datetime.strptime(
                raw["event_timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"
            ).replace(tzinfo=timezone.utc)
            rows.append(
                {
                    "event_id": (
                        f"{raw['exchange_name']}:{raw['asset_symbol']}:"
                        f"{raw['source_trade_id']}:{line_number}"
                    ),
                    "schema_version": 1,
                    "exchange_name": raw["exchange_name"],
                    "asset_symbol": raw["asset_symbol"],
                    "source_trade_id": raw["source_trade_id"],
                    "event_timestamp": event_dt.isoformat(),
                    "ingested_at": ingested_at.isoformat(),
                    "price": raw["price"],
                    "quantity": raw["quantity"],
                    "event_date": event_dt.date().isoformat(),
                }
            )
    return rows


def write_partitioned_parquet(rows: list[dict]) -> None:
    RAW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(
        """
        CREATE TABLE raw_events (
            event_id VARCHAR,
            schema_version INTEGER,
            exchange_name VARCHAR,
            asset_symbol VARCHAR,
            source_trade_id BIGINT,
            event_timestamp TIMESTAMP,
            ingested_at TIMESTAMP,
            price DECIMAL(20, 8),
            quantity DECIMAL(20, 8),
            event_date DATE
        )
        """
    )
    con.executemany(
        """
        INSERT INTO raw_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                r["event_id"],
                r["schema_version"],
                r["exchange_name"],
                r["asset_symbol"],
                r["source_trade_id"],
                r["event_timestamp"],
                r["ingested_at"],
                r["price"],
                r["quantity"],
                r["event_date"],
            )
            for r in rows
        ],
    )
    con.execute(
        f"""
        COPY raw_events TO '{RAW_OUTPUT_DIR.as_posix()}'
        (FORMAT PARQUET, PARTITION_BY (event_date), OVERWRITE_OR_IGNORE)
        """
    )
    counts = con.execute(
        "SELECT event_date, COUNT(*) FROM raw_events GROUP BY 1 ORDER BY 1"
    ).fetchall()
    con.close()
    print(f"Wrote {len(rows)} raw events to {RAW_OUTPUT_DIR}")
    for event_date, count in counts:
        print(f"  event_date={event_date}: {count} rows")


def main() -> None:
    rows = load_fixture_rows()
    write_partitioned_parquet(rows)


if __name__ == "__main__":
    main()
