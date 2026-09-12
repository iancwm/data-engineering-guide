# Instructional Enrichment Specification

**Status:** Implementation pass complete; final visual review pending
**Source:** `docs/ChatGPT_critique.md`
**Scope:** Manuscript, diagram fragments, and `publication-guidelines.md` for
*A Practical Guide to Data Engineering*. This specification does not change the
publication engine itself, but names the engine capabilities that must exist
before the affected figures can be safely shipped.

## 1. Outcome

Make the guide feel like a practical technical ebook: readers should be able
to see invisible system behavior, connect each lifecycle stage to the same
crypto-trade capstone, and adapt compact examples into their own projects.

This is an instructional-enrichment pass, not a rewrite or a visual-polish
pass. Preserve the current eleven-section structure, the existing capstone
contract, and the publication's table of contents, metadata, and page-start
rules.

### Success measures

- Add seven mechanism figures, two structural replacement figures, and revise
  the cumulative capstone figure.
- Add ten short, explicitly classified code listings tied to the capstone.
- Replace or materially reduce three dense/low-value tables; do not add new
  explanatory tables for motion, state, topology, or cardinality concepts.
- End Sections 2--7 with a clearly labelled capstone continuation that names
  the prior input, the new output, and the next handoff.
- Add practical decision guidance for stack selection, beginner mistakes,
  minimum viable production, vendor-boundary awareness, and cost.
- Retain legibility at final A4 print width, with no clipping, stranded table
  rows, unresolved sentinels, or hard-coded figure numbers.

## 2. Editorial decisions

### 2.1 Keep the stable instructional structure

- Keep all current H1 and H2 headings. Do not introduce H3 headings.
- Keep comparison and reference tables where readers compare stable attributes:
  delivery semantics, storage-layout choices, tool categories, quality test
  categories, and architecture-pattern trade-offs.
- Use diagrams when a reader must follow time, state, data movement, physical
  layout, or a one-to-many relationship. Use a captioned listing when a reader
  needs an implementation anchor.
- All additions use the `BTCUSDT` capstone conventions already established in
  Section 2: the composite trade key, UTC event-time partitions, raw payload
  retention, `ingested_at`, manifest `landed_at`, and retry-safe processing.
- Examples must never imply that Binance, Kafka, Iceberg/Delta, dbt, Airflow,
  or a cloud platform is required. The selected names are concrete examples;
  the surrounding text identifies the capability boundary and a local option.

### 2.2 Code-listing contract

Every new listing must have:

1. A nearby lead-in that states the scenario, input, and output.
2. A caption in the form `Listing: <purpose>.` and a stable semantic label
   (`lst:secNN-<purpose>`), using the publication's established listing syntax
   or the closest supported Markdown equivalent.
3. One visible classification immediately before the block: **Runnable with
   adaptation**, **Pseudocode**, or **Illustrative**.
4. An explicit language fence, lines that fit the final code width, no
   credentials or destructive commands, and a short explanation after the
   listing of the guarantee it demonstrates.

"Runnable with adaptation" means the algorithm and interfaces are complete
enough to run after the reader supplies documented dependencies, endpoint
configuration, and local paths. It does not mean the guide provides a
production-ready application.

### 2.3 Diagram contract

Each new figure has a manuscript sentinel and a matching
`fragments/fig-<slug>.tex` source. Use a semantic figure label, a standalone
caption, `source={Author's synthesis.}`, and a plain-language `description`.
The description must convey the causal or failure path, not merely list nodes.

Prefer compact horizontal, timeline, swimlane, before/after, and state-machine
layouts. Avoid tall single columns of generic boxes. Labels use concrete
capstone names where doing so makes the architecture more tangible, for
example `raw_trades`, `curated_trades`, `fct_hourly_ohlcv`, `quality_alerts`,
and `quarantine/trades`.

## 3. Manuscript changes

### 3.1 Section 1 — `manuscript/01-introduction.md`

