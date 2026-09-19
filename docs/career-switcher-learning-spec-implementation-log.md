# Career-Switcher Learning Experience Implementation Log

**Spec:** `docs/career-switcher-learning-spec.md` (as given in the task; not
separately committed to this repo -- this log is its record of execution).
**Branch:** `claude/career-switcher-learning-spec-jy6pd9`.
**Method:** eight parallel agents, each scoped to a non-overlapping set of
files, followed by a sequential integration, build, and QA pass by the
orchestrating session. Every agent's changes were reviewed, committed, and
pushed individually before the next integration step ran, per commit list
below.

## Work package -> files -> commit map

### P0 -- Correct the hourly-OHLCV SQL

**Files:** `manuscript/04-transformation-processing.md`,
`companion/scripts/build_models.py`,
`companion/scripts/test_manuscript_sql_alignment.py` (new).
**Commit:** `5860c2d` fix: repair invalid two-box hourly-OHLCV SQL listing.

The `lst:sec04-hourly-ohlcv` listing was not valid SQL: box 1 terminated the
`candidate_hours` CTE with a semicolon (`SELECT * FROM candidate_hours;`),
then box 2 opened a *new* `WITH bars AS (...)` statement that still read from
`candidate_hours` -- a name that does not survive its own statement's
terminator. Implemented the spec's preferred option 1: box 1 now leaves the
`WITH` clause open (no terminating `SELECT`/semicolon); box 2 continues the
same clause with a leading comma (`, bars AS (...)`) instead of a new `WITH`
keyword, ending in the one real `SELECT ... FROM bars;` terminator.
Reclassified the listing from **Illustrative** to **Runnable with
adaptation** and rewrote the paragraph between the boxes to state plainly
that this is one continuous statement, not two independent queries.

`companion/scripts/build_models.py`'s DuddDB translation of the same query
was realigned to the identical `candidate_hours -> bars` CTE shape (it
previously had only a single `bars` CTE -- a silent structural divergence
from the manuscript), with the exact dbt-Jinja-to-DuckDB substitutions
documented in a docstring. `test_manuscript_sql_alignment.py` asserts the
manuscript listing and `build_models.py` keep matching shapes, so a future
edit to either without the other fails loudly instead of silently
diverging. Verified: `companion/scripts/run_all.py` still reports 49 raw
events -> 48 deduplicated trades -> 3 hourly OHLCV bars, all 10 quality
checks passing, `PASSED`, before and after.

### P0 -- Add an early guided success

**Files:** `manuscript/00-frontmatter.md`, `manuscript/01-introduction.md`.
**Commit:** `dcc2200` feat: add early reader routes + quick start, tighten
Section 1.

Added a "Reader Routes and a Guided Quick Start" section to the front
matter, landing on PDF page 4 (well inside the "first five PDF pages"
requirement, confirmed by the rendered PDF's own text extraction and visual
review below). It states the three required reader routes (learn the field
/ build while learning / use as a reference) as a table, then a bounded
`practice`-callout quick start that runs `companion/scripts/run_all.py`
against the bundled fixture -- no credentials, no external services -- and
states what it produces, why the count drop demonstrates data-engineering
concerns beyond ordinary analytics code (dedup, event-time vs. arrival-time,
idempotent replay, quality checks), the expected final counts, and where
each of Sections 2-9 later explains a piece of the same pipeline. Verified
live twice (before and after the Section 4 SQL fix landed elsewhere) against
the actual companion output.

### P1 -- Tighten Section 1

**Files:** `manuscript/01-introduction.md`, `fragments/fig-sec01-lifecycle.tex`.
**Commit:** `dcc2200` (same commit as the quick start, since both touch
`01-introduction.md` and were done as one continuous pass per the spec's own
implementation-sequence ordering).

Compressed Section 1 by 20.8% (4101 -> 3248 words), inside the requested
20-30% band, while retaining ~79% of the original: kept the lifecycle
overview, all eight common-confusions distinctions, the role-comparison
table, the pipeline/layered/contract views, grain/data-shape material, and
the analytics/ML/application/finance serving bridge. Removed repeated
vendor-name enumerations already covered in later tooling tables, merged
subsections restating the same source-to-consumer flow a third or fourth
time, and tightened duplicate term definitions. Added a closing transition
into Section 2 tying back to the quick start.

