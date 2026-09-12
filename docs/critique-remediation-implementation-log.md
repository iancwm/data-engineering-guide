# Critique Remediation Implementation Log

**Spec:** `docs/critique-remediation-spec.md`
**Plan:** `docs/superpowers/plans/2026-09-12-critique-remediation.md`
**Branches:** Tasks 1–7 (original attempt) and the plan's own progress
analysis landed on `feat/chatgpt-critique-remediation`, merged to `main` via
PR #2. Task 7's fix loop and Tasks 8–9 landed on
`claude/data-engineering-guide-spec-pqi0p2`. This document closes out the
spec per the plan's Task 10.

## Two consecutive clean release builds (Task 10, Step 1)

```
run 1: passed v1.0
blocking diagnostics: []
total diagnostics: 24

run 2: passed v1.0
blocking diagnostics: []
total diagnostics: 24
```

Both runs used `rm -rf build && setup.sh build/.venv && reportkit build
--mode combined --profile release` from a genuinely empty output directory,
back to back. The 24 non-blocking diagnostics are pre-existing warning-only
entries (unchanged in count and kind across both runs).

## Acceptance criteria re-check (Task 10, Step 2)

| Criterion | Result |
|---|---|
| Two consecutive clean combined release builds | Pass (above) |
| Strict diagnostics: no fatal/overflow/clipping/unresolved-reference/duplicate-label/unresolved-sentinel | 0 blocking diagnostics in either run |
| No visible raw `\label{` markup, no draft footer | 0 label leaks; 0 pages mention "draft" |
| All pages and affected figures reviewed at A4 print size and grayscale | 76/76 pages reviewed (Task 7); see the visual review log |
| Every runnable listing passes its documented fixture smoke test | `companion/scripts/run_all.py` prints `PASSED` (run twice) |
| Companion path completes from fixture to validated OHLCV output | 49 raw events -> 48 deduplicated trades -> 3 hourly OHLCV bars, all quality checks pass |
| Final capstone figure agrees with the manuscript's named artifacts/grains/controls/consumers | Task 6: `source -> producer/broker -> raw_trades + manifest -> curated_trades + catalog -> stg/fct/OHLCV`, five explicit Data path stages |
| Implementation log records fixes, removals, reclassifications, workarounds, deferred issues | This document |

Figure/table/listing counts: 22 figure fragments (`ls fragments/*.tex \|
wc -l`), 36 unique table+listing hypertargets (26 tables + 10 listings,
`grep -oh 'hypertarget{(tbl\|lst):[a-zA-Z0-9_-]*}' build/combined/body*.tex
\| sort \| uniq -d` returns nothing, confirming no duplicates).

## Per-task summary

### Task 1 — Clean, release-profile combined build (`731e268`)

Root-caused the `\@writefile`/`\contentsline` fatal to a stale
`build/combined/` output directory reused across incompatible runs, not a
ReportKit defect — reproduced clean from an empty directory. Added a
`profiles: release:` section to `publication.yaml` (`version: v1.0`) to
drop the `draft` footer marker. Documented the required `build/.venv` setup
step and the always-build-into-an-empty-directory workaround in
`README.md`. Recorded both as deferred-upstream notes in
`docs/reportkit-known-issues.md` (never edited the engine repo itself).

### Task 2 — Retry-state figure edge/label collision (`7a1f261`)

Widened the two `retrying`<->`running` transition arcs to asymmetric bend
angles (25°/35°, up from a colliding symmetric 15°/15°) and dropped the
duplicate "retry" label from the return edge. Confirmed at 200 DPI: no
collision, exactly one "retry" label.

### Task 3 — Caption-label leakage (`433416a`)

Pandoc converts this manuscript with `raw_tex` disabled, so a bare
`\label{...}` in `Table:`/`Listing:` caption text was escaped to literal
text instead of executing. Replaced across all 36 (26 table + 10 listing)
captions at the time with the supported Pandoc fenced-Div id wrapper (`:::
{#tbl:...}` / `::: {#lst:...}`), rendering as `\hypertarget{...}`. Zero
leakage, zero duplicate ids, independently confirmed.

### Task 4 — Stale README fragment count (`ea0e685`)

14 -> 23 (later 22, see Task 5).

### Task 5 — Redundant ingestion-semantics figure (`a852214`)

