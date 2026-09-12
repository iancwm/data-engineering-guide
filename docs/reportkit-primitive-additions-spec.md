# ReportKit Primitive Additions — Minimal Implementation Spec

**Status:** Engine shipped; consumer migration complete for all four
findings, plus the related `fig-sec07-lineage.tex` cleanup from §4/§6. One
new engine bug was found and locally worked around during migration (see
§2, Watermark) — worth filing against report-kit separately.  
**Date:** 2026-09-07 (spec); progress updated 2026-09-12  
**Consumer reviewed:** `/home/iancwm/git/data-engineering-guide`  
**Engine reviewed:** `/home/iancwm/git/report-kit` at `71c8bd960efda48721c99cac9624bc4bac91abfe`  
**Engine shipped:** `report-kit` commit `a63208c` ("feat: add positioned report
primitives"), now on `main` at `6527036`

## Progress summary

The engine side of this spec is fully implemented, tested, and documented in
report-kit — nothing further is needed there. The consumer repo has now
migrated all four findings, plus the separate `text width=24mm` cleanup in
`fig-sec07-lineage.tex` that §4/§6 tracked alongside them.

| # | Finding | Engine | Consumer migration |
|---|---|---|---|
| P0 | Swimlane `columns=` | Done | **Migrated** — `fig-sec06-capstone-milestones.tex` now passes `columns=5`; all 5 columns confirmed inside the declared 12.2cm width |
| P0 | Positioned/routed state & DAG branches | Done | **Migrated** — `fig-sec05-retry-state.tex`, `fig-sec05-orchestration-dag.tex` (commit `8b4ed24`) |
| P1 | Architecture annotation | Done | **Migrated** — `fig-sec08-platform-boundaries.tex` (commit `8b4ed24`) |
| P1 | Watermark `label-position` | Done | **Migrated** — `fig-sec02-event-time-watermark.tex` now uses `\watermark[label-position=below,label-width=...]` with descriptive labels; required a local per-fixture workaround for an engine bug (see §2) |

Consumer commits: `bcfa9da` (content pass, bumped `reportkit.lock` to
`71c8bd9`, added the new fixtures using the *old* raw-primitive style),
`8b4ed24` (migrated the retry-state, orchestration-DAG, and
platform-boundaries fixtures to the new API), plus this pass (swimlane
columns, watermark labels, lineage `text width` cleanup — not yet committed
as of this doc update).

## 1. Purpose

Make the semantic primitives sufficient for the figures now used by the guide
without adding a general-purpose layout engine. The additions should remove
raw-coordinate workarounds, make sizing keys truthful, and provide regression
coverage for the failure modes exposed by the current content.

## 2. Findings

### P0 — Make swimlane columns derive from the declared width

**Engine status: done.** `reportkit-process.sty` now supports `columns=`,
`node width=`, `column spacing=`, and `label gutter=` on `reportswimlane`,
deriving evenly spaced centers inside the declared width and raising a
package error when `columns` is below the highest declared step. Documented
in `SKILL.md` and the changelog.

**Consumer status: migrated.** `fragments/fig-sec06-capstone-milestones.tex`
now passes `columns=5` on `reportswimlane` alongside its existing `lanes=`,
`lane spacing=`, and `width=12.2` keys. No `node width=`/`column spacing=`
override was needed — the engine's automatic even-spacing fit cleanly.
Verified by building section 06 individually
(`publication_build.py --mode section --section 06-quality-reliability.md`,
zero diagnostics) and visually confirming all 5 columns sit inside the
12.2cm lane width with no overlap.

`reportswimlane` accepts `width`, but `\lanestep` places every column at
`#4*2.55` regardless of that width (`latex_templates/reportkit-process.sty`,
lines 45--99). The guide's five-column swimlanes therefore use a hard-coded
coordinate model; column 5 is centered at 12.75 cm while the declared lane
width is 12.2 cm (`fragments/fig-sec06-capstone-milestones.tex:9-18`).

Add width-aware layout keys:

- `columns=<integer>`: declared maximum process column;
- `node width=<length>`: usable node width, defaulting to the current value;
- `column spacing=<length>`: optional explicit override; otherwise derive
  evenly spaced centers inside the declared width; and
- `label gutter=<length>`: reserve space for lane labels without changing the
  process area.

Existing calls without these keys must retain their current appearance. When
`columns` is supplied, all node rectangles and lane edges must remain inside
the declared process width. Edges may be straight for this pass; routing is a
separate requirement below.

### P0 — Support positioned and routed state/DAG branches

**Engine status: done.** `\stateat`, `\terminalstateat`, `\stepat`, and a
routed `\transition`/`\flowedge` option (`route=straight|orthogonal|bend
left=<deg>|bend right=<deg>`, plus `label-position=`) all ship in
`reportkit-grammar.sty` / `reportkit-process.sty`, covered by
`test_positioned_state_branches_and_routed_labels_render` and
`test_positioned_flow_dag_renders_validation_branch` in report-kit's test
suite (both pass).

**Consumer status: migrated** (commit `8b4ed24`). Both fixtures now use the
positioned API:

- `fig-sec05-retry-state.tex` uses `\terminalstateat` and routed, labeled
  `\transition`s (`route={bend left=15}` / `route={bend right=12}`,
  `label-position=below`).
- `fig-sec05-orchestration-dag.tex` uses `\stepat` for every node.

`\RKEdge[...]{optional}{...}` is deliberately kept for the DAG's
validation-error branch: it is the same stable, public primitive that
`\handoff`, `\networkedge`, and `\causaledge` wrap, and `reportflow` has no
dashed/optional edge kind of its own — using it here is correct, not a
leftover raw call. The acceptance bar's "without raw `\RKNode`/`\RKEdge`
calls" language is satisfied for `\RKNode` (fully removed); `\RKEdge` used
for a typed edge kind is the intended API, not the workaround the finding
was about.

Migrating these two fixtures to real positions/routing surfaced two
pre-existing overlap bugs the raw-coordinate version was hiding, confirmed
present before the migration touched them and fixed in the same commit:

- `fig-sec05-retry-state.tex`: `running`→`succeeded` was a straight line that
  passed directly through the colinear `retrying` node (three states
  declared in one sequence with `retrying` physically between the other
  two). Fixed by positioning `retrying` off the main line as a recovery loop
  via `\stateat`.
- `fig-sec05-orchestration-dag.tex`: the `Failed or quarantined` and
  `Blocked downstream` terminal nodes sat 3.15 cm apart (the same spacing as
  the main flow) with a "do not publish" edge label crammed into the gap.
  Fixed by repositioning `Blocked downstream` under `Publish`.
- A TikZ node-border-clipping artifact was also found and fixed: a shallow
  `bend` route between adjacent nodes drew straight through the target
  node's text instead of clipping to its border. Routing through `.north`/
  `.south` anchors (e.g. `running.north`, `retrying.south`) fixes it — worth
  keeping in mind for any future bent transition between nodes that are
  close together.

`reportstate` places ordinary states on one horizontal sequence and
`\transition` always draws a straight segment (`latex_templates/reportkit-grammar.sty`,
lines 20--45). The guide's retry state therefore adds terminal nodes with raw
`\RKNode` coordinates and raw `\RKEdge` calls
(`fragments/fig-sec05-retry-state.tex:9-21`); the retry loop is visually close
to a bidirectional overlap. The compact orchestration DAG has the same issue
and uses seven manually positioned `\RKNode` calls
(`fragments/fig-sec05-orchestration-dag.tex:11-23`).

Add a bounded explicit-layout API while preserving the declaration-order API:

- `\stateat[<style>]{id}{x}{y}{label}` and
  `\terminalstateat[<style>]{id}{x}{y}{label}`;
- a routed transition option supporting `straight`, `bend left=<degrees>`,
  `bend right=<degrees>`, and `orthogonal`; and
- a label-placement option (`above`, `below`, `left`, `right`) for routed
  transitions.

The same routing helper should be available to `reportflow` branches, either
through `\stepat` plus routed `\flowedge`, or an equivalent documented API.
Do not introduce automatic graph layout. Explicit positions keep diagrams
deterministic and make page-fit review possible.

Acceptance requires the retry-state and orchestration-DAG fixtures to compile
without raw `\RKNode`/`\RKEdge` calls, with readable branch labels, no edge
overlap at normal A4 width, and unchanged output for the existing sequential
`reportstate` and `reportflow` examples.

### P1 — Add a first-class architecture annotation

**Engine status: done.** `reportarchitecture` supports `annotation=` and
`annotation-position=top|bottom`, measured inside the primitive's own
bounding box, covered by
`test_architecture_annotation_is_rendered_inside_the_diagram_bounds` (passes).

**Consumer status: migrated** (commit `8b4ed24`). `fig-sec08-platform-boundaries.tex`
now declares `annotation=`/`annotation-position=top` on `reportarchitecture`
and no longer has a raw `\node[...]` after the environment. Visually verified:
the vendor-span note now renders as an integrated typographic line above the
layer stack instead of a separate bordered TikZ box.

`reportarchitecture` models responsibility layers but has no supported place
for a cross-cutting vendor/ownership annotation. The guide currently inserts a
raw TikZ node after the architecture environment
(`fragments/fig-sec08-platform-boundaries.tex:18-22`).

Add optional environment keys:

```latex
\begin{reportarchitecture}[
  width=15.2,
  annotation={One product may span layers; ownership and exit planning remain explicit.},
  annotation-position=top
]
```

Support `top` and `bottom` positions, wrap the text within the declared width,
and include the annotation in the primitive's measured bounding box. The
annotation must inherit ReportKit typography and remain legible after
`diagram`-level resizing. No raw TikZ is required in the consumer fixture.

### P1 — Give timeline markers label-placement controls

**Engine status: done.** `\watermark` accepts `label-position=above|below|
left|right`, `label-width=`, and `label-anchor=`, defaulting to the original
below-marker placement. Covered by
`test_timeline_marker_labels_avoid_track_name_and_page_boundary` (passes).

**Consumer status: migrated**, with a caveat. `fig-sec02-event-time-watermark.tex`
now uses two `\watermark[label-position=below,label-width=...]` calls on the
`Watermark` track with descriptive labels (tying the marker values to the
allowed-lateness/window-close narrative in the caption), replacing the
terse `\event`-only markers that track previously had. Verified by building
section 02 individually (zero diagnostics) and visually confirming the
labels sit below the track, don't collide with the track name, each other,
or neighboring-track markers.

**Engine bug found during migration:** `\watermark`'s label styling reuses
`rk transition label`, which bakes in TikZ's `midway` key
(`reportkit-grammar.sty:15-18`) — a key meaningful only for a node placed
*on a path* (`node[midway]` inside a `\draw ... to node{}`). `\watermark`
instead places a *standalone* `\node ... at (coord) {...}`; `midway` on a
standalone node silently discards the `at` coordinate, collapsing every
`\watermark` label onto the picture origin regardless of `label-position`,
track, or fractional position. Confirmed independently with a minimal
non-ReportKit TikZ reproduction (a plain `\node[midway] at (3,3){}` renders
at the origin, not at `(3,3)`). The engine's own regression test
(`test_timeline_marker_labels_avoid_track_name_and_page_boundary`) only
asserts weak relative conditions that happen to hold even when the label is
at the origin, so it didn't catch this.

Worked around locally in this one fixture only: a `\tikzset` inside the
`reporttimeline` environment's own `\begingroup`/`\endgroup` scope
redefines `rk transition label` without `midway`, restoring the documented
`label-position` behavior for this figure without touching report-kit. This
is a real engine defect, not just a consumer gap — **recommend filing it
against report-kit** so `\watermark` (and anything else reusing
`rk transition label` for a standalone node) is fixed upstream and the
regression test is tightened to actually catch a collapsed-to-origin label.

`\watermark` always places its label below the marker
(`latex_templates/reportkit-grammar.sty:158-165`). Long labels near the track
label or a neighboring marker can collide. The guide removed the long
`\watermark` labels from its event-time figure and retained only event marks
(`fragments/fig-sec02-event-time-watermark.tex:8-15`).

Extend the command with optional keys:

- `label-position=above|below|left|right`;
- `label-width=<length>`; and
- `label-anchor=<TikZ anchor>` for advanced cases.

Defaults must preserve the current below-marker behavior. Add a fixture with
`allowed lateness` and an endpoint marker to prove that labels do not collide
with track names, markers, or the diagram boundary.

## 3. Required regression coverage

**Status: done, engine side.** All five fixtures below have dedicated
geometry tests in report-kit's `tests/test_primitive_additions.py`
(6 tests, including a bonus roadmap-arrow regression), all passing as of
this update, plus a compile-only acceptance fixture registered in
`scripts/acceptance_check.sh`. `SKILL.md`'s primitive reference and
`CHANGELOG.md` were updated as part of the same engine change. Nothing
further is needed here; this section is retained for context only.

Add rendered-geometry tests and acceptance fixtures for:

1. a five-column swimlane whose nodes remain inside a 12.2 cm lane;
2. a retry state with a loop, two terminal branches, and labeled routed edges;
3. a horizontal DAG with a validation-error branch and blocked downstream path;
4. an architecture with a top annotation; and
5. a timeline with two long marker labels near the endpoints.

Tests must assert geometry, not only successful TeX compilation: node bounds
remain inside the declared width, labels remain present in extracted text, and
the fixture has no known-overlap or outside-media-box result. Keep the existing
legacy and visual-grammar acceptance tests unchanged.

Update the primitive reference in `SKILL.md`, add changelog entries, and expose
clear package errors for invalid positions, unknown routing modes, and a
`columns` value below the highest declared step.

## 4. Consumer migration after the engine change

- [x] replace the manual state/DAG coordinates with the positioned semantic
      API — done in `8b4ed24` (`\RKEdge` for the DAG's optional/typed branch
      edges intentionally kept; see §2 above)
- [x] remove the raw architecture annotation node — done in `8b4ed24`
- [x] restore the event-time `\watermark` labels using placement keys —
      **done**; required a local per-fixture workaround for an engine bug
      (see §2, Watermark)
- [x] pass `columns=5` to the capstone swimlanes — **done**; verified all 5
      columns inside the declared 12.2cm width
- [x] remove the `text width=24mm` workaround in `fig-sec07-lineage.tex`,
      since the current `reportnetwork` spacing fix already prevents fused
      nodes — **done**; the stale explanatory comment describing the old
      bug was removed along with the workaround, and the default `rk node`
      width renders correctly at the engine's current 3.9cm grid spacing

No changes to the publication engine, manuscript structure, or content
semantics are part of this spec.

## 5. Definition of done

- [x] The five fixtures compile through `scripts/acceptance_check.sh` —
      engine side, confirmed.
- [x] Geometry tests run in the supported PyMuPDF test environment and pass —
      confirmed 2026-09-12 (`pytest tests/test_primitive_additions.py`, 6
      passed).
- [ ] The current guide rebuilds with no new diagnostics, clipping, or
      unresolved references after migration — **partially verified**: all
      five touched sections (02, 05, 06, 07, 08) now rebuild individually
      with `publication_build.py --mode section` and zero diagnostics. The
      **combined** build (`--mode combined`) currently fails on an unrelated,
      pre-existing LaTeX aux/label error in Section 4 ("Common
      Transformation Anti-Patterns"), confirmed present on the
      already-committed state before this migration and untouched by it.
      That failure blocks a true whole-guide verification and should be
      tracked and fixed separately from this spec.
- [x] Existing primitive call sites remain source-compatible unless they opt
      into the new keys or positioned commands — confirmed for all migrated
      fixtures; unmigrated fixtures are, by definition, still using the old
      call sites unchanged.

## 6. Remaining consumer work

All consumer migration items this spec tracked are done:

1. ~~Add `columns=5` to `fig-sec06-capstone-milestones.tex`'s
   `reportswimlane`~~ — done, all 5 columns confirmed inside the declared
   12.2 cm width.
2. ~~Restore descriptive `\watermark` labels in
   `fig-sec02-event-time-watermark.tex`~~ — done, using `label-position=`/
   `label-width=`; surfaced an engine bug worked around locally (§2).
3. ~~Remove the `text width=24mm` workaround in `fig-sec07-lineage.tex`~~ —
   done; `reportnetwork`'s current default spacing keeps edges pointing the
   correct direction without any override.

One item remains, out of this spec's scope but blocking full end-to-end
verification:

4. Investigate and fix the pre-existing combined-build failure in Section 4
   so the whole guide can be rebuilt and diagnosed end-to-end again.

And one new item surfaced by this pass, to track upstream rather than here:

5. File the `\watermark`/`midway` label-placement bug (§2, Watermark)
   against report-kit, and tighten
   `test_timeline_marker_labels_avoid_track_name_and_page_boundary` so it
   would actually fail on a label collapsed to the picture origin.
