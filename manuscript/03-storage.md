# Section 3 - Data Storage

Storage is not just where data sits. It is where data becomes durable, queryable, governable, and economically manageable. A storage layer must preserve raw facts, support downstream access patterns, and provide enough structure for performance, security, and operational control.

In modern data engineering, storage design is no longer simply "put data in a database." The engineer must choose physical formats, logical models, table layouts, access patterns, and reliability guarantees. The central trade-off is usually between cost, performance, flexibility, and consistency.

## Storage Requirements

Before choosing a warehouse, lake, database, or table format, define what the storage layer must do.

Important requirements include:

- durability: data should survive hardware failure, process failure, and routine operational mistakes;
- scalability: the system should handle expected growth in volume, users, files, tables, and workloads;
- query performance: common access patterns should be fast enough for consumers;
- cost efficiency: storage and compute costs should be proportional to business value;
- consistency: readers should have clear guarantees about what version of the data they are seeing;
- governance: sensitive data should be controlled, classified, retained, and audited;
- interoperability: data should be usable by the tools that need it;
- recoverability: teams should be able to restore, replay, or rebuild data when something goes wrong.

These requirements often conflict. A system optimized for millisecond application reads may be a poor fit for scanning billions of rows. A cheap raw data lake may be flexible but difficult to govern without metadata and table management. A highly managed warehouse may be productive but expensive or less portable.

## OLTP and OLAP Workloads

Storage architecture follows workload. The most important distinction is between OLTP and OLAP.

OLTP means online transaction processing. These systems support live applications: creating orders, updating balances, recording payments, changing user settings, or serving a shopping cart. They are optimized for many small reads and writes, concurrency, low latency, and transactional correctness.

OLAP means online analytical processing. These systems support analysis: scanning large histories, joining datasets, calculating aggregates, building dashboards, and training models. They are optimized for large read-heavy queries, compression, columnar execution, and parallel processing. The workload table contrasts the access patterns that drive the storage choice.

