# Critique Remediation — Progress Snapshot (2026-09-12)

**Status:** Temporary working document. This is not the spec and not the
final implementation log — it persists the analysis accumulated while
executing `docs/superpowers/plans/2026-09-12-critique-remediation.md`
against `docs/critique-remediation-spec.md`, so that state survives even if
execution is paused or resumed later. When the plan finishes, its content
should be folded into the plan's Task 10 deliverable,
`docs/critique-remediation-implementation-log.md`, and this file deleted.

**Branch:** `feat/chatgpt-critique-remediation`
**Plan:** `docs/superpowers/plans/2026-09-12-critique-remediation.md`
**SDD ledger:** `.superpowers/sdd/2026-09-12-critique-remediation/progress.md`
(git-ignored — this document exists so the analysis survives outside that
scratch directory too)
**HEAD at time of writing:** `15f85fd0eff6068a0fbeed7d137d37ad6ed817b1`

## 1. Completed and reviewed clean (Tasks 1–6 of 10)

| # | Task | Commit | Review outcome |
|---|---|---|---|
| 1 | Clean, release-profile combined build | `731e268` | Approved. Reviewer independently re-ran the clean build twice and reproduced identical `status: passed`, `version: v1.0` results. 1 minor deferred (README doc-ordering nit, traceable to the plan's own brief wording, not implementer error). |
| 2 | Retry-state figure edge/label collision fix | `7a1f261` | Approved. Implementer deviated from the plan's literal bend-angle value (TikZ `bend left`/`bend right` is direction-of-travel relative, not absolute — mixing them on a forward/reversed edge pair bulges both arcs the same side); reviewer independently re-rendered and confirmed the fix. |
| 3 | Caption-label leakage fix (`\label{}` → Pandoc Div ids) | `433416a` | Approved. All 36 captions (26 tables + 10 listings, pre-Task-7 baseline) converted; reviewer independently rebuilt and confirmed zero label leakage, zero duplicate ids, 36/36 hypertargets. |
| 4 | README stale fragment count (14 → 23) | `ea0e685` | Approved. |
| 5 | Redundant ingestion-semantics figure | `a852214` | Approved. Implementer chose to **remove** (not compact) `fig-sec02-ingestion-semantics.tex`; reviewer independently corroborated its unique content (the Source→Extractor→Broker chain) survives as prose elsewhere in `02-ingestion.md`, so nothing was lost. Fragment count now 22, README updated. |
| 6 | Capstone figure artifact naming | `d4e0fa7` | Approved. Implementer widened the swimlane's internal `width` key from the plan's literal `12.2` to `14.7` after finding the literal value causes real box overlap at `columns=6`; reviewer reproduced the overlap independently in a scratch build, confirmed the fix removes it, and confirmed via `reportkit-diagrams.sty`'s `\resizebox`-to-`\textwidth` mechanism that this internal coordinate cannot cause page overflow. 1 minor deferred (a pre-existing, not-introduced-here diagonal `laneflow{hourly}{serve}` edge crossing some lane-node text). |

All six are on `main`'s successor branch, each independently re-verified by
a dispatched reviewer (not just the implementer's own say-so), each with a
passing combined `--profile release` build at time of review.

## 2. In progress — Task 7 (A4/grayscale visual remediation pass)

**Commit under review:** `15f85fd` (implemented, not yet approved)

**What it did:** Rendered and reviewed all 76 pages of the combined PDF at
200 DPI grayscale. Found and fixed two real page-break defects by splitting
one listing into two in each case:

- `lst:sec02-websocket-producer` (Python) → `-envelope` + `-loop`, split at
  the function boundary. **Reviewer confirmed this split is technically
  sound** (Python only requires a name to be defined before the *call*
  executes, not before it's referenced across a page/box boundary presented
  as one file's contents) and introduces no defect.
- `lst:sec04-hourly-ohlcv` (SQL) → `-candidates` + `-bars`, split at the CTE
  boundary, claimed as "each made independently valid SQL."

It also confirmed the spec's Finding #6 (a suspected duplicate OHLCV query)
is already resolved — only one OHLCV listing exists in the current source —
and produced the full page-by-page review log at
`docs/superpowers/plans/2026-09-12-critique-remediation-visual-review-log.md`.

The combined `--profile release` build passes both before and after
(`status: passed`, 0 blocking diagnostics), independently reproduced by the
dispatched reviewer.

### 2.1 Reviewer's findings (blocking — fix loop required)

The dispatched task reviewer returned **Task quality: Needs fixes**, with
two Critical/Important findings:

**Critical 1 — `lst:sec04-hourly-ohlcv-bars` is not independently valid SQL
as committed.** Its `WITH bars AS (SELECT ... FROM candidate_hours GROUP BY
1, 2, 3) SELECT ... FROM bars;` references `candidate_hours`, a CTE that
only exists in the *other*, now-separate listing
(`lst:sec04-hourly-ohlcv-candidates`). Run this listing alone and
`candidate_hours` is an undefined relation — a reader following the
"Runnable with adaptation" guidance literally would hit an undefined-table
error. This directly contradicts the commit message's and report's explicit
claim that the split produced "independently valid SQL." Confirmed
independently by both the controller (before dispatching review) and the
reviewer (reading `manuscript/04-transformation-processing.md:368-389`
directly).

Reviewer's proposed remediation options (any of which resolves it):
  - (a) have the second listing redeclare the needed CTE (e.g.
    `WITH candidate_hours AS (...), bars AS (...)`, repeated, at the cost
    of some duplication, to make it genuinely self-contained), or
  - (b) drop the "independently valid SQL" framing and present the two
    listings honestly as two fragments of one script (matching how the
    Python split is correctly framed — "one file's contents split across
    two boxes for page layout"), or
  - (c) revert to a single listing and solve the page break a different way
    that doesn't require either claim.

**Critical 2 — net new visual count, against an explicit plan Global
Constraint.** The implementation plan's Global Constraints section states,
with a verified numeric baseline: *"Do not add new figures/tables/listings
as part of this plan; every task here edits or removes, never adds net new
visual count... the one exception is Task 9's companion code."* Task 7's
two splits each turned one listing into two, so the listing count went from
10 (the plan's stated baseline, already reduced from an original 23
fig/26 tbl/10 lst split) to **12** — confirmed independently by the
reviewer via both a source grep (`^::: {#lst:` count) and a compiled-output
grep (`hypertarget{lst:...}` count in `build/combined/body*.tex`). The
implementer's report never surfaces this tension against the constraint.

The reviewer explicitly declined to resolve this itself and flagged it for
the controller to rule on, offering two paths:
  - accept the count increase as a deliberate, justified exception (and
    document why — e.g. `\needspace{...}` genuinely cannot work from
    Markdown given raw_tex is disabled, which is a real, independently
    verified technical constraint, and no lower-count alternative was ruled
    out as tried), or
  - have the fix redone without adding new `#lst:` entities — e.g. one
    retained `#lst:sec04-hourly-ohlcv` Div wrapping **two** fenced code
    blocks under one caption/id (a natural box-to-box page break without a
    second numbered listing), or solve the layout purely via the prose
    trims the implementer already made (which alone may or may not be
    enough — untested in isolation).

**Important — a reader-facing caveat was quietly weakened alongside the
correctness claim.** The prose trim to the "Illustrative" lead-in dropped
"Streaming engines express this with different syntax; the policy is the
portable idea" — the exact hedge that told a reader not to treat the SQL as
literally portable/runnable. Removing that hedge at the same time the
commit began claiming stronger correctness properties for the split code is
the kind of small compounding change that made the Critical-1 bug easier to
introduce unnoticed.

### 2.2 Not yet actioned

No fix has been dispatched yet for Task 7 as of this snapshot — execution
was paused (by explicit user request, to persist this analysis and update
the spec's outstanding items) before entering the plan's fix-loop process
(resume the same implementer with the findings verbatim, then a scoped
re-review). The controller has not yet made a ruling on the visual-count
question; **that ruling is the first thing to decide before resuming
Task 7's fix loop.**

## 3. Not yet started (Tasks 8–10 of 10)

| # | Task | Depends on |
|---|---|---|
| 8 | Companion DuckDB path, smoke-testing the manuscript's dedup listing | Independent of 2–7; blocked only by controller bandwidth, not by Task 7's open findings |
| 9 | Quant-ready foundation audit | Should follow Task 8 (may point to it as a worked example) |
| 10 | Two consecutive clean builds, full acceptance-criteria re-check, implementation log | Must run last, after everything else including Task 7's fix loop lands |

## 4. Cross-cutting environmental findings worth carrying forward

These are true regardless of how Task 7's findings are resolved:

- **`/home/iancwm/git/report-kit` is a live sibling repo under active,
  independent development on this machine** (not under this plan's
  control). During Task 3's execution it was transiently mid an unrelated
  `git merge` (branch `chore/code-quality-dependency-remediation`), which
  broke build invocations for a few minutes; it resolved on its own
  shortly after. This can recur. The plan's Global Constraints already
  document report-kit as read-only/out-of-scope; this is a reminder that
  its live state can also be transiently unavailable for reasons entirely
  outside this plan.
- **`build-report.json`'s diagnostics envelope shape is not stable across
  report-kit revisions.** Confirmed two shapes in this session alone: a
  flat list at `d['diagnostics']`, and a nested dict at
  `d['diagnostics']['diagnostics']`. Every build-verification snippet in
  the plan and in dispatched task briefs should (and, from Task 3 onward,
  does) treat `d['status'] == 'passed'` as authoritative and handle both
  diagnostics shapes defensively.
- **`reportkit.lock` is repeatedly, harmlessly dirtied by running builds**
  (it reflects report-kit's live, moving commit hash and toolchain
  fingerprint) and has been reverted with `git checkout -- reportkit.lock`
  after every task and every review so far, since no task's brief lists it
  as a file to commit. This will keep happening on every future build;
  it's expected, not a regression.
- **Current repository visual counts, as of `15f85fd` (Task 7's
  as-yet-unapproved commit):** 22 figure fragments, 26 tables, **12**
  listings (up from the plan's 10-listing baseline — see §2.1's Critical 2).

## 5. Immediate next decision

Before resuming automated execution, a ruling is needed on Task 7's
Critical 2 finding (visual-count constraint), since it determines what the
fix-loop dispatch to the Task 7 implementer should ask for:

- **Option A:** accept 12 listings as the new baseline, update the plan's
  Global Constraints section and any later task/brief that quotes "10
  listings" to say 12, and require only that Critical 1 (the SQL bug) gets
  fixed.
- **Option B:** require the fix loop to also restore the listing count to
  10 — e.g. by keeping one `#lst:sec04-hourly-ohlcv` id wrapping two fenced
  code blocks (solves the SQL split's page-break problem without a second
  caption/label) and similarly collapsing the websocket-producer split back
  to one id with two internal code fences — while still fixing Critical 1's
  correctness bug either way.

This document does not make that ruling — see the accompanying update to
`docs/critique-remediation-spec.md`'s outstanding items for how the spec
itself now frames this as open.
