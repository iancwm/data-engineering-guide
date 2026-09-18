# Deferred Issues: Career-Switcher Learning Experience Pass

This list separates issues found or created during this revision that are
**not** fixed in this pass, split by which repository owns the fix, per
`docs/reportkit-known-issues.md`'s existing convention and this repo's
`references/repository-boundary.md`-equivalent split (publication vs.
engine).

## ReportKit engine (upstream, not this repository)

All seven items below are recorded in full, with evidence and suggested
fixes, in `docs/reportkit-known-issues.md`. Summary:

| # | Issue | Blocks this pass? |
|---|---|---|
| 1 | Combined build has no output-directory cleanup; reusing a dirty one produces an opaque fatal | No -- documented workaround (empty `--output-root`) already in `README.md` |
| 2 | `render_pdf_pages.py`'s missing-PyMuPDF error doesn't name the `setup.sh` fix | No -- documented workaround already in `README.md` |
| 3 | Release PDF is untagged, no accessible structure tree | No, but blocks any claim of full PDF accessibility |
| 4 | Pinned Libertinus font archive needs manual TDS extraction + `updmap-sys` registration; no script performs this | No -- worked around locally this session, documented for the next operator |
| 5 | `publication_build.py`'s page-render step only fails (unhelpfully) at the very last step when `<output-root>/.venv` is missing | No -- same root cause as #2, same workaround |
| 6 | Publication-details page prints "Classification: ." even when unset (`\ifx`/`\newcommand` empty-macro comparison bug) | No -- cosmetic only |
| 7 | Inline-code "→" (U+2192) loses its glyph on PDF text extraction (font ToUnicode gap) | No -- visual rendering unaffected, only text-layer/accessibility fidelity |

None of these are filed as GitHub issues against `report-kit` yet, per that
file's own standing note -- do so manually when convenient, referencing
`docs/reportkit-known-issues.md`.

## This publication (in scope for a future pass, not this one)

1. **Book-wide "→" vs. "->" convention in inline code.** Issue 7 above's
   root cause is engine/font-level, but this publication could sidestep it
   independently by preferring the ASCII `->` (which pandoc/LaTeX pass
   through unchanged) over a literal "→" character inside inline code spans
   that are prose rather than a runnable command. This appears in at least
   three capstone-handoff sentences (`03-storage.md`, `04-transformation-
   processing.md`, `05-orchestration.md`) and possibly others not spot-
   checked. Out of scope for this pass because it is a book-wide style
   sweep unrelated to any of the spec's chartered P0/P1/P2 work packages;
   flagged here so it isn't lost.

2. **`fragments/fig-sec07-data-contract.tex` is deleted, not archived.**
   The figure was judged to restate its adjacent YAML listing rather than
   teach a relationship a table couldn't, and its manuscript usage was
   replaced with a table (commit `53f7f26`). The now-orphaned fragment file
   was deleted outright (`e80a1cb`) rather than left in the tree unused,
   since the repo's git history already preserves it if a future editor
   wants to revisit the decision. Not treated as a defect, but noted here
   for visibility since it's a removal, not a pure addition.

3. **CI/automated smoke test for the manuscript-companion SQL alignment
   check.** `companion/scripts/test_manuscript_sql_alignment.py` is a plain
   script with asserts, run manually in this pass (and by
   `companion/scripts/run_all.py`'s own smoke test). It is not wired into
   any CI workflow, because this repository does not currently have one for
   the companion path (only the ReportKit combined build is automated, and
   that's a separate, external process). Wiring it up is a reasonable
   follow-up but is infrastructure work outside this spec's scope.

Nothing in this list blocks the outcome-based acceptance criteria in the
parent spec: the reader-facing content, figures, and companion path are all
complete, correct, and verified as of this pass.
