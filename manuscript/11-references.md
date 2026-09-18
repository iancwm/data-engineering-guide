# Section 11 - References

The references below use one publication style so that each source can be
identified and retrieved without relying on a raw URL alone. They are split
into two groups: sources that a claim, figure, or design choice elsewhere in
this guide is directly attributed to, and further reading that supports the
book's scope more generally but is not tied to one specific in-text claim.
Each in-section "Further Learning" list (ends of Sections 2-9) points to
narrower, section-specific sources; this list is the book's formal
bibliography.

## Sources Cited

These sources back a specific factual claim, named result, or implementation
choice made in the manuscript.

- Databricks. [“What Is Data Engineering?”](https://www.databricks.com/blog/what-is-data-engineering) *Databricks blog*. Accessed 6 September 2026. Section 1's summary of data engineering's core activities is explicitly drawn from this article.
- Kimball, Ralph, and Margy Ross. [*The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling*](https://www.wiley.com/en-us/The+Data+Warehouse+Toolkit%3A+The+Definitive+Guide+to+Dimensional+Modeling%2C+3rd+Edition-p-9781118530801). 3rd ed. Wiley, 2013. The standard reference for the star schemas, surrogate keys, and slowly changing dimension types Section 4 introduces.
- Gilbert, Seth, and Nancy Lynch. [“Brewer's Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services.”](https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf) *ACM SIGACT News* 33, no. 2 (2002): 51-59. The formal statement and proof behind the CAP theorem as presented in Section 3's "Distributed Storage, CAP, and PACELC" discussion.
- Abadi, Daniel. [“Consistency Tradeoffs in Modern Distributed Database System Design: CAP Is Only Part of the Story.”](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf) *IEEE Computer* 45, no. 2 (2012): 37-42. Introduces the PACELC framework Section 3 extends the CAP discussion with.
- Dehghani, Zhamak. [*Data Mesh: Delivering Data-Driven Value at Scale*](https://www.oreilly.com/library/view/data-mesh/9781492092384/titlepage01.html). O'Reilly Media, 2022. The originating source for the domain-ownership, data-as-a-product, and federated-governance model Section 8 characterizes as "data mesh."

## Further Reading

These sources support the guide's overall scope and are recommended next
steps; no single passage in the manuscript is drawn from or attributed to
them.

- Kleppmann, Martin. [*Designing Data-Intensive Applications*](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/). O'Reilly Media, 2017. Broad, deeper treatment of the distributed-systems trade-offs (replication, partitioning, consistency, delivery guarantees) that Sections 2 and 3 introduce at an applied level.
- Reis, Joe, and Matt Housley. [*Fundamentals of Data Engineering*](https://www.oreilly.com/library/view/fundamentals-of-data/9781098108298/). O'Reilly Media, 2022. A broad overview of the data engineering lifecycle covering the same ground as this guide at a similar level.
