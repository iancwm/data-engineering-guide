# Quant Finance Overlay: Multi-Agent Implementation Plan

**Status:** Implemented; all verification and publication gates passed.

**Source of truth:** `docs/finance-overlay-spec.md` (2026-09-26). If this plan and that spec disagree, follow the spec and record the plan correction before editing code or manuscript.

**Outcome:** An optional finance route in the existing ReportKit book, one point-in-time (PIT) research lab, one feed-sequence lab, and a clean combined PDF build. The original BTCUSDT companion path must still produce 49 raw events, 48 deduplicated trades, and 3 hourly bars.

## 1. Team shape and edit rules

Use one lead/integrator plus three implementation agents. This fits a four-agent concurrency limit. Agents may work at the same time only after Gate 1 below; the lead coordinates shared contracts and performs final integration.

| Role | Exclusive write ownership during parallel work | Handoff |
| --- | --- | --- |
| **Lead / integrator** | This plan, `docs/finance-overlay-implementation-log.md`, `manuscript/05-orchestration.md` through `manuscript/11-references.md`, `companion/finance/README.md`, `companion/README.md`, `publication-guidelines.md` | Resolves interfaces, validates all deliverables, runs the combined build, and makes final cross-file corrections after agents stop writing. |
| **Agent A: PIT lab** | `companion/finance/fixtures/pit_case.jsonl`, `companion/finance/scripts/run_pit_case.py`, `companion/finance/tests/test_pit_case.py` | A deterministic result table, the exact query used for PIT selection, command output, and test results. |
| **Agent B: feed lab** | `companion/finance/fixtures/feed_sequence.jsonl`, `companion/finance/scripts/check_feed_sequence.py`, `companion/finance/tests/test_feed_sequence.py` | A gap/recovery trace, declared sequence-domain rules, command output, and test results. |
| **Agent C: early manuscript and figures** | `manuscript/00-frontmatter.md` through `manuscript/04-transformation-processing.md`; new `fragments/fig-sec02-finance-gap-repair.tex` and `fragments/fig-sec04-pit-revision-timeline.tex` if used | Changed-section map, figure IDs, listing ID and tested SQL equivalence, plus print-width concerns. |

All four roles read the spec and the current files before editing. Do not edit another role's files during the parallel stage; send the proposed change to the owner through the lead. Do not run concurrent git staging, commits, resets, or publication builds in the shared checkout. The lead may run read-only checks during parallel work, but waits until all owners hand off before the final combined build. Keep the untracked `.superpowers/finance-overlay-spec-scratch.md` untouched. Do not edit the sibling `report-kit` engine repository.

The current `docs/finance-overlay-spec.md` is untracked. The lead must include it with the implementation plan in the eventual reviewable change set; workers should not assume it is already in git history.

## 2. Gate 0: establish the baseline

- [x] Lead records `git status --short` in `docs/finance-overlay-implementation-log.md` and checks the manuscript/fragment contract, `manuscript/order.txt`, and Section 9's existing six optional tracks. Preserve unrelated working-tree changes.
- [x] Lead runs `companion/.venv/bin/python companion/scripts/run_all.py` and `python3 companion/scripts/test_manuscript_sql_alignment.py`. If the existing virtual environment is absent, create it using the pinned dependencies in `companion/README.md`. Record baseline output; do not change the BTCUSDT fixture or `companion/scripts/run_all.py`.
- [x] Lead confirms the ReportKit build entry point is available. The engine is a separate repository and is read-only for this work. No need for a baseline full build if the current release artifact and known build state are already documented; the final build is mandatory.

**Exit:** Baseline counts and the exact pre-existing dirty files are recorded. Any pre-existing failure is attributed before new work begins.

## 3. Gate 1: freeze one shared teaching contract

The lead posts this contract to all three agents before parallel edits. Changes to it require the lead to notify every dependent agent and record the change in `docs/finance-overlay-implementation-log.md`. Use the same synthetic identities and dates in code, prose, diagrams, and expected-output tables; do not invent a second example in a manuscript section.

