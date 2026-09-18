# Section 9 - A Learning Path and Project Roadmap

Data engineering is best learned by building and operating a system, not by finishing a checklist of tools. This path is organized as seven outcome-based milestones rather than a calendar. Readers have different available time, so no milestone names a week or a month; move to the next milestone when you can produce its artifact and answer its interview question, not when a clock runs out.

Every milestone builds on the same capstone: a small BTCUSDT trade pipeline that recurs across Sections 2 through 7. Milestones 1 through 6 are the required path to a job-ready, generalist portfolio project. Milestone 7 is a single optional deep dive, chosen from six tracks; it is not a required seventh step for every reader.

The learning-roadmap figure gives the shape of that progression before the milestones spell out what to understand, do, prove, break, and be able to explain at each one.

[[REPORTKIT-VISUAL:fig:sec09-learning-roadmap]]

## Milestone 1: Foundation

**Understand.** The lifecycle from Section 1 (source, ingestion, storage, transformation, orchestration, quality, governance, serving) as a loop with cross-cutting concerns, not a one-way pipe. Grain: what one row represents, and why `curated_trades`, `fct_trades`, and `fct_hourly_ohlcv` each have a different grain over the same underlying trades. Event time versus ingestion time versus processing time. The difference between a file (one of the `raw_trades` Parquet objects under `companion/output/raw/`), a table (`curated_trades`, a queryable structure with a schema, a catalog entry, and a location), a job (a script such as `load_raw.py` that produces or updates a table), and a data product (`fct_hourly_ohlcv`, served under an owner and a freshness target).

**Do.** Re-read Section 1's lifecycle figure and Section 4's grain discussion, then write one sentence stating the grain of `curated_trades`, `fct_trades`, and `fct_hourly_ohlcv`, and one sentence stating what `dim_asset` and `dim_exchange` add that the fact tables do not.

**Artifact.** The four grain statements, saved as a short markdown note kept with the portfolio repository.

**Break it.** Swap two of your grain statements and try to write a query that would silently return a wrong answer as a result — for example, counting rows in `fct_hourly_ohlcv` to answer "how many trades happened." Explain in one sentence why the count is wrong.

**Interview question.** "What's the difference between a file, a table, and a data product? Give a concrete example of each from something you built."

## Milestone 2: Local Pipeline

**Understand.** How a bounded, credential-free path exercises the whole lifecycle end to end: fixture to normalized raw envelope to partitioned Parquet to DuckDB `curated_trades` to a deduplicated trade model to hourly OHLCV to quality checks. This is the same quick-start companion path introduced earlier in this guide; this milestone is about running it and explaining every stage, not re-deriving it from scratch.

**Do.** Run `companion/scripts/run_all.py` and read its stage-by-stage console output. Then open `load_raw.py`, `build_curated.py`, and `build_models.py` and match each function to the manuscript listing it implements (`lst:sec04-deduplicate-trades`, `lst:sec04-hourly-ohlcv`, `lst:sec06-dbt-tests`).

**Artifact.** The terminal transcript ending in `PASSED`, plus a short paragraph, in your own words, explaining why `curated_trades` and `fct_trades` have different row counts.

**Break it.** Edit `build_models.py` so the dedup query no longer filters `WHERE row_rank = 1`, then rerun. The fixture's one exact duplicate (`source_trade_id` 100005, redelivered as the file's last line) means a correct run leaves `fct_trades` at 48 rows against `curated_trades`'s 49; confirm you can explain why removing the filter should make `fct_trades` also read 49, and why seeing 48 again after restoring the filter is the actual proof that dedup works — not just that the script ran.

**Interview question.** "Your row count in the raw layer doesn't match the row count in the cleaned layer. Walk me through how you'd determine whether that's a bug or expected behavior."

## Milestone 3: Reliable Models

**Understand.** Deduplication by a stable business key (`exchange_name`, `asset_symbol`, `source_trade_id`), not by an ingestion artifact like arrival order alone. The difference between a full rebuild and an incremental model bounded by a lookback window. Why hourly aggregation needs both an explicit grain and a late-data boundary. This ties to Section 4's `stg_trades` to `fct_trades` to `fct_hourly_ohlcv` chain; the companion script's `fct_trades` plays the staging role the manuscript's dbt model assigns to `stg_trades`.

