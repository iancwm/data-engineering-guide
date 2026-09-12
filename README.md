# Data Engineering Guide

A guided technical book on data engineering — ingestion, storage,
transformation, orchestration, quality, governance, and a learning path —
written as a ReportKit publication.

This repository holds the **publication**: manuscript, diagram fragments,
and identity (`publication.yaml`). It contains no build tooling of its own.
Building it requires a clone of the
[ReportKit](https://github.com/iancwm/report-kit) engine, which supplies the
LaTeX class/styles and the `publication_pipeline/` build/validate/inspect
harness. See that repo's
[`references/repository-boundary.md`](https://github.com/iancwm/report-kit/blob/main/references/repository-boundary.md)
for the full engine/publication split this follows.

## Structure

```text
manuscript/               12 Markdown chapters + order.txt (reading order)
fragments/                 22 LaTeX diagram fragments, one per
                            [[REPORTKIT-VISUAL:fig:<slug>]] sentinel in the manuscript
publication.yaml           title, author, and other publication identity
publication-guidelines.md  editorial spec for this specific guide
build/, output/            gitignored -- created by a build, never hand-edited
reportkit.lock             written by a successful build; pins the ReportKit
                            ref/commit and toolchain versions used
```

## Building

From a clone of ReportKit:

```bash
python3 <report-kit-clone>/publication_pipeline/scripts/publication_build.py \
  --mode combined \
  --source-root <this-repo-clone> \
  --output-root <this-repo-clone>/build
```

This validates the manuscript/fragment contract, renders each chapter through
Pandoc, splices in the diagram fragments, compiles twice with the strict
diagnostic gate, renders every page, and inspects the resulting PDF. See
[`publication_pipeline/README.md`](https://github.com/iancwm/report-kit/blob/main/publication_pipeline/README.md)
in the engine repo for the section-build and validation commands.

Before the first build, set up the render environment once:

```bash
bash <report-kit-clone>/publication_pipeline/scripts/setup.sh build/.venv
```

Always build into an empty `build/` — a stale `build/combined/` left over
from a previous run can produce an opaque `\@writefile`/`\contentsline`
fatal error at `\begin{document}`. `rm -rf build` before rebuilding, or use
a fresh `--output-root` each time. See
[`docs/reportkit-known-issues.md`](docs/reportkit-known-issues.md) for the
full diagnosis.

For a release build (no `draft` version marker), add `--profile release`:

```bash
python3 <report-kit-clone>/publication_pipeline/scripts/publication_build.py \
  --mode combined \
  --source-root <this-repo-clone> \
  --output-root <this-repo-clone>/build \
  --profile release
```

## Licence

Original prose and diagrams here are CC BY 4.0 — see [`LICENSE`](LICENSE).
The ReportKit engine used to build this guide is separately licensed
(GPL-3.0-or-later for its source and tooling).

## History

This content was originally developed on report-kit's
`data-engineering-guide-content` branch, back when publications lived
alongside the engine. It was extracted into this standalone repository once
report-kit's tooling was hardened to build any external project — see
[`references/migrating-content-branches.md`](https://github.com/iancwm/report-kit/blob/main/references/migrating-content-branches.md)
in the engine repo.
