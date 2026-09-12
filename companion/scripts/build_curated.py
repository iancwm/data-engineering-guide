"""Partitioned Parquet -> DuckDB `curated_trades`.

Opens (or creates) `companion/output/curated.duckdb` and materializes a
`curated_trades` table over the partitioned raw Parquet written by
`load_raw.py`, via `read_parquet(..., hive_partitioning=true)`. This is the
durable, queryable landing point that `build_models.py`'s dedup/OHLCV SQL
reads from -- matching the guide's `source -> raw_trades + manifest ->
curated_trades` handoff (manuscript/09-learning-path.md's capstone figure).
"""

from __future__ import annotations

from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_GLOB = REPO_ROOT / "companion" / "output" / "raw" / "**" / "*.parquet"
DB_PATH = REPO_ROOT / "companion" / "output" / "curated.duckdb"


def build_curated_trades(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        f"""
        CREATE OR REPLACE TABLE curated_trades AS
        SELECT
            event_id,
            schema_version,
            exchange_name,
            asset_symbol,
            source_trade_id,
            event_timestamp,
            ingested_at,
            price,
            quantity
        FROM read_parquet('{RAW_GLOB.as_posix()}', hive_partitioning=true)
        """
    )
    row_count = con.execute("SELECT COUNT(*) FROM curated_trades").fetchone()[0]
    print(f"curated_trades: {row_count} rows (includes raw redelivery duplicates)")


def main() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(DB_PATH))
    build_curated_trades(con)
    return con


if __name__ == "__main__":
    main().close()
