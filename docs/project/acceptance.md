# Local DeepAgent acceptance

Active workspace: `/home/jrs/deep-agent`; changes remain uncommitted.
Original reviewed candidate: branch `codex/a2a-assistant`, `/tmp/deep-agent-a2a`.
The 42 candidate files were transferred byte-for-byte, independently checked, and
`make smoke` passed in the primary workspace: 22 tests in 4.30 seconds plus harness,
formatting, lint, types and packaging. Transfer evidence is retained in
[workspace-integration](../../.harness/runs/workspace-integration/report.md).
No commit/push, actual procurement integration or OCI deployment is claimed.

Verified locally: 22 focused application tests; Ruff and Pyright clean. Actual DGX
Qwen3.6-35B-A3B-NVFP4 delegated through the official SDK-backed, explicitly simulated
procurement endpoint. Live existing SciFact MCP returned evidence through DeepAgents.
Chromium passed both starter journeys, owned history reload, evidence download and
375px layout. A separate delayed-stream browser probe verified session navigation
locks and evidence attribution. Wheel/sdist and non-root ARM container are packaged;
local ARM build does not establish OCI x86 compatibility or deployed HTTPS acceptance.

Independent review found three medium defects: MCP redirect/preparse bounds,
refreshed-task persistence, and active-stream session switching. One repair batch
uses the maintained MCP HTTP factory, bounded byte streams, existing owned event
storage and guarded DOM handlers. Focused JSON/SSE/redirect and working-to-completed
history tests pass. Final full gate and independent repaired-candidate verdict are
recorded in [a2a-assistant](../../.harness/runs/a2a-assistant/report.md): revision 2,
attempt 2 approved independently, with one passing final gate for that attempt.
Historical failures and the superseded gate remain recorded.

Actual procurement integration, exact human approval/save, final OCI HTTPS acceptance
and invitations remain pending external handoff. The local simulator demonstrates
protocol only. Model quality across arbitrary questions is not established. Start a
new investigation when changing project/cutoff to avoid reusing earlier chat context.

## October 6 actual bridge/browser attempt — incomplete

The current DGX model was available on172.17.0.1:8000;127.0.0.1:8000 no longer
accepted connections during this check. Temporary services used explicit endpoint
configuration; the GPU runtime was not changed. Chromium's actual model invocation
called the authenticated A2A bridge, saved completed synthetic procurement findings
and downloaded their source artifacts. The final answer was not produced in two
browser attempts, so cross-viewer/science/mobile stages of the new script did not run.
Prior successful simulated browser results remain historical and are not substituted.

Isolated HTTP replay with the original prompt used an existing task status read only
and exposed OpenAITimeoutError: Request timed out. The model has a hard-coded30second
request timeout, while the existing validated overall run deadline is300seconds.
The proposed repair aligns the model timeout to that deadline, retains retries0,
and requires a reviewed resume because the loop's three-failure ceiling was reached.
No repair or fourth acceptance attempt was made. See retained
[blocked loop](../../.harness/runs/real-bridge-browser/report.md).

## Approved timeout resume — October 6

The owner approved a reviewed resume and one fresh browser pass. The model now uses
the existing validated run deadline instead of a separate30second timeout; retries
remain0 and the enclosing run deadline remains at most300seconds. A custom90second
constructor regression failed before repair and passed after it.

The fresh browser pass instead revealed a separate model behavior defect: zero tool
calls, zero task events and zero remote task records, but an answer claiming delegation.
The evidence wait was stopped after that semantic failure. No fresh complete browser,
scientific MCP, cross-viewer or mobile acceptance is claimed. Proposed next repair:
use maintained first-call tool_choice and reject final answers without an actual
verified evidence/tool result. That guard is a proposal; it has not been applied.


## Evidence guard and corrected live journey — October 6

The owner approved continued bounded repairs without arbitrary one-pass gates.
Maintained first-call tool choice and a successful-result guard now reject unsupported
final answers. Deterministic tests cover ignored tool choice, failed service calls,
successful delegation and required-to-optional choice transition. Result presence
does not prove entailment of every generated claim.

The fresh actual browser journey passed in76.16seconds after correcting temporary
SciFact host URLs. Artifact: /tmp/deepagent-real-browser-results.json. Procurement
returned completed GPU-A findings, required8/ordered6 and12sources. Final answer,
owned download/reload, Bob404 session/download/task, actual SciFact MCP (5cited
evidence records) and375px layout passed. Download SHA256:
1be519b104042eebd41c8464de62f1c028da041fe88af67abfe83fa4ecc98d97.
Screenshots: /tmp/deepagent-real-a2a-browser.png,
/tmp/deepagent-real-science-browser.png, /tmp/deepagent-real-mobile-browser.png.
No production procurement, human approval/save or OCI release claim.


## October 8 — observable A2A showcase

Verified browser boundary: actual DGX DeepAgents → authenticated A2A bridge → existing
procurement corpus read services. GPU-A returned required8/ordered6 and12source records.
UI showed an actual SendMessage request and task reply with matching correlation IDs,
round-trip timing, source-read count and compact quantities; raw artifact remained collapsed.
Owned evidence/trace downloads matched persisted events; Bob received404 for foreign
session, artifact, trace and task access. Reload, actual SciFact MCP and375px layout passed.
Command: `PLAYWRIGHT_BROWSERS_PATH=/tmp/deepagent-playwright .venv/bin/python tests/app/browser_bridge_acceptance.py`.
Elapsed75.81seconds. Download SHA256:
`184327f69168434ca3f3ad057fd603d9ed75e3dc5bd408502347c1b30dcacd70`.
Artifacts: `/tmp/deepagent-real-a2a-browser.png`, `/tmp/deepagent-real-trace.json`,
`/tmp/deepagent-real-browser-results.json` (temporary local artifacts).

Tracing boundary: mocked maintained RunTree exports verified parent relationships
root→A2A SendMessage→Procurement A2A task→investigation/source reads across the ASGI
transport. Default disables export even if global LANGSMITH_TRACING is set; credentials
are only read with explicit opt-in. A real LangSmith upload is not yet verified:
automatic approval review requires explicit approval of exported prompts/results.
The credential was found privately under LCA; it is not committed or exposed in events.
No second LLM, full procurement LangGraph workflow, OCI deployment or correctness
benchmark is implied by the observed bridge exchange.


## Public hosting acceptance boundary

The owner-authorized VPS route is `https://deepagent.ediacarian.dedyn.io/`.
Current executed checks and exact source/image identity belong to the local
`.harness/runs/vps-deployment` run. The opt-in browser command in deploy/README exercises
that HTTPS entrypoint with private randomized acceptance viewers. Its required assertions
cover actual procurement A2A, scoped request/reply,8required/6ordered/12sources, actual
SciFact MCP, reload/downloads, cross-viewer404 and narrow layout. Separate checks must
prove TLS, authentication, persistent service restart and preservation of sibling services.
Configuration alone is not public acceptance. LangSmith export remains a separate consent.
