# Finance Overlay Implementation Log

## Baseline and shared contract

Started 2026-09-26. The pre-existing working-tree state was:

```text
?? .superpowers/
?? docs/finance-overlay-spec.md
?? docs/superpowers/plans/2026-09-26-finance-overlay.md
```

`.superpowers/` is preserved untouched. The two untracked finance source documents are part of the requested change set.

Baseline commands, run before implementation:

- `companion/.venv/bin/python companion/scripts/run_all.py` — passed; 49 raw events, 49 curated rows, 48 deduplicated trades, 3 hourly bars, all quality checks passed.
- `python3 companion/scripts/test_manuscript_sql_alignment.py` — passed; the hourly OHLCV listing aligns with the companion SQL shape.
- ReportKit entry point is available at `../report-kit/publication_pipeline/scripts/publication_build.py`. Final build will use a fresh ignored output root.

The manuscript order is the existing front matter and Sections 1–11. Section 9 currently has six optional Milestone 7 tracks; the finance track will be revised in place. Existing figure sentinels pair with fragments under `fragments/`.

### Frozen teaching contract

- `EQ1` and `EQ2` are stable instrument IDs. `EQ1` maps from `AAA` to `AAB` effective 2026-01-09. `EQ2` is in the historical universe for D1 and removed by a historically available event effective 2026-01-12.
- For `EQ1`, period end 2025-12-31 has revision F1 (100, available 2026-01-06T14:00:00Z) and F2 (95, available 2026-01-10T14:00:00Z). Preserve both revisions.
- Decisions: D1 2026-01-07T21:05:00Z and D2 2026-01-13T21:05:00Z, after the synthetic session close. D1 selects F1 / AAA / universe including EQ2; D2 selects F2 / AAB / universe excluding EQ2.
- EQ1 has a 2-for-1 split announced and available 2026-01-08, effective 2026-01-09. Preserve raw prices; a D2 comparison in post-split units applies 0.5 to pre-split raw prices. D1 cannot use the future factor.
- The explicit calendar includes timezone, session IDs, and closed 2026-01-11. Labels use the next open session and begin strictly after a decision. Prices carry event, receipt, and availability timestamps.
- Availability is inclusive (`available_at <= decision_at`); equality is eligible. Tied revisions use a documented stable revision-ID ordering. No chosen row may have availability after its decision.
- Feed SIM / channel A / session 2026-01-07 receives sequences 10, 11, 13, duplicate 13, repair 12. Include independent channel B and another session. Channel A remains incomplete until repair 12 is applied and buffered 13 released.
- Frozen shared names: PIT `kind`, `instrument_id`, `revision_id`, `available_at`, `received_at`, `effective_from`, `effective_to`, `period_end`, `event_at`, `session_id`, `symbol`, `raw_close`, `value`; feed `feed`, `channel`, `session`, `sequence`, `kind`, `repair_of`. Labs may add fields and must report full dictionaries to the lead and manuscript owner before examples are finalized.

## Handoffs and verification

### Agent B handoff — feed-sequence lab

- Fields: required shared `feed`, `channel`, `session`, `sequence`, `kind`, `repair_of`; additions `arrival_index`, unique transmission `message_id`, UTC `event_at` and `received_at`, and synthetic `payload`.
- Sequence numbers count logical messages, not transport packets. State is scoped to `(feed, channel, session)`. The first observed number initializes that scope; a later number buffers behind a gap; duplicates are ignored; unseen lower arrivals are reported as out of order. A repair must identify the logical ID `feed/channel/session/sequence`, fill the currently expected number, then releases contiguous buffered messages.
- Observed trace: channel A on 2026-01-07 accepts 10 and 11; 13 buffers and marks the scope incomplete while expecting 12; repeated 13 is a duplicate; channel B and A on 2026-01-08 progress independently; repair 12 releases `[12, 13]`, restoring channel A to complete with next expected 14.
- Agent command `companion/.venv/bin/python companion/finance/scripts/check_feed_sequence.py` succeeded; `companion/.venv/bin/python -m unittest discover -s companion/finance/tests -v` passed 6 tests. Lead reviewed the owned files and asked the agent to stop editing.

### Agent A handoff — PIT lab

