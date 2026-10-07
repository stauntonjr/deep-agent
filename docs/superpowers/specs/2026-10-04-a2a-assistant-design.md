# DeepAgent evidence assistant

Status: implementation proposal reflecting the owner's agreed A2A direction.
Supersedes the generic starter-task proposal; no OCI or procurement mutation authorized.

## Scope and acceptance

Build an invited-viewer DeepAgents browser application with DGX-local Qwen inference.
Its flagship task delegates a scoped procurement investigation to a fixed specialist
over A2A, displays task progress and the returned evidence artifact, and exposes
explicit human review. A secondary task checks a scientific claim through SciFact's
existing MCP tools. Arbitrary coding execution is deferred from this first slice.

The owner is finishing procurement separately and will notify this project when
the work is on main. Do not edit, merge, deploy or invent endpoints in that repo.
Use a labeled simulated A2A specialist for local contract development. Real
integration remains a separate gate against procurement's accepted adapter.
The simulator owns only test messages and synthetic artifacts, never domain rules.
It must be disabled in production configuration and clearly marked in local UI.

AC1: Unauthenticated requests fail; two viewer identities cannot access each
other's sessions, tasks, events, artifacts or review operations.
AC2: The actual DeepAgents graph uses the configured DGX model and delegates one
bounded investigation through the official A2A client to a fixed configured endpoint.
AC3: Submitted/working/input-required/completed/failed/cancelled states and artifacts
are displayed according to actual protocol results; unsupported states fail safely.
AC4: Agent tools cannot approve or save a brief. A separate explicit human action
binds viewer, owned task, exact brief ID and digest. Until the real specialist's
review contract is accepted, real approve/save is disabled rather than guessed.
AC5: Source references and unresolved quantities survive rendering and downloads;
remote text is untrusted data, never HTML or instructions granting authority.
AC6: SciFact tools return actual cited evidence or insufficiency. Service failure
is visible; no fabricated citations or substitute model answers.
AC7: One active model run globally, one waiting request per viewer, five total
waiting requests and a five-minute deadline. Disconnect/timeout cancels local
orchestration and releases capacity; remote cancellation outcome may remain unknown.
AC8: Installed local browser completes a simulated procurement interaction and
real-model SciFact interaction. Report simulator and real boundaries separately.
AC9: OCI package/configuration and rollback are reviewable, but actual HTTPS
deployment and real procurement integration remain pending external prerequisites.

## Architecture

Python >=3.11, FastAPI, DeepAgents, explicit ChatOpenAI-compatible DGX client,
official Apache-2.0 A2A Python SDK, and maintained LangChain MCP adapter. Resolve and
lock exact compatible package versions before code depends on their APIs. Use the
SDK's supported protocol version negotiated against the specialist's card; do not
handwrite JSON-RPC or adopt Agent Server merely to obtain an A2A endpoint.

Modules: configuration; owned session/task storage; specialist client; SciFact
adapter; DeepAgents construction; HTTP application; static browser presentation.
Store session/task ownership and protocol identifiers in application SQLite.
Do not deserialize arbitrary graph checkpoints supplied by clients. Keep agent
conversation state process-local initially; persisted task history is recoverable,
but resuming conversation generation after restart is not claimed.

Tools expose read/investigate/status operations only. A2A metadata carries no
user-controlled authority. Server-side task ownership and configured credentials
govern access. Fixed endpoint allowlist, redirects disabled, bounded responses and
timeouts prevent remote cards/artifacts from selecting arbitrary network targets.
No dynamic agent marketplace, push notification URLs or model-selected endpoints.

Local app binds loopback, using FastAPI HTTP Basic with an owner-created private
credential file and BCrypt verification. OCI release uses HTTPS through Traefik
and the same application authentication, avoiding trusted identity headers. Secrets
and per-viewer credentials are outside Git and are never included in prompts/tools.
Verify Origin on state-changing browser requests; expose no cross-origin policy.
Browser-native credential handling is temporary demo UX, with manual revocation.

Visible progress contains task states, tool names, safe summaries and artifact
references, not hidden reasoning or private prompts. Disable external tracing.
Persist only displayable content; warn viewers to use demonstration data and provide
owned reset/delete. Source links must be configured service links or plain references,
not arbitrary clickable URLs from remote artifacts.

## Assessment and capability reuse

Disposition: adapt maintained DeepAgents, A2A SDK and existing SciFact tools.
Build only thin application orchestration, ownership and presentation adapters.
Defer unrestricted coding sandbox, persistent personal memory, autonomous saving,
agent-to-agent approval, geospatial functionality and public anonymous access.

Owner's agreed implementation direction authorizes proposed activation of
application-composition-root, http-api-interface and web-interface for this slice.
Each activation must bind real paths/dependencies/checks. MCP use is an outbound
adapter; it does not activate an inbound mcp-interface server. Other catalog
capabilities remain inactive/not-applicable, including reusable project memory
and domain parallel-role analysis. Ordinary SQLite task records are application
state, not a competing project-memory system.

## Delivery authority and verification

Implement in this repository only; preserve the workspace file. Keep GitHub writes,
OCI changes, invitations and procurement integration/deployment gated separately.
No product dependency installation or implementation before the written-plan gate.
Record local scope and deferred gates in an engineering loop; never declare the
whole showcase complete from simulator tests.

Focused tests cover isolation, authority, artifacts, endpoint restrictions, failures
and queue cleanup. Verify real model tools before a browser acceptance run.
Independent read-only verification is required for the stable implementation.
Native implementation with one final independent verifier is recommended to keep
the tightly connected client/server/UI work coherent.

## Primary-source research (2026-10-04)

- https://docs.langchain.com/oss/python/deepagents/models
- https://github.com/a2aproject/a2a-python (Apache-2.0; current documentation describes
  protocol 1.0 and 0.3 compatibility; installed revision still to be pinned)
- https://a2a-protocol.org/latest/topics/life-of-a-task/
- https://docs.langchain.com/oss/python/langchain/mcp (current integration is beta;
  inspect locked compatibility rather than adopting an unpinned example)

Procurement's draft stack and local-only transport do not constitute an A2A contract.
After the owner's notification, inspect main, the actual card/API and acceptance
evidence before deciding the final adapter and human-review mapping.