::: {#tbl:oltp-olap}
Table: OLTP and OLAP workloads.

| Workload | Optimized for | Common systems | Example query |
| --- | --- | --- | --- |
| OLTP | Small reads and writes, transactions, application latency | PostgreSQL, MySQL, SQL Server, Oracle, DynamoDB, MongoDB | Update one customer order |
| OLAP | Large scans, joins, aggregates, analytical latency | Snowflake, BigQuery, Redshift, Databricks SQL, ClickHouse, DuckDB | Calculate revenue by region for three years |
:::

Data engineers often extract from OLTP systems and load into OLAP systems. This protects application databases from heavy analytical queries and allows analytical storage to preserve history, denormalize data, and optimize for reporting or machine learning.

## Row-Oriented and Columnar Storage

The physical layout of data has a large effect on performance.

Row-oriented systems store values for the same record together. This is efficient when an application needs to read or update a whole record, such as one account, one user, or one order. Traditional OLTP databases are usually row-oriented.

Columnar systems store values from the same column together. This is efficient when a query reads only a few columns across many rows, such as calculating average price, total volume, or monthly revenue. Analytical engines can skip unused columns, compress similar values efficiently, and perform vectorized operations. The layout table compares row-oriented and columnar storage on the dimensions that matter for this choice.

::: {#tbl:storage-layouts}
Table: Row-oriented and columnar storage layouts.

| Layout | Strengths | Weaknesses | Best fit |
| --- | --- | --- | --- |
| Row-oriented | Fast point reads and writes; good for transactions | Inefficient for large analytical scans over few columns | OLTP applications |
| Columnar | Efficient scans, compression, and aggregation | Less natural for high-frequency single-row updates | Warehouses, data lakes, analytics |
:::

For example, a query such as:

```sql
SELECT AVG(price)
FROM curated_trades
WHERE event_date = :target_event_date;
```

does not need every field in the trade record. A columnar engine can read only the `price` and `event_date` columns, skipping fields such as exchange, symbol, trade identifier, ingestion timestamp, and raw payload. The parameter represents a date in UTC; using a parameter keeps the example reproducible without tying it to the day on which the guide was written.

## Distributed Storage, CAP, and PACELC

Distributed storage systems run across multiple machines. This gives scale and resilience, but it introduces unavoidable trade-offs.

The CAP theorem says that during a network partition, a distributed system must choose between consistency and availability:

- consistency: reads return the latest committed write, or fail rather than return stale data;
- availability: requests receive a non-error response, even if the response may not reflect the latest write;
- partition tolerance: the system continues to behave predictably when messages between nodes are delayed or lost.

In practical distributed systems, partition tolerance is not optional. Networks fail. The real design question is how the system behaves when failure happens. Some systems favor consistency and may reject or delay operations rather than return stale data. Others favor availability and may accept temporary divergence, reconciling later.

PACELC extends the idea. If there is a partition, choose between availability and consistency. Else, during normal operation, choose between latency and consistency. This matters because even without obvious failures, stronger consistency can add coordination cost.

For data engineering, CAP and PACELC are most useful as design vocabulary, not as labels to paste onto products. A cloud warehouse, a distributed cache, and an object store may all provide different consistency guarantees for different operations. The correct question is: what guarantee does this system provide for the specific read, write, commit, list, or query operation my pipeline depends on?

## Storage Architecture: Warehouse, Lake, and Lakehouse

The modern storage landscape is often described through three architectural patterns: warehouse, lake, and lakehouse.

## Data Warehouses

A data warehouse is designed for analytical queries over structured and semi-structured data. Warehouses typically support SQL, columnar execution, workload management, access control, and performance optimization.

Warehouses are strong choices for:

- business intelligence;
- governed reporting;
- dimensional models;
- interactive SQL analysis;
- curated datasets with stable schemas;
- teams that want managed infrastructure and strong SQL ergonomics.

Modern cloud warehouses often separate compute and storage. This means stored data can remain durable while query compute scales up, scales down, or runs in separate clusters for different workloads. Snowflake virtual warehouses, BigQuery slots, Redshift RA3, and Databricks SQL warehouses all reflect this broader shift, though their architectures differ.

Common examples include Snowflake, BigQuery, Redshift, Synapse, and Databricks SQL.

## Data Lakes

A data lake stores data in files, usually on object storage. It can hold raw, structured, semi-structured, and unstructured data at large scale. Data lakes are flexible and cost-effective, but without governance, metadata, and quality controls they can become difficult to trust.

Common file formats include:

- CSV and JSON for simple interchange and raw landing;
- Avro for row-oriented serialization and schema evolution;
- Parquet and ORC for efficient analytical reads;
- text, image, audio, and document formats for unstructured data.

Object storage systems such as S3, Azure Data Lake Storage, and Google Cloud Storage are not databases. They store objects addressed by keys. Folder-like paths are usually prefixes, not true hierarchical directories. Query engines impose table structure on top of these objects.

## Lakehouse Architecture

A lakehouse attempts to combine the flexibility and scale of a data lake with the reliability and management features of a warehouse. It typically uses object storage, columnar files, a table format, a catalog, and one or more query engines.

Lakehouses are useful when teams need the same data foundation to support several workloads, including SQL analytics, data science, machine learning, streaming, and large-scale batch processing.

The lakehouse layers figure separates physical files from table metadata, compute, analytical surfaces, and consumers so those responsibilities are not conflated.

[[REPORTKIT-VISUAL:fig:sec03-lakehouse-layers]]

## Open Table Formats

An open table format is a metadata layer that manages files in object storage as database-like tables. The best-known examples are Delta Lake, Apache Iceberg, and Apache Hudi.

Raw Parquet files alone do not provide full table semantics. A query may read half-written data, miss newly added files, include files that should have been deleted, or struggle with schema changes. A table format tracks which files belong to a table at a point in time and provides a commit protocol for changes.

Open table formats commonly support:

- atomic commits, so readers do not see partial writes;
- snapshot isolation, so queries see a consistent table version;
- schema evolution, so columns can be added or changed in controlled ways;
- partition evolution, so table layout can change over time;
- time travel, so earlier table versions can be queried;
- deletes, updates, and merges, depending on the format and engine;
- metadata pruning, so engines can skip irrelevant files.

Open table formats improve interoperability, but they do not remove all vendor dependence. Engine support varies. A feature written by one engine may not be readable by another if the integration is incomplete or uses format-specific extensions. The safe design principle is to test the actual engines that will read and write the table.

**Illustrative.** The following table-definition pseudocode separates the
Parquet files from the transactional table metadata around them. Exact syntax
varies by engine and table format; the durable design decisions are the schema,
UTC partition, logical key, and table location.

::: {#lst:sec03-table-definition}
Listing: Curated table definition over trade files.

```sql
CREATE TABLE curated_trades (
    exchange_name VARCHAR,
    asset_symbol VARCHAR,
    source_trade_id BIGINT,
    event_timestamp TIMESTAMP,
    ingested_at TIMESTAMP,
    price DECIMAL(20, 8),
    quantity DECIMAL(20, 8),
    raw_payload JSON
)
USING ICEBERG                 -- or the equivalent Delta table command
PARTITIONED BY (days(event_timestamp), hours(event_timestamp))
LOCATION 's3://crypto-lake/curated/trades';
```
:::

The table format can make commits and snapshots atomic, but it does not infer
that two rows with the same composite trade key are duplicates. The model still
needs deterministic deduplication and quality checks.

It is also important not to overstate idempotency. Delta, Iceberg, and Hudi provide transactional table commits, but they do not automatically know that two rows represent the same business event. Deduplication still requires stable keys, merge logic, constraints, or explicit data quality checks.

## File Formats

File format affects performance, schema handling, and interoperability. The file-format table summarizes the practical trade-offs among common interchange and analytical formats.

::: {#tbl:file-formats}
Table: File formats and their engineering trade-offs.

| Format | Strengths | Weaknesses | Common use |
| --- | --- | --- | --- |
| CSV | Human-readable, widely supported | No strong types, poor compression, ambiguous parsing | Simple exports and interchange |
| JSON | Flexible, handles nested data | Verbose, expensive to scan | API responses and raw events |
| Avro | Compact, schema-aware, good for row events | Less convenient for ad hoc analytics | Kafka and event serialization |
| Parquet | Columnar, compressed, efficient for analytics | Less suitable for frequent tiny writes | Data lakes, warehouses, lakehouses |
| ORC | Columnar, compressed, efficient scans | Less common outside some ecosystems | Hadoop/Hive-style analytics |
:::

For analytical storage, Parquet is often the default choice because it is columnar, compressed, widely supported, and works well with Spark, DuckDB, Trino, Snowflake external tables, BigQuery external tables, and lakehouse formats.

## Partitioning, Clustering, and File Layout

A data lake or lakehouse can be slow and expensive if files are poorly organized. Physical layout matters.

Partitioning divides a table into groups based on one or more columns, often represented as path prefixes such as:

```text
s3://example-lake/trades/{event_date}/{event_hour}/...
```

When a query filters by a partition column, the engine can use partition pruning to skip irrelevant partitions. Partitioning works best on low- to medium-cardinality columns that are frequently used in filters, such as date, region, environment, or source.

The partition-pruning figure shows the intended physical-read decision: a predicate selects the matching event-time partition while unrelated partitions are skipped.

[[REPORTKIT-VISUAL:fig:sec03-partition-pruning]]

**Runnable with adaptation.** This DuckDB query makes partition pruning
concrete by filtering the same UTC event-time columns used to derive the
`event_date` and `event_hour` path. The local glob can be replaced by an
object-store URI when the relevant DuckDB extension and credentials are
configured.

::: {#lst:sec03-parquet-partition-query}
Listing: Partition-pruned Parquet query.

```sql
SELECT
    exchange_name,
    asset_symbol,
    source_trade_id,
    event_timestamp,
    price,
    quantity
FROM read_parquet('data/raw/trades/**/*.parquet', hive_partitioning = true)
WHERE event_timestamp >= TIMESTAMP '2026-09-07 02:00:00+00'
  AND event_timestamp < TIMESTAMP '2026-09-07 03:00:00+00';
```
:::

The predicate is useful only when it matches the layout and statistics the
engine can inspect; partitioning is not a substitute for measuring the query
plan.

Bad partitioning can hurt performance. Partitioning by a high-cardinality field such as user ID may create too many tiny partitions. Partitioning by a column that queries rarely filter on may add complexity without benefit.

Clustering or sorting organizes records within files or partitions. This helps engines skip file ranges using metadata such as minimum and maximum values. Techniques include sorting, bucketing, Z-ordering, and engine-specific clustering.

The small file problem occurs when a table has many tiny files. Object storage and query engines have overhead per file, so reading 10,000 tiny files is usually much slower than reading a smaller number of well-sized files. Streaming and micro-batch pipelines often create small files unless compaction jobs merge them later.

Typical mitigations include:

- writing larger batches;
- compacting small files into larger files;
- avoiding excessive partition granularity;
- using table-format maintenance commands;
- separating raw landing frequency from curated table optimization.

Compaction changes the physical file layout, not the logical grain of
`curated_trades`. The before/after view makes the trade-off concrete: many
small micro-batch files can represent the correct rows and still impose query
overhead until a maintenance job rewrites them into fewer right-sized files.

[[REPORTKIT-VISUAL:fig:sec03-small-files-compaction]]

The right file size depends on engine, workload, compression, and cloud environment. Rules of thumb such as 128 MB to 1 GB per file can be useful starting points, but production systems should measure.

## Catalogs and Table Metadata

Storage systems need a way to find tables, schemas, partitions, permissions, and versions. This is the role of catalogs and metastores.

Examples include Hive Metastore, AWS Glue Data Catalog, Unity Catalog, Iceberg catalogs, Nessie, BigQuery datasets, Snowflake databases and schemas, and other platform-native catalogs.

A catalog may manage:

- table names and locations;
- schemas and column types;
- partitions and table properties;
- owners and descriptions;
- permissions and policies;
- table versions and metadata pointers;
- lineage and usage metadata.

The catalog is often the difference between a pile of files and a usable data platform.

## Storage Tooling Landscape

The storage-tooling table maps each physical or logical layer to representative choices.

::: {#tbl:storage-tooling}
Table: Storage layers and representative tools.

| Layer | Purpose | Examples |
| --- | --- | --- |
| Object storage | Durable file and object storage | S3, ADLS, GCS, MinIO |
| File formats | Physical representation of records | Parquet, ORC, Avro, JSON, CSV |
| Open table formats | Transactional table metadata over files | Delta Lake, Apache Iceberg, Apache Hudi |
| Cloud warehouses | Managed analytical SQL | Snowflake, BigQuery, Redshift, Synapse |
| Lakehouse platforms | Managed data lakehouse and processing | Databricks, EMR, Fabric, Starburst |
| Query engines | SQL over files, tables, or warehouses | Spark, Trino, Presto, DuckDB, ClickHouse |
| Catalogs | Table metadata and discovery | Hive Metastore, Glue, Unity Catalog, DataHub, OpenMetadata |
| Local development | Laptop-scale prototyping | DuckDB, MinIO, local Parquet, Docker |
:::

DuckDB is particularly useful for local data engineering because it can query local Parquet files and, with extensions and configuration, object storage. MinIO is useful because it provides an S3-compatible object store for local testing. Together, they let a developer prototype lake-style workflows without immediately relying on cloud infrastructure.

## Choosing Storage

The storage-choice table maps common needs to a likely starting point; it is a decision aid, not a product prescription.

::: {#tbl:storage-choices}
Table: Storage needs and likely choices.

| Need | Likely storage choice |
| --- | --- |
| Application transactions | Operational database |
| Governed reporting and dashboards | Data warehouse or lakehouse |
| Raw large-scale files | Data lake or lakehouse raw layer |
| Open-format analytical tables | Lakehouse with Iceberg, Delta, or Hudi |
| Machine learning feature reuse | Feature store or curated lakehouse tables |
| Search over documents or logs | Search index |
| Low-latency application reads | Serving database, cache, or key-value store |
| Local analytical prototyping | DuckDB with local Parquet |
:::

There is rarely one perfect storage system. Most mature architectures use several, with each serving a clear purpose. The key is to avoid accidental architecture: do not use an operational database as a warehouse, a raw object store as a governed semantic layer, or a cache as a system of record.

## Capstone Continuation: Building a Local Lakehouse

The crypto trade ingestion project from Section 2 can be extended into a storage project. The input is the append-only raw landing and manifest produced there, not a fresh read from the exchange. The goal is to organize those events into a local lakehouse that supports SQL queries, table metadata, and safe incremental writes while preserving the source trade key and the distinction between event time and ingestion time.

The capstone uses these storage conventions:

- Raw files remain under `s3://crypto-lake/raw/trades/{event_date}/{event_hour}/...`, with partition values derived from the UTC `event_timestamp`.
- Each event retains `event_timestamp` (when the trade happened) and `ingested_at` (when the producer received it). Neither is silently replaced by the other; file-write time belongs in the manifest rather than being substituted into the event record.
- `curated_trades` is the normalized analytical table. Its logical key is `(exchange_name, asset_symbol, source_trade_id)`, and its grain is one row per unique source trade.
- A late event may update an older event-time partition. Curated writes must therefore support a bounded merge or partition replacement and must be safe to retry.
- `price` is USDT per BTC and `quantity` is BTC for this single-symbol example. Currency conversion is outside the storage milestone.

One possible architecture:

1. Object storage: run MinIO locally and create a bucket such as `crypto-lake`.
2. Input: register or read the Section 2 raw files and manifest without overwriting the raw history.
3. File format: keep the raw micro-batches as Parquet and write normalized records to `s3://crypto-lake/curated/trades/...`.
4. Curated table: create `curated_trades` over the normalized files, using a Delta Lake or Iceberg table when transactional commits, merges, and snapshots are required.
5. Catalog: use the table format's local catalog option, or a lightweight catalog suitable for local development, and record the table location and schema.
6. Query engine: use DuckDB, Spark, or another engine that is known to read the chosen format and catalog. For the smallest local path, DuckDB can query the Parquet dataset directly before a table format is added.
7. Maintenance: run compaction and cleanup jobs so micro-batch writes do not create an unmanageable number of small files.
8. Validation: check row counts, unique composite trade keys, timestamp ranges, late-event handling, and partition completeness.

Example analytical query:

```sql
SELECT
    exchange_name,
    asset_symbol,
    date_trunc('hour', event_timestamp) AS hour_start_utc,
    AVG(price) AS average_price,
    SUM(quantity) AS traded_quantity
FROM curated_trades
WHERE event_timestamp >= :start_timestamp_utc
  AND event_timestamp < :end_timestamp_utc
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
```

This project teaches the important storage questions:

- Are raw events preserved before transformation?
- Are tables partitioned by event time while ingestion time remains available for freshness analysis?
- Can a late event be merged into the correct older partition?
- Can the table be queried while new data is being written?
- Can a failed write be retried without corrupting the table or duplicating a trade key?
- Can old snapshots be inspected or restored?
- Are small files compacted?
- Which engines can read the table successfully?
- Does the table layout match the actual query patterns?

For an advanced storage extension, register both the raw event files and `curated_trades` as tables with documented locations and schemas. Leave the hourly aggregate to Section 4, where its business grain and late-data policy can be defined alongside the transformation logic. This separation keeps storage responsible for durable, queryable inputs and transformation responsible for derived analytical meaning.

## Storage Output and Handoff

At the end of this stage, the project should expose:

- an immutable raw event history under the agreed event-time path;
- a manifest that links raw files to ingestion batches and broker offsets, including UTC `landed_at` timestamps;
- a queryable `curated_trades` table with one row per unique `(exchange_name, asset_symbol, source_trade_id)`;
- documented UTC timestamp fields, partition columns, schema, table location, and retry or merge behavior.

Section 4 consumes `curated_trades` as its input. It should not infer the trade key, reconstruct event time from a path, or mix raw and curated rows without saying so. Its staging model will preserve the one-row-per-trade grain, and its hourly model will deliberately change that grain.

The capstone handoff is `raw_trades + manifest → curated_trades + catalog`.
Storage owns durable files, table commits, metadata, and compaction; Section 4
owns the meaning of derived models and their grain.

**Common beginner mistakes.** Partitioning by a high-cardinality identifier,
confusing Parquet with table transactions, and treating raw files as a governed
curated model all create costs that later transformations cannot hide.

## Checkpoint: Partition Pruning Under a Different Filter

::: practice
**Practice.** `curated_trades` is partitioned by `event_date` and
`event_hour`, both derived from `event_timestamp`. Take the query in Listing
sec03-parquet-partition-query and rewrite its `WHERE` clause to filter on
`ingested_at` instead of `event_timestamp`, keeping the same UTC bounds.

1. Predict which partitions the engine can skip for the rewritten query.
2. Explain why the answer differs from the original query.
3. Name one situation, from the late-data material in Section 2, where
   `event_timestamp` and `ingested_at` would place the same row in different
   partitions.
:::

## Storage Design Checklist

Before implementing a storage layer, define:

- the workload: OLTP, OLAP, search, feature serving, or mixed;
- the data model and grain;
- expected data volume and growth rate;
- read and write latency requirements;
- consistency requirements for reads and writes;
- raw, cleaned, and curated retention rules;
- file format and compression choices;
- partitioning and clustering strategy;
- table format and catalog choice;
- event-time and ingestion-time semantics, including late-event handling;
- schema evolution policy;
- access control and sensitive data handling;
- backup, restore, replay, and time-travel requirements;
- compaction and maintenance strategy;
- cost monitoring and ownership.

Good storage design makes later work easier. Poor storage design turns every transformation, query, quality check, and dashboard into an argument with the physical layout of the data.

## Further Learning {#sec03-further-learning}

- Apache Parquet documentation, ["Overview"](https://parquet.apache.org/docs/overview/), *Apache Parquet documentation*. Accessed 18 September 2026. The columnar-format reference behind the File Formats and row-versus-column discussion above.
- Apache Iceberg documentation, ["Introduction"](https://iceberg.apache.org/docs/latest/), *Apache Iceberg documentation*. Accessed 18 September 2026. Covers the atomic commits, snapshot isolation, schema and partition evolution, and time travel listed under Open Table Formats.
- Delta Lake documentation, ["Welcome to the Delta Lake Documentation"](https://docs.delta.io/latest/delta-intro.html), *Delta Lake documentation*. Accessed 18 September 2026. Describes the transaction log and ACID guarantees behind the alternative table-format choice named in the capstone architecture.
- DuckDB documentation, ["Hive Partitioning"](https://duckdb.org/docs/current/data/partitioning/hive_partitioning.html), *DuckDB documentation*. Accessed 18 September 2026. Documents the `hive_partitioning` option and filter pushdown used in the partition-pruned query listing above.