- Convert the most explanatory (rather than comparative) material in
  `tbl:common-confusions`, `tbl:data-layers`, `tbl:common-data-sources`, and
  `tbl:data-shapes` into short prose, key-concept, decision, or warning
  callouts. Retain only a compact table when a reader must compare the same
  attributes across alternatives.
- Add a **Common beginner mistakes** warning callout near the end: treating a
  warehouse as an ingestion tool, choosing a vendor before writing
  requirements, conflating file and table formats, and treating a successful
  run as proof of correct data.
- Add a short bridge that names analytics, ML, and finance/quant consumers as
  distinct serving needs; do not introduce a resume-focused edition in this
  pass.

### 3.2 Section 2 — `manuscript/02-ingestion.md`

- Insert the backpressure, delivery-retry, and event-time figures specified in
  Section 4.
- Add the producer skeleton and raw-event-envelope listings specified in
  Section 5.
- Add a **Common beginner mistakes** warning covering offset commit before
  durable write, using arrival time as event time, assuming exactly-once
  across systems, and dropping malformed data without an auditable path.
- Extend the capstone continuation with a concise handoff callout:
  `source → producer → broker → raw_trades + manifest`; state that Section 3
  consumes the raw landing and manifest, never a new source read.

### 3.3 Section 3 — `manuscript/03-storage.md`

- Insert the small-files/compaction figure after the current small-files
  explanation.
- Add a DuckDB partition-pruning listing after the partition-pruning figure
  and an illustrative Iceberg/Delta table-definition listing after the open
  table-format discussion.
- Add a **Common beginner mistakes** warning covering excessive partition
  cardinality, confusing Parquet with table transactions, and querying raw
  files as if they were a governed curated model.
- The capstone continuation must visibly update the chain to
  `raw_trades + manifest → curated_trades + catalog`, state one row per unique
  trade key, and name compaction as a maintenance task rather than an
  ingestion responsibility.

### 3.4 Section 4 — `manuscript/04-transformation-processing.md`

- Insert the join-cardinality figure immediately after the existing grain and
  join explanation. It replaces prose that merely warns that joins can
  multiply rows; retain a short interpretation paragraph.
- Add a runnable-with-adaptation SQL/dbt listing that declares the input
  grain, deduplicates by the composite trade key, and produces a named output
  grain. Add an illustrative windowed-aggregate listing that uses a bounded
  late-data lookback before finalizing hourly OHLCV.
- Add a **Common beginner mistakes** warning: undeclared grain, joining two
  facts directly, full-refreshing a growing history by default, and treating a
  late event as a reason to rewrite all history.
- The capstone continuation ends with
  `curated_trades → stg_trades → fct_trades → fct_hourly_ohlcv`, including the
  grain at each transition and the next orchestration dependency.

### 3.5 Section 5 — `manuscript/05-orchestration.md`

- Replace the current tall linear `fig:sec05-orchestration-dag` with a compact
  DAG that shows the data path (`Extract`, `Load`, `Validate`, `Transform`,
  `Publish`) and labels the blocked downstream path after a validation error.
- Add the retry-state figure and a compact illustrative Airflow- or
  Dagster-style DAG listing. The listing must show a data interval, retry
  policy, timeout, and a publish dependency; business transformation logic
  remains outside the orchestration definition.
- Convert `tbl:orchestration-concerns` into a short capability-boundary prose
  section with a decision callout. Retain `tbl:workflow-start-conditions` and
  `tbl:orchestration-tooling` because both support meaningful comparison.
- Add a **Common beginner mistakes** warning: using wall-clock time instead
  of an explicit data interval, retrying deterministic validation errors,
  embedding transformations in the scheduler, and running a backfill without
  concurrency/rate-limit controls.
- End the capstone continuation with a handoff callout naming the scheduled
  workflow, retry/backfill policy, and the quality gate it hands to Section 6.

### 3.6 Section 6 — `manuscript/06-quality-reliability.md`

- Insert the reconciliation-flow figure immediately before the numbered
  implementation list in the capstone continuation. Its prose must distinguish
  accepted raw attempts, quarantined records, duplicate attempts, distinct
  trade keys, and finalized hourly aggregate counts.
