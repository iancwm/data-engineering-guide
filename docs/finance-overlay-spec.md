# Quant Finance Overlay Specification

**Status:** Proposed; implementation has not started

**Date:** 2026-09-26

**Source:** `.superpowers/finance-overlay-spec-scratch.md`, reviewed against the current manuscript, companion, and publication contract.

**Scope:** This publication repository. Keep the general data engineering book and its BTCUSDT capstone intact; add an optional, clearly marked finance learning path within the existing publication and a small offline companion extension.

## 1. Purpose and editorial boundary

Teach the data engineering controls that make a small historical market-data research exercise reproducible: which observation was available at a decision time, which instrument it referred to, how later corrections change the current view, how missing feed messages are detected, and what evidence a replay used. The worked finance case is educational. It must not imply that a toy backtest predicts returns, models executions, or satisfies a regulatory or model-risk program.

The main book remains a generalist guide. Finance material should occupy short, optional subsections in existing Sections 2-9, with a route in the Reader's Roadmap and Section 9. The new runnable work belongs under `companion/finance/` and uses local synthetic fixtures. This makes the material appear in the ReportKit PDF while keeping the existing 49-event BTCUSDT quick start and its output contract unchanged.

The current source of truth is `manuscript/order.txt`: front matter, Sections 1-11, and no finance chapter. Publication figures are `[[REPORTKIT-VISUAL:fig:<slug>]]` sentinels paired with `fragments/fig-<slug>.tex`; raw Mermaid files in a new directory would not become PDF figures. Follow `publication-guidelines.md`: manuscript H1s remain the eleven numbered sections, instructional topics use H2, listings are classified and labelled, and figures have semantic labels, captions, sources, and accessible descriptions.

## 2. Disposition of the scratch proposals

| Proposal | Decision and reason |
| --- | --- |
| Keep the general DE spine and BTCUSDT capstone | **Keep.** They already teach event/arrival time, deduplication, OHLCV, reconciliation, contracts, and local reproducibility. |
| Add PIT/bitemporal reasoning, reference data, universe history, corporate actions, features/labels, replay, quality, and evidence | **Keep, scoped.** These are the central finance gaps. Give each one a concrete failure mode and an explicit time/grain contract. |
| Add an optional second equities/futures/fundamentals track | **Narrow to synthetic equities and one fundamental series.** Futures roll rules, FX conventions, full order books, and vendor feeds would multiply scope without an executable teaching dataset. List them as follow-on study, not promises for this pass. |
| Create eleven `quant-overlay/*.md` modules and link them from each existing section | **Reject as the primary publication structure.** Those files are outside `manuscript/order.txt` and would not enter the PDF. Eleven modules also duplicate Sections 1-11 and the glossary/references. Integrate concise material into the existing ordered manuscript and put longer lab instructions in the companion. |
| Require a diagram, runnable listing, two exercises, interview question, checklist, glossary, and references in every module | **Reject as a quota.** This would add repetitive material and many diagrams without distinct learning purposes. Use at most two mechanism figures, one complete runnable PIT lab, one small feed-gap lab, and focused checkpoints where they teach a new decision. |
| Add eight separate labs with DuckDB, Python, dbt, YAML, and SQL | **Consolidate to two offline labs.** The companion already uses pinned DuckDB and direct Python scripts; a new dbt project and multiple disconnected mini-pipelines add setup and alignment work without improving the main PIT lesson. |
| Use Mermaid/Graphviz/PlantUML files as publication figures | **Reject for the PDF path.** The current pipeline consumes LaTeX fragments at sentinels. Add only figures that are implemented as matching fragments and checked at A4 print size. |
| Copy `is_final` into PIT bars as proof of historical availability | **Reject.** The current `fct_hourly_ohlcv` is rebuilt from current deduplicated trades; its `is_final` flag is a window state on that rebuilt view, not a stored history of what was visible earlier. Preserve observation and revision times separately. |
| Treat a split/dividend factor and “total return” as one generic adjustment | **Reject.** State the adjustment convention and distinguish raw price, split-adjusted price, dividend cash flow, and a total-return series. The lab may show a split; dividend/merger handling stays conceptual. |
| Prescribe snapshot repair for every sequence gap | **Reject as a universal algorithm.** Sequence scope and recovery differ by feed; teach gap detection and a protocol-dependent repair decision. For example, Nasdaq MoldUDP64 specifies retransmission requests, while some NYSE feeds publish refresh snapshots. |
| Claim immutable evidence or regulatory compliance from a local lab | **Reject.** Require reproducible manifests and append-only synthetic revisions in the example; explain that production retention, tamper evidence, access audit, and legal controls require separate system design and review. |
| Add low-latency/alpha-decay architecture and lambda/kappa comparisons | **Defer the trading-system depth.** Section 8 already compares architecture patterns and cost. Add one decision table on research freshness, replay cost, and operating latency; avoid unmeasured alpha or exchange-colocation claims. |

