# Critique Remediation and Publication Hardening Specification

**Status:** Implemented — see
`docs/critique-remediation-implementation-log.md`. All 10 tasks of
`docs/superpowers/plans/2026-09-12-critique-remediation.md` are complete;
two consecutive clean `--profile release` builds pass and every acceptance
criterion in `## 5` below has been re-verified.
**Date:** 2026-09-12
**Source:** `docs/ChatGPT_critique.md` and the follow-up decisions recorded in
the working discussion
**Scope:** Publication repository only. ReportKit source changes are out of
scope for this pass.

## 1. Decisions and constraints

- The guide remains a conceptual reference supported by one small, tested
  companion implementation. Listings should teach the implementation boundary;
  they should not pretend to be a production deployment.
- The primary deliverable is a print-first A4 PDF. Screen and tablet legibility
  still matter, but A4 print size is the acceptance baseline.
- The guide is intended to become more quant/finance-oriented later. This pass
  should preserve the general spine while making provenance, timestamps,
  corrections, units, reproducibility, and point-in-time reasoning strong
  foundations for that future shift.
- There is no page ceiling. Additional pages are justified when they add
  understanding, implementation ability, decision guidance, failure diagnosis,
  or reference value; repetition and decorative content are not sufficient.
- This change records the plan only. It does not modify ReportKit and does not
  implement the publication fixes.

## 2. Current baseline and findings

The original critique describes an earlier build. The current source already
contains 23 figure sentinels/fragments, 26 tables, 10 classified listings, the
requested mechanism figures, stack and cost guidance, and capstone handoffs.
The enrichment pass is recorded as complete with final visual review pending in
`docs/instructional-enrichment-spec.md`.

The remaining work is therefore a hardening pass rather than another quota of
figures, tables, or listings.

Observed issues in the available combined draft/build artifacts:

1. **Resolved (Task 1, commit `731e268`).** The combined build repeatedly fails while reading generated auxiliary data
   with a runaway `\\@writefile`/`\\contentsline` argument. The known blocker
   is also recorded in `docs/reportkit-primitive-additions-spec.md`; it must be
   reproduced from a clean output directory before its ownership is assigned.
   Root cause confirmed: a stale `build/combined/` output directory reused
   across incompatible runs, not a ReportKit defect — building from empty
   makes it disappear. Filed as a non-blocking upstream note in
   `docs/reportkit-known-issues.md` rather than a bug against ReportKit
   itself, per item 3 below.
2. **Resolved (Task 3, commit `433416a`).** Table and listing captions in the rendered draft expose raw
   `\\label{...}` text, indicating that the source caption-label convention is
   not being consumed by the current publication pipeline.
   Root cause confirmed: Pandoc converts this manuscript with `raw_tex`
   disabled, so a bare `\label{...}` in caption text is escaped to literal
   text rather than executed. Replaced with a supported Pandoc fenced-Div id
   wrapper (`::: {#tbl:...}` / `::: {#lst:...}`) across all captions in
   scope at the time; independently reviewed with zero leakage and zero
   duplicate ids. Task 7's listing splits (see item 6) added further ids
   using the same wrapper convention.
3. **Resolved (Task 1, commit `731e268`).** The available PDF uses a `draft` footer even though the earlier critique
   expected a publication-like build.
   Fixed by adding a `profiles: release:` section to `publication.yaml`
   (`version: v1.0`) and building with `--profile release`.
4. **Resolved (Task 2, commit `7a1f261`).** The retry-state figure has an edge/label collision around `Retrying` at A4
   size.
5. **Resolved (Task 6, commit `d4e0fa7`).** The cumulative capstone fragment describes `raw_trades + manifest`, but its
   visible node is currently a combined `producer and broker` label. The figure
   should make the named durable artifacts and their handoffs visible.
   Now shows `source → producer/broker → raw_trades + manifest →
   curated_trades + catalog → stg/fct/OHLCV` as five explicit Data-path
   stages.
6. **Resolved (Task 7, fix loop complete).** Some listings began or continued across page boundaries awkwardly. The
   transformation section also contains a second OHLCV query immediately after
   the new late-data listing; its distinct teaching purpose should be confirmed.
   The "second OHLCV query" concern is confirmed resolved (only one OHLCV
   listing exists in the current source). Two genuine page-break defects
   were found and fixed by splitting the content of one listing into two
   boxes in each case (`lst:sec02-websocket-producer` and
   `lst:sec04-hourly-ohlcv`), while keeping each listing's original single
   id/caption. A dispatched reviewer's fix-loop findings against the first
   attempt (the SQL split's second half was not independently-valid SQL as
   first committed; both splits together had raised the listing count from
   10 to 12) are both resolved by this final form: framing each pair of
   boxes as one script shown in two boxes, not two independently-runnable
   snippets, removes the correctness claim, and keeping one id per listing
   keeps the count at 10. See
   `docs/critique-remediation-progress-2026-09-12.md` §2 for full detail.
