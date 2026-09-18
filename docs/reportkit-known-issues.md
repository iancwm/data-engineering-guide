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
$ pdfinfo <release-pdf>
...
Tagged:             no
...
```

**Status of this evidence:** at the time this entry was written, no PDF had
yet been produced by the in-progress full engine build for this publication,
so the `Tagged: no` line above is the expected/documented result based on
ReportKit's LaTeX templates (`latex_templates/*.cls`/`*.sty` do not load a
tagging package such as `tagpdf`/`accessibility` or invoke `\DocumentMetadata`
with `tagged=true`), not a value captured from a run against this
publication's actual output. `pdfinfo` (poppler-utils) has been installed in
this environment so this can be re-verified directly: once a build exists
under `build/` or `output/`, run `pdfinfo <path-to-pdf>` and paste the real
`Tagged:` line here in place of this note.

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