## 3. Technical contract for the teaching case

Use one synthetic equities example throughout. Include two stable `instrument_id` values, historically changing `symbol` mappings, a membership interval including an eventual delisting, two versions of one fundamental observation (original and later correction), a two-for-one split, daily raw prices, and a short sequence-numbered message stream with a gap. No live market, broker, or EDGAR access is needed. Dates and prices are deliberately invented and labelled synthetic.

Every example must name **grain** and **clock**. Separate:

- `event_at`: when an exchange event occurred;
- `received_at`: when this pipeline received it;
- `available_at`: the earliest time the chosen source and pipeline could use the value (conservative in a toy fixture, explicitly assumed); and
- `effective_from`/`effective_to` or `period_end`: the time interval or reporting period the value describes.

Do not call a report's `period_end` its publication time. Do not use `ingested_at` as proof of public availability. A vendor's later delivery can make pipeline availability later than public release. State which clock a decision-time query actually uses, and record the source version and revision identifier. The synthetic fixture should supply all times explicitly instead of deriving knowledge from file order or the wall clock.

**Point-in-time selection.** At decision time `t`, filter records to `available_at <= t`; for a particular logical observation key, choose the most recent *available* revision with a deterministic tie breaker. Then apply its business-valid interval or report-period rule as appropriate. If a valid interval was itself revised later, derive the interval from versions visible at `t`; do not use today's retroactively shortened `effective_to`. For fundamentals, select the latest `period_end <= t` that has an available observation, then its latest available revision. Missing eligible observations stay missing. State whether decisions at an exact release timestamp can consume the release (`<=`) and use the same boundary in tests.

**Instrument and universe selection.** Join through stable `instrument_id`, not ticker alone. Apply membership, mapping, delisting, and any correction using records available by `t`. Show a current-only universe selecting an impossible historical set as a failing case. No claim that the toy membership data represents a vendor-quality historical universe.

**Bars and replay.** An event-time bar for a past decision must use only constituent trades with `available_at <= t` and the bar definition published by `t`. A current rebuilt bar, even with `is_final=true`, is not a PIT snapshot. Keep the existing OHLCV output as a current analytical view and explain this distinction in Section 4. The finance lab can use daily prices to keep the PIT demonstration short; it does not need a production streaming bar store. Replay advances a simulated decision clock over fixed synthetic sessions, queries only eligible versions at each decision, and records selected source IDs and code/fixture version in its run manifest. It must not silently use corrected final tables.

**Features and labels.** A feature window ends by the decision boundary and uses only values available by that time. A label window begins after the decision, is computed for evaluation only, and is never joined into a decision feature. Define non-overlap explicitly. The lab demonstrates data selection and a toy factor/label table, not strategy performance or execution quality.

**Corporate actions and calendars.** Preserve raw prices. Show one documented split-adjusted comparison and its effective/availability times; do not apply a future split to an earlier decision before its information was available or silently mutate historical raw rows. Explain that dividends require cash-flow and reinvestment assumptions and that total-return and execution prices answer different questions. Use a short synthetic session calendar with an explicit timezone, session IDs, and a closed day; do not turn the lab into a full exchange calendar implementation.

