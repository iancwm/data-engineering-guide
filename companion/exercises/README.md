# Checkpoint Answer Key

Sections 2 through 8 of the guide each end with a short applied checkpoint
(a `practice` or `checklist` callout) that asks you to inspect, predict,
modify, or diagnose the shared BTCUSDT capstone pipeline rather than recall a
definition. The questions are printed in the manuscript; the answers are kept
here instead, so working through a checkpoint before reading this file is
worth more than reading both at once.

Each entry below repeats the question for context, then gives a concise
answer. Where a checkpoint references a specific listing or script, it means
the one in this repository -- try reproducing the scenario against
`companion/` before checking the answer.

## Section 2 -- Checkpoint: Trace a Lost Acknowledgement

**Question.** The producer publishes a trade event to the `raw_crypto_trades`
topic. The broker durably appends it and sends an acknowledgement, but the
acknowledgement is lost before the producer receives it. The producer's
bounded-backoff reconnect logic treats this as a failed send and republishes
the same event.

1. Does this create a gap or a duplicate in the raw landing?
2. Which stage is responsible for making that outcome harmless: the broker,
   the raw landing write, or the load into `curated_trades`?
3. Which field in the event envelope makes that stage's job possible?

**Answer.** A lost ACK produces a duplicate, not a gap -- the producer cannot
tell "never received" from "received but ACK lost," so at-least-once
delivery means it resends the same trade, and the append-only raw landing is
expected to hold that retry. It is not made harmless at the broker or
raw-write stage; it becomes harmless when `curated_trades` is built, because
the merge/upsert there uses the logical key to collapse both copies into one
row. The field that makes this possible is `source_trade_id` (combined with
`exchange_name` and `asset_symbol`) -- the deterministic composite key set in
the envelope -- not `ingested_at` or the broker offset.

## Section 3 -- Checkpoint: Partition Pruning Under a Different Filter

**Question.** `curated_trades` is partitioned by `event_date` and
`event_hour`, both derived from `event_timestamp`. Take the query in Listing
`sec03-parquet-partition-query` and rewrite its `WHERE` clause to filter on
`ingested_at` instead of `event_timestamp`, keeping the same UTC bounds.

1. Predict which partitions the engine can skip for the rewritten query.
2. Explain why the answer differs from the original query.
3. Name one situation, from the late-data material in Section 2, where
   `event_timestamp` and `ingested_at` would place the same row in different
   partitions.

**Answer.** The rewritten query gets no partition pruning at all --
`event_date`/`event_hour` are derived from `event_timestamp`, and
`ingested_at` is not the partition key, so the engine has no partition-level
metadata to match the filter against and must scan every partition (or fall
back to weaker file-level statistics). This differs from the original query,
which filters directly on the partitioning column and lets the engine skip
files outside the requested hour. A late-arriving trade is the concrete
case: its `event_timestamp` falls in an earlier hour's partition, but its
`ingested_at` is close to processing time, so the two timestamps land in
different partitions for the same row.

## Section 4 -- Practice: Diagnose a Shortened Lookback Window

**Question.** The capstone's incremental staging job rebuilds `stg_trades`
from `curated_trades` using a 3-day event-time lookback (the `WHERE
event_timestamp >= CURRENT_TIMESTAMP - INTERVAL '3 days'` guard in
`lst:sec04-deduplicate-trades`). A teammate shortens it to 30 minutes to cut
compute cost. Two days later, a correction for a trade that first landed in
`curated_trades` last week is redelivered with a later `ingested_at`.

1. Will this correction ever reach `fct_trades`? Why or why not?
2. Which values in `fct_hourly_ohlcv` end up wrong as a result, and would
   they look obviously wrong or "plausible but wrong"?
3. Name one quality check from this project's companion path (Section 6)
   that would catch this, and one failure mode it would not catch.

**Answer.** No. The dedup CTE only re-selects `curated_trades` rows whose
`event_timestamp` falls inside the 30-minute lookback window, and the
correction's `event_timestamp` (last week's original trade time) is far
outside that window in every subsequent run, so it is never scanned again --
the correction is silently dropped forever, not merely delayed. The affected
hour's `open_price`, `close_price`, `high_price`, `low_price`,
`total_quantity`, and `trade_count` in `fct_hourly_ohlcv` are computed from
the original, uncorrected trade only, and the result looks entirely
plausible -- valid prices, reasonable volume -- with no null, error, or
obviously-off value to flag it. The uniqueness test on `(exchange_name,
asset_symbol, source_trade_id)` in `fct_trades` (Section 6) would catch a
case where a duplicate slips through instead of a clean replace, but it does
nothing for a row that is silently dropped and never arrives at all -- only
a reconciliation check comparing `curated_trades` counts against
`fct_trades` counts per lookback window would surface a missing row.

## Section 5 -- Checkpoint: Should This Failure Retry?

