# Optional finance research labs

These two offline exercises extend the guide with synthetic point-in-time
equity research inputs and a scoped feed-sequence gap. They teach how data
availability, revisions, reference data, labels, and sequence recovery affect
reproducibility. They are not a trading strategy, an execution simulator, a
vendor-feed implementation, or evidence of production or regulatory controls.

The data is invented for this guide. No market, broker, issuer, or vendor
service is contacted, and no credentials are needed. The PIT runner creates
an in-memory DuckDB database; it writes no database or generated output file.

## Requirements and commands

Use the pinned companion environment from the repository root. If it is not
set up yet, follow the [main companion setup](../README.md#running-it), which
installs DuckDB 1.1.3.

Run each lab and the focused tests:

```bash
companion/.venv/bin/python companion/finance/scripts/run_pit_case.py
companion/.venv/bin/python companion/finance/scripts/check_feed_sequence.py
companion/.venv/bin/python -m unittest discover -s companion/finance/tests -v
```

Each script uses a fixture next to itself and produces deterministic output.
To check repeatability, run each script twice and compare the output. The PIT
manifest omits wall time and absolute paths; its fixture, code, query, and
output hashes change when their corresponding inputs change.

## PIT fixture and clock assumptions

`fixtures/pit_case.jsonl` is a typed union of synthetic record kinds. Every
row has a unique `record_id` and declares its grain. The kinds are decisions,
symbol mappings, membership versions, fundamental revisions, a split, a
small session calendar, and daily raw closes. Key clocks are separate:

- `event_at` is the source or exchange event time;
- `received_at` is when the local pipeline receives the record;
- `available_at` is the first explicit time the validated record can be used;
- `period_end` describes a fundamental's reporting period;
- `effective_from` and `effective_to` describe a half-open business interval
  `[effective_from, effective_to)`.

All timestamps are explicit UTC values. The synthetic session calendar names
`America/New_York`, includes session IDs, and marks 2026-01-11 closed. A
fundamental's period end is never used as its publication time. At decision
time `t`, availability is inclusive: `available_at <= t`. When eligible
revisions tie on availability, the lexicographically greatest `revision_id`
wins. The fixture is deliberately small and does not represent a
vendor-quality historical universe. F2 is eligible at exactly 2026-01-10
14:00:00 UTC; one microsecond earlier, F1 remains the latest eligible
revision.

The fixed decisions use stable `instrument_id` values. EQ1 changes its
displayed symbol from AAA to AAB effective 2026-01-09. EQ2's earlier
membership remains visible at D1 and a later available interval revision ends
that membership effective 2026-01-12. For EQ1's 2025-12-31 fundamental, F1
has value 100 and is available 2026-01-06 14:00 UTC; F2 corrects it to 95 and
is available 2026-01-10 14:00 UTC.

The result demonstrates the decision-time selection:

| Decision | Fundamental | Symbol | Universe | Feature close | Next-open label | Split comparison |
| --- | --- | --- | --- | --- | --- | --- |
| D1, 2026-01-07 21:05 UTC | F1 = 100 | AAA | EQ1, EQ2 | Jan 7: 100 | Jan 8: 102 | No factor was available. |
| D2, 2026-01-13 21:05 UTC | F2 = 95 | AAB | EQ1 | Jan 13: 55 | Jan 14: 56 | Jan 8 raw 102 × 0.5 = 51 post-split units. |

The deliberately wrong latest-value view selects F2 = 95 for D1. Each
selected input's `available_at` is checked against its decision. Features use
only records with event and availability times at or before the decision;
labels begin after the decision and use the next open session, so they are
evaluation outputs rather than feature inputs. Raw closes remain unchanged.
The 2-for-1 split was announced and available on Jan 8, effective Jan 9; only
D2 uses its stated 0.5 comparison factor for the pre-split raw close.

The printed manifest records fixture, script, query, and output SHA-256
hashes, decision parameters, and selected record or revision IDs for the
fundamental, symbol, membership, split, feature, and label inputs. It is
reproducibility evidence for this local exercise, not tamper-proof audit
storage.

## Feed-sequence fixture and recovery rule

`fixtures/feed_sequence.jsonl` declares an invented feed named `SIM`.
Sequence numbers count logical feed messages, not network packets or
transmissions. The independent sequence scope is exactly
`(feed, channel, session)`. The fixture uses channel A on session 2026-01-07
with arrivals 10, 11, 13, duplicate 13, then repair 12. Channel B and channel
A on a new session have independent state.

The checker initializes a scope from its first observed sequence, buffers a
later sequence behind a gap, ignores a repeated applied or buffered number,
and reports an unseen lower arrival as out of order. The affected channel
stays incomplete while 13 is buffered behind expected 12. A repair must carry
the expected sequence and identify its stable logical message ID in
`repair_of`; after repair 12 is accepted, buffered 13 is released and the
scope becomes complete through 13, with 14 next expected. This is one
deterministic policy for the local fixture. Other feed protocols use their
own recovery rules; this script does not call or implement one.