**Feed gaps.** Partition sequence checks by the sequence domain defined in the example (feed, channel, session), distinguish duplicate/reordered packets from missing numbers, and emit a gap record with expected and received sequence. The lab marks affected output as incomplete and shows a deterministic recovery choice over local fixture data. Describe snapshots or retransmission only as feed-specific options, not an API the fixture actually calls.

## 4. Publication changes

| Location | Required addition | Prior material to reuse |
| --- | --- | --- |
| `manuscript/00-frontmatter.md` and Section 1 | Add an optional finance route and a one-paragraph scope note. | Reader's Roadmap and lifecycle. |
| Section 2 | Add source/receipt/availability clocks and protocol-dependent sequence-gap handling. | `fig:sec02-event-time-watermark`, raw envelope, delivery and late-data sections. |
| Section 3 | Add append-only revision storage, a stable instrument key, PIT membership, and historical symbology. | Storage layers, current table definitions. |
| Section 4 | Add a correct PIT selection explanation and feature/label timeline. Amend the current paragraph that presents `is_final` as sufficient for historical reconstruction. Include one short classified SQL listing whose local equivalent is exercised in the lab. | Type 2 discussion, join cardinality, OHLCV. |
| Section 5 | Add simulated-time replay and a run manifest with fixed fixture, code version, parameters, and selected input revisions. | Backfill and retry sections. |
| Section 6 | Add market-data quality checks: sequence gaps, invalid prices, stale/crossed quotes when quotes exist, correction counts, and vendor-count limits. Distinguish checks possible on the synthetic trade-only fixture from quote-specific checks discussed only in prose. | Reconciliation flow and quality gates. |
| Section 7 | Add a PIT data-contract example with field meanings, clock source, correction policy, owner, and availability SLO; avoid promising legal or regulatory compliance. | Contract YAML and lineage. |
| Section 8 | Add a compact research/replay/production decision table for freshness, latency, cost, and evidence. | Existing architecture and cost discussion. |
| Section 9 | Add finance as a choice within optional Milestone 7, pointing to the new companion lab with an artifact, failure exercise, and interview question. | Existing optional-track framing and capstone. |
| Sections 10-11 | Add only new glossary terms and cited primary references; retain existing alphabetic/style conventions. | Existing glossary and bibliography. |

Keep callouts and cross-references concise. Do not add a second full finance capstone architecture to the generalist figure or expand Section 9's required milestones. Use semantic IDs, never hard-coded figure numbers from the scratch document; figure numbers can change at build time. Prefer explanation and a compact table where another figure would repeat an existing mechanism.

Add at most two new figures, each with a manuscript sentinel and matching `fragments/fig-<slug>.tex`:

1. `fig:sec04-pit-revision-timeline`: show effective/reporting time, source availability, later correction, and two decision times; caption must state which revision each decision can see. This extends the reasoning of `fig:sec02-event-time-watermark` without pretending the two clocks are identical.
2. `fig:sec02-finance-gap-repair`: show a scoped sequence gap, quarantine/incomplete state, and a labelled protocol-specific recovery decision. Omit if a compact sequence table teaches it more clearly at A4 width.

Both figures need standalone captions, `source={Author's synthesis.}`, descriptive text, grayscale-safe labels, and review at final PDF size. Add no decorative quota figures.

## 5. Companion deliverables

Add a self-contained optional directory, without changing `companion/scripts/run_all.py` or the 49-event fixture:

```text
companion/finance/
  README.md
  fixtures/
    pit_case.jsonl
    feed_sequence.jsonl
  scripts/
    run_pit_case.py
    check_feed_sequence.py
  tests/
    test_pit_case.py
    test_feed_sequence.py
```

The implementation may simplify this layout if fewer files make the fixture easier to audit. Use the existing documented Python/DuckDB environment, pin any new dependency, and require no credentials, network, proprietary data, dbt, Kafka, or Airflow. `README.md` must state exact commands, fixture grain, clock assumptions, expected outputs, and why the lab is educational rather than a trading simulator.

