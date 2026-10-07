# DeepAgent A2A Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native implementation; one independent read-only verifier reviews the stable candidate.

**Goal:** Build and verify the invited-viewer DeepAgents application locally while real procurement integration waits for the owner's main-ready notification.

**Architecture:** FastAPI serves an owned-session browser application. DeepAgents calls a fixed specialist through the official A2A SDK and SciFact through a maintained MCP adapter. An explicitly labeled local simulator permits independent development without changing procurement.

**Tech Stack:** Python >=3.11, DeepAgents, langchain-openai, FastAPI, HTTPX, official a2a-sdk, maintained LangChain MCP adapter, SQLite, BCrypt, pytest, Ruff, Pyright, Playwright.

**Spec:** docs/superpowers/specs/2026-10-04-a2a-assistant-design.md

## Execution status — October 5

The local implementation slice completed and was independently approved in
[the recorded engineering loop](../../../.harness/runs/a2a-assistant/report.md).
It is now in `/home/jrs/deep-agent`, the owner's VS Code workspace. The transfer
was independently checked and the workspace gate passed with 22 tests; see
[workspace integration](../../../.harness/runs/workspace-integration/report.md).

- [x] Task 1: owned application and product contracts implemented and checked.
- [x] Task 2: official A2A client and labeled SDK-backed simulator implemented and checked.
- [x] Task 3: actual DGX DeepAgents delegation and existing SciFact MCP journeys recorded.
- [x] Task 4: browser journeys, owned reload/download, mobile layout and local package verified.
- [x] Three independent findings repaired as one batch and independently approved.
- [ ] Real procurement integration: owner confirmed it is still in progress.
- [ ] OCI release readiness, deployment and invitation distribution: external gates remain.

The original detailed checklist below is retained as the execution recipe. Its
individual challenge descriptions are not a claim that every proposed negative case
was executed. Exact checks and assurance limits are in the loop records and
[acceptance report](../../project/acceptance.md). No new product or release authority
is granted by this status reconciliation.

## Global Constraints

- One active model run globally, one waiting request per viewer, five total waiting requests, five-minute deadline.
- No procurement repository writes, OCI deployment, GitHub writes, invitations or automatic human approval.
- Fixed service endpoints; disabled redirects, bounded responses; no external tracing.
- Local simulation is visible and cannot be enabled in production configuration.
- Product version starts at 0.1.0, separate from the inherited harness version; runtime values and HTTP schemas are the public compatibility surface.
- Preserve unrelated files and template assets; reconcile product-facing records rather than delete history.

## Review Focus

- Cross-viewer guessed identifiers: every stream/download/review operation checks ownership.
- Prompt injection in specialist artifacts: text rendering and tools cannot grant authority.
- Unknown remote outcome: no blind retry or invented success after timeout/restart.
- Alternate proxy/API route: application authentication remains required on every route.
- Client disconnect and full queue: cancellation releases capacity without auto-repeating work.

### Task 1: Owned HTTP application and project initialization

**Files:** Create `src/deep_agent/config.py`, `store.py`, `app.py`, `__init__.py`, `__main__.py`; `tests/app/test_access.py`; modify `pyproject.toml`, `uv.lock`, `Makefile`, `README.md`, `.gitignore`, `.env.example`, `harness/project.yaml`, `harness/capabilities.json`, `.github/planning.json`; reconcile `docs/project/{charter,working-agreements,handoff}.md` and `harness/intake.json`; add `docs/adr/0013-deepagent-demo-boundaries.md`.

**Interfaces:** `Settings` owns fixed endpoints/private credential path; `Store` creates and retrieves viewer-owned sessions/tasks; `create_app(settings, store, assistant)` returns FastAPI; `Assistant.run(viewer_id, session_id, prompt)` is asynchronous.

- [ ] Start loop before mutations, recording AC1–AC9 with real integration/deployment explicitly pending; record adapt assessment and capability dispositions. Use local request reference while GitHub writes remain unapproved.
- [ ] Write failing tests: unauthenticated 401; wrong credentials 401; viewer B gets 404 for viewer A's session/task/artifact; spoofed identity body/header rejected; foreign Origin writes rejected.
- [ ] Run `uv run pytest tests/app/test_access.py -q` and retain RED evidence.
- [ ] Initialize approved product records using intake refresh; lock compatible dependencies and inspect SDK APIs. Implement application-level authentication, owned SQLite records and validated endpoints. Private credential material never enters Git or output.
- [ ] Run the targeted test plus Ruff/Pyright for touched modules; retain GREEN evidence. Capability activation lists actual implementation paths/dependencies/checks.

### Task 2: Procurement delegation through real A2A transport

**Files:** Create `src/deep_agent/specialist.py`, `tests/app/simulated_specialist.py`, `tests/app/test_specialist.py`.

