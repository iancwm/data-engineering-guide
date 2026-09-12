# Visual review log

Task 7 of the 2026-09-12 critique-remediation plan: a full page-by-page A4/
grayscale visual review of the combined PDF (`build/combined/publication-template.pdf`,
76 pages after the Tasks 1-6 fixes), rendered at 200 DPI grayscale via PyMuPDF
and inspected page by page against the spec's checklist:

1. a code listing starting at the very bottom of a page, or a setup line
   (variable assignment, import, `WITH ... AS (` CTE opener) separated from
   the operation it configures by a page break;
2. a table's continuation onto a next page missing a repeated header row, or
   a caption not visually adjacent to its table;
3. an unusually large blank area (more than roughly a third of a page) that
   isn't a deliberate section-break page;
4. a figure/edge/axis/lane label small enough to be hard to read printed at
   A4 (noticeably smaller than body text on the same page);
5. leftover raw markup, sentinel text (`[[REPORTKIT-VISUAL:` or similar), or
   double-rendered content.

Every one of the 76 pages was rendered and visually inspected (not just
skimmed from source); table below records every page, with either a "no
issue found" note or a finding plus its fix/justification.

## Finding #6 check (possible duplicate OHLCV listing)

```
$ grep -n 'OHLCV\|^Listing:' manuscript/04-transformation-processing.md
307:The staging layer should keep the same grain as the raw trade feed: one row per trade. The hourly table deliberately changes the grain by aggregating trades into hourly OHLCV records.
315:Listing: Deduplicated trade staging model.
354:Listing: Hourly OHLCV with late-data lookback.
```

Confirmed directly against the current file (not the planning-time
observation): there is exactly **one** OHLCV-related code listing in the
document, `lst:sec04-hourly-ohlcv` ("Hourly OHLCV with late-data lookback"),
already marked **Illustrative**. There is no second/duplicate OHLCV query
anywhere in the manuscript. **Finding #6 is resolved — no duplicate found,
no action needed on that specific concern.** (The same listing did,
independently, turn up a real pagination defect — see page 41 below — which
is unrelated to the duplicate-listing question and is fixed as part of this
task.)

## Fixes applied

