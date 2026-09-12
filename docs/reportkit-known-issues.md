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