- Add a runnable-with-adaptation dbt tests YAML listing. It must include
  `not_null`, `unique` (or a composite-key equivalent), an accepted/range rule,
  and an explicit note that reconciliation and freshness need additional
  custom checks.
- Replace `tbl:capstone-milestones` with the capstone milestone swimlane in
  Section 4. The surrounding paragraph becomes prose describing inputs,
  outputs, and handoff conditions rather than reintroducing the same table.
- Add a **Common beginner mistakes** warning: tests only after publication,
  comparing counts at incompatible grains, alerting without ownership, and
  silently discarding quarantined data.

### 3.7 Section 7 — `manuscript/07-metadata-governance-serving.md`

- Add an illustrative YAML data-contract listing after the contract figure.
  It declares the dataset name, version, owner, composite key, grain,
  fields/units, freshness expectation, quality expectation, classification,
  and breaking-change policy.
- Add a compact serving-surfaces prose/callout directly after the BI, ML, and
  operational-serving discussions; it must contrast the consumer contract for
  a dashboard, model/feature, and application API without a new table.
- Add a **Common beginner mistakes** warning: cataloguing tables without an
  owner, treating schema as semantics, granting raw-layer access by default,
  and changing a contract without a compatibility window.
- The capstone continuation states the named owner, contract location,
  consumer-facing `fct_hourly_ohlcv` contract, and serving freshness promise.

### 3.8 Section 8 — `manuscript/08-practitioner-topics.md`

- Replace `tbl:core-tool-landscape` and the single-row
  `tbl:cross-cutting-tool-landscape` with one platform-boundaries architecture
  figure plus concise capability prose. The figure must show that a vendor may
  implement multiple boundaries without erasing them: source, transport,
  storage/tables, processing, orchestration, quality/observability,
  governance, and serving.
- Add a short **Choosing a stack under constraints** decision section, with
  four named contexts: solo learner, small company, enterprise platform, and
  regulated-finance workload. Each context specifies a default bias, the
  constraint that changes it, and what to defer. This is guidance, not a vendor
  recommendation matrix.
- Keep the architecture-pattern and learning-order tables. Convert any other
  low-value, paragraph-like table cells into nearby prose/callouts.
- Expand the cost section into five visible cost drivers: storage, compute,
  orchestration, always-on streaming, and observability/data-transfer. Give
  one measurable unit metric for each where applicable.
- Add the explicit warning that products can span lifecycle stages, but the
  conceptual boundaries still matter for ownership, failure handling, cost,
  and exit planning.

### 3.9 Section 9 — `manuscript/09-learning-path.md`

- Add an illustrative minimal repository-tree listing immediately after the
  portfolio project. It includes `ingestion/`, `models/`, `orchestration/`,
  `tests/`, `contracts/`, `docs/`, and local configuration/example files; it
  must not present secrets or a required tool-specific layout.
- Revise `fig:sec09-capstone-architecture` to be the culmination of the
  Section 2--7 continuation callouts. It must show the concrete named assets,
  control paths for scheduling/replay and quality/quarantine, ownership/data
  contract, and dashboard/report consumers.
- Add one closing paragraph mapping the completed project to analytics
  consumption, ML/feature use, and finance/quant research without changing the
  guide's general-audience positioning.

## 4. Figure registry