Removed `fragments/fig-sec02-ingestion-semantics.tex` (a tall, purely
linear 8-node flow) after confirming its teaching content — checkpoint,
retry, dedup before an idempotent sink — is fully covered by
`fig-sec02-delivery-retry-dedup.tex` plus the dedicated
backpressure/CDC-vs-polling figures, and that the surrounding prose in
`02-ingestion.md` survives the removal unchanged. Figure count: 23 -> 22.

### Task 6 — Capstone figure artifact naming (`d4e0fa7`)

The Data path lane conflated the producer/broker process with the
`raw_trades + manifest` artifact it produces into one "producer and
broker" node. Inserted a new column so the lane now reads `source ->
producer/broker -> raw_trades + manifest -> curated_trades + catalog ->
stg/fct/OHLCV` — five explicit stages — widening the swimlane's internal
`width` from the plan's literal `12.2` to `14.7` after finding the literal
value causes real box overlap at `columns=6` (verified in a scratch build;
this internal coordinate cannot cause page overflow, per
`reportkit-diagrams.sty`'s `\resizebox`-to-`\textwidth` mechanism).
One pre-existing, not-introduced-here diagonal `laneflow{hourly}{serve}`
edge crossing some lane-node text was noted and deliberately left
unchanged (not this task's scope).

### Task 7 — A4/grayscale visual remediation pass (`15f85fd`, then fix-loop resolved on this branch)

Rendered and reviewed all 76 pages of the combined PDF at 200 DPI
grayscale (full log at
`docs/superpowers/plans/2026-09-12-critique-remediation-visual-review-log.md`).
Confirmed the spec's Finding #6 (a suspected duplicate OHLCV query) was
already resolved — only one OHLCV listing exists in the source.

Found two genuine page-break defects: `lst:sec02-websocket-producer`'s
`run_forever()` reconnect loop was severed from its `retries = 0` init line
by a page break, and `lst:sec04-hourly-ohlcv`'s `WITH candidate_hours AS
(...)` CTE broke mid-`WHERE`-clause. The original fix (commit `15f85fd`)
split each listing into two separately-id'd/captioned listings. A
dispatched reviewer found this introduced two problems: the SQL split's
second half (`-bars`) referenced `candidate_hours`, a CTE that only existed
in the separate `-candidates` listing, so it was not independently valid
SQL as committed; and the two splits together raised the listing count
from the plan's 10-listing baseline to 12, against the plan's explicit "no
net new visual count" Global Constraint. A third, related finding: the
Illustrative lead-in's hedge ("Streaming engines express this with
different syntax; the policy is the portable idea") was dropped in the
same pass that began claiming independent validity.

**Resolution (this branch, commit "fix: resolve Task 7 fix-loop
findings...")**: both splits were redone. Each listing keeps its original
single `#lst:` id and caption, now wrapping **two** fenced code blocks
instead of two separately-captioned listings. Pandoc still renders each
fenced block as its own LaTeX `Highlighting`/`Verbatim` box regardless of
how many share one Div, so the page break still falls cleanly between the
two boxes (re-rendered and confirmed at 200 DPI on both page pairs) without
a second id. Both listings are now framed explicitly as "one script shown
in two boxes," not two independently-runnable snippets, removing the
correctness claim entirely. Listing count is back to 10. The dropped hedge
sentence was restored verbatim. Full ruling and rationale recorded in
`docs/critique-remediation-progress-2026-09-12.md` §2 and §5.

### Task 8 — Smoke-tested companion path (this branch)

Added `companion/` (Python + DuckDB, no dbt, no external services):
`fixtures/trades_sample.jsonl` (49 hand-authored synthetic BTCUSDT trade
events across 3 UTC hours, including one exact duplicate redelivery, one
out-of-order arrival pair, and one late-arriving row for an
otherwise-closed hour), `scripts/load_raw.py` (fixture -> normalized raw
envelope -> Hive-partitioned Parquet), `scripts/build_curated.py`
(partitioned Parquet -> DuckDB `curated_trades`), `scripts/build_models.py`
(the manuscript's exact `lst:sec04-deduplicate-trades` dedup query and
`lst:sec04-hourly-ohlcv` aggregation, translated from dbt Jinja to plain
DuckDB SQL, plus `lst:sec06-dbt-tests`'s checks as `SELECT COUNT(*)`
assertions), and `scripts/run_all.py` (orchestrates all three, prints
`PASSED`/`FAILED`).