**Question.** In the hourly capstone DAG (Listing `sec05-capstone-dag`), the
`validate_and_publish` task fails because it finds duplicate trade
identifiers inside the hour's partition. The DAG's `default_args` give every
task 2 retries with a 5-minute delay.

1. Predict what happens across both retry attempts.
2. Decide whether this failure should consume the retry budget, and justify
   it using the transient-versus-deterministic distinction from the Retries
   and Timeouts section.
3. State what should happen instead: which downstream step should stay
   blocked, and who should be notified.

**Answer.** Both retries fail for the same reason -- duplicate trade
identifiers are a deterministic data problem, not a transient one, so
retrying the unchanged input just burns 10 minutes before the run still ends
in failure. The retry budget should not be spent on it; the task should fail
fast. The correct response is to keep downstream publication blocked for
that hour, alert the owning team with the affected data interval (per the
Failure Handling control loop), and route the interval to repair/backfill
once the duplicate source is fixed, rather than letting the default retry
policy mask a deterministic defect.

## Section 6 -- Checkpoint: Does the Interval Reconcile?

**Question.** For one finalized UTC hour, the pipeline reports 100,240
received raw attempts, 15 records quarantined for a malformed price field,
225 duplicate accepted attempts from an at-least-once retry, and 100,000
distinct trade keys in `stg_trades`. `fct_hourly_ohlcv`'s `trade_count` for
that same hour is 99,940.

1. Predict whether the raw attempts, quarantined records, and duplicate
   attempts reconcile against the 100,000 distinct trade keys.
2. Decide whether the `fct_hourly_ohlcv` trade count agrees with
   `fct_trades` for the same interval, and name the reconciliation check
   that should have caught a mismatch before publication.
3. Diagnose the 60-row shortfall: is it more consistent with a quarantine
   defect, a grain mismatch, or trades that arrived after the hour was
   finalized? State which additional check you would add.

**Answer.** Yes: 100,240 raw attempts minus 15 quarantined minus 225
duplicate accepted attempts equals 100,000, matching the distinct trade-key
count in `stg_trades`, so the ingestion-side reconciliation holds. The
`fct_hourly_ohlcv` trade count of 99,940 does not agree with the 100,000
trades expected in `fct_trades` for the same hour -- a 60-row shortfall.
Because the ingestion-side reconciliation already balances, this points to a
downstream grain or timing issue rather than a source-delivery or quarantine
defect -- most likely trades that arrived after the hour was finalized but
before `fct_trades` was rebuilt, i.e. the aggregate was built before the
allowed-lateness window closed. The check to add is comparing
`sum(trade_count)` in `fct_hourly_ohlcv` against `fct_trades` for the same
closed interval, gated by the documented lookback and allowed-lateness
policy, before publishing the aggregate.

## Section 7 -- Practice: Is This Schema Change Backward-Compatible?

**Question.** The `curated_trades` contract (`lst:sec07-data-contract`)
declares `compatibility: backward-compatible additions only`. A producer
proposes two simultaneous changes: renaming `quantity` to `base_quantity`,
and changing its unit from BTC to satoshis. A downstream dashboard built on
`fct_hourly_ohlcv` sums that column into an hourly traded-volume tile.

1. Under the contract's stated compatibility rule, is this change
   backward-compatible? Why or why not?
2. If it ships without a version bump or producer notice, what does the
   dashboard's traded-volume tile show -- and would the error be obviously
   wrong, or silently "plausible but wrong"?
3. Name the two mechanics in `change_policy` (from `lst:sec07-data-contract`)
   that would need to happen before this change could ship safely.

**Answer.** No -- this is not backward-compatible. Renaming a field is not
an addition, and changing the unit from BTC to satoshis (a ~10^8 scale
change) breaks any consumer's existing interpretation of the values even if
the field name were kept. Without a version bump or notice, the dashboard
would either error (field not found) or, worse, silently sum the
renamed/rescaled values as if they were still BTC quantities, producing a
wildly inflated traded-volume tile that looks "plausible but wrong" rather
than obviously broken. To ship safely, the producer must bump the contract
version and provide a migration window, and give required owner notice
before deployment, per the `change_policy` block.

## Section 8 -- Practice: Which Platform Boundary Owns This Failure?

**Question.** The `fct_hourly_ohlcv` dashboard is showing BTC/USD prices
that are six hours old. The page loads normally and shows no error to the
viewer. Using the platform-boundaries figure, which boundary should the
on-call engineer check first -- ingestion, storage, orchestration, or
serving -- and why?

**Answer.** Check orchestration first. A dashboard that loads without error
but shows stale data is the signature of a scheduled job that stopped
running, is stuck, or silently skipped a run, not of a serving-layer bug:
serving only renders whatever `fct_hourly_ohlcv` currently holds. Confirm
whether the job that rebuilds `fct_hourly_ohlcv` actually ran and completed
on schedule. If it did, move one boundary upstream and check ingestion for
whether new `raw_trades` records are still landing; only after both come
back healthy should storage or serving be suspected.