| Item | Fixed teaching case |
| --- | --- |
| Instruments | `EQ1` and `EQ2` are stable `instrument_id` values. `EQ1` changes its displayed symbol from `AAA` to `AAB` effective 2026-01-09; ticker is never the join key. |
| Universe | `EQ2` is a member at the first decision and no longer a member at the second, through a historically available delisting/membership event effective 2026-01-12. Preserve its earlier membership. |
| Fundamental | For `EQ1`, one observation with `period_end=2025-12-31`: revision `F1` has value 100 and `available_at=2026-01-06T14:00:00Z`; revision `F2` has value 95 and `available_at=2026-01-10T14:00:00Z`. Both stay in the fixture. |
| Decisions | `D1=2026-01-07T21:05:00Z`; `D2=2026-01-13T21:05:00Z`. Both occur after the synthetic session close. `D1` selects `F1`, symbol `AAA`, and a universe containing `EQ2`; `D2` selects `F2`, symbol `AAB`, and a universe excluding `EQ2`. |
| Split | `EQ1` has a synthetic 2-for-1 split, announced and available on 2026-01-08, effective 2026-01-09. Raw prices are never overwritten. For a `D2` comparison expressed in post-split share units, multiply a pre-split raw price by 0.5; `D1` must not consume the later factor. |
| Sessions and prices | Use a small explicit calendar with timezone and session IDs, including closed 2026-01-11, plus enough price rows before/after each decision to build a feature and a future-only label. A label uses the next open session, never a closed date. Prices are synthetic and carry `event_at`, `received_at`, and `available_at`. |
| Boundary | A row with `available_at == decision_at` is eligible. One microsecond earlier than that timestamp does not see it. Tied revisions use a stable `revision_id` ordering chosen and documented by Agent A. |
| Feed | Invented feed `SIM`, channel `A`, session `2026-01-07`: receive sequences 10, 11, 13, duplicate 13, then repair 12. Include channel `B` and a new session with independent sequences. A gap leaves channel A incomplete until repair 12 is applied, then buffered 13 can be released. |

Freeze these shared field names now: `kind`, `instrument_id`, `revision_id`, `available_at`, `received_at`, `effective_from`, `effective_to`, `period_end`, `event_at`, `session_id`, `symbol`, `raw_close`, and `value` for the PIT fixture; `feed`, `channel`, `session`, `sequence`, `kind`, and `repair_of` for the feed fixture. Agent A and Agent B may add necessary fields, but they must send their full field dictionaries to Agent C and the lead as their first handoff, before Agent C finalizes examples or the lead finalizes the contract. For the PIT fixture, distinguish `period_end` or `effective_from` from public/reported time, `received_at`, and pipeline `available_at`; do not infer one clock from another. Both labs use the same decision-boundary rule and UTC timestamp syntax.

**Exit:** Lead confirms the golden D1/D2 results, event order, shared field names, and `<=` boundary in the implementation log. Agent C may draft conceptual text in parallel but must wait for the two lab owners' full field dictionaries before finalizing examples or listings.

## 4. Parallel workflow: Agent A, PIT lab

- [x] Create `pit_case.jsonl` with typed synthetic record kinds for historical symbol mapping, membership, fundamental revisions, split, calendar, and raw prices. Every record declares its grain and relevant clocks; no live vendor names or real prices appear.
- [x] Implement an offline DuckDB query that filters by `available_at <= decision_at`, chooses an available revision deterministically, and applies the business-valid interval **from the revision visible at that decision**. For fundamentals, choose the latest eligible `period_end`, then the latest eligible revision. Keep missing observations visible as missing rather than silently dropping decision rows.
- [x] Build a small decision/feature/label output and a deliberately wrong latest-value comparison. Ensure labels use future sessions and cannot enter feature selection. Preserve raw prices; apply the documented split comparison only when its knowledge and effective boundaries permit.
- [x] Emit a stable run manifest containing fixture hash, code/query version or hash, decisions, parameters, selected revision IDs, and output hash. Exclude wall time and absolute paths from the deterministic core.
- [x] Add focused tests for D1/D2 golden values, unavailable and exact-boundary revisions, tied revisions, historical membership/symbol mapping, join uniqueness, split timing, feature/label separation, and repeatability. Use standard-library `unittest` with the existing pinned DuckDB dependency.
- [x] Send the full field dictionary early, then send the lead and Agent C the minimal tested SQL snippet, result table, and command/test transcript. Stop editing owned files after handoff unless the lead requests a fix.

