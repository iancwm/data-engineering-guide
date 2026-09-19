# Section 8 - Topics in Data Engineering

The earlier sections describe the core lifecycle: ingest data, store it durably, transform it, orchestrate the work, test its quality, and make the result discoverable and useful. This section collects practitioner concerns that cross those stages or become important as a system grows. They are not a second mandatory lifecycle. Read the parts that match the risk, scale, and operating context of the system you are building.

The central question is not "Which fashionable tool should we use?" It is "Which capability does this system need, and what is the simplest dependable way to provide it?" A small daily report and a global event platform may use different products while relying on the same engineering principles.

**Reader expectation.** You are not expected to implement every concern in a first project.

- **Implement now:** structured logging, secrets outside source code, basic access hygiene, one cost measure, and one incident or runbook example.
- **Be able to explain:** least privilege, retention, architecture trade-offs, ownership, observability signals, and compatibility policy.
- **Defer until required:** enterprise IAM design, specialized governance platforms, multi-region resilience, and complex organizational controls.

**Connecting failure scenario.** A pipeline is technically correct, but its dashboard is stale, its cloud cost has risen unexpectedly, an overly broad group can query sensitive raw data, and nobody knows who owns the failing dataset. Keep this scenario in view: observability should detect and explain the stale output; cost management should attribute and control the increase; security should restrict inappropriate access; ownership and contracts should identify who must respond and what was promised; and architecture and tool selection should avoid solving every symptom by adding another platform.

## Security, Privacy, and Compliance

Data platforms often combine operational, behavioral, financial, and personal information. Security is therefore a system property, not a final checklist. Controls should be designed at the point where data is collected, copied, transformed, stored, and served.

In the connecting scenario, basic access hygiene should stop the overly broad group from querying sensitive raw data; the rest of the controls should scale with the harm a failure could cause.

At a minimum, reason about:

- **Identity and authorization:** authenticate people and services, assign the least privilege needed, and separate read, write, administer, and deploy permissions.
- **Isolation:** separate development, test, and production environments; restrict network paths; and keep untrusted workloads away from sensitive stores.
- **Protection:** encrypt data in transit and at rest, manage keys and secrets outside source code, and avoid placing sensitive values in logs or error messages.
- **Lifecycle controls:** classify data, minimize collection, define retention periods, support approved deletion or correction requests, and document where copies exist.
- **Accountability:** record access and administrative changes, preserve enough audit context to investigate incidents, and review permissions as roles change.

The security-layers figure groups these controls by responsibility and emphasizes that a single product may implement more than one layer.

[[REPORTKIT-VISUAL:fig:sec08-security-layers]]

Access control can be implemented with roles, attributes, row-level policies, column masking, tokenization, or a combination. The mechanism matters less than making the policy explicit. For example, "analysts can read aggregated regional revenue but not customer email addresses" is a testable rule; "the warehouse is secure" is not.

Sensitive data includes personally identifiable information, health records, payment data, credentials, confidential business data, and regulated records. Classify sensitive fields near the source, propagate that classification through metadata and contracts, and create realistic but non-sensitive development datasets. A raw landing zone is not exempt from these controls merely because it is not user-facing.

Compliance obligations vary by industry, region, and contract. Examples include GDPR, HIPAA, PCI DSS, SOC 2, and internal controls. Data engineers normally share responsibility with security, legal, privacy, and platform teams. Their systems should make retention, deletion, access review, lineage, reproducibility, and evidence collection possible rather than relying on manual memory.

## Observability and Operations

Data systems are production systems. A successful process can still publish an empty table, stale data, duplicate facts, or a plausible result with a broken definition. Observability makes these failures visible and helps a team decide what to do next.

For the connecting scenario, observability must detect and explain why the dashboard is stale, not merely report that a job returned successfully.

Separate three related practices:

- **Testing:** checks an expected condition, such as a non-null key, before or during a run.
- **Monitoring:** records a signal over time and compares it with a threshold or target, such as freshness or job duration.
- **Observability:** provides enough context to explain an unexpected state, including the run, inputs, code version, data version, and affected consumers.

A useful minimum signal set covers:

- job state, duration, retry count, and queue delay;
- source and destination volume, freshness, and completeness;
- schema changes and contract violations;
- key quality measures such as null rates, uniqueness, valid ranges, and distribution changes;
- resource use, query performance, and cost;
- lineage or dependency information for assets that were not refreshed.

