"""Orchestrate the companion path end-to-end and print a PASSED/FAILED summary.

    fixture -> normalized raw envelope -> partitioned Parquet
    -> DuckDB curated_trades -> deduplicated trade model
    -> hourly OHLCV -> quality and reconciliation checks

Imports each stage's functions directly (rather than shelling out) so a
failure raises a Python exception with a clear traceback. No credentials,
network, Kafka, Airflow, cloud storage, or a distributed engine are
required -- everything runs against the local bounded fixture.

Usage:
    companion/.venv/bin/python companion/scripts/run_all.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_curated  # noqa: E402
import build_models  # noqa: E402
import load_raw  # noqa: E402


def _reset_output() -> None:
    """Start from a clean output/ each run, so build_fct_trades sees a
    genuine first load (no fct_trades left over from a prior run) rather
    than exercising the incremental-lookback branch by accident."""
    output_dir = Path(__file__).resolve().parents[1] / "output"
    if output_dir.exists():
        shutil.rmtree(output_dir)


def main() -> int:
    _reset_output()
    print("== Step 1/3: load_raw (fixture -> normalized raw envelope -> partitioned Parquet) ==")
    rows = load_raw.load_fixture_rows()
    load_raw.write_partitioned_parquet(rows)

    print("\n== Step 2/3: build_curated (partitioned Parquet -> DuckDB curated_trades) ==")
    con = build_curated.main()

    print("\n== Step 3/3: build_models (dedup, hourly OHLCV, quality checks) ==")
    try:
        build_models.run(con)
    finally:
        con.close()

    print("\nPASSED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 -- surface any stage failure clearly
        print(f"\nFAILED: {exc}")
        sys.exit(1)
