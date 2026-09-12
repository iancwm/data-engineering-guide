# Companion path

A small, smoke-tested reference implementation of the guide's capstone
trade pipeline, independent of the LaTeX build. It exercises the exact
lifecycle the guide teaches:

```text
fixture -> normalized raw envelope -> partitioned Parquet
-> DuckDB curated_trades -> deduplicated trade model
-> hourly OHLCV -> quality and reconciliation checks
```

It requires **no credentials, network access, Kafka, Airflow, cloud
storage, or a distributed engine** -- everything runs locally against a
bounded, hand-authored fixture using DuckDB's Python API.

## Why plain DuckDB SQL, not a dbt project

`manuscript/04-transformation-processing.md`'s `lst:sec04-deduplicate-trades`
listing is written as a dbt model (using `{{ ref(...) }}` and
`{% if is_incremental() %}`). This companion path reimplements that exact
SQL logic -- the `ROW_NUMBER() OVER (PARTITION BY ...)` dedup and the
lookback-windowed incremental filter -- as portable DuckDB SQL, translating
only the two dbt-specific constructs (see `scripts/build_models.py`'s
module docstring for the exact mapping). A minimal dbt project would be a
heavier, slower-to-verify way to satisfy the same "smoke-tested with
documented local fixtures and dependencies" bar the guide's own editorial
principles set for a **Runnable with adaptation** classification.

## What each script does

| Script | Stage |
|---|---|
| `scripts/load_raw.py` | Reads `fixtures/trades_sample.jsonl`, assigns a synthetic monotonically-increasing `ingested_at` (standing in for real arrival order), normalizes each row into the capstone's raw event envelope shape, and writes Hive-partitioned Parquet under `output/raw/event_date=.../`. |
| `scripts/build_curated.py` | Materializes `curated_trades` in `output/curated.duckdb` over the partitioned Parquet via `read_parquet(..., hive_partitioning=true)`. |
| `scripts/build_models.py` | Runs the translated `lst:sec04-deduplicate-trades` dedup query to build `fct_trades`, the translated `lst:sec04-hourly-ohlcv` aggregation to build `fct_hourly_ohlcv`, then the translated `lst:sec06-dbt-tests` checks as plain `SELECT COUNT(*)` assertions. |
| `scripts/run_all.py` | Orchestrates the three stages above in order (importing their functions, not shelling out, so a failure raises a clear Python traceback) and prints a final `PASSED`/`FAILED` line. |

## The fixture

`fixtures/trades_sample.jsonl` is 49 hand-authored synthetic BTCUSDT trade
events spanning three UTC hours (02:00, 03:00, 04:00 on 2026-09-07),
covering:

- normal in-order trades across all three hours;
- one exact duplicate delivery (`source_trade_id` 100005, redelivered as
  the very last line in the file with a later synthetic `ingested_at`, to
  exercise dedup by "latest arrival wins");
- one out-of-order arrival pair (a 03:58 trade delivered before a 03:56
  trade);
- one late-arriving row for the 02:00 hour, delivered only after the
  03:00 and 04:00 hours have already mostly arrived, to exercise the
  late-data lookback window.

## Running it

```bash
cd <this-repo-clone>
python3 -m venv companion/.venv
companion/.venv/bin/pip install duckdb==1.1.3 pytest==8.3.4
companion/.venv/bin/python companion/scripts/run_all.py
```

Expect a final `PASSED` line and exit code 0. `output/` (the Parquet files
and `curated.duckdb`) is regenerated from scratch on every run and is
git-ignored, like `.venv/`.

## Build-inertness

Nothing under `companion/` is referenced by `publication.yaml`,
`manuscript/order.txt`, or any `fragments/*.tex` file -- it cannot affect
the LaTeX build or the compiled PDF.
