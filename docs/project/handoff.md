# DeepAgent handoff

## Current accepted work

The owner approved native execution of the
[2026-10-04 A2A assistant plan](../superpowers/plans/2026-10-04-a2a-assistant.md).
Active working directory: `/home/jrs/deep-agent`, the owner's VS Code workspace.
The reviewed candidate originated in `/tmp/deep-agent-a2a` on
`codex/a2a-assistant`, from base `68da52f`. It was transferred byte-for-byte to the
primary checkout after the owner requested workspace execution. The implementation
is uncommitted in the primary checkout; the workspace file was preserved. Continue
all implementation here, rather than in the temporary worktree.

Local completion evidence:
[implementation review](../../.harness/runs/a2a-assistant/report.md) and
[workspace transfer review](../../.harness/runs/workspace-integration/report.md).
Product0.1.0 is separate from the inherited template harness version.

Implemented candidate: FastAPI application authentication; private viewer credentials;
owned SQLite sessions/tasks; bounded request/response bodies; official A2A SDK1.2.1
JSONRPC1.0 client; labeled test-only simulator; actual DeepAgents0.7.21 graph; fixed
read/investigation tool boundary; SciFact MCP adapter; single-worker queue/deadline;
browser task/evidence/history/download/reset; wheel and non-root container package.
Composition, HTTP and web catalog capabilities are active under owner-approved scope.
Other optional capabilities remain inactive.

## Verified boundaries

22 focused tests pass, Ruff passes, Pyright reports0errors. Actual DGX Qwen delegated
through the SDK-backed simulator and returned its task/artifact. Actual SciFact MCP
returned an explicit insufficient-evidence answer through the DeepAgents graph.
Wheel installs with browser assets. These are local development checks, not current
procurement acceptance, comprehensive model quality or OCI release evidence.
Chromium journeys, downloads, reload and mobile layout passed; local ARM container built.
Three independent findings were repaired in one bounded batch; consult the
[execution ledger](execution.md) and [acceptance report](acceptance.md) for final status.

## External prerequisites

On October 5, the owner notified that procurement was pushed to main. The clean local
main was inspected at92ec704. It contains the merged review workflow but no A2A server.
The owner approved a read-only bridge in this repository; see [bridge](bridge.md).
Do not edit or merge that repository. The bridge exposes local authenticated SDK1.0 JSONRPC investigation/source tasks.
Viewer scope and exact human-review/save integration remain separate gates. Real human
review/save remains disabled here. The simulator never certifies procurement semantics.

The previous session verified OCI access over Tailscale and the older procurement
inspector; those operational observations have not been refreshed in this documentation
pass. DeepAgent has not been deployed by these loops. Release readiness, final deployment authority,
service credentials/private routes and invited-viewer distribution remain separate.
See [operator instructions](deployment.md); existing OCI services must be preserved.

## Operational limits

One Uvicorn worker only. Persistent task history does not resume process-local chat.
Local stop cannot prove that remote inference/task execution stopped. Unknown outcomes
require inspection, never automatic retry. Use demonstration data only. No unrestricted
coding, autonomous approval/purchasing, geospatial or production uptime claims.

Start a new investigation when changing project/cutoff; chat context retains prior messages.

## Historical browser failures — October 6

Actual browser→DGX→bridge→procurement findings/download were observed, but final
answer generation timed out. Current model socket was172.17.0.1:8000. Isolated
same-prompt HTTP replay with an existing task confirmed OpenAITimeoutError from the
hard-coded30second model timeout; the overall run deadline remains300seconds.
`real-bridge-browser` reached its three-failure ceiling and is blocked. Proposed
next slice aligns model timeout to the existing validated deadline, retains retries0,
adds a focused constructor regression, and runs one fresh browser acceptance after
human-reviewed resume. No successful new science/isolation/mobile claim or OCI
release is made. See [acceptance](acceptance.md) and the retained loop handoff.

The owner subsequently approved the timeout fix and a fresh browser pass. That fix
is now implemented and constructor-tested; the source uses Settings.timeout_seconds
with retries0. The fresh pass exposed a separate false-delegation answer without any
tool calls or tasks. The subsequent repair used a maintained first-call tool choice
and a verified-result guard before accepting a model answer. That guard was then applied and the full journey passed, as recorded below.
The failures above are retained as historical evidence.


## Current verified local state — October 6

Owner authorized continued repairs and superseded the arbitrary one-pass stop.
The evidence guard is implemented: first model call requires an approved tool;
unsupported final answers are rejected before history/persistence. Retries remain0.
The corrected actual browser journey passed in76.16seconds: DGX procurement A2A
completed with required8/ordered6 and12sources; final answer, owned download/reload,
cross-viewer404, actual SciFact MCP and375px layout passed. Science returned5cited
evidence records. These are local synthetic-corpus checks; no OCI publication.
Continuation loop: evidence-runtime-repair. Prior failures remain in real-bridge-browser.
Temporary local services use host model URL172.17.0.1:8000 and MCP host URLs;
container DNS defaults do not resolve from the host.


## Main publication — October 7

Owner requested the working app and README pushed to main. Runtime listeners were
refreshed and the authenticated app remains available on DGX loopback8100. README
now describes actual read-only integration and full startup; personal VS Code workspace
file is excluded from publication. No OCI mutation or invitation distribution is implied.


## Stronger local showcase — October 8

In the owner's VS Code workspace, the new showcase candidate adds observed model milestones,
A2A scoped request/reply cards with shared correlation IDs and actual timings, compact
procurement quantities/source counts, collapsed raw evidence, and viewer-owned trace downloads.
Read-only bridge authority and evidence guards remain unchanged. SDK-based LangSmith tracing
is implemented with explicit app/bridge opt-in; a mocked exporter confirms distributed parentage.
Credential discovery from the LCA environment succeeded without publishing the key.

Current live browser acceptance passed in75.81seconds with actual DGX inference,
procurement required8/ordered6/12sources, evidence/trace download and reload, Bob404,
SciFact MCP and375px layout. Local app/bridge remain on127.0.0.1:8100/8101 with export off.
Automatic approval review rejected external payload export; explicit permission was requested.
A real LangSmith upload/tree is pending that permission and has not been claimed verified.
The candidate is uncommitted; the personal workspace file remains untouched.
No OCI deployment or procurement LangGraph approval/save integration was performed.
See [showcase ADR](../adr/0014-showcase-observability.md) and
[showcase run](../../.harness/runs/showcase-observability/run.json).


## VPS hosting continuation — October 8

Owner authorized `deepagent.ediacarian.dedyn.io` using the established VPS edge pattern.
The production profile is [deploy/README](../../deploy/README.md): Traefik/deSEC on VPS,
private Tailscale18100 to DGX loopback8100, non-root read-only app container, persistent
user-service backing readers, randomized private credentials and durable data. Existing
model and sibling applications remain under their existing supervisors. No LangSmith
export or invitation distribution is authorized by this hosting request. Exact artifact,
public browser and rollout status are recorded in the local `vps-deployment` engineering
run; consult that evidence rather than inferring public readiness from these files.
