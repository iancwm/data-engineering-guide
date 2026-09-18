---
title: "A Practical Guide to Data Engineering"
subtitle: "Core Concepts, Systems, Pipelines, and Production Practices"
author: "Ian Chong"
date: "2026-09-06"
version: "Version 1.0"
license: "Original prose and diagrams are licensed CC BY 4.0; code examples and third-party assets retain their separate licences."
disclaimer: "Educational material only. Verify examples against your systems and current documentation; this guide is not operational, financial, legal, or security advice."
project-url: "https://github.com/iancwm/data-engineering-guide"
documentclass: article
papersize: a4
fontsize: 11pt
geometry: margin=1in
toc: true
toc-depth: 1
numbersections: false
---

## Preface

This guide introduces data engineering from first principles and then develops the subject into a practical map of the discipline. It begins with the central idea that data engineering is the work of designing, building, operating, and improving the systems that move data from raw sources into trustworthy forms that people and software can use.

The guide is prepared as a publication source. It uses ordinary Markdown headings, tables, and references so that the publication workflow can convert it to LaTeX. Formatting and diagram conventions for that workflow are collected separately in `publication-guidelines.md`.

## Reader's Roadmap

This linked roadmap is a reading aid for the Markdown manuscript; the generated publication table of contents remains the authoritative contents list.

- [Section 1 - Introduction to Data Engineering](#section-1---introduction-to-data-engineering)
- [Section 2 - Data Ingestion](#section-2---data-ingestion)
- [Section 3 - Data Storage](#section-3---data-storage)
- [Section 4 - Data Transformation and Processing](#section-4---data-transformation-and-processing)
- [Section 5 - Orchestration and Scheduling](#section-5---orchestration-and-scheduling)
- [Section 6 - Data Quality and Reliability](#section-6---data-quality-and-reliability)
- [Section 7 - Metadata, Governance, and Serving Data](#section-7---metadata-governance-and-serving-data)
- [Section 8 - Topics in Data Engineering](#section-8---topics-in-data-engineering)
- [Section 9 - A Learning Path and Project Roadmap](#section-9---a-learning-path-and-project-roadmap)
- [Section 10 - Glossary](#section-10---glossary)
- [Section 11 - References](#section-11---references)

## Reader Routes and a Guided Quick Start

This guide can be read three ways. Pick the route that matches what you need
right now; you can switch routes at any point.

::: {#tbl:reader-routes}
Table: Three routes through this guide.

| Reader mode | Route |
| --- | --- |
| Learn the field | Read linearly from Section 1. |
| Build while learning | Run the companion quick start below now, then return to it at each section's capstone continuation. |
| Use as a reference | Jump through the contents above, the glossary (Section 10), and each section's design checklist. |
:::

Before the lifecycle survey in Section 1, consider running the guide's own
worked pipeline. It is the exact BTCUSDT trade pipeline every later section's
capstone continuation builds on, reduced to a bounded, offline fixture: no
credentials, no network access, and no Kafka or Airflow to install.

::: practice
**Practice.** From the repository root:

```bash
python3 -m venv companion/.venv
companion/.venv/bin/pip install duckdb==1.1.3 pytest==8.3.4
companion/.venv/bin/python companion/scripts/run_all.py
```

The script loads 49 hand-authored synthetic BTCUSDT trade events, deduplicates
them into 48 trades, aggregates those trades into 3 hourly OHLCV bars, and
runs ten quality and reconciliation checks before printing `PASSED`. See
`companion/README.md` for full setup and troubleshooting notes, and the
guide's repository at
[iancwm/data-engineering-guide](https://github.com/iancwm/data-engineering-guide)
for the companion path's full source under `companion/`.

Expected result: **49 raw events -> 48 deduplicated trades -> 3 hourly OHLCV
bars, with all ten quality checks passing.**
:::

The count dropping from 49 to 48, and the checks that pass afterward, are the
point -- not the script exiting successfully. One of the 49 events is an exact
redelivery of an earlier trade, and the pipeline has to recognize and drop it
rather than double-count it. Two more events arrive out of the order they
occurred in, and a fourth arrives late for an hour that has already mostly
closed, so the pipeline has to treat "when a record arrived" and "when the
trade actually happened" as two different clocks. A successful exit code
alone would not tell you any of that was handled correctly; the row counts
and the ten passing checks are the evidence, and the pipeline can be re-run
from scratch and reproduce the same evidence every time.

Each later section returns to a piece of this same pipeline:

- Section 2 explains why the raw events needed deduplication in the first
  place, and how late and out-of-order arrivals are handled at ingestion.
- Section 3 shows the partitioned Parquet and local lakehouse layer the raw
  events land in.
- Section 4 shows the actual SQL that performs the deduplication and the
  hourly OHLCV aggregation.
- Section 5 explains how an orchestrator would run these same stages in
  dependency order, with retries and backfills.
- Section 6 shows the quality checks that produced the `PASSED` line.
- Section 7 covers the data contract and ownership behind `curated_trades`
  and `fct_hourly_ohlcv`.
- Section 8 places this pipeline's security, observability, and cost
  concerns in context.
- Section 9 shows the same pipeline as a cumulative capstone architecture and
  a template for your own project.
