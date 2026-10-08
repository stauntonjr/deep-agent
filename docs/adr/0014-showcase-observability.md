# ADR-0014: Inspectable A2A showcase and opt-in distributed tracing

Status: accepted for implementation by owner request “Make a stronger showcase now”.

Expose actual scoped A2A requests/replies, task identities, elapsed time and evidence
summaries through the existing viewer-owned event store. Retain raw artifacts behind
collapsed details. These records describe observed actions, never hidden reasoning or
invented dialogue. The procurement specialist remains a read-only deterministic bridge.

Use the installed LangSmith SDK for optional graph/tool/server spans and distributed
parent headers carried in A2A metadata. Export is disabled unless the operator explicitly
sets DEEPAGENT_LANGSMITH_TRACING=1 and supplies credentials. The owner authorized locating an existing LCA credential; keep it outside the repository.
External payload export requires explicit approval separately from credential discovery.
Default operation creates a local event trace only. Never serialize service tokens or
HTTP authorization headers. Trace IDs correlate observations but grant no viewer access.

Reuse active composition, HTTP and web capabilities; no new ledger service, agent tools,
procurement workflow authority or unrestricted execution. Show model messages/tool results,
not chain-of-thought. Exported traces include demonstration prompts/results; use demo data.
