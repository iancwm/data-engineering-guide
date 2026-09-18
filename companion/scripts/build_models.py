"""DuckDB SQL: deduplicated trade model + hourly OHLCV + quality checks.

Translates manuscript/04-transformation-processing.md's
`lst:sec04-deduplicate-trades` (the `ROW_NUMBER() OVER (PARTITION BY
exchange_name, asset_symbol, source_trade_id ORDER BY ingested_at DESC,
event_timestamp DESC)` dedup) and `lst:sec04-hourly-ohlcv` (the late-data
lookback window and hourly aggregation) from dbt Jinja to plain DuckDB SQL,
so that manuscript listing's "Runnable with adaptation" claim is
smoke-tested rather than aspirational. Only the two dbt-specific constructs
are translated:

- `{{ ref('curated_trades') }}` becomes the `curated_trades` table directly.
- `{% if is_incremental() %} ... {% endif %}` becomes a plain SQL WHERE
  clause, guarded in Python to run unconditionally when `fct_trades` does
  not exist yet (first load) and applied only on a subsequent incremental
  run.

Everything else -- the exact column casts, the `ROW_NUMBER()` ordering, the
`arg_min`/`arg_max` OHLC aggregation, the allowed-lateness `is_final` flag --
is copied verbatim from the manuscript listings, so this script is
demonstrably testing the guide's own SQL, not a different query that merely
does something similar. `build_fct_hourly_ohlcv` below also mirrors
`lst:sec04-hourly-ohlcv`'s two-box CTE *chain shape*: `candidate_hours`
followed by a `, bars AS (...)` continuing the same `WITH` clause, exactly as
the manuscript's two boxes now do across their page break. See that
function's docstring for the parameter-to-value translation, and
`test_manuscript_sql_alignment.py` in this directory for a fixture assertion
that fails loudly if this shape and the manuscript listing's shape drift
apart.

Then runs the checks translated from `lst:sec06-dbt-tests` (unique trade
key, non-null timestamps, positive price/quantity, `high_price >=
low_price`, positive `trade_count`) as plain `SELECT COUNT(*)` queries that
must each return 0.
"""

from __future__ import annotations

import duckdb

LOOKBACK_INTERVAL = "3 days"
ALLOWED_LATENESS = "15 minutes"


def _table_exists(con: duckdb.DuckDBPyConnection, name: str) -> bool:
    row = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [name],
    ).fetchone()
    return bool(row and row[0] > 0)


def build_fct_trades(con: duckdb.DuckDBPyConnection) -> None:
    """Deduplicated trade staging model (translates lst:sec04-deduplicate-trades)."""
    incremental = _table_exists(con, "fct_trades")
    lookback_where = (
        f"""WHERE event_timestamp >= (
            SELECT MAX(event_timestamp) FROM fct_trades
        ) - INTERVAL '{LOOKBACK_INTERVAL}'"""
        if incremental
        else ""
    )
    dedup_query = f"""
        -- Grain: one row per (exchange_name, asset_symbol, source_trade_id).
        WITH ranked AS (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY exchange_name, asset_symbol, source_trade_id
                    ORDER BY ingested_at DESC, event_timestamp DESC
                ) AS row_rank
            FROM curated_trades
            {lookback_where}
        )
        SELECT
            exchange_name,
            asset_symbol,
            source_trade_id,
            event_timestamp,
            ingested_at,
            CAST(price AS DECIMAL(20, 8)) AS price,
            CAST(quantity AS DECIMAL(20, 8)) AS quantity
        FROM ranked
        WHERE row_rank = 1
    """
    if incremental:
        # "The destination must merge or replace the same lookback partitions
        # idempotently" -- delete the rows the lookback query could have
        # touched, then re-insert its (deduplicated) result.
        con.execute(
            f"""
            DELETE FROM fct_trades
            WHERE event_timestamp >= (
                SELECT MAX(event_timestamp) FROM fct_trades
            ) - INTERVAL '{LOOKBACK_INTERVAL}'
            """
        )
        con.execute(f"INSERT INTO fct_trades {dedup_query}")
        mode = "incremental (lookback merge)"
    else:
        con.execute(f"CREATE TABLE fct_trades AS {dedup_query}")
        mode = "first load (unconditional)"
    row_count = con.execute("SELECT COUNT(*) FROM fct_trades").fetchone()[0]
    print(f"fct_trades: {row_count} rows ({mode})")