Logs describe events and decisions. Metrics provide numeric time series that can be alerted on. Traces connect a request or pipeline run across services. A batch pipeline may need only structured logs, run metrics, and dataset-level signals; a highly distributed streaming system may also need end-to-end traces. Instrumentation should match the failure modes rather than be added indiscriminately.

Alerts should be actionable. An alert should identify the affected asset, the failed check, the relevant run or partition, the likely owner, and the next diagnostic step. Alerting on every small fluctuation creates fatigue and teaches people to ignore the system. Pair important alerts with a short runbook that explains whether to retry, pause downstream publication, quarantine data, roll back, or escalate to the source owner.

When an incident occurs, preserve the evidence needed to reconstruct it: code and configuration versions, input offsets or partitions, schema versions, test results, and deployment history. After recovery, distinguish the immediate failure from the control that would have detected or prevented it. This turns operations into feedback for design rather than a sequence of one-off repairs.

## Cost Management

Cost is part of correctness for a production data system. A pipeline that meets its latency target by consuming an unreasonable amount of compute, storage, or network capacity is not complete. Cost should be considered alongside reliability and performance, not optimized in isolation.

For the connecting scenario, cost management means attributing the unexpected increase to a workload or owner and applying a control that brings it back within the agreed budget.

The largest levers are usually:

- storing data in an efficient columnar format and retaining only the history and copies that have a purpose;
- partitioning or clustering for the access patterns that actually occur, without creating thousands of tiny partitions;
- processing only new or changed data when a full refresh is unnecessary;
- right-sizing compute and turning off idle resources;
- avoiding repeated scans through incremental models, sensible caching, and query review;
- controlling cross-region or cross-cloud transfer and unplanned egress;
- assigning spend to teams, products, or workloads so that the owner of a decision can see its effect.

Track unit measures such as cost per successful pipeline run, cost per gigabyte processed, or cost per dashboard refresh. Set budgets and review unusually expensive queries, retries, and storage growth. A cheaper design is not automatically better if it loses data or requires excessive on-call work; compare total cost of ownership, including people and failure recovery.

Record the main cost drivers—storage, compute, orchestration, streaming,
observability, and transfer—in the design record, with a unit measure for each,
such as cost per retained terabyte, interval, run, monitored asset, or dashboard
refresh. Products may collapse several lifecycle stages, but the conceptual
boundaries still matter for ownership, evidence, cost, and exit planning.

## Architecture Patterns

Architecture patterns are useful vocabulary for discussing trade-offs, not templates to copy. They operate at different levels and can be combined: Lambda and Kappa describe processing paths, medallion describes data organization, and data mesh describes an organizational model. The pattern-comparison table keeps the choice tied to a workload and its main risk.

