# DeepAgent invited-viewer showcase

Status: proposed; awaiting owner review. Date: 2026-10-04.
Target showcase: 2026-10-05, America/New_York.

## Intent and evidence

Build a LangChain DeepAgents personal assistant and coding demo using DGX-local
inference, deployed on the owner's OCI VPS. The owner confirmed invited viewers.
The current repository is still template-mode, with no assistant implementation or
open project Issues. Template smoke passed during initial review. DGX model
discovery and OCI-to-DGX model discovery succeeded; generation and tool calling
have not yet been verified. These observations are prerequisites, not acceptance.

## Proposed first slice

An authenticated browser application offers two starter tasks and free-text chat:

1. Personal planning: turn supplied demonstration notes into an action plan and
   downloadable Markdown document.
2. Coding: inspect a bundled small Python project, edit files, run its tests in a
   disposable isolated environment, and present the actual diff and test outcome.

Show streamed assistant output, tool activity, failures, and downloadable artifacts.
Test failure must remain visible. Downloads and conversations belong to their
authenticated viewer. No private repository, email, calendar, account credentials,
or unrestricted host filesystem is available to the agent.

## Architecture and reuse assessment

Disposition: **adapt** maintained DeepAgents and the existing OCI Traefik deployment.
Use `create_deep_agent` with an explicit OpenAI-compatible model client targeting
the existing DGX Qwen3.6 service. Pin resolved dependencies in the project lockfile.
A small Python HTTP application serves the browser UI and agent API on OCI.
Inference uses the existing private Tailscale connection; no new public model route.
All inference for the demo is DGX-local; disable external tracing by default.

Prefer Traefik's existing BasicAuth middleware over a new identity service for
this one-day demonstration. Provision a distinct username and random password per
viewer, stored outside Git with BCrypt hashes at the proxy. The browser presents
its standard authentication prompt. Strip caller-provided identity headers before
authentication, then pass the authenticated username to the application. Strip
Authorization before forwarding. The application is reachable only through the
trusted proxy, and missing authenticated identity fails closed. Verify this trust
boundary end to end before accepting it. This is temporary demo access, with manual
revocation and browser-managed credentials, not a full account-management product.
The owner distributes invitations; no automated notifications are in scope.

The authenticated principal, not a caller-supplied viewer ID, owns each session,
run and artifact. Every read, mutation, stream and download checks ownership.
Use ephemeral session state for the showcase; restart clears sessions and artifacts.
Offer explicit reset. Tell viewers to use demonstration data.

Coding runs in disposable non-root containers with no network, host directories,
credentials, privileged mode or Docker socket. Enforce CPU, memory, process, output,
disk and wall-clock limits. The web/agent process receives no Docker socket.
An internal execution component launches only the fixed demo image and mounts
only the server-created workspace belonging to that run. Agent output cannot choose
container flags, image, host paths or mount targets. Test commands are fixed to
the bundled project's test runner; arbitrary shell execution is excluded.
This constrained coding boundary demonstrates file edits and test execution.
Its isolation must be verified; Docker alone is not a claim of a hostile-code sandbox.

Start with one active model run globally, one queued run per viewer, a queue of
at most five waiting runs, and a five-minute total run deadline. Reject excess
requests visibly; cancel disconnects and expired runs without losing the slot.
These are proposed demo defaults, adjustable only with corresponding verification.

## Capability dispositions

Propose activation: `application-composition-root`, `http-api-interface`,
`web-interface`. Each must receive project-specific paths, dependencies and checks
after approval; no inactive contract is silently bypassed.

Not applicable for this slice: CLI and MCP interfaces, durable project memory,
governed reflection, semantic evidence ledger, point-in-time provenance,
Python architecture metrics, computational complexity reports, challenge corpus
and domain role-separated analysis. Ordinary focused acceptance tests do not
activate a reusable challenge-corpus capability. Persistent personal memory and
additional tools are later work.

## Alternatives and tradeoffs

- Recommended: OCI application and constrained execution; DGX inference. Matches
  the requested hosting location and keeps coding activity off the GPU host.
- OCI edge with the application on DGX: follows existing local deployment examples,
  but puts demo orchestration alongside GPU workloads and changes the hosting scope.
- CLI-only showcase: less UI work, but does not give invited viewers the requested
  browser experience.

Do not build a new orchestration framework, authentication service, general shell
sandbox, dependency installer, or multi-agent worker platform for the showcase.

## Acceptance contract

- AC1: Unknown/revoked credentials are rejected over HTTPS; application routes
  cannot be reached through an alternate unprotected route or forged identity.
- AC2: Two invited identities cannot access each other's conversations, streams,
  run controls, workspaces or artifacts, even with known identifiers.
- AC3: Planning produces a downloadable document using actual DGX generation.
- AC4: Coding edits the sample project and executes its tests in the constrained
  environment; displayed diff and test outcome match retained execution results.
- AC5: Execution cannot read host secrets or another workspace, use network,
  exceed configured resource bounds, or select privileged container settings.
- AC6: Queuing, cancellation, timeout and model-unavailable responses behave
  predictably and release capacity for the next run.
- AC7: A real browser completes both tasks through the final OCI HTTPS URL.
- AC8: An exact deployment revision, health checks, startup instructions and
  rollback procedure are recorded; existing OCI applications remain healthy.

Verify static contracts, ownership tests and constrained execution locally, then
real-model tool calling and both browser journeys. An independent verifier reviews
the stable candidate, especially authentication, ownership and execution boundaries.
Execute the final current-attempt full gate once after repairs. Release readiness
and explicit final deployment approval precede infrastructure writes.

## Delivery and authority

First replace inherited template product claims with accepted DeepAgent intake,
charter, handoff and application checks without deleting unrelated template assets.
Create a governing Issue only when GitHub writes are authorized. Record accepted
architecture separately in an ADR. Use one bounded implementation plan and a
separate read-only verification lane as required by the project contract.

Spec approval accepts the proposed scope and named capability activations and
permits preparing the implementation plan. It does not authorize release, DNS
changes, invitations, infrastructure writes or credential distribution. The plan
must identify exact write paths and independent review before implementation.

Unresolved deployment parameter: hostname. Proposed `deepagent.ediacarian.dedyn.io`
is only a suggestion; inspect DNS and existing routing before requesting any change.
If reliable tool calling, cross-viewer isolation or execution isolation fails,
report the failed boundary and obtain a narrowed showcase decision; never silently
present a reduced chat-only demo as accepted coding functionality.

## Primary sources inspected

- https://docs.langchain.com/oss/python/deepagents/overview
- https://reference.langchain.com/python/deepagents/backends/local_shell/LocalShellBackend
- https://doc.traefik.io/traefik/v2.10/middlewares/http/basicauth/

Inspected 2026-10-04. Exact dependency versions, image digest and model behavior
must be established in implementation evidence; this proposal does not assert them.