def build_fct_hourly_ohlcv(con: duckdb.DuckDBPyConnection) -> None:
    """Hourly OHLCV with late-data lookback (translates lst:sec04-hourly-ohlcv).

    Mirrors the corrected manuscript listing's two-box CTE chain shape
    exactly -- `candidate_hours` then a `, bars AS (...)` that continues the
    *same* `WITH` clause (leading comma, not a new `WITH`) -- so this
    translation cannot silently diverge from the manuscript SQL's shape
    without this comment (and `test_manuscript_sql_alignment.py`, which
    checks both files) going stale.

    Translated constructs (everything else -- the `arg_min`/`arg_max` OHLC
    picks, `GROUP BY 1, 2, 3`, and the `is_final` boundary -- is copied
    verbatim from the manuscript listing):

    - `FROM stg_trades` becomes `FROM fct_trades`: this companion path's
      already-materialized deduplicated trade table is the manuscript's
      `stg_trades` staging grain (see the capstone handoff
      `curated_trades -> stg_trades -> fct_trades -> fct_hourly_ohlcv`).
    - `:run_hour_utc - INTERVAL '3 hours'` / `:run_hour_utc + INTERVAL
      '1 hour'` (the per-run hour-plus-lookback window bind parameter) is
      dropped from the WHERE bounds here: `run_all.py` builds the whole
      bounded fixture in one pass rather than one incremental hourly run, so
      `candidate_hours` below is that same filter's degenerate case with no
      hour boundary applied -- every row currently in `fct_trades`. The
      manuscript listing keeps the parameterized, single-hour form; this is
      the "process every hour at once" case of the identical query shape.
    - `:watermark_utc` becomes `(SELECT MAX(event_timestamp) FROM
      fct_trades)`, i.e. "the latest event this run has seen" -- a concrete,
      data-derived stand-in for "now" so the fixture needs no wall-clock
      dependency.
    """
    con.execute(
        f"""
        CREATE OR REPLACE TABLE fct_hourly_ohlcv AS
        WITH candidate_hours AS (
            SELECT * FROM fct_trades
        )
        , bars AS (
            SELECT
                exchange_name,
                asset_symbol,
                date_trunc('hour', event_timestamp) AS hour_start_utc,
                arg_min(price, (event_timestamp, source_trade_id)) AS open_price,
                max(price) AS high_price,
                min(price) AS low_price,
                arg_max(price, (event_timestamp, source_trade_id)) AS close_price,
                sum(quantity) AS total_quantity,
                count(*) AS trade_count
            FROM candidate_hours
            GROUP BY 1, 2, 3
        )
        SELECT
            *,
            hour_start_utc < (
                SELECT MAX(event_timestamp) FROM fct_trades
            ) - INTERVAL '{ALLOWED_LATENESS}' AS is_final
        FROM bars
        """
    )
    row_count = con.execute("SELECT COUNT(*) FROM fct_hourly_ohlcv").fetchone()[0]
    print(f"fct_hourly_ohlcv: {row_count} hourly bars")


def run_checks(con: duckdb.DuckDBPyConnection) -> None:
    """Translates lst:sec06-dbt-tests into plain SELECT COUNT(*) assertions."""
    checks = [
        (
            "fct_trades: exchange_name not null",
            "SELECT COUNT(*) FROM fct_trades WHERE exchange_name IS NULL",
        ),
        (
            "fct_trades: asset_symbol not null",
            "SELECT COUNT(*) FROM fct_trades WHERE asset_symbol IS NULL",
        ),
        (
            "fct_trades: source_trade_id not null",
            "SELECT COUNT(*) FROM fct_trades WHERE source_trade_id IS NULL",
        ),
        (
            "fct_trades: event_timestamp not null",
            "SELECT COUNT(*) FROM fct_trades WHERE event_timestamp IS NULL",
        ),
        (
            "fct_trades: price not null and positive",
            "SELECT COUNT(*) FROM fct_trades WHERE price IS NULL OR NOT (price > 0)",
        ),
        (
            "fct_trades: quantity not null and positive",
            "SELECT COUNT(*) FROM fct_trades WHERE quantity IS NULL OR NOT (quantity > 0)",
        ),
        (
            "fct_trades: unique (exchange_name, asset_symbol, source_trade_id)",
            """
            SELECT COUNT(*) FROM (
                SELECT exchange_name, asset_symbol, source_trade_id, COUNT(*) AS n
                FROM fct_trades
                GROUP BY 1, 2, 3
                HAVING COUNT(*) > 1
            )
            """,
        ),
        (
            "fct_hourly_ohlcv: hour_start_utc not null",
            "SELECT COUNT(*) FROM fct_hourly_ohlcv WHERE hour_start_utc IS NULL",
        ),
        (
            "fct_hourly_ohlcv: high_price not null and >= low_price",
            """
            SELECT COUNT(*) FROM fct_hourly_ohlcv
            WHERE high_price IS NULL OR NOT (high_price >= low_price)
            """,
        ),
        (
            "fct_hourly_ohlcv: trade_count not null and positive",
            """
            SELECT COUNT(*) FROM fct_hourly_ohlcv
            WHERE trade_count IS NULL OR NOT (trade_count > 0)
            """,
        ),
    ]
    failures = []
    for name, query in checks:
        violations = con.execute(query).fetchone()[0]
        status = "ok" if violations == 0 else f"FAILED ({violations} violations)"
        print(f"  check: {name} -> {status}")
        if violations != 0:
            failures.append(name)
    if failures:
        raise AssertionError(f"Quality checks failed: {', '.join(failures)}")


def run(con: duckdb.DuckDBPyConnection) -> None:
    build_fct_trades(con)
    build_fct_hourly_ohlcv(con)
    print("Running quality checks (translated from lst:sec06-dbt-tests):")
    run_checks(con)


if __name__ == "__main__":
    from pathlib import Path

    db_path = Path(__file__).resolve().parents[1] / "output" / "curated.duckdb"
    connection = duckdb.connect(str(db_path))
    run(connection)
    connection.close()
