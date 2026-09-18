# Known ReportKit Engine Issues (Deferred Upstream)

This file tracks engine-level (ReportKit) behavior noticed while hardening
this publication that is out of scope to fix here (spec:
`docs/critique-remediation-spec.md`, scope note: "ReportKit source changes
are out of scope for this pass"). Nothing here has been filed as a GitHub
issue against `report-kit` yet — do that manually, referencing this file,
when convenient.

## 1. Combined build has no output-directory cleanup, and reusing a dirty
   one produces a fatal, confusing LaTeX error

`reportkit build --mode combined` (and the underlying
`publication_pipeline/scripts/publication_build.py`) never clears
`--output-root` before compiling. Re-running a combined build into a
directory that already holds a completed prior run's `.aux`/`.toc`/`.out`
files can produce:

```
Runaway argument? {\contentsl
File ended while scanning use of \@writefile.
==> Fatal error occurred, no output PDF file produced!
```

at `\begin{document}`, with no diagnostic pointing at "stale output
directory" as the cause — an operator unfamiliar with this failure mode
has no way to guess it from the error text alone. Reproduced and
confirmed by deleting the output directory entirely and rebuilding from
nothing, which succeeds. Suggested upstream fix: either refuse to compile
into a non-empty `--output-root` that wasn't produced by a prior run of
the same tool (a marker file check), or clean the relevant aux extensions
before the first compile pass, or surface a specific diagnostic
(`RK_STALE_OUTPUT_DIR` or similar) instead of an opaque fatal.

## 2. `render_pdf_pages.py`'s `ModuleNotFoundError` for PyMuPDF doesn't name the fix

When `<output-root>/.venv` doesn't exist yet (e.g. right after `rm -rf
build`), the page-rendering step fails with a bare Python traceback
(`ModuleNotFoundError: No module named 'pymupdf'`) surfaced as
`RK_RENDER_FAILED`. The fix (`publication_pipeline/scripts/setup.sh
<output-root>/.venv`) is documented in `publication_pipeline/README.md`,
but the error message itself doesn't point there. Suggested upstream fix:
have `build-report.json`'s remediation text for `RK_RENDER_FAILED` mention
`setup.sh` by name when the underlying stderr contains
`ModuleNotFoundError`.

## 3. Release PDF is untagged and does not expose an accessible structure tree

The PDF produced by `publication_build.py` (both draft and `--profile
release` builds) is not a Tagged PDF. Evidence:

```
$ pdfinfo build/combined/data-engineering-guide.pdf
Title:           Data Engineering Guide
Subject:         Core concepts, systems, pipelines, and production practices for data engineering.
Keywords:        data engineering, data systems, pipelines, storage, orchestration, data quality
Author:          Ian Chong
Creator:         LaTeX with hyperref
Producer:        pdfTeX-1.40.25
Custom Metadata: yes
Metadata Stream: no
Tagged:          no
UserProperties:  no
Suspects:        no
Pages:           81
Page size:       595.276 x 841.89 pts (A4)
PDF version:     1.5
```

**Status of this evidence:** captured from a real `--profile release`
combined build of this publication (two consecutive clean builds, zero
blocking diagnostics) run against the pinned ReportKit commit
(`e1d55be784416fdfb89635dc407bdd80b4f85255`). `Tagged: no` is confirmed, not
inferred -- the author/title/subject/keywords metadata (also part of this
same accessibility/credibility pass) round-trips correctly, but there is no
structure tree at all beneath it.

**Desired outcome.** The release PDF should be a PDF/UA or Tagged PDF with a
complete accessible structure tree, specifically:

- a heading hierarchy (`/H1`, `/H2`, ...) matching the manuscript's H1/H2
  structure (`# Section N - ...`, `## ...`);
- a logical reading order (`/StructTreeRoot` order) matching the visual
  layout, including multi-column or floated content;
- `/Figure` structure elements for each diagram, wired to the figure's
  accessible text (see below);
- `/Table` structure elements for the manuscript's pipe tables, with header
  cells marked as `/TH` so a screen reader can announce row/column context;
- `/Code` (or an equivalent marked-content role) for fenced code listings, so
  they are not read as undifferentiated body text;
- tagged links (`/Link` structure elements with real `/Contents` or
  `/Alt` text), not bare, unlabeled hyperlink annotations.

**Figure descriptions currently do not reach the PDF.** Each
`[[REPORTKIT-VISUAL:fig:<slug>]]` sentinel's corresponding fragment already
carries a `description=` field intended as the figure's alt text (see the
fragments under `fragments/` in this repository). Today that text has nowhere
to land: because the PDF has no structure tree at all, there is no `/Figure`
element for a `description=` value to attach to as `/Alt` text, so the
content is present in the source but inaccessible in the shipped PDF. Fixing
the tagging gap must therefore also thread `description=` through to each
image's structure-element alt text, not just add a structure tree in the
abstract.