`run_pit_case.py` should build a temporary or gitignored DuckDB database, make two or more decisions around the correction and delisting, select the eligible fundamental and universe at each decision, construct a feature table and future-only labels, apply the stated split convention to an example comparison, and emit a small run manifest. The result should include selected revision IDs so the PIT choice is inspectable. Keep a deliberately wrong current-value query beside the correct result for contrast; it is a teaching output, not a production code path.

`check_feed_sequence.py` should read the synthetic stream, report a known gap within its declared sequence domain, and show that the affected segment stays incomplete until the fixture's recovery record is applied. Keep the recovery algorithm explicitly tied to the invented feed contract. Do not represent it as implementation of Nasdaq, NYSE, or any vendor protocol.

Use targeted tests for the failure modes that are easy to get wrong:

- A pre-correction decision sees the original value; a post-correction decision sees the revision; today's latest value must fail the pre-correction expectation.
- An unavailable observation, a revision timestamp exactly at the decision boundary, and two candidate revisions with the same availability time have deterministic outcomes.
- A historical mapping or membership change does not erase an earlier member; a decision after delisting excludes it.
- Feature inputs cannot postdate the decision; labels begin strictly after it; no duplicate rows appear after PIT joins.
- Raw prices remain unchanged and the stated split factor is applied only where the example's convention and decision-time availability call for it.
- The sequence test separates a gap from a duplicate and does not cross session/channel boundaries.
- Repeating the labs with the same fixtures and code yields the same selected IDs, outputs, and manifest content apart from an explicitly documented run-generated field.

## 6. Implementation sequence and acceptance

1. Add the synthetic fixture and PIT query first; use a small table in the companion README to prove the expected revision selected at each decision. Validate the time inequalities and uniqueness before writing book prose.
2. Add the finance lab, sequence-gap lab, and their focused tests. Keep the original companion smoke test passing unchanged.
3. Add short manuscript subsections and correct the Section 4 `is_final` claim. Every runnable manuscript listing must have the same demonstrated semantics as the companion implementation.
4. Add only the figure or figures whose mechanisms remain hard to understand in text; verify sentinel/fragment pairing and captions.
5. Update the Reader's Roadmap, glossary, references, and any publication-guideline figure inventory affected by the change. Build from a **fresh output directory** using the ReportKit clone; inspect the rendered A4 pages for code width, figure legibility, cross-references, and raw markup.

Completion requires: (a) both finance labs run offline and their targeted tests pass; (b) the existing `companion/scripts/run_all.py` still reports its original 49 raw / 48 deduplicated / 3 bar result; (c) the PIT example proves different pre- and post-correction answers and exposes the selected revision IDs; (d) no row chosen by a decision uses `available_at > decision_time`; (e) every manuscript figure sentinel has exactly one matching fragment and the ReportKit validation/build passes; and (f) the rendered PDF makes the optional route and the limits of the toy backtest clear.

## 7. Sources to verify during implementation

Use primary technical sources for any feed or tool behavior described in the manuscript, and record access dates for mutable pages:

- [DuckDB documentation: FROM and JOIN clauses](https://duckdb.org/docs/stable/sql/query_syntax/from), for the behavior and limits of `ASOF JOIN`. A two-clock PIT lookup may require an explicit staged query; do not assume one ASOF predicate solves it.
- [Nasdaq MoldUDP64 protocol specification](https://nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/moldudp64.pdf), for one example of sequence-gap retransmission.
- [NYSE XDP Options Client Specification](https://www.nyse.com/publicdocs/nyse/data/XDP_Options_Client_Specification_v1.4a.pdf), for an example of refresh-based recovery. Cite the exact feed specification whenever a specific behavior is taught.
- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), if fundamentals are connected to real filings in prose. Explain that a reporting period, filing acceptance, API dissemination, and local receipt are different clocks; the lab still uses synthetic records.

Do not add a source to Section 11 merely because it appears here. Cite it when a specific manuscript claim depends on it.