**Done when:** The lab runs without network access or credentials; all PIT tests pass; its output proves `F1` before correction and `F2` after correction; no selected row has `available_at > decision_at`.

## 5. Parallel workflow: Agent B, feed-sequence lab

- [x] Create `feed_sequence.jsonl` with the fixed channel-A gap, duplicate, recovery record, an independent channel, and a new session. State whether sequence numbers count messages or packets in this invented protocol, and make that rule consistent throughout.
- [x] Implement a deterministic checker that tracks expected sequence per `(feed, channel, session)`, buffers later messages behind a gap, ignores exact duplicates, reports out-of-order arrivals separately, and marks affected output incomplete until the fixture's repair record fills the gap. Never reset or bridge sequence state across channels or sessions.
- [x] Add tests for gap vs duplicate, independent sequence scopes, recovery order, missing repair, and repeated identical output. Use standard-library `unittest`; no broker, socket, or vendor API.
- [x] Send the full field dictionary early, then send the lead and Agent C a short trace with expected sequence, received sequence, incomplete/complete state, and the invented recovery policy. Stop editing owned files after handoff unless the lead requests a fix.

**Done when:** The initial `10,11,13` produces an incomplete gap for 12; repair 12 restores a complete 10–13 span; channel B and the next session are unaffected.

## 6. Parallel workflow: Agent C, early manuscript and figures

- [x] Add an optional finance reading route to front matter and a short scope note to Section 1. Keep the generalist quick start and existing section hierarchy intact.
- [x] In Section 2, explain exchange/event, receipt, and availability clocks; sequence domains; and protocol-dependent gap recovery. Reuse the existing event-time/watermark figure. If a new gap figure does not teach more than a compact table, omit it and tell the lead.
- [x] In Section 3, explain append-only revisions, stable instrument IDs, historical symbol mappings and universe membership, and the distinction between `period_end` and availability. Do not imply ordinary Type 2 validity dates alone solve two-clock PIT queries.
- [x] In Section 4, replace the existing misleading `is_final` paragraph with a precise current-view-versus-historical-view explanation. Add one short, classified, labelled PIT SQL listing, verified against Agent A's local query; explain feature/label windows and the synthetic split convention. Keep the existing OHLCV listing and its alignment test valid.
- [x] Add `fig:sec04-pit-revision-timeline` as a manuscript sentinel paired with `fragments/fig-sec04-pit-revision-timeline.tex`. Include caption, `source={Author's synthesis.}`, and descriptive accessibility text. Add `fig:sec02-finance-gap-repair` only if it improves the explanation at A4 size, and pair it with its fragment.
- [x] Report the exact sections, listing ID, figure IDs, and links that the lead must add to references or guidelines. Stop editing owned files after handoff unless the lead requests a fix.

**Done when:** The new prose matches the tested fixture outputs, has no hard-coded figure numbers or extra H1/H3 headings, and makes clear that today's `fct_hourly_ohlcv.is_final` cannot replay yesterday's knowledge state.

## 7. Parallel workflow: lead, later manuscript and integration draft

- [x] In Section 5, teach a simulated decision clock and deterministic run manifest; make replay read versioned inputs, not today's corrected rows.
- [x] In Section 6, add scoped market-data quality/reconciliation checks. Say which checks run on trade-only synthetic data and which (stale/crossed quotes) need quote records absent from this lab. Do not duplicate the existing generic quality material.
- [x] In Section 7, add a compact PIT contract example or extension with field meanings, clock source, correction policy, owner, and availability target. Do not edit the existing BTCUSDT `curated_trades` contract so that it falsely promises finance PIT semantics.
- [x] In Section 8, add one narrow decision table covering research freshness, replay cost, and operating latency; make no alpha-decay or production execution claims.
- [x] In Section 9, revise the existing **Finance or quant data** option inside Milestone 7 to point to the finance lab. Explain that the existing current-view BTCUSDT table alone does not retain correction history. Do not add Milestone 8 or turn all finance topics into required work.
- [x] Add only missing glossary entries and sources that support actual manuscript claims. Update `companion/finance/README.md` after both lab outputs are stable; link it from `companion/README.md`. Update `publication-guidelines.md` only for figures actually added.