**This must be fixed upstream, not patched here.** Per this engine's own
repository-boundary convention
(`/home/user/iancwm/report-kit/references/repository-boundary.md`: "If you
are changing a `.cls`/`.sty` file ... you are working **on the engine**"),
PDF tagging is a document-class/style concern — it has to be implemented in
ReportKit's `.cls`/`.sty` files (e.g. via `\DocumentMetadata{tagged=true,
...}` plus explicit `\Alt{...}` text at each figure/table insertion point in
the class, driven by the fragment's `description=` field), not worked around
with publication-local TeX patches in this manuscript or its fragments.
Publication-local patches are not an acceptable permanent solution: they
would have to be re-applied by hand on every ReportKit upgrade and would
leave every other ReportKit-built publication still untagged.

**Impact.** This does not block the rest of this revision's content or
visual work — text, diagrams, tables, and the build itself are otherwise
unaffected. It does block any claim that the release PDF is "fully
accessible": until the structure tree exists, screen-reader users cannot
navigate the PDF by heading, get meaningful figure/table announcements, or
rely on the reading order matching the visual layout.

## 4. Pinned Libertinus font assets require manual TDS extraction and
   `updmap-sys` registration that no script performs

`reportkit.lock`'s `toolchain.expected.fonts` pins
`font_data/reportkit-libertinus-fonts.tar.gz` (a proper TDS-structured
archive: `tex/latex/libertinus/`, `tex/latex/libertinust1math/`,
`fonts/{tfm,type1,afm,vf,enc,map}/...`), but nothing under
`publication_pipeline/scripts/` (including `setup.sh`, which only creates
the Python render venv) extracts this archive into a TeX tree or registers
its two map files (`fonts/map/dvips/libertinus-type1/libertinus.map` and
`fonts/map/dvips/libertinust1math/libertinust1math.map`) with `updmap-sys`.

Symptom without that step: `\documentclass{reportkit}` (which
`\RequirePackage{libertinus}` in `reportkit-theme-default.sty`) fails
immediately with `! LaTeX Error: File 'libertinus.sty' not found.` once the
font isn't on `TEXMFLOCAL`/`TEXMFHOME` at all. Once the archive is manually
extracted (e.g. into `/usr/local/share/texmf` + `texhash`), `libertinus.sty`
loads, but compilation still fails with a *different*, much harder to
diagnose fatal at the very first page shipout (`\RKContents`, before any
publication content is processed):

```
pdfTeX error (font expansion): auto expansion is only possible with scalable fonts.
<argument> ...shipout:D \box_use:N \l_shipout_box
==> Fatal error occurred, no output PDF file produced!
```

Root cause: `reportkit-core.sty` loads `microtype` with its default
font-expansion behavior, which requires the active fonts' Type 1 outlines to
be registered in `pdftex.map`; the Libertinus TDS archive ships its map
files, but they are inert until enabled with `updmap-sys --enable
Map=<name>.map`. Two calls resolve it:

```
sudo updmap-sys --enable Map=libertinus.map
sudo updmap-sys --enable Map=libertinust1math.map
```

Neither the LaTeX error text nor the build-report diagnostic (`RK_MISSING_FONT`
/ `RK_LATEX_ERROR`) names font-map registration as the fix, so an operator
who only extracts the TDS archive (the seemingly-complete fix for the first
error) hits a second, unrelated-looking fatal with no pointer back to fonts
at all. Suggested upstream fix: have `setup.sh` (or a new
`setup-fonts.sh`) extract `font_data/reportkit-libertinus-fonts.tar.gz` into
the venv-local or a project-local `TEXMFHOME`/`TEXMFLOCAL` tree and run the
two `updmap-sys --enable` calls above as part of environment bootstrap,
rather than leaving font installation as an undocumented manual step; at
minimum, surface a specific `RK_FONT_MAP_NOT_REGISTERED` diagnostic instead
of the generic pdfTeX expansion fatal.

## 5. `publication_build.py`'s page-render step ignores `--output-root`'s
   own venv when a fresh `<output-root>` is reused

Deleting and recreating only part of an output tree (for example `rm -rf
<output-root>/combined` to force a clean recompile while intentionally
keeping `<output-root>/.venv` from an earlier `setup.sh` run) works
correctly. But `rm -rf <output-root>` in full, followed by re-running
`publication_build.py` without re-running `setup.sh` first, produces the
same `RK_RENDER_FAILED` / `ModuleNotFoundError: No module named 'pymupdf'`
failure documented in Issue 2 above, because the LaTeX compile and validate
steps succeed and only the final page-render step needs the venv -- so the
build gets most of the way through (gate: passed on the PDF compile itself)
before failing at rendering, which can read as a flaky or partial failure
rather than the same missing-venv cause as Issue 2. Suggested upstream fix:
have `publication_build.py` check for `<output-root>/.venv` up front (before
starting the compile passes) and fail fast with the `setup.sh` remediation
from Issue 2, rather than discovering the missing venv only at the last
step.