7. **Resolved (Task 4, commit `ea0e685`; count further changed by Task 5's
   commit `a852214`).** The README still describes 14 diagram fragments, which is stale relative to
   the current 23-fragment source.
   Fixed to 23, then to 22 after Task 5 removed the redundant
   ingestion-semantics figure (§4 P1's compaction/removal item) — README
   stays in sync with `ls fragments/*.tex | wc -l` as of each change.

These findings take precedence over the critique's historical page numbers and
counts.

## 3. Editorial principles and challenges

- Do not increase visual count by default. Recompose, consolidate, or remove a
  low-information figure when an existing mechanism figure teaches the same
  idea.
- Treat the three-column table preference as a heuristic. Retain four-column
  tables when comparison is clearer than prose or multiple smaller tables.
- Keep beginner-mistake warnings specific to genuine failure modes; avoid a
  repeated box template solely to satisfy section symmetry.
- Classify an example as **Runnable with adaptation** only when it can be
  smoke-tested with documented local fixtures and dependencies. Framework-
  dependent excerpts with undefined adapters or macros should be
  **Illustrative** unless that support is supplied.
- Make capstone continuations incremental: name the prior artifact, new
  artifact, grain/time assumption, and next handoff without repeating the full
  architecture in every section.
- Treat quant material as an application lens over the same lifecycle. Do not
  replace general data-engineering concepts with trading advice or a
  vendor-specific market-data stack.

## 4. Work packages

### P0 — Establish a trustworthy release build

1. Reproduce the combined-build failure from an empty output directory using
   the pinned ReportKit revision in `reportkit.lock`.
2. Determine whether stale `.aux`, `.toc`, or `.out` files are the cause. If a
   publication-local cleanup or unique output directory resolves it, encode
   that workaround in the publication workflow/documentation.
3. If the root cause is generic ReportKit behavior, record a minimal upstream
   bug report without editing the ReportKit repository.
4. Produce a release-profile PDF and verify metadata, bookmarks, contents,
   links, page numbering, and the absence of draft markers.

### P0 — Repair publication semantics

1. Replace the unsupported caption-label form with a supported syntax or a
   publication-local preprocessing workaround.
2. Verify all 23 figure, 26 table, and 10 listing identifiers for uniqueness,
   resolution, and invisibility of implementation markup in PDF text.
3. Update stale repository documentation, including the fragment count in
   `README.md`.

### P1 — Perform selective A4 visual remediation

Review every affected page at normal A4 print scale and in grayscale:

- fix the retry-state edge/label collision;
- reassess the tall, generic ingestion-semantics visual for compaction or
  removal if it is redundant;
- revise the cumulative capstone visual to show
  `source → producer/broker → raw_trades + manifest → curated_trades + catalog
  → stg/fct/OHLCV`, with explicit scheduling/replay, quality/quarantine,
  contract/owner, and consumer paths;
- increase diagram text or reduce content where event-time, reconciliation,
  milestone, or architecture labels are too small;
- prevent code listings from starting at the bottom of a page or splitting a
  setup line from the operation it configures;
- remove redundant code where it adds no distinct explanation;
- check table continuation headers, caption proximity, and accidental large
  blank areas.

### P1 — Build and test one companion path

Provide a deterministic, local path using a bounded fixture:

```text
fixture → normalized raw envelope → partitioned Parquet
→ DuckDB curated_trades → deduplicated trade model
→ hourly OHLCV → quality and reconciliation checks
```

The path should exercise the composite trade key, event versus receipt versus
landing time, event-time partitioning, deduplication, late-data lookback, and
OHLCV grain. It should run without credentials, Kafka, Airflow, cloud storage,
or a distributed engine. Kafka-compatible streaming and Airflow remain
optional production extensions.

Smoke-test every listing marked **Runnable with adaptation**. Reclassify
framework-specific snippets as **Illustrative** when their dependencies cannot
be kept small and explicit.

### P2 — Prepare the quant-ready foundation

Add or verify, where relevant:

- source identifiers and raw-payload retention;
- separate event, receipt, and durable-landing timestamps;
- explicit price and quantity units;
- correction, duplicate, and ordering policies;
- reproducible interval reconstruction and transformation versions;
- point-in-time correctness and look-ahead-bias guidance;
- market-calendar/session semantics when the source requires them.

Keep these as labelled applications or extensions until the planned quant
edition is explicitly scoped.

## 5. Acceptance criteria

- Two consecutive clean combined release builds succeed from a fresh output
  directory.
- Strict diagnostics report no fatal, overflow, clipping, unresolved
  reference, duplicate-label, or unresolved-sentinel errors.
- The PDF contains no visible raw `\\label{` markup and no draft footer.
- All pages and affected figures are reviewed at A4 print size and in grayscale.
- Every runnable listing passes its documented fixture smoke test.
- The companion path completes from fixture to validated OHLCV output.
- The final capstone figure agrees with the manuscript's named artifacts,
  grains, controls, ownership, and consumer contracts.
- The implementation log records fixes, removals, reclassifications, local
  workarounds, and ReportKit issues deferred upstream.

## 6. Deliverables and non-goals

Deliverables are a release-quality A4 PDF, a tested companion path, updated
publication documentation, and an implementation/changelog entry explaining
what changed and what remains for the quant-focused edition.

This specification does not authorize ReportKit repository changes, a complete
production trading system, credentials or live endpoints, or a vendor-specific
reference architecture.

## 7. Closed out

All 10 tasks of `docs/superpowers/plans/2026-09-12-critique-remediation.md`
are complete. This section previously tracked outstanding items during
implementation; that running commentary, and the fuller analysis in
`docs/critique-remediation-progress-2026-09-12.md`, is now superseded by
`docs/critique-remediation-implementation-log.md`, which records the final
per-task summary, the two-consecutive-clean-builds evidence, every §5
acceptance criterion re-verified, local workarounds adopted, and issues
deferred upstream to ReportKit.