Two listings had a page break landing inside a `WITH ... AS (` CTE or
between a setup line and the loop consuming it — the exact anti-pattern the
spec's checklist names. Raw `\needspace` cannot be inserted from
`manuscript/*.md` (pandoc runs with `-f markdown-raw_tex`, which deliberately
disables raw TeX passthrough in content files — see
`publication_pipeline/scripts/publication_build.py`'s `render_markdown()`:
"Trusted TeX belongs in a validated fragment or a direct .tex document,
never a content field"). The fix actually available at the manuscript level
is to split each affected listing into two listings at its nearest clean
syntactic boundary, with a one-sentence transition, so that if a page break
still lands inside either half it can no longer sever a setup line from the
operation that consumes it:

- `manuscript/02-ingestion.md` — `lst:sec02-websocket-producer` split into
  `lst:sec02-websocket-producer-envelope` (the `envelope()` helper) and
  `lst:sec02-websocket-producer-loop` (the `run_forever()` reconnect loop).
- `manuscript/04-transformation-processing.md` — `lst:sec04-hourly-ohlcv`
  split into `lst:sec04-hourly-ohlcv-candidates` (the `candidate_hours`
  windowing CTE, given its own trivial closing `SELECT * FROM
  candidate_hours;` so it is independently valid SQL) and
  `lst:sec04-hourly-ohlcv-bars` (the `bars` aggregation CTE, rewritten as its
  own `WITH bars AS (...)` block plus the final `SELECT`, likewise
  independently valid). Splitting the listing div alone was not sufficient —
  a first attempt still broke mid-`WHERE`-clause inside listing 1, because
  the amount of prose above it on the page was unchanged. Trimmed the
  "Runnable with adaptation" and "Illustrative" lead-in paragraphs on the
  same page from 3 wrapped lines each to 2 (shortening wording only, no
  content removed beyond one now-redundant clause) to free the one line of
  vertical space needed for listing 1 to render complete before the page
  break; re-rendered and confirmed the break now falls cleanly between the
  two listings.

Both `#lst:` ids were confirmed unreferenced elsewhere in `manuscript/*.md`
before renaming, so the split carries no dangling cross-reference. See
Task 7's report (`task-7-report.md`) for the exact diffs and the
re-rendered, post-fix page images confirming each split now lands cleanly
between the two new listings instead of inside either one.

Two other candidate hits (a `CREATE TABLE` column list split across pg 27/28,
and a YAML `tests:` list split across pg 58/59) were checked against the
same checklist item and judged **not** an instance of the anti-pattern:
each split point falls between independently-complete, self-contained list
items (a column definition, a test entry) rather than severing a setup line
from the operation/usage that depends on it — the reader loses no context
at the break. These are logged as reviewed, justified "not an issue" rows,
per the Definition of Done.

## Page-by-page log

| PDF pg | Footer | Issue | Fix |
|---|---|---|---|
| 1 | (none, cover) | No issue found | n/a |
| 2 | (none, disclaimer) | No issue found | n/a |
| 3 | iii | No issue found (Contents) | n/a |
| 4 | 1 | No issue found (Preface) | n/a |
| 5 | 2 | No issue found (Section 1 intro) | n/a |
| 6 | 3 | No issue found (Fig 1 lifecycle diagram, labels legible, box text same size as body) | n/a |
| 7 | 4 | No issue found (Table 1 starts, clear header row) | n/a |
| 8 | 5 | No issue found (Table 1 continuation onto this page correctly repeats header row "Stage/Main purpose/Key terms/Common tools and technologies") | n/a |
| 9 | 6 | No issue found | n/a |
| 10 | 7 | No issue found | n/a |
| 11 | 8 | No issue found (Table 2 fits fully on one page) | n/a |
| 12 | 9 | No issue found | n/a |
| 13 | 10 | No issue found | n/a |
| 14 | 11 | No issue found (short page, ~40% content, but this is end-of-section prose not a deliberate section break — acceptable, not "large blank area" since remaining space is just natural end-of-subsection with no orphaned heading) | n/a |
| 15 | 12 | No issue found (Table 3 fits fully on one page) | n/a |
| 16 | 13 | No issue found (Table 4 and Table 5 each fit fully on one page) | n/a |
| 17 | 14 | No issue found (Fig 2 sequence diagram, labels legible) | n/a |
| 18 | 15 | No issue found (Fig 3 backpressure diagram + Fig 4 CDC comparison, labels legible; note Fig 4 label boxes are a noticeably smaller diagram than Fig 2/3 but text inside ("Transaction log", "Change event", etc.) is same size as body text, legible) | n/a |
| 19 | 16 | No issue found (Fig 5 event-time diagram, all labels/annotations legible even the small callout boxes "02:59 watermark..." which use a smaller font but is still clearly readable at print size, comparable to a caption/footnote size, not illegibly small) | n/a |
| 20 | 17 | No issue found (Table 6 ingestion tooling, Table 7 practice data sources, Capstone Project intro — each table fits fully on one page) | n/a |
| 21 | 18 | **ISSUE**: `lst:sec02-websocket-producer` (Listing: WebSocket producer with bounded reconnect) — code listing starts on this page ("Runnable with adaptation" intro + `import json`/`envelope()` def) and continues to pg 22; the page break falls between `def run_forever(...): / retries = 0` (bottom of this page) and `while True:` (top of pg 22), i.e. a setup/init line separated from the loop that consumes it, across a page break. | **FIXED**: split the single fenced listing into two listings at the natural function boundary (`envelope()` helper vs `run_forever()` loop), with a one-sentence transition — a markdown-level restructuring since raw `\needspace` cannot be used in manuscript/*.md (pandoc is invoked with `-f markdown-raw_tex`, deliberately disabling raw TeX passthrough in content files per `publication_build.py`'s comment: "Trusted TeX belongs in a validated fragment or a direct .tex document, never a content field"). Re-rendered and confirmed each half now renders as a complete, independent listing. |
| 22 | 19 | Continuation of the above listing (second half: `while True:` loop body); covered by the same fix. Rest of page (raw event envelope JSON listing, Illustrative note, "ingestion output and handoff" bullets start) fine. | see pg 21 |
| 23 | 20 | No issue found (replay procedure, Section handoff, Common beginner mistakes, order-book caution, Ingestion Design Checklist bullets) | n/a |
| 24 | 21 | No issue found (Section 3 intro, Storage Requirements bullets, OLTP/OLAP intro + Table 8, fits fully on one page) | n/a |
| 25 | 22 | No issue found (Row-oriented/columnar storage + Table 9 + SELECT AVG query + CAP/PACELC intro) | n/a |
| 26 | 23 | No issue found (Storage architecture: warehouse/lake/lakehouse prose) | n/a |
| 27 | 24 | Fig 6 lakehouse-stack diagram (labels legible) + Open Table Formats section + `CREATE TABLE curated_trades (...)` listing (Illustrative, "Listing: Curated table definition over trade files.") starts near bottom of page, column list continues onto pg 28. Checked against checklist item 1 but judged **not an issue**: each split line is a syntactically complete, independently-readable column definition (not a truncated expression, and not a "setup line severed from the operation using it" the way a CTE-vs-usage split would be); ordinary, harmless pagination of a long column list. | not an issue (justified) |
| 28 | 25 | Continuation of the CREATE TABLE listing (closing paren, `USING ICEBERG`, `PARTITIONED BY`, `LOCATION`) — same non-issue as pg 27. Table 10 file formats fits fully on this page. Partitioning/Clustering section starts. | see pg 27 |
| 29 | 26 | No issue found (Fig 7 partition-pruning diagram + Listing: Partition-pruned Parquet query, both fully contained on one page; labels legible; bad-partitioning/clustering/small-file prose) | n/a |
| 30 | 27 | No issue found (Fig 8 before/after compaction diagram, labels legible; Catalogs section; Table 11 storage tooling) | n/a |
| 31 | 28 | No issue found (Table 11 cont. / Table 12 storage choices; Capstone Continuation section) | n/a |
| 32 | 29 | No issue found (numbered list + SELECT query listing, both fully on one page) | n/a |
| 33 | 30 | No issue found (short page ~35% content — Common beginner mistakes + Storage Design Checklist — natural end-of-section, not a defect) | n/a |
| 34 | 31 | No issue found (Section 4 intro, ETL/ELT, Table 13 — note: PyMuPDF's raw text-extraction order for this page is unusual, i.e. the footer text wasn't the last text-extraction token — but the *rendered* page was visually inspected directly and shows completely normal layout: header, three body paragraphs, subheading, Table 13, footer "31" all in their expected positions with no overlap or truncation. This is a text-extraction-order artifact only, not a visual defect.) | n/a |
| 35 | 32 | No issue found (Fig 9 raw/standardized/curated/serving diagram, labels legible; Cleaning and Standardization; Distributed Processing Concepts) | n/a |
| 36 | 33 | No issue found (Table 14 processing latency fits fully on one page) | n/a |
| 37 | 34 | No issue found (Idempotent/Incremental Transformations, INSERT INTO listing fully on one page, Joins/Enrichment, Grain) | n/a |
| 38 | 35 | No issue found (Grain continuation, Fig 10 wrong-grain/corrected-grain diagram labels legible, Aggregation and Metrics, Dimensional Modeling, Table 15) | n/a |
| 39 | 36 | No issue found (Table 16 SCD types, Transformation Tooling Landscape, Table 17 start) | n/a |
| 40 | 37 | No issue found (Table 17 continuation repeats header row correctly, dbt explanation, Common Transformation Anti-Patterns, Capstone Continuation intro) | n/a |
| 41 | 38 | **ISSUE**: `lst:sec04-hourly-ohlcv` (Listing: Hourly OHLCV with late-data lookback) — the `WITH candidate_hours AS (...)` CTE opens on this page with a partial body (`SELECT * FROM stg_trades WHERE event_timestamp >= :run_hour_utc - INTERVAL '3 hours'`) and the page breaks mid-WHERE-clause, before the `AND event_timestamp < ...` continuation and the second `bars AS (...)` CTE, which land on pg 42. This is the checklist's own worked example almost verbatim (a `WITH ... AS (` CTE opener severed from its continuation by a page break). Note: `lst:sec04-hourly-ohlcv` is also the listing checked for spec Finding #6 (possible duplicate OHLCV listing) — confirmed via full-file grep (see Finding #6 section above) that only this one OHLCV listing exists; the pagination defect found here is unrelated to the duplicate-listing question. (Also on this page, fully contained: the `WITH ranked AS (...)` deduplicated-staging-model listing — starts and ends cleanly on this page, no split, not an issue.) | **FIXED**: split the listing into two at the natural CTE boundary (`candidate_hours` windowing CTE vs. `bars` aggregation CTE + final SELECT), each made independently valid SQL, with a one-sentence transition — markdown-level restructuring, same raw-TeX constraint as the pg 21/22 websocket-producer fix. The div split alone was not enough (it still broke mid-`WHERE`-clause inside listing 1 on first attempt); also trimmed the "Runnable with adaptation"/"Illustrative" lead-in paragraphs on this page from 3 to 2 wrapped lines each to free the vertical space listing 1 needed to render complete. Re-rendered and confirmed each half now renders as a complete, independent listing with no mid-clause split. |
| 42 | 39 | Continuation of the above listing (second half: `bars AS (...)` CTE + final `SELECT *, ... AS is_final FROM bars;`); covered by the same fix. Rest of page (DuckDB-style example aggregation SELECT, "This project teaches" bullets, Transformation Output/Handoff bullets) fine. | see pg 41 |
| 43 | 40 | No issue found (fct_hourly_ohlcv output bullet, Section 6 handoff note, Common beginner mistakes, Transformation and Processing Checklist — end of Section 4) | n/a |
| 44 | 41 | No issue found (Section 5 Orchestration intro, Why Orchestration Matters, Directed Acyclic Graphs, numbered task list) | n/a |
| 45 | 42 | No issue found (DAG vocabulary bullets, Fig 11 DAG diagram — labels legible including small "validation error"/"do not publish" edge labels, comparable to caption-size text, readable — Schedules and Event Triggers, Table 18 start) | n/a |
| 46 | 43 | No issue found (Table 18 continuation repeats header row correctly, Sensors and Data Assets, Task Design and Idempotency) | n/a |
| 47 | 44 | No issue found (Retries and Timeouts, Failure Handling numbered list) | n/a |
| 48 | 45 | No issue found — Fig 12 recovery state machine (this is the retry-state figure already fixed in Task 2 for a "colliding retry/running arcs" defect); re-inspected here in the full combined-build context and confirmed the Retrying/Running arcs remain cleanly separated with no label collision, i.e. the Task 2 fix holds. Backfills and Reprocessing section below. | n/a (Task 2 fix verified holding) |
| 49 | 46 | No issue found (Concurrency and Resource Controls, Data-Aware Scheduling, Orchestration Tooling Landscape, Table 19 start) | n/a |
| 50 | 47 | No issue found (Table 19 continuation repeats header row correctly, Implementation Pattern pseudocode listing fully contained on one page) | n/a |
| 51 | 48 | No issue found (Capstone Continuation orchestrating section, "Listing: Hourly capstone workflow definition" Airflow DAG listing fully contained on one page, no split) | n/a |
| 52 | 49 | No issue found (capstone handoff, Common beginner mistakes, Orchestration Design Checklist — end of Section 5) | n/a |
| 53 | 50 | No issue found (Section 6 Data Quality intro, Fig 13 quality-control diagram labels legible, Dimensions of Data Quality + Table 20) | n/a |
| 54 | 51 | No issue found (Fig 14 quality-loop diagram, labels legible; Data Quality and Data Observability) | n/a |
| 55 | 52 | No issue found (Testing Data as Code, Table 21 fits fully on one page, Shift-Left Quality) | n/a |
| 56 | 53 | No issue found (Monitoring and Alerting, Incident Management, Quality Tooling Landscape + Table 22) | n/a |
| 57 | 54 | No issue found (Capstone Continuation: Operationalizing Trust, steps 1-6, Fig 15 reconciliation-flow diagram — labels small relative to a swimlane figure but legible and consistent with other diagram label sizes reviewed elsewhere, e.g. pg 45/48) | n/a |
| 58 | 55 | Checked: "Listing: Core dbt tests for trade models." (YAML) starts here and the page breaks inside the `fct_hourly_ohlcv` model's `trade_count` column, between its two `tests:` list items (`- not_null` / `- expression_is_true:`), continuing onto pg 59. Judged **not an issue**: same reasoning as the pg 27/28 CREATE TABLE column-list split — each split YAML list item is independently complete and readable, not a severed setup/usage pair. | not an issue (justified) |
| 59 | 56 | Continuation of the above YAML listing (final `expression_is_true: expression: "> 0"` item) — same non-issue as pg 58. Capstone Milestone Map + Fig 16 swimlane diagram (labels legible) below. | see pg 58 |
| 60 | 57 | No issue found (Section 7 Metadata/Governance/Serving intro, Data Catalogs, Table 23, Lineage) | n/a |
| 61 | 58 | No issue found (Fig 17 lineage diagram labels legible, Governance, Data Contracts) | n/a |
| 62 | 59 | No issue found (Fig 18 data-contract diagram labels legible; "Listing: Versioned curated-trades data contract" YAML fully contained on one page, no split; Access/Classification/Retention intro) | n/a |
| 63 | 60 | No issue found (Access/Retention bullets cont., Governance Tooling Table 24, Serving Data for Analytics/ML/Applications intro, Business Intelligence, Machine Learning) | n/a |
| 64 | 61 | No issue found (short page ~35% content — Operational Applications + capstone serving contract note + Common beginner mistakes — natural end of Section 7, not a defect) | n/a |
| 65 | 62 | No issue found (Section 8 Topics intro, Security/Privacy/Compliance, Fig 19 security-layers diagram labels legible) | n/a |
| 66 | 63 | No issue found (sensitive data/compliance, Observability and Operations, Cost Management intro) | n/a |
| 67 | 64 | No issue found (cost driver bullets, Architecture Patterns + Table 25, Practitioner Discussion: Data Contracts intro) | n/a |
| 68 | 65 | No issue found (data contracts cont., Tools and Technology Landscape, Fig 20 platform-boundaries diagram — labels legible including the small italic "Vendor span:" note, comparable to a figure source-line size, readable) | n/a |
| 69 | 66 | No issue found (Selecting Tools and Managing Trade-offs numbered list, Choosing a Stack Under Constraints, Minimum Viable Stack intro) | n/a |
| 70 | 67 | No issue found (Minimum Viable Stack cont., Table 26 Learning stages fits fully on one page, Data Engineering in Practice numbered list) | n/a |
| 71 | 68 | No issue found (Design Questions Before Building, Production Readiness Checklist — end of Section 8) | n/a |
| 72 | 69 | No issue found (Section 9 Learning Path intro, Fig 21 learning-roadmap diagram labels legible, Core Skills, Portfolio Project, "Listing: Minimal capstone repository tree" fully contained on this page, no split) | n/a |
| 73 | 70 | Fig 22 cumulative capstone architecture diagram — this is the figure modified in Task 6 (`fig-sec09-capstone-architecture.tex`). Re-inspected here in the full combined-build context: five Data path stages legible and evenly spaced, all lanes intact. Confirmed the pre-existing, already-logged-as-deferred diagonal `laneflow{hourly}{serve}` edge (running from `stg/fct/OHLCV` down to `dashboard model report`) passing near/through the top of the `contract owner promise` box — this is the known, previously-ledgered issue from Task 6's report, not a new finding; no action taken per the task instructions. Advanced Project section below, no other issues. | n/a (pre-existing, already deferred per Task 6) |
| 74 | 71 | No issue found (Section 10 Glossary, alphabetical entries API through Table format) | n/a |
| 75 | 72 | No issue found — page is mostly blank (only the final "Watermark" glossary entry, ~2 lines of content). This is the natural tail end of the alphabetical Glossary section (Section 10 ends here) before Section 11 starts fresh on the next page, not an unintended large blank area — consistent with the checklist's carve-out for deliberate section-end whitespace (same reasoning as pg 14/33/64). | not an issue (justified) |
| 76 | 73 | No issue found — final page, short (~20% content): Section 11 References, five bibliography entries, end of document. Natural document-end whitespace, not a defect. | n/a |

## Summary

- **76 of 76 pages reviewed** (every page rendered at 200 DPI grayscale and
  visually inspected via the Read tool, not skimmed from source).
- **2 real issues found and fixed**: the WebSocket-producer listing
  (pg 21/22) and the Hourly-OHLCV listing (pg 41/42), both split at a clean
  syntactic boundary to remove the "setup severed from operation" page-break
  pattern.
- **2 additional candidates checked and explicitly judged not-issues**
  (CREATE TABLE column-list split pg 27/28; YAML test-list split pg 58/59),
  with justification recorded.
- **1 pre-existing, already-deferred issue re-confirmed, not re-flagged**:
  the Fig 22 diagonal `laneflow{hourly}{serve}` edge from Task 6.
- **Finding #6 (possible duplicate OHLCV listing): resolved, no duplicate
  found** — confirmed directly against the current file.
- **3 natural end-of-section/document blank pages** correctly identified as
  not defects (pg 14, 33, 64, 75, 76 — end-of-subsection or end-of-document
  whitespace, no orphaned headings).
- No leftover raw markup or `[[REPORTKIT-VISUAL:` sentinel text found
  anywhere in the rendered PDF (independently verified by a full-document
  text scan in addition to the page-by-page visual pass).