::: {#tbl:architecture-patterns}
Table: Data architecture patterns and trade-offs.

| Pattern | Useful when | Main cost or risk |
| --- | --- | --- |
| Lambda | A system needs a low-latency view and an independent batch recomputation path | Batch and streaming logic can diverge, creating duplicate code and reconciliation work |
| Kappa | Durable, replayable events are the primary source of truth and consumers can rebuild state | Replay depends on event quality, retention, and an affordable way to reprocess history |
| Medallion | A lakehouse needs recognizable raw, refined, and curated boundaries | Layer names do not define semantics; uncontrolled copies can create confusion and storage cost |
| Data mesh | Multiple domains need ownership of data products while a platform supplies shared capabilities | It requires strong contracts, discoverability, and federated standards; decentralization alone does not create quality |
:::

Choose a pattern only after stating the workload, failure model, ownership model, and expected change. A straightforward batch pipeline is often a better starting point than a dual-path architecture. A streaming architecture is justified by a real latency or event-replay requirement, not by the presence of a message broker in a diagram.

In the connecting scenario, this means asking whether the architecture can explain the stale output, cost, access, and ownership boundaries before adding another platform to the diagram.

## Practitioner Discussion: Data Contracts

Section 7 defines data contracts and provides the `lst:sec07-data-contract` YAML example. At this level, the conclusion is practical: contracts become more formal as independent producers and consumers increase. A small project may need only a versioned schema, an owner, and a change rule; a shared dataset needs explicit schema, meaning, freshness, quality, compatibility, and response responsibilities.

Tools may change, but those responsibilities remain. In the connecting scenario, the contract and ownership record identify who must respond and what freshness and quality were promised; they do not guarantee that the data is good, so boundary checks and an appropriate migration window still matter.

## Tools and Technology Landscape

Tool names change faster than capabilities. A single product may implement
several responsibilities, but the boundaries still matter for ownership,
failure handling, cost, and exit planning. The platform-boundaries figure maps
source and transport, storage and processing, orchestration, quality and
governance, and serving around the capstone artifacts; it is a capability map,
not a vendor recommendation.

[[REPORTKIT-VISUAL:fig:sec08-platform-boundaries]]

Products may bundle boundaries, but ownership, failure diagnosis, cost, and exit
planning remain distinct. Name the capability first so a product change does not
change the architecture by accident.

::: practice
**Apply the connecting failure scenario.** Its dashboard is showing BTC/USD prices that are six hours old. The page loads normally and shows no error to the viewer. Using the platform-boundaries figure, which boundary should the on-call engineer check first — ingestion, storage, orchestration, or serving — and why?

**Answer.** Check orchestration first. A dashboard that loads without error but shows stale data is the signature of a scheduled job that stopped running, is stuck, or silently skipped a run, not of a serving-layer bug: serving only renders whatever `fct_hourly_ohlcv` currently holds. Confirm whether the job that rebuilds `fct_hourly_ohlcv` actually ran and completed on schedule. If it did, move one boundary upstream and check ingestion for whether new `raw_trades` records are still landing; only after both come back healthy should storage or serving be suspected.
:::

## Selecting Tools and Managing Trade-offs

Evaluate tools against the workload and the team that will operate them. A compact decision record should answer:

1. **What data arrives, from where, and at what rate?** Consider protocols, source limits, volume, schema variability, and whether deletes or corrections must be captured.
2. **What latency and recovery behavior is required?** Specify acceptable freshness, replay or backfill needs, recovery time, and delivery or processing semantics.
3. **Where should data live and who will query it?** Decide whether the workload needs an operational database, analytical warehouse, object storage, table format, or more than one.
4. **What constraints are non-negotiable?** Include privacy, residency, security, compatibility, portability, budget, and existing platform standards.
5. **Who will own the service at 02:00?** Count upgrades, patching, scaling, incident response, support, and the skills already present on the team.
6. **How will the choice be tested?** Run a small representative workload and measure correctness, recovery, latency, cost, and operational effort before committing.

Managed services usually reduce infrastructure work, provide integrated scaling and support, and let a small team reach a service level sooner. They can also introduce usage-based cost, data-transfer charges, provider-specific interfaces, migration effort, and less control over failure behavior. Open-source software can offer portability, customization, and inspectable behavior, but the team owns deployment, upgrades, security, capacity planning, and on-call response. "Open source" is not the same as "free."

Use a managed option by default when the team is small, the operational requirement is urgent, or the capability is not a source of competitive advantage. Consider self-managed or open-source components when portability, deep customization, local deployment, or existing operational expertise justifies the additional work. A hybrid is often reasonable: managed storage or warehouse services with open formats and version-controlled transformation code. Record the trade-off and the exit cost rather than treating one operating model as universally superior. In the connecting scenario, diagnose the missing capability and accountable owner before adding another platform to solve the symptom.

**Choosing a Stack Under Constraints.**

The right default depends on who must learn, operate, and explain the system. Keep a learner's path small and reproducible; favor managed services when operating burden dominates; standardize capability interfaces, ownership, identity, lineage, and contracts across an enterprise; and prioritize immutable evidence, access audit, retention, correction provenance, and reproducibility where regulation demands it. These are selection biases, not vendor stacks. Change them when measured freshness, volume, recovery, portability, regulatory, or team constraints require it.

## Minimum Viable Stack and Learning Order

Most learners can build a complete, credible batch pipeline without adopting a distributed cluster or a long list of services. A practical minimum stack is:

- SQL and Python for querying, modeling, and small integrations;
- version control and a reproducible environment;
- Parquet files on local or object storage for durable analytical data;
- DuckDB or a small analytical warehouse for queries;
- SQL models or dbt for transformations;
- one orchestrator once the manual workflow is understood;
- assertions, structured logs, run metadata, and a basic freshness check.

Learn and add capability in this order. The learning-order table makes the recommended progression explicit and names what to defer until the current limitation is measured.

::: {#tbl:learning-order}
Table: Learning stages and capabilities to defer.

| Stage | Learn or use | Defer until there is evidence of need |
| --- | --- | --- |
| 1. Foundations | SQL, Python, Git, relational modeling, JSON/CSV/Parquet | Cloud-specific abstractions and distributed execution |
| 2. Durable batch | A source database or API, Parquet, DuckDB or one warehouse | Multiple storage systems and several table formats |
| 3. Reusable models | Incremental SQL, tests, documentation, and optionally dbt | A separate transformation framework for every language |
| 4. Reliable operation | One orchestrator, retries, backfills, logs, metrics, and alerts | Complex event-driven scheduling before dependencies are understood |
| 5. Scale and latency | Partitioning, query plans, object-store layout, and workload measurement | Distributed processing or streaming capabilities until single-node limits or latency targets require them |
| 6. Platform concerns | Cloud IAM, secrets, cataloging, lineage, retention, and cost controls | Enterprise governance products before the ownership and policy needs are clear |
| 7. Streaming | Events, offsets, replay, watermarking, and one compatible event broker or cloud service | A second streaming engine unless the workload needs its distinct processing model |
:::

When choosing the next tool, write down the limitation it resolves. "The current job cannot meet a measured latency target" is a reason to consider streaming; "this tool is popular" is not. Learning one complete stack end to end builds more judgment than sampling several products without operating any of them.

## Design Questions Before Building

Before selecting products or writing pipeline code, answer:

- Who will use the data, and what decision or process will it support?
- What does one row represent, and what are the keys and valid time fields?
- What is the source of truth for each important fact?
- What freshness, completeness, and recovery targets matter?
- How are inserts, updates, deletes, late events, and corrections represented?
- What history must be preserved, and what may be deleted or aggregated?
- Which quality checks block publication, and which produce warnings?
- What data is sensitive, and who may access each layer?
- Who owns the source, pipeline, dataset, and consumer-facing definition?
- How will a failed run be retried, replayed, backfilled, or rolled back?
- How will cost and usage be measured as volume grows?

These questions prevent overbuilding and expose missing requirements early. They also make a tool decision explainable: the architecture follows the workload and its obligations rather than the other way around.

## Production Readiness Checklist

A business-critical pipeline should have, at an appropriate level of rigor:

- version-controlled code, configuration, and schemas;
- documented inputs, outputs, grain, owners, and service expectations;
- reproducible environments and a deployment path;
- explicit delivery, retry, deduplication, and idempotency behavior;
- schema compatibility checks and data-quality tests;
- structured logs, run metadata, freshness signals, and actionable alerts;
- access controls, secret handling, classification, retention, and audit evidence;
- a backfill and recovery procedure that has been exercised;
- lineage or dependency visibility for downstream consumers;
- cost monitoring and a review process for unexpected growth;
- a short runbook explaining common failures and escalation paths.

Not every pipeline needs every platform feature. The standard should be proportional to the harm caused by stale, incorrect, unavailable, exposed, or unexpectedly expensive data. A clear risk decision is stronger than an accidental omission.

Section 8 is a production-awareness layer, not a prerequisite checklist. Section 9 now turns the full guide into staged project and portfolio evidence, so carry these concerns forward in proportion to the system you are building.

## Further Learning {#sec08-further-learning}

These sources go deeper on specific claims made in this section. They
supplement, and do not duplicate, the bibliography in Section 11.

- NIST. [*Security and Privacy Controls for Information Systems and Organizations* (SP 800-53 Rev. 5)](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final). National Institute of Standards and Technology, 2020 (updated 2023). A primary reference for the least-privilege, audit, and classification controls described under Security, Privacy, and Compliance.
- Amazon Web Services. [“Security Pillar — AWS Well-Architected Framework.”](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html) *AWS Well-Architected Framework*. Accessed 18 September 2026. A worked reference architecture organizing identity, network, data, and workload controls into layers, similar to the security-layers figure.
- Marz, Nathan, and James Warren. *Big Data: Principles and Best Practices of Scalable Real-Time Data Systems*. Manning, 2015. The primary source for the Lambda architecture pattern in the architecture-patterns table.
- Kreps, Jay. [“Questioning the Lambda Architecture.”](https://www.oreilly.com/radar/questioning-the-lambda-architecture/) *O'Reilly Radar*, 2 July 2014. Accessed 18 September 2026. The original argument for the single-path, replay-based Kappa architecture in the architecture-patterns table.
- Dehghani, Zhamak. [“How to Move Beyond a Monolithic Data Lake to a Distributed Data Mesh.”](https://martinfowler.com/articles/data-monolith-to-mesh.html) *martinfowler.com*, 20 May 2019. Accessed 18 September 2026. The original data mesh article that introduced the ownership model summarized in the architecture-patterns table, distinct from the 2022 book already cited in Section 11.