| ID and fragment | Insert after | Required teaching content | Layout and acceptance criteria |
| --- | --- | --- | --- |
| `fig:sec02-backpressure`; `fragments/fig-sec02-backpressure.tex` | Section 2 backpressure introduction | Producer at 10,000 msg/s, consumer at 1,000 msg/s, durable broker queue grows, lag alert, then scaled/caught-up consumer | Rate-over-time or queue-depth before/after. It must show that a broker absorbs overload temporarily, not eliminate capacity limits. |
| `fig:sec02-delivery-retry-dedup`; `fragments/fig-sec02-delivery-retry-dedup.tex` | Delivery semantics discussion, after the existing semantic table | Sink commits event, ACK is lost, producer retries, dedup key detects duplicate, idempotent sink has one logical result | Sequence diagram with an explicit uncertain-ACK failure path. Do not replace this with the existing linear semantics flow. |
| `fig:sec02-event-time-watermark`; `fragments/fig-sec02-event-time-watermark.tex` | Late and out-of-order data discussion | Event time, arrival/processing time, watermark, allowed lateness, a late event, closed hourly window, repair/finalization action | Horizontal timeline. State in labels/caption which window can still change and what happens after allowed lateness. |
| `fig:sec03-small-files-compaction`; `fragments/fig-sec03-small-files-compaction.tex` | Section 3 small-files explanation | Many small Parquet files in one event-time partition, compaction job, fewer right-sized files, same logical rows | Compact left-to-right before/after physical-layout figure; distinguish files from the table's logical data. |
| `fig:sec04-join-cardinality`; `fragments/fig-sec04-join-cardinality.tex` | Section 4 grain/join discussion | One trade/fact row, several matching reference rows due to wrong join grain, multiplied result, pre-aggregate/deduplicate correction | Before/after row illustration, not a dense ERD. Caption names the input and output grain and the inflated measure risk. |
| `fig:sec05-retry-state`; `fragments/fig-sec05-retry-state.tex` | Section 5 failure/retry discussion | `scheduled → running → retrying → succeeded`; terminal `failed` and `skipped`; timeout/validation failure branches | State machine with bounded retries and clear terminal states. It must show that a deterministic validation failure is not blindly retried. |
| `fig:sec06-reconciliation-flow`; `fragments/fig-sec06-reconciliation-flow.tex` | Section 6 capstone implementation, before reconciliation item | Source count → received raw attempts → accepted/quarantined/duplicate accounting → `curated_trades` distinct-key count → finalized OHLCV count → exception queue | Horizontal or swimlane reconciliation path. Every count comparison states its grain and interval. |
| `fig:sec06-capstone-milestones`; `fragments/fig-sec06-capstone-milestones.tex` | Replace `tbl:capstone-milestones` | Ingest, store, model, operationalize-trust milestones; each owns inputs, outputs, control/quality condition, and next handoff | Four-lane capstone swimlane. It must fit one page and replace the table, not duplicate it. |
| `fig:sec08-platform-boundaries`; `fragments/fig-sec08-platform-boundaries.tex` | Replace the two Section 8 tool-landscape tables | Capability boundaries and representative artifacts; vendor-span annotation; serving shown as a full boundary, not a stranded table row | Layered architecture figure with a cross-cutting observability/governance/cost annotation. No vendor logos or product popularity claims. |
| Revised `fig:sec09-capstone-architecture`; `fragments/fig-sec09-capstone-architecture.tex` | Existing Section 9 sentinel | Public market stream → producer/broker → raw files/manifest → `curated_trades` → models → schedule/replay and quality/quarantine → contract/owner → dashboard/report | Compact architecture/swimlane hybrid. Data and control paths must use labels or line styles in addition to color; no empty central space. |

The final figure total becomes 23: fourteen existing figures (including the
revised capstone) plus nine new figures. The release changelog must identify
the capstone as revised, rather than double-counting it as a new figure.

## 5. Code-listing registry

