"""Fixture assertion: keep build_models.py's hourly-OHLCV SQL shape aligned
with the manuscript listing it translates.

manuscript/04-transformation-processing.md's `lst:sec04-hourly-ohlcv` is one
continuous `WITH ... , ... SELECT` statement split visually across two boxes
at a page break: box 1 opens `WITH candidate_hours AS (...)` with no
terminating semicolon, and box 2 continues the *same* WITH clause with a
leading comma, `, bars AS (...)`, before the final `SELECT ... FROM bars;`.
`companion/scripts/build_models.py`'s `build_fct_hourly_ohlcv` is a DuckDB
translation of that exact listing (see its docstring for the parameter-to-
value mapping) and is written to keep the identical two-CTE chain shape.

This script has no test-framework dependency (no pytest required -- see
companion/README.md's venv install list, which is optional) so it can run
with only the standard library. It performs two checks:

1. The manuscript listing itself has NOT regressed into two independent
   statements (the bug this alignment check exists to catch in the first
   place: a stray terminating `;` after `candidate_hours`, or box 2
   restarting with its own `WITH` instead of continuing with a comma).
2. build_models.py's translated query keeps the same `candidate_hours` then
   `, bars AS (...)` chain shape and still names the manuscript listing it
   translates, so an edit to the query shape without a matching translation
   note fails loudly here instead of silently diverging.

Run directly:
    python3 companion/scripts/test_manuscript_sql_alignment.py

Exits 0 and prints PASSED on success; raises AssertionError (exit 1) with a
descriptive message on any drift.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
BUILD_MODELS = SCRIPTS_DIR / "build_models.py"
MANUSCRIPT = SCRIPTS_DIR.parents[1] / "manuscript" / "04-transformation-processing.md"

LISTING_ANCHOR = "{#lst:sec04-hourly-ohlcv}"
LISTING_WINDOW_CHARS = 3000  # generous slice covering both boxes + prose


def _read(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"expected file not found: {path}")
    return path.read_text(encoding="utf-8")


def check_manuscript_listing_shape() -> None:
    """lst:sec04-hourly-ohlcv must remain one CTE chain, not two independent
    statements."""
    text = _read(MANUSCRIPT)
    assert LISTING_ANCHOR in text, (
        f"manuscript listing anchor {LISTING_ANCHOR!r} not found in "
        f"{MANUSCRIPT} -- has lst:sec04-hourly-ohlcv been renamed or removed?"
    )
    start = text.index(LISTING_ANCHOR)
    listing_text = text[start : start + LISTING_WINDOW_CHARS]

    assert "WITH candidate_hours AS (" in listing_text, (
        "lst:sec04-hourly-ohlcv's first box must open with "
        "`WITH candidate_hours AS (`"
    )
    assert "SELECT * FROM candidate_hours;" not in listing_text, (
        "lst:sec04-hourly-ohlcv regression: box 1 must NOT terminate the "
        "statement with a standalone `SELECT * FROM candidate_hours;` -- "
        "that closes the WITH clause before `bars` can be appended, so box "
        "2 (which references `candidate_hours`) would no longer parse as "
        "part of the same statement"
    )
    assert re.search(r"\n,\s*bars AS \(", listing_text), (
        "lst:sec04-hourly-ohlcv's second box must continue the same WITH "
        "clause with a leading comma (`, bars AS (`), not restart with its "
        "own `WITH` keyword"
    )
    assert not re.search(r"\nWITH bars AS \(", listing_text), (
        "lst:sec04-hourly-ohlcv regression: box 2 must not open a second "
        "`WITH` -- that would make it a new, independent statement in which "
        "`candidate_hours` is out of scope and undefined"
    )
    assert "Runnable with adaptation" in listing_text or (
        "Runnable with adaptation"
        in text[max(0, start - 1000) : start]
    ), (
        "lst:sec04-hourly-ohlcv's classification note should say "
        "'Runnable with adaptation' now that the statement parses as one "
        "continuous query -- if you intentionally reclassified it, update "
        "this assertion to match"
    )


def check_build_models_shape() -> None:
    """build_models.py's DuckDB translation must mirror the same two-member
    WITH chain shape as the manuscript listing."""
    text = _read(BUILD_MODELS)
    assert "candidate_hours AS (" in text, (
        "build_models.py must keep a `candidate_hours` CTE mirroring "
        "lst:sec04-hourly-ohlcv's first box"
    )
    assert re.search(r",\s*bars AS \(", text), (
        "build_models.py must continue with `, bars AS (` (same WITH "
        "clause, leading comma), mirroring lst:sec04-hourly-ohlcv's second "
        "box -- if you changed this to a separate statement or a new "
        "`WITH`, the translation has diverged from the manuscript shape"
    )
    assert "lst:sec04-hourly-ohlcv" in text, (
        "build_models.py must keep a comment naming lst:sec04-hourly-ohlcv "
        "so the translation stays traceable to the manuscript listing it "
        "implements"
    )


def main() -> int:
    check_manuscript_listing_shape()
    check_build_models_shape()
    print(
        "PASSED: build_models.py's hourly-OHLCV SQL shape matches "
        "manuscript listing lst:sec04-hourly-ohlcv (candidate_hours, "
        "then , bars AS (...) continuing the same WITH clause)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
