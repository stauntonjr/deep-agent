# Read-only procurement A2A bridge

The owner approved this separate slice after procurement main was ready. Inspected
upstream: `92ec704`, clean primary main on October 5. No upstream A2A server exists.
This bridge is implemented here; procurement code and domain policy remain unchanged.

It adapts the official A2A SDK1.2.1 JSONRPC1.0 server to the existing procurement
`/api/corpus/investigate` and `/api/corpus/source` GET services. It returns the actual
investigation DTO and original source DTOs as one text artifact. Upstream evidence
URLs never select transport destinations. Project and cutoff are exact validated
request fields; one explicit canonical item such as GPU-A is required in the question.
Ambiguous items produce input_required without a domain call. Unknown items/service
failures produce failed with no invented substitute. Completed is a protocol result,
not a resolved anomaly, accepted authority or human approval.

The configured service token authenticates the broker, not individual human viewers.
The existing DeepAgent application owns viewer/task mappings and access checks.
Bridge task storage is SDK-owned, in-memory and lost on restart; stored local artifacts
remain available in DeepAgent. An unavailable remote task is not automatically retried.
Use only the admitted synthetic demonstration corpus. There are no review/save,
reconciliation, purchase, arbitrary query or filesystem tools. This bridge invokes
read-only deterministic domain services; it does not run procurement's LangGraph
review workflow or confer its human review authority.

Local verification invoked actual merged procurement HTTP and official SDK send/get
for Atlas GPU-A and GPU-C at2026-10-01T00:00:00Z. GPU-A returned8required/6ordered with
12source DTOs; GPU-C preserved not_assessed and null quantities with12sources.
These demonstrate current synthetic domain behavior, not production procurement.
Exact results and checks are recorded in `.harness/runs/procurement-bridge`.

This is local integration only. No OCI routing, deployed acceptance or invitations
are claimed. See [deployment instructions](deployment.md) for startup and secrets.