| ID | Location | Classification | Required content |
| --- | --- | --- | --- |
| `lst:sec02-websocket-producer` | Section 2 capstone architecture | Runnable with adaptation | Python WebSocket reconnect loop; preserves raw payload, builds normalized envelope, logs source ID/offset context, and uses bounded retry/backoff. |
| `lst:sec02-raw-event-envelope` | Section 2 immediately after producer listing | Illustrative | JSON event with `event_id`/source trade ID, raw payload, `source_timestamp`, `event_timestamp`, `ingested_at`, `landed_at` location/manifest reference, and `schema_version`. Explain which times are event versus landing metadata. |
| `lst:sec03-parquet-partition-query` | Section 3 after partition pruning | Runnable with adaptation | DuckDB SQL reads the event-time partitioned Parquet path and filters an event-time interval so partition pruning has a visible predicate. |
| `lst:sec03-table-definition` | Section 3 open table formats | Illustrative | Iceberg- or Delta-style table creation pseudocode, with schema, event-time partitioning, composite trade key note, and table location. It must label table semantics separately from Parquet files. |
| `lst:sec04-deduplicate-trades` | Section 4 capstone continuation | Runnable with adaptation | SQL/dbt model declares one row per unique trade key, uses `row_number` or equivalent deterministic deduplication, and documents its incremental boundary. |
| `lst:sec04-hourly-ohlcv` | Section 4 aggregation discussion | Illustrative | Windowed hourly aggregate with an explicit late-data lookback and finalization condition. It must not claim generic streaming SQL syntax is portable. |
| `lst:sec05-capstone-dag` | Section 5 capstone continuation | Illustrative | Airflow/Dagster-style DAG with data interval, retries, timeout, task dependencies, and a separate transformation command/task. |
| `lst:sec06-dbt-tests` | Section 6 capstone continuation | Runnable with adaptation | dbt schema YAML for grain/key, non-null, positive price/quantity, and OHLCV relationship/range tests; note the project-specific test macro needed for a composite key. |
| `lst:sec07-data-contract` | Section 7 data contracts | Illustrative | Versioned YAML contract for `curated_trades` or `fct_hourly_ohlcv`, including owner, grain, schema/units, freshness, quality rules, classification, compatibility, and change procedure. |
| `lst:sec09-capstone-repo-tree` | Section 9 portfolio project | Illustrative | Minimal portable repository tree with paths for ingestion, SQL models, orchestration, tests, contracts, documentation, and local sample/config files. |

The source critique calls for nine examples but identifies ten useful anchors.
Implement all ten because the raw envelope is deliberately a tiny companion
listing to the producer rather than a second full program. If page budget
requires a cut, retain the envelope as an annotated code comment in the
producer and report that consolidation in the changelog.

## 6. Publication-guidelines updates

Update `publication-guidelines.md` in the same change set:

- Add the new semantic figure IDs and their learning purposes to the
  section-by-section visual plan and the source/output-file examples.
- Add a **mechanism diagrams** rule: timelines, state machines, sequences,
  before/after physical layouts, and swimlanes are preferred for time, state,
  retry, cardinality, and reconciliation explanations.
- Add a **code listings** subsection that formalizes the classification,
  caption/label, page-width, and safety rules from Section 2.2.
- Amend the tables rules: favour three columns; use prose or a callout for a
  single-row decision; do not split a table merely to avoid a stranded row;
  replace capability-boundary tables with diagrams when structure matters more
  than comparison.
- Add capstone-thread rules: each continuation explicitly names the previous
  artifact, output artifact, grain/time assumptions, and next handoff.
- Add visual QA criteria for diagram text size at A4 width, whitespace balance,
  data/control-path distinction, caption self-sufficiency, and grayscale
  legibility.

## 7. Dependencies, sequence, and deliverables

### Required publication-engine support

The current guideline log says that recomposition, diagram width/scale
controls, and denser timeline/state-machine primitives were deferred pending
tooling support. Before authoring the new fragments, verify that the ReportKit
diagram layer can provide all of the following without per-page manual hacks:

- horizontal and swimlane layouts with labelled arrows;
- sequence/timeline and state-machine primitives;
- before/after grouped layouts;
- diagram-level width, height, spacing, and font-size controls;
- captions/descriptions that retain accessibility text; and
- no figure clipping or unreadable labels at A4 width.

If an item is unavailable, record it as an engine dependency and defer only
the figures it blocks. Do not substitute a tall generic flowchart that loses
the specified mechanism. Listings, callouts, capstone handoffs, and table
reductions may proceed independently.

### Implementation order

1. **Prepare the source contract:** add listing support if required; update
   `publication-guidelines.md`; confirm available diagram primitives and the
   manuscript-to-fragment sentinel contract.
2. **Improve instructional prose:** add beginner-mistake callouts, capstone
   handoffs, stack-constraint guidance, cost drivers, and vendor-boundary
   warning. Replace the specified tables without adding compensating table
   density.