Result: 49 raw events -> 48 deduplicated trades (the one redelivered
duplicate collapses to its latest-arrival copy) -> 3 hourly OHLCV bars, all
10 quality checks pass. Run twice, both clean. Confirmed build-inert (`grep
-rn "companion" publication.yaml manuscript/order.txt fragments/` returns
nothing beyond the one prose sentence added to
`manuscript/04-transformation-processing.md`'s classification note). The
manuscript's `lst:sec04-deduplicate-trades` **Runnable with adaptation**
classification is now verified rather than aspirational, with a pointer to
`companion/`.

### Task 9 — Quant-ready foundation audit (this branch)

Audited the manuscript against the spec's seven-item checklist. Five items
were already present with confirmed locations (source identifiers,
event/receipt/landing timestamps, explicit units, correction/duplicate/
ordering policies, and reproducible interval reconstruction /
transformation versions — the last now also backed concretely by
`companion/`). Two genuine gaps were closed with small, labelled additions:

- **Look-ahead-bias guidance**: added a short paragraph next to the hourly
  OHLCV aggregation in `04-transformation-processing.md` connecting the
  late-data lookback window to look-ahead bias for any backtest or feature
  pipeline reading from a fully-corrected `fct_trades` — keep the
  finalized-vs-still-open distinction (`is_final`) rather than serving only
  the latest value per hour.
- **Market-calendar/session semantics**: added a "Session semantics" bullet
  to the ingestion project contract in `02-ingestion.md` explaining that
  this capstone (a continuously-traded spot crypto pair) has no market
  calendar to model, while flagging it as a required project-contract
  input for a future listed-exchange quant edition.

No new figures/tables/listings.

### Task 10 — Final acceptance pass (this document)

Two consecutive clean `--profile release` builds; every acceptance
criterion re-checked (table above); this log written; spec status line
flipped.

## Local workarounds adopted

- `publication.yaml`'s `profiles: release: version: v1.0` section (Task 1)
  — required to drop the `draft` footer marker; `--profile release` has no
  effect without it.
- Always `rm -rf build` before rebuilding, and re-run
  `publication_pipeline/scripts/setup.sh build/.venv` afterward — a stale
  `build/combined/` reused across runs produces an opaque
  `\@writefile`/`\contentsline` fatal, and a missing `build/.venv` produces
  `RK_RENDER_FAILED` (PyMuPDF not installed). Both documented in
  `README.md` and `docs/reportkit-known-issues.md`.
- Pandoc fenced-Div ids (`::: {#tbl:...}` / `::: {#lst:...}`) in place of
  the unsupported bare `\label{...}` caption suffix (Task 3), since this
  pipeline runs Pandoc with `raw_tex` disabled.
- A page-break fix at the manuscript level (two fenced code blocks under
  one retained `#lst:` id/caption) in place of a raw `\needspace{...}`
  command, which cannot be written directly in `manuscript/*.md` for the
  same `raw_tex`-disabled reason (Task 7).

## Deferred upstream (ReportKit engine issues)

Recorded in `docs/reportkit-known-issues.md`, not filed as GitHub issues
against `report-kit` yet:

1. `reportkit build --mode combined` never clears `--output-root` before
   compiling; reusing a dirty prior-run directory can produce an opaque
   fatal `\@writefile`/`\contentsline` error with no diagnostic pointing at
   the actual cause (stale output directory).
2. `render_pdf_pages.py`'s `ModuleNotFoundError` for PyMuPDF (when
   `<output-root>/.venv` doesn't exist yet) surfaces as a bare traceback
   under `RK_RENDER_FAILED` without naming the fix (`setup.sh`).

## Known reproducibility caveat

The implementation plan's Global Constraints note that
`/home/iancwm/git/report-kit` (the sibling engine repo used during the
original Tasks 1–7 work) had a dirty working tree at commit
`65270362b2f49a38e256e7e1fa4f45a45b1638d4`
(`v1.3.0-118-g6527036`), not a clean tag — builds in that phase necessarily
ran against that exact working tree. This branch's later work (Task 7's
fix loop, Tasks 8–10) ran the combined build in a separate environment
against a freshly cloned `report-kit` checkout with the pinned Debian
Trixie toolchain packages (`pandoc`, `texlive-*`) installed via `apt` on
Ubuntu 24.04 rather than the toolchain's own pinned Debian-snapshot base
image — the resulting `reportkit.lock` toolchain fingerprint therefore does
not match the Dockerfile's pinned `REPORTKIT_TOOLCHAIN_FINGERPRINT` (this
is a reproducibility note, not a build failure: `status: passed` in every
run regardless). Neither environment is under this plan's control; both
are recorded here as known limitations rather than something this pass can
fix.