- Fixture uses an explicit union schema for decisions, symbol mappings, membership versions, fundamental revisions, split, calendar, and raw prices. It carries a unique `record_id`, kind-specific grain and record key, stable instrument/revision IDs, explicit UTC clocks, effective/report dates, session data, and the split convention. Calendar timezone is `America/New_York`; business intervals are half-open.
- Fundamental selection filters `period_end <= decision_date` and `available_at <= decision_at`, then orders by period end descending, availability descending, and lexicographically greatest revision ID. The query uses a left lateral join so decisions with no eligible observation remain visible. Equality at the decision boundary is eligible; the one-microsecond-before case excludes F2.
- Golden: D1 selects F1=100 / AAA / EQ1+EQ2 / S20260107 close 100 / S20260108 label close 102 / no split factor. D2 selects F2=95 / AAB / EQ1 / S20260113 close 55 / S20260114 label close 56 / Jan 8 raw 102 × 0.5 = 51 post-split units. The deliberately wrong current view gives D1 F2=95. A test also confirms closed Jan 11 is skipped for D3's next-open label.
- Agent reported 11 PIT tests passing. During integration review, the lead extended the manifest's selected source IDs to include symbol, split, feature, previous-feature, and label records, in addition to fundamentals and membership. The pre-landing review also found that a decision after a split announcement but before its effective date must not use the factor. The runner now requires both availability and effective-date eligibility, and the split test covers that boundary. After these corrections, the PIT suite passed and the documented script printed the golden D1/D2 table and deterministic manifest.

The companion README now links the optional lab and the new finance README documents fixture grains, clocks, expected results, commands, and limitations.

Lead manuscript changes: Sections 5–9 now include simulated-time replay and evidence, scoped market-data checks, an optional PIT contract, research/replay/latency trade-offs, and a revised Milestone 7 finance route. Glossary additions and protocol references are recorded in the working diff. Final review confirmed the Section 4 listing semantics, figure pairing, Section 9 correction-history wording, and companion command examples.

### Gate 3 — verification and publication

- Both documented lab commands were run twice. PIT output including the deterministic manifest matched byte-for-byte; feed trace output matched byte-for-byte.
- `companion/.venv/bin/python -m unittest discover -s companion/finance/tests -v` — passed 17 tests, including the announced-but-not-effective split case.
- `companion/.venv/bin/python companion/scripts/run_all.py` — passed with 49 raw events, 49 curated rows, 48 deduplicated trades, and 3 hourly bars; all ten original quality checks passed.
- `python3 companion/scripts/test_manuscript_sql_alignment.py` — passed; the original hourly OHLCV listing remains aligned with companion SQL.
- `python3 ../report-kit/publication_pipeline/scripts/validate_publication.py --root . --profile release` — passed: 12 manuscripts, 22 visuals, 22 labels, no image slots.
- Combined ReportKit release build from the fresh ignored output root `build/finance-overlay-release-pr` — passed, A4, 85 pages. Build diagnostics reported zero publication, layout, unresolved-reference, missing-asset, or blocking errors; 25 nonblocking package warnings came from the current local toolchain. The ReportKit PDF inspection found zero errors and blank pages.
- Visual review covered the new route and scope note, clock and feed explanation, storage history, PIT figure/listing and corrected `is_final` explanation, replay, quality checks, contract, decision table, Milestone 7, and references. The first build showed the small clock table split across a page break, so it was replaced with compact prose; the final build shows the clock definitions together and the feed recovery table intact. The PIT timeline and SQL listing are readable at A4 size with no overflow or raw sentinel/label text.
- `git diff --check` — passed. The spec and completed plan were present as untracked source documents before implementation and are included in the reviewable change; `.superpowers/` remains untouched. The build's automatic `reportkit.lock` update was restored because the lock was clean before the run; generated output and PDF remain under ignored `build/`.

### Final ownership summary

Changed project files are the companion README, the seven files under `companion/finance/`, manuscript front matter and Sections 1–11, the new `fragments/fig-sec04-pit-revision-timeline.tex`, `publication-guidelines.md`, the finance overlay spec and completed plan, and this implementation log. No BTCUSDT fixture, `companion/scripts/run_all.py`, or ReportKit engine file was changed. The Section 2 gap mechanism uses a compact table; no second feed-gap figure was added.