Recomposed `fig-sec01-lifecycle.tex`: reduced the main chain from 8 nodes to
the 6 genuinely sequential stages (Sources -> Ingestion -> Storage ->
Processing and Transformation -> Orchestration -> Serving) and moved
Quality/Reliability, Metadata/Governance, Observability, Security, and Cost
out of the sequential chain into a single dashed, shaded cross-cutting band
spanning the whole figure -- the prior version wrongly implied these
concerns happen only after Orchestration by drawing them as sequential
stages 6-7. Confirmed by visual review (below) that the band's label does
not cross any node text and the figure is grayscale-legible.

### P1 -- Recompose weak visuals

**Files:** `fragments/fig-sec01-lifecycle.tex` (above),
`fragments/fig-sec06-quality-loop.tex`, `fragments/fig-sec07-lineage.tex`,
`fragments/fig-sec07-data-contract.tex` (retired),
`fragments/fig-sec08-security-layers.tex`,
`fragments/fig-sec08-platform-boundaries.tex`,
`fragments/fig-sec09-learning-roadmap.tex`,
`fragments/fig-sec09-capstone-architecture.tex`, `publication-guidelines.md`.
**Commits:** `ac50371`, `53f7f26`, `91f09fa`, `4963cc4`, `e80a1cb`.

- **`fig:sec06-quality-loop`** (`ac50371`): switched from a strict
  `reportcycle` (which cannot branch) to `reportflow` primitives. Main row
  (solid): Contract -> Test -> Publish. Exception row (dashed, `optional`
  edge kind, labeled): Test --fail--> Alert --quarantine--> Remediate or
  Quarantine --loop back--> Contract. This makes the publish/block decision
  visible, which the prior 4-node circle omitted entirely.
- **`fig:sec07-lineage`** (`53f7f26`): the prior `reportnetwork` chain
  (Producer -> Dataset -> Catalog or Steward -> Consumer, all one `[flow]`
  edge style) visually contradicted its own caption's claim that the catalog
  "does not receive or forward data itself." Rebuilt as Producer -> Dataset
  -> Consumer (solid flow), with Catalog or Steward connected to Dataset by
  a separate dashed "documents" edge.
- **`fig:sec07-data-contract`** (`53f7f26`, deletion in `e80a1cb`):
  evaluated against the spec's "teaching a relationship vs. restyling a
  table" test and judged to be the latter -- its 3-layer stack restated
  facts the adjacent YAML contract listing already made concrete. Replaced
  with a 3-row table mapped to the listing's actual field names; the now-
  orphaned fragment file was deleted once nothing referenced it.
- **`fig:sec08-security-layers`** and **`fig:sec08-platform-boundaries`**
  (`91f09fa`): both evaluated independently; both kept (their content is
  genuinely ordered/topological, which the guidelines say belongs in a
  figure, not a table) but tightened -- generic per-layer restatements
  replaced with concrete cross-layer span examples, and the platform-
  boundaries figure's follow-up prose rewritten to walk the capstone's
  actual named artifacts instead of re-listing all 8 layers a second time.
- **`fig:sec09-learning-roadmap`** (`4963cc4`): replaced the static
  Beginner/Core/Advanced horizons (which cannot express a branch) with a
  `reportflow` chain matching the new 7-milestone structure, plus a dashed
  `optional` edge into a clearly marked "pick one" specialization node.
- **`fig:sec09-capstone-architecture`** (`4963cc4`): fixed the diagonal
  `laneflow{hourly}{serve}` edge that crossed the Control path and Trust
  boundary lanes' node text. Reordered lanes to Control path / Data path /
  Trust boundary / Consumers and split the final handoff into two adjacent-
  lane hops (`hourly -> contract`, then `contract -> serve`), so data only
  reaches consumers after passing through the trust boundary's `contract`
  node, with no edge crossing another lane's text.
- **`publication-guidelines.md`** (`e80a1cb`): consolidated, rather than let
  five different agents restyle independently, the finalized semantic edge
  vocabulary (solid flow/dependency = data movement; dashed handoff/optional
  = control/exception paths with a text label; shaded band = a cross-cutting
  concern; a trust-boundary node stays in the data path's own lane
  sequence), the applied-checkpoint addition to the section rhythm and
  callout table, the Section 1 figure's six-stage-plus-band structure, and a
  note on retiring a figure in favor of a table.

### P1 -- Turn the learning path into a study plan

**Files:** `manuscript/09-learning-path.md`.
**Commit:** `4963cc4` feat: rewrite Section 9 as a 7-milestone outcome-based
study plan.