**Do.** In `build_models.py`, change `LOOKBACK_INTERVAL` from `3 days` to something too short, such as `1 hour`, then run `build_models.run(con)` a second time against the same DuckDB file (skip `run_all.py`'s reset) so the incremental branch actually executes. Compare `fct_trades`'s row count before and after.

**Artifact.** A short before/after note: the changed value, the two row counts, and one or two sentences explaining what a too-short lookback window risks dropping.

**Break it.** Duplicate a trade that is not `source_trade_id` 100005 in `companion/fixtures/trades_sample.jsonl` (same id, a new line), rerun the pipeline, and confirm `fct_trades` still holds one row per unique trade key rather than growing by one.

**Interview question.** "How would you design an incremental model so a late-arriving correction isn't silently dropped by too short a lookback window?"

## Milestone 4: Operational Control

**Understand.** The difference between a schedule and a trigger; retryable versus deterministic failures; why a backfill must run the same code path as a normal run; how tests, reconciliation, and quarantine gate publication before bad data reaches a consumer, building on Section 2's `raw_trades` + manifest and Section 3's `curated_trades` + catalog handoffs. Ties to Section 5's Airflow-style DAG (`retries`, `retry_delay`, `execution_timeout`) and Section 6's quarantine path (`quarantine/trades/{event_date}/{event_hour}/...`) and dbt-style tests, which the companion path runs as plain `SELECT COUNT(*)` assertions in `run_checks` — the same checks a real deployment would wire into an alerting table such as `quality_alerts`.

**Do.** Read Section 5's DAG listing and Section 6's `lst:sec06-dbt-tests`. Then insert a negative `quantity` into the fixture and rerun `run_all.py` to see `run_checks` raise `AssertionError` and the script exit with `FAILED: ...`.

**Artifact.** The failing run's console output, showing which named check failed, plus one paragraph explaining why this specific failure should not consume a retry budget.

**Break it.** Delete `companion/output/raw/` after `build_curated.py` has run, then invoke `build_models.py` directly instead of through `run_all.py`, and observe what happens when a downstream stage's expected upstream table is gone. Compare that to what a manifest and a quarantine path are meant to prevent in a real deployment.

**Interview question.** "A nightly job fails at 3 a.m. Its policy is three retries with exponential backoff, and all three fail with the same error. What do you check first, and how do you decide whether to page someone?"

## Milestone 5: Consumer Contract

**Understand.** What a data contract states — owner, grain, freshness target, quality rules, and a compatibility policy — and why lineage matters when a producer changes a field. Ties to Section 7's `lst:sec07-data-contract` for `curated_trades` (owner `market-data-platform`, a stated grain, a freshness target, and `compatibility: backward-compatible additions only`).

**Do.** Write a contract for `fct_hourly_ohlcv` modeled on Section 7's `curated_trades` contract: an owner, the grain (`one row per (exchange_name, asset_symbol, hour_start_utc)`), a freshness target, and a compatibility rule for adding a new OHLCV field.

**Artifact.** The contract file, saved as `contracts/fct_hourly_ohlcv.yml` alongside the capstone repository's existing `contracts/curated_trades.yml`.

**Break it.** Propose renaming `trade_count` to `n_trades` and check the change against your own `change_policy`. Decide, using only what your contract states, whether that change can ship without warning downstream consumers.

**Interview question.** "How do you decide whether a schema change is backward-compatible, and who needs to sign off before it ships?"

## Milestone 6: Portfolio Evidence

**Understand.** What makes a project legible to someone who did not build it: an architecture diagram, a README that states scope and how to run it, visible test output, one incident or runbook example, and a written record of a non-obvious design decision — a "why," not just a "what." The capstone architecture figure is the cumulative view of the handoffs from Milestones 2 through 5, with named data assets and separate data, control, trust, and consumer paths.

[[REPORTKIT-VISUAL:fig:sec09-capstone-architecture]]

**Do.** Assemble the repository below: run the companion path and capture its `PASSED` transcript, write a runbook entry for the failure you diagnosed in Milestone 4, and write one design-decision record (decision, alternatives considered, why this one) for a choice you made in Milestones 3 through 5.

**Illustrative.** A small repository can make the lifecycle visible without committing to one orchestrator or cloud provider:

::: {#lst:sec09-capstone-repo-tree}
Listing: Minimal capstone repository tree.

```text
crypto-lakehouse/
|-- ingestion/{producer.py, consumer.py}
|-- models/{staging.sql, fct_hourly_ohlcv.sql}
|-- orchestration/hourly_workflow.py
|-- tests/{fixtures/, test_contracts.yml}
|-- contracts/{curated_trades.yml, fct_hourly_ohlcv.yml}
|-- docs/{runbook.md, decisions.md}
|-- config.example.yml
`-- README.md
```
:::

The tree is a thinking aid, not a required framework layout. Secrets belong in the runtime's secret store or an ignored local file, never in the repository.

**Artifact.** The five items above in one repository: `README.md`, an architecture diagram, the captured test transcript, `docs/runbook.md`, and `docs/decisions.md`.

**Break it.** Hand the repository to someone who has not read this guide and time how long it takes them to answer "what does this pipeline produce, and how would I know if it broke?" using only the README and the diagram. Any question they cannot answer from those two artifacts is a documentation gap, not a gap in their own knowledge.

**Interview question.** "Walk me through a project on your resume in three minutes: what it does, one thing that broke, and what you'd change with more time."

## Milestone 7: Optional Specialization

Milestone 6 already produces a job-ready, generalist portfolio project. Milestone 7 is one optional deep dive, chosen from the six tracks below — not a checklist to complete. The project also naturally bridges to three kinds of consumers: an analytics consumer who queries the documented hourly mart, an ML consumer who builds point-in-time features from the trade facts, and a finance or quant consumer who needs a reproducible UTC interval with source identifiers and correction history. Three of the six tracks below correspond directly to those three consumers; pick at most one.

- **Batch analytics.** Deepen dbt-style modeling and BI serving: add a rolling-window feature to `fct_hourly_ohlcv` and a small dashboard on top of it.
- **Streaming.** Replace the fixture read with a real broker, such as a local Kafka or Redpanda instance, and rebuild `fct_trades` as a continuously updated model; ties to Section 2's delivery-semantics material.
- **Platform.** Containerize the companion path, run the Section 5 DAG shape against a real orchestrator (Airflow or Dagster) with real schedules and retries, and replace local Parquet with object storage.
- **Reliability and quality.** Build out full reconciliation across source, raw, curated, and aggregate counts (Section 6), wire the checks into an alerting table such as `quality_alerts`, and add a replay mechanism to the quarantine path.
- **ML data.** Build a point-in-time feature table from `fct_trades` for a simple model, such as predicting next-hour volatility, taking care to avoid label leakage from the future.
- **Finance or quant data.** Reproduce one UTC interval exactly from `fct_hourly_ohlcv`, including source identifiers, correction history, and the quality evidence a trading desk would require before trusting a bar.

**Artifact.** One additional deliverable specific to the chosen track: a streaming demo, a running orchestrator UI, a reconciliation dashboard with alerting, a feature table, or a reproduced-interval report.

**Interview question.** "Why did you go deeper on this track instead of the others, and what trade-off did you learn about that the generalist path wouldn't have taught you?"

## Further Learning {#sec09-further-learning}

- GitHub Docs. [“About READMEs.”](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) *GitHub Docs*. Accessed 18 September 2026. A concrete guide to writing the README that Milestone 6 treats as required portfolio evidence.
- Martin, Donne. [“The System Design Primer.”](https://github.com/donnemartin/system-design-primer) *GitHub repository*. Accessed 18 September 2026. A widely used, continually maintained study guide for the scalability and trade-off discussions that come up in data engineering and platform interviews.
- Google. [“Postmortem Culture: Learning from Failure.”](https://sre.google/sre-book/postmortem-culture/) *Site Reliability Engineering*. Accessed 18 September 2026. A model for the blameless incident write-up Milestone 6's runbook entry is meant to resemble, and a common interview topic in its own right.
- Awesome Data. [“Awesome Public Datasets.”](https://github.com/awesomedata/awesome-public-datasets) *GitHub repository*. Accessed 18 September 2026. A maintained, cross-domain list of open datasets — transit, weather, government, finance, and more — for a next project once the crypto capstone is complete.
