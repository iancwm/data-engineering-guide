# ReportKit Primitive Additions — Minimal Implementation Spec

**Status:** Review complete; implementation not started  
**Date:** 2026-09-07  
**Consumer reviewed:** `/home/iancwm/git/data-engineering-guide`  
**Engine reviewed:** `/home/iancwm/git/report-kit` at `71c8bd960efda48721c99cac9624bc4bac91abfe`

## 1. Purpose

Make the semantic primitives sufficient for the figures now used by the guide
without adding a general-purpose layout engine. The additions should remove
raw-coordinate workarounds, make sizing keys truthful, and provide regression
coverage for the failure modes exposed by the current content.

## 2. Findings

### P0 — Make swimlane columns derive from the declared width

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

Once the engine is released and the content repo updates its lock:

- replace the manual state/DAG coordinates with the positioned semantic API;
- remove the raw architecture annotation node;
- restore the event-time `\watermark` labels using placement keys;
- pass `columns=5` to the capstone swimlanes; and
- remove the `text width=24mm` workaround in `fig-sec07-lineage.tex`, since the
  current `reportnetwork` spacing fix already prevents fused nodes.

No changes to the publication engine, manuscript structure, or content
semantics are part of this spec.

## 5. Definition of done

- The five fixtures compile through `scripts/acceptance_check.sh`.
- Geometry tests run in the supported PyMuPDF test environment and pass.
- The current guide rebuilds with no new diagnostics, clipping, or unresolved
  references after migration.
- Existing primitive call sites remain source-compatible unless they opt into
  the new keys or positioned commands.