Replaced the prior Core Skills / Portfolio Project / Advanced Project
layout with 7 outcome-based milestones (Foundation, Local pipeline, Reliable
models, Operational control, Consumer contract, Portfolio evidence, Optional
specialization), each stating what to understand, what to run/change, the
completion artifact, a failure to deliberately inject, and an interview
question -- all grounded in this repo's actual companion scripts and
capstone artifact names. No calendar language. Milestone 7 is explicitly
optional and non-mandatory (six tracks, pick at most one).

### P1 -- Add active-learning checkpoints

**Files:** `manuscript/02-ingestion.md`, `manuscript/03-storage.md`,
`manuscript/04-transformation-processing.md`, `manuscript/05-orchestration.md`,
`manuscript/06-quality-reliability.md`,
`manuscript/07-metadata-governance-serving.md`,
`manuscript/08-practitioner-topics.md`, `companion/exercises/README.md` (new).
**Commits:** `5860c2d`, `4488e2b`, `ac50371`, `53f7f26`, `91f09fa`,
`e80a1cb`.

One compact (`practice`/`checklist` callout, under half a page) applied
checkpoint added to each of Sections 2-8, each asking the reader to inspect,
predict, modify, or diagnose the shared BTCUSDT capstone: a lost-ACK
duplicate trace (Section 2), a partition-pruning rewrite (Section 3), a
shortened-lookback diagnosis (Section 4), a retry-vs-deterministic-failure
decision (Section 5), an interval reconciliation (Section 6), a schema
backward-compatibility decision (Section 7), and a platform-boundary
failure diagnosis (Section 8). Answer keys assembled centrally into
`companion/exercises/README.md` rather than placed next to the questions.

### P2 -- Improve credibility and navigation

**Files:** `publication.yaml`, `manuscript/00-frontmatter.md`,
`manuscript/11-references.md`, all `manuscript/0[2-9]-*.md` (Further
Learning lists).
**Commits:** `591f147`, `286cd5f`, plus a Further Learning list in each
section's own commit above.

Set `publication.yaml`'s blank `author` field to "Ian Chong" (the identity
established by this repo's own git history). Reconciled
`manuscript/00-frontmatter.md`'s YAML block, which still carried
`author: "ReportKit contributors"` and a `project-url` pointing at the
`report-kit` engine repo (leftovers from when this content lived inside that
repo) -- both flagged independently by two parallel agents working from
opposite sides of the mismatch, fixed centrally in `286cd5f` to match
`publication.yaml`. Restructured `manuscript/11-references.md` into explicit
"Sources Cited" and "Further Reading" subsections and closed a real gap: two
new citations (Gilbert & Lynch on CAP, Abadi on PACELC) for results
`03-storage.md` names by name with no prior citation anywhere. Added a short,
section-specific "Further Learning" list to the end of Sections 2-9 (8
lists total), each tied to a specific claim already made in that section,
using stable/authoritative sources with access dates for mutable pages.

### P2 -- Record upstream accessibility requirements

**File:** `docs/reportkit-known-issues.md`.
**Commits:** `591f147`, `19370ae`, `e562daa`.