3. **Add listings:** implement and review the ten listings against the code
   contract, then make their inputs/outputs consistent across chapters.
4. **Add/recompose figures:** create fragments and sentinels in section order;
   update nearby prose, captions, descriptions, and references together.
5. **Build and perform visual QA:** render the complete publication; inspect
   every new/revised figure and every page affected by removed tables. Iterate
   on layout only after the source is semantically correct.
6. **Publish the change record:** add a changelog section to this document or
   the implementation PR description with tables changed, figures added or
   revised, listings added, engine dependencies resolved, and deferred
   PDF-QA findings.

## 8. Acceptance criteria

### Source validation

- Every visual sentinel has exactly one matching fragment and every fragment
  has exactly one manuscript sentinel, semantic label, caption, source, and
  descriptive accessibility text.
- All new code fences declare a supported language and carry one of the three
  classifications. Every listing label is unique.
- References to figures and listings use semantic cross-reference support or
  nearby descriptive prose; no hard-coded page or figure numbers are added.
- `rg` confirms that `tbl:capstone-milestones`,
  `tbl:core-tool-landscape`, and `tbl:cross-cutting-tool-landscape` are absent
  after their replacements, unless a label is intentionally retained as a
  redirect supported by the renderer.
- The existing capstone data contract remains internally consistent: the
  composite key, timestamp definitions, UTC partitions, source/landing
  boundary, and stated model grains do not conflict between Sections 2--9.

### Rendered-PDF QA

- The build completes with the repository's strict diagnostics and no
  unresolved references, visual sentinels, or manuscript/fragment-contract
  failures.
- All new or revised figures fit a page, have readable labels at normal A4
  viewing/print size, and remain understandable in grayscale.
- No figure has excessive unused canvas area, a tall uninformative chain, or
  a caption separated from its figure. No table splits into a one-row
  continuation merely to preserve source structure.
- Listing lines, tables, captions, and long identifiers stay inside page
  margins; code blocks do not split in a way that separates a setup line from
  the operation it configures.
- A reviewer can trace the capstone from source to consumer in Section 9 and
  recognize each intermediate stage from the earlier Section 2--7
  continuations.
- The final changelog names all changed tables, added/revised diagrams, added
  listings, and remaining visual-QA follow-ups.

## 9. Out of scope

- Changing the guide's audience, title, license, structure, or general
  technology-neutral posture.
- Fabricating a cover, adopting a vendor-specific production stack, or adding
  live credentials/endpoints.
- Replacing the ReportKit build system or implementing unrelated engine work
  beyond the diagram/listing support required by this specification.
- Treating the examples as complete production deployments or financial/trading
  advice.

## 10. Implementation log

### 2026-09-07 — initial source and build pass

- Added the instructional-enrichment guidance to `publication-guidelines.md`,
  including diagram, listing, accessibility, table-density, and capstone-
  continuity rules.
- Added beginner-mistake callouts and capstone handoffs across Sections 1--9,
  plus stack-constraint, cost-driver, and vendor-boundary guidance in Section
  8.
- Added the planned source listings for ingestion, storage, transformation,
  orchestration, quality, governance, and the Section 9 capstone repository
  tree.
- Added mechanism figures for retry/deduplication, backpressure, event-time
  watermarks, compaction, join cardinality, retry state, reconciliation,
  capstone milestones, and platform boundaries; revised the cumulative
  capstone architecture figure into a swimlane view.
- Replaced the explanatory Section 1 tables, orchestration-concerns table,
  capstone milestone table, and Section 8 tool-landscape tables with prose or
  figures. The retained orchestration tables compare start conditions and
  tooling categories, while the revised DAG now shows the horizontal data path
  and blocked validation branch.
- Updated the ReportKit lock to the engine revision used for the new diagram
  primitives.

Validation completed for this pass:

- strict diagnostics: passed (0 fatal, overfull, undefined, duplicate-label,
  or allowlist issues);
- PDF inspection: passed, 77 pages, 30 links, no content outside the media box;
- `git diff --check`: passed.

Remaining work is a final human visual review of every affected page at print
size before publication.