**Interfaces:** `SpecialistClient.investigate(viewer_id, session_id, question, project, as_of)` returns an owned `TaskRecord`; `status(viewer_id, task_id)` returns verified protocol state and safe artifacts; `cancel(viewer_id, task_id)` records acknowledged or unknown outcome. `TaskRecord` contains local ID, remote ID, state, source references and artifact text, never authority supplied by an agent.

- [ ] Write failing tests against an SDK-backed local HTTP simulator: card discovery, real send/get exchange, working→input-required/completed, failed/cancelled, timeout, malformed/oversized artifacts, redirects, arbitrary card endpoint, known foreign task ID.
- [ ] Run `uv run pytest tests/app/test_specialist.py -q` and retain RED evidence.
- [ ] Implement official SDK client adapter, fixed card/transport validation, owned task mapping and bounded polling. Simulator implements protocol behavior only, with clearly synthetic artifact text and no copied procurement policy.
- [ ] Run targeted tests; verify actual HTTP exchange rather than mocks alone. Leave real review/save disabled with a clear pending-integration explanation.

### Task 3: DeepAgents and SciFact tools with bounded runs

**Files:** Create `src/deep_agent/assistant.py`, `scifact.py`, `runs.py`; `tests/app/test_assistant.py`, `test_runs.py`, `test_scifact.py`.

**Interfaces:** `build_assistant(settings, store, specialist, scifact)` returns the `Assistant` used by Task1. `SciFactClient.search(query)` and `answer(query)` return validated evidence/citations. `RunCoordinator` enforces the global/viewer queue and deadline.

- [ ] Write failing tests: required message-state invocation; exact delegation tool arguments; no approval/save tool; remote artifacts cannot override instructions; no model-produced fallback evidence; queue limits and cancelled/expired capacity recovery.
- [ ] Run `uv run pytest tests/app/test_assistant.py tests/app/test_runs.py tests/app/test_scifact.py -q` and retain RED evidence.
- [ ] Construct the actual DeepAgents graph with explicit ChatOpenAI DGX configuration, read/investigate/status tools and SciFact MCP adapter. Expose only safe visible events; persist owned task history, not hidden reasoning.
- [ ] Run GREEN tests, then inspect DGX/SciFact service health and execute one bounded real-model delegation to the simulator and one SciFact claim check. Record model identity, tool events, citations and boundary; avoid retries masquerading as independent success.

### Task 4: Browser journey and deployable package

**Files:** Create `src/deep_agent/web/{index.html,app.js,app.css}`, `tests/app/test_browser.py`, `Dockerfile`, `compose.yaml`, `deploy/traefik.example.yaml`, `docs/project/deployment.md`; update `app.py`, `README.md`, handoff and loop evidence.

**Interfaces:** Owned request/stream/status/download/reset routes invoke Task1–3 services. Human review control is disabled until the specialist contract is accepted; no client approval boolean is forwarded to an agent.

- [ ] Write failing browser/API cases: sign-in, simulated-mode banner, scoped project/cutoff controls, actual task activity, safe artifact rendering, download, source references, service failure, refresh/restart displaying prior task without reissuing inference, disconnect cleanup.
- [ ] Run `uv run pytest tests/app/test_browser.py -q` and retain RED evidence.
- [ ] Implement the UI and a non-root container without Docker socket or private host mounts. Compose defaults to loopback; example Traefik config retains application authentication and HTTPS requirements. Document startup, credentials, reset, health, rollback and simulation limitations.
- [ ] Run actual local browser journeys and installed-package smoke. Validate Compose without changing OCI.
- [ ] Record product release impact, stabilize the candidate, execute one final `make smoke`, `python3 tools/product_version.py`, `git diff --check`, `git status --short`; retain exact outcomes and elapsed times.
- [ ] Obtain a bounded independent read-only review of AC1–AC9; collect one batch before repair and follow proportionality rules. Report local completion separately from pending AC9 external gates.

## External handoff after procurement is ready

Inspect procurement main only after owner notification. Compare actual A2A card,
supported version, scoped invocation and human-review contract with the client.
Do not automatically publish a new A2A server for that repo. If no accepted adapter
exists, identify that exact integration gap and propose the smallest separate slice.
Verify real task/artifact ownership, explicit exact human review and idempotent save.
Obtain release readiness and final OCI authorization against the exact candidate.

## Self-review

AC1→Task1; AC2–5→Tasks2–3; AC6–7→Task3; AC8→Task4; AC9→Task4 packaging plus deferred external handoff. Review-focus failures have corresponding targeted tests. The simulator cannot satisfy real procurement acceptance. Native execution is recommended because all four tasks share application/session/client interfaces; independent review remains mandatory at the stable boundary.