Recorded Issue 3 (the release PDF's missing accessibility structure tree)
with real `pdfinfo` evidence captured from this revision's own passing
build (`Tagged: no`, confirmed rather than inferred), the desired outcome
for headings/reading-order/figures/tables/code/links, the note that
`description=` alt text currently has nowhere to attach without a structure
tree, and an explicit statement that this must be fixed in ReportKit's
`.cls`/`.sty` files, not patched here. Also recorded four further
engine-level findings surfaced while getting this revision's own build
green (Issues 4-7 below) -- none block content or visual work; all are
deferred upstream per the repository-boundary convention.

### P3 -- Reduce Section 8 reader friction

**Files:** `manuscript/08-practitioner-topics.md`.
**Commit:** this changeset.

Added a compact implement-now / explain / defer callout, one connecting
failure scenario with callbacks for observability, cost, security, ownership,
contracts, and tool selection, and a transition into Section 9. Condensed the
Section 7 contract synthesis, cost-driver prose, and stack-selection guidance;
removed repeated vendor enumeration and the redundant standalone revenue
dashboard walkthrough. Preserved the security and platform-boundary figures,
architecture and learning-order tables, minimum viable stack, production
readiness checklist, and the Section 8 practice checkpoint. The revised source
is 3,249 words versus 3,508 before the edit.

## Build and QA

**Toolchain setup performed in this session** (none of this touches
report-kit's own source; all environment-local): installed
`pandoc`/`texlive-*` via apt per `reportkit.lock`'s pinned package list;
extracted the pinned `font_data/reportkit-libertinus-fonts.tar.gz` into
`/usr/local/share/texmf` and registered its two font maps with
`updmap-sys --enable` (undocumented manual steps -- see Issue 4 in
`docs/reportkit-known-issues.md`); ran `publication_pipeline/scripts/setup.sh`
to create the render venv.

**Two consecutive clean `--profile release` combined builds**, each from an
emptied `build/combined/` (keeping the render venv, since a full `rm -rf
build` silently drops it -- see Issue 5): both `status: passed`,
`gate: passed`, zero blocking diagnostics, identical non-blocking
`package_warning` count (23, all pre-existing-pattern `caption`/`hyperref`/
`hyphenat` cosmetic warnings, none new or concerning). One real defect was
caught and fixed between builds: eight sections' independently-added
"## Further Learning" H2 headings collided on the same Pandoc-derived
`further-learning` anchor, producing 7 duplicate-label warnings; fixed with
explicit unique heading-attribute IDs (`ec14bb0`).

**Page-by-page visual review** (200 DPI render via
`render_pdf_pages.py`, `build/combined/pages/page-NN.png`): reviewed the
title page, publication-details page, contents page, the quick-start page
(confirmed at PDF page 4, `pdftotext`-verified), all 7 rebuilt/retained
figures in their final rendered form (`fig:sec01-lifecycle` page 6,
`fig:sec06-quality-loop` page 55, `fig:sec07-lineage` page 63,
`fig:sec08-security-layers` page 67, `fig:sec08-platform-boundaries` page
70, `fig:sec09-learning-roadmap` page 75, `fig:sec09-capstone-architecture`
page 77), the retired data-contract table's replacement page (page 64),
Section 9's Milestone 1/2 pages, and the references page. In every case: no
edge or label crosses node text, captions state a conclusion rather than
just listing components, grayscale legibility holds (dashed/shaded
distinctions do not rely on color alone), and content matches what each
owning agent reported.

**PDF text extraction check** (`pdftotext -layout`): no leaked TeX markup,
no unresolved `??` references, no `{{`/`}}`/`[[REPORTKIT` sentinel leakage
(the one `{{ ref(...) }}` match is legitimate dbt Jinja inside a code
listing), no Unicode replacement characters. One genuine, pre-existing
font-encoding finding surfaced (inline-code "→" glyphs losing their
ToUnicode mapping on extraction) -- recorded as Issue 7, not fixed in this
pass (see deferred-issues list).

### Section 8 reader-friction follow-up

The publication validation passed with 12 manuscripts, 21 visuals, and 21
labels. Two consecutive clean `--profile release` combined builds passed with
`status: passed`, `gate: passed`, 81 pages, and zero blocking diagnostics;
each retained the same 24 warning-only diagnostics already present in the
toolchain baseline. The release PDF is at
`build/combined/data-engineering-guide.pdf`.

Rendered pages 66–75 at 200 DPI in grayscale on the A4 PDF canvas
(595.276 x 841.890 points): page 66 is the Section 7 buffer, pages 67–74 are
Section 8, and page 75 begins Section 9. Reviewed those pages for overflow,
stranded headings, awkward whitespace, figure/table displacement, and
grayscale legibility. No new layout defect was found; the learning-order table
continues with its header intact, both Section 8 figures remain legible, and
the Section 9 transition lands cleanly before the new section.

## Deliverables checklist

1. Updated manuscript, fragment, companion, metadata, and guideline files --
   done, see commit map above.
2. Updated/new automated tests for the corrected SQL and quick start --
   `companion/scripts/test_manuscript_sql_alignment.py` (new); the quick
   start reuses and re-verifies the existing `companion/scripts/run_all.py`
   smoke test, no separate test needed since it runs the same script.
3. Release-profile PDF -- built at
   `build/combined/data-engineering-guide.pdf` (81 pages; `build/` is
   gitignored per repository convention, not committed).
4. Page-by-page visual review log -- this document's "Build and QA"
   section.
5. Implementation log mapping each work package to files and commits --
   this document.
6. Deferred-issues list -- see
   `docs/career-switcher-learning-spec-deferred-issues.md`.