**Done when:** Later sections use the same clocks, IDs, and limits as the labs, and no section claims the toy exercise is an execution simulator or a compliance implementation.

## 8. Gate 2: integrate the four handoffs

- [x] Lead stops parallel writes and reviews every changed file against the spec and Gate 1 golden table. Record each agent's handoff and any contract change in the implementation log. Resolve disagreements with the owner first; then the lead owns all cross-file fixes.
- [x] Check that the Section 4 PIT listing and Agent A's executed query have equivalent predicates, ranking, and tie-break semantics. If the book uses shorter illustrative SQL, label it accurately and state omitted setup; do not call an unexecuted fragment runnable.
- [x] Check all new figure sentinels have exactly one matching fragment and unique semantic labels. Update figure inventory only for fragments actually included.
- [x] Check that Section 9's old claim about reproducing correction history is qualified and that no other new prose treats `ingested_at`, `is_final`, or a latest-value table as proof of historical availability.
- [x] Check the companion README's commands and expected outputs against actual command transcripts. Keep the original BTCUSDT quick-start command and fixtures unchanged.

**Exit:** One coherent diff, no workers editing, and a written list of any deferred follow-ups. Do not postpone a failing acceptance criterion as a follow-up.

## 9. Gate 3: verification and publication

- [x] Run the PIT lab and feed lab twice from the documented commands. Run `companion/.venv/bin/python -m unittest discover -s companion/finance/tests -v`. Compare the deterministic output/manifests.
- [x] Run `companion/.venv/bin/python companion/scripts/run_all.py` and `python3 companion/scripts/test_manuscript_sql_alignment.py`; confirm the original 49/48/3 results and alignment check.
- [x] Run ReportKit's validation and a **combined release build** from a fresh, ignored output root. Do not reuse a stale `build/combined/` directory. In this workspace the engine is at `../report-kit`; initialize the selected output root's render environment per `README.md` if needed.
- [x] Inspect the generated A4 PDF pages that contain new text, listing, table, or figure: readable labels, no overflow, no unresolved sentinels, no raw `\label` text, and correct cross-references. Verify that every new figure has a caption and descriptive text.
- [x] Review `git diff --check`, changed-file ownership, glossary ordering, reference style/access dates, and `git status --short`. Do not include generated outputs, virtual environments, or scratch files in the implementation change set unless the user explicitly asks for them.

**Release gate:** All criteria in `docs/finance-overlay-spec.md` Section 6 pass. The lead reports the commands, observed results, PDF build status, material limitations, and exact changed files. The lead does not describe the overlay as implemented until this gate passes.

## 10. Agent launch briefs

Use these as the task briefs after Gate 1. Each agent should read `docs/finance-overlay-spec.md` and this plan before editing.

- **Agent A:** “Implement Section 4 of this plan: the synthetic PIT fixture, DuckDB/Python lab, and focused tests. Edit only your owned files. Return your field dictionary, golden D1/D2 output, tested query, commands, and any unresolved semantic decisions.”
- **Agent B:** “Implement Section 5 of this plan: the synthetic scoped-sequence fixture, checker, and focused tests. Edit only your owned files. Return the invented feed contract, gap/recovery trace, commands, and unresolved decisions.”
- **Agent C:** “Implement Section 6 of this plan: front matter and Sections 1-4 plus the approved figure fragments. Edit only your owned files. Coordinate listing fields and example outcomes with Agent A, feed semantics with Agent B, and return changed anchors and print concerns.”
- **Lead:** Own Gate 0 and Gate 1, implement Section 7 during parallel work, then run Gates 2 and 3 alone. Resolve cross-file changes and report measured evidence.
