# Failure correction log

This log retains sanitized, reusable corrections for agent or tooling mistakes that are likely to
recur. It is not a transcript, retry counter, incident archive, or substitute for a regression
test. Never record tokens, secrets, private prompts, hidden reasoning, or unnecessary user data.

## Recording contract

Record a correction when a failed approach is repeatable or when another agent could plausibly
choose it again. Include:

- a stable ID, date, affected workflow, and public or synthetic provenance;
- the attempted approach and a short sanitized error signature;
- whether any local or external mutation occurred and how that was verified;
- the corrected command or decision path, including authorization boundaries;
- the exact verification that proved the correction; and
- the durable prevention surface: skill instruction, test, challenge candidate, or tool guard.

Do not rewrite a failure as success. If the correction is not verified, label it proposed. If the
failure exposes an escaped defect with a deterministic oracle, create a candidate under
`harness/challenges/`; do not store a live network call as a replay fixture.

## GH-PLANNING-001: Classic Project shortcut used for a Projects v2 item

- Date: 2026-08-24.
- Workflow: create GitHub Issues and add them to the configured Project v2 roadmap.
- Provenance: Agentic Application Assessor greenfield publication, sanitized operator-visible CLI
  evidence.
- Failed approach: passed `--project` to `gh issue create`.
- Error signature: the CLI attempted the deprecated Projects (classic) lookup and returned a
  Projects-classic deprecation error.
- Mutation check: the command created no Issue; a subsequent complete Issue-list read returned an
  empty list.
- Classification: client-command routing error, not Project drift, authentication failure, or a
  GraphQL API limitation.
- Corrected path:
  1. Create the Issue without `--project` and retain its exact URL.
  2. Preview `python3 tools/github_planning.py add-item --url ISSUE_URL`.
  3. After authorization, run the same command with `--yes`.
  4. Re-read Project items and the Issue's `projectItems` membership.
- Verification: seven Issues were created, added to Projects v2 Project #16, and re-read with exact
  membership; the final live planning audit reported no managed drift.
- Prevention: the GitHub-planning skill forbids the classic shortcut; the idempotent `add-item`
  command pre-reads membership, rejects duplicates, uses `gh project item-add` only when absent,
  and verifies post-write membership; unit tests assert each boundary.

## GH-PLANNING-008: corrected source remained absent from the active plugin cache

- Date: 2026-08-25.
- Workflow: create an Assessor follow-up Issue after its Macro Technical Pulse dogfood loop.
- Provenance: sanitized installed-plugin, canonical-source, and generated-application comparison.
- Failed approach: reused `gh issue create --project` while an installed plugin cache still exposed
  version `0.1.0`, then relied on the corrected canonical template as if it controlled the session.
- Error signature: the CLI attempted deprecated Projects (classic); the active cached planning
  skill lacked both the explicit prohibition and the supported `add-item` sequence.
- Mutation check: GitHub rejected the command before creating an Issue; a complete Issue re-read
  found no partial or duplicate object. The Issue was then created once through the supported flow.
- Classification: combined execution and distribution failure. The agent skipped a required
  safety-reference read, and corrected source was not cache-busted or reinstalled.
- Corrected path:
  1. Bump the plugin patch version and add a unique local cache identity during installation.
  2. Regenerate provenance and validate the canonical package.
  3. Reinstall from the reviewed local marketplace and compare the installed planning skill and
     safety-reference bytes with the reviewed generated distribution.
  4. Start a new thread so Codex loads the new plugin version.
- Verification: Issue #55 gives the plugin a new cache identity, regenerates provenance, and makes
  the isolated lifecycle probe compare the two exact installed planning files with the reviewed
  distribution.
- Prevention: refresh and verify the installed distribution whenever corrected plugin guidance
  changes. Command interception and general shell policy are explicitly outside this correction.

## GH-PLANNING-006: successful Project item write was immediately invisible

- Date: 2026-08-24.
- Workflow: add pull request #43 to the configured Projects v2 roadmap during publication.
- Provenance: sanitized live GitHub CLI evidence from the agentic-project-template repository.
- Failed approach: treated the first complete item-list response after `gh project item-add` as
  immediately consistent.
- Error signature: `Project v2 membership verification found 0 items ... expected 1`.
- Mutation check: no retry of `item-add` occurred. Independent complete re-reads found exactly one
  matching Project item, `PVTI_lAHOAiy8Ic4BhKnPzg30Ghk`, and the pull request's `projectItems`
  field named the expected roadmap.
- Classification: post-mutation read visibility lag, not a failed write, duplicate membership,
  invalid authentication, or Projects-classic routing.
- Corrected path:
  1. Perform the complete pre-read and one authorized `item-add` exactly as before.
  2. If the first complete post-write read has no exact match, retry only the complete read with
     bounded delays.
  3. Stop immediately on one match; fail closed on duplicates, truncation, malformed data, or
     persistent absence.
  4. Never repeat the mutation automatically; re-read live state before any operator retry.
- Verification: unit regressions prove delayed visibility succeeds after one mutation and bounded
  reads, while exhausted visibility fails after one mutation; live state contains exactly one pull
  request #43 membership.
- Prevention: the `add-item` implementation now separates its single mutation from bounded
  post-write reads, and the GitHub-planning guide documents the eventual-consistency boundary.

## GH-PR-METADATA-007: `gh pr edit` queried deprecated Project cards

- Date: 2026-08-24.
- Workflow: update pull request #43's body after pushing verified correction evidence.
- Provenance: sanitized live GitHub CLI evidence from the agentic-project-template repository.
- Failed approach: ran `gh pr edit NUMBER --body-file FILE` with GitHub CLI 2.45.0.
- Error signature: `GraphQL: Projects (classic) is being deprecated ... (projectCards)`.
- Mutation check: an exact pull-request re-read showed that neither correction-loop evidence nor
  the current test count was present; the head commit and existing Project membership were
  unchanged.
- Classification: installed-client GraphQL query incompatibility, not an invalid body file,
  authentication failure, Projects v2 membership error, or pull-request write rejection.
- Corrected path:
  1. Stop after the first failed `gh pr edit`; do not retry the same client route.
  2. Send the reviewed body file to the exact REST pull-request endpoint with
     `gh api --method PATCH repos/OWNER/REPOSITORY/pulls/NUMBER -F body=@FILE`.
  3. Re-read that pull request and require both the expected head SHA and distinguishing body
     content before reporting success.
- Verification: the REST mutation returned pull request #43; a subsequent REST read returned head
  `7cdca280d2ecd5d937126ba155a70c74995827ee` and both the correction-evidence marker and current
  206-test marker.
- Prevention: the GitHub-planning safety reference preserves the REST/body-file fallback and
  mandatory re-read; a repository test requires that packaged guidance and this ledger entry
  remain present.

## GH-AUTH-002: Sandboxed network failure reported as an invalid token

- Date: 2026-08-24.
- Workflow: validate GitHub CLI authentication before a read-only planning audit.
- Provenance: sanitized local CLI evidence from the agentic-project-template workspace.
- Failed approach: treated `gh auth status` inside a network-restricted sandbox as proof that the
  stored credential was invalid.
- Error signature: `Failed to log in` and `token ... is invalid`, followed by `gh api user`
  reporting that it could not connect to `api.github.com`.
- Mutation check: no local credential, GitHub object, or repository state was changed.
- Classification: unavailable network validation misclassified as credential rejection.
- Corrected path:
  1. Check for environment-token overrides without printing values.
  2. Retry the read-only check through the approved network-permission path.
  3. Call `gh api user` and require an authenticated HTTP success before declaring the token valid.
  4. Treat an unreachable API as indeterminate; rotate or reauthenticate only after an actual
     authentication rejection.
- Verification: the network-enabled API returned HTTP 200 for `stauntonjr`; `gh auth status`
  confirmed the keyring credential and expected scopes; the live Projects v2 audit passed.
- Prevention: the GitHub-planning safety reference requires sandbox-blocked network operations to
  use the approved permission path instead of being reported as GitHub or credential limitations.

## LOCAL-RUNTIME-003: Sandboxed loopback failure reported as an offline model

- Date: 2026-08-24.
- Workflow: determine whether the local SparkRun Qwen endpoint was available before a model-diversity
  canary run.
- Provenance: sanitized host Docker, SparkRun, listener, and OpenAI-compatible API evidence from the
  DGX workspace.
- Failed approach: called `http://127.0.0.1:8000/v1/models` only from a restricted sandbox and
  treated its connection failure as proof that the model was offline.
- Error signature: a sandbox-local connection failure to port 8000 even though the host service was
  already running.
- Mutation check: the corrective commands were read-only; they did not start, stop, restart, or
  reconfigure a container, model, listener, or repository.
- Classification: restricted loopback visibility misclassified as a host-runtime outage.
- Corrected path:
  1. Treat a failed network or loopback probe from a restricted runtime as indeterminate.
  2. Use the approved host-permission path to inspect the workload supervisor, such as
     `sparkrun status`.
  3. Inspect the candidate container and its start/restart state with `docker inspect`.
  4. Confirm the host listener with `ss`, then call the expected health or discovery endpoint, such
     as `/v1/models`, from the host boundary.
  5. If host verification is unavailable, report availability as unverified rather than offline.
  6. Never start a replacement workload before checking for an existing instance, especially when
     it can reserve GPU memory or collide on a host port.
- Verification: SparkRun reported job `8337765ded59` running the official
  `qwen3-coder-next-int4-autoround-vllm` recipe; Docker reported its host-network container running
  since `2026-08-24T02:12:31Z` with no restart or OOM state; the host listened on port 8000; and
  `/v1/models` returned `Intel/Qwen3-Coder-Next-int4-AutoRound`. The container start preceded the
  sandbox-only probe.
- Prevention: the engineering-loop skill requires host supervisor/container/listener/API evidence
  before classifying a local service unavailable and forbids starting a duplicate workload first;
  repository tests preserve the correction and reject the superseded availability claim.

## LOCAL-RUNNER-004: Pi shebang lost its adjacent Node runtime

- Date: 2026-08-24.
- Workflow: begin the first bounded paired Qwen canary through the repository model-stress runner.
- Provenance: sanitized local runner preflight in the agentic-project-template workspace.
- Failed approach: invoked the explicitly supplied `bin/pi` with an allowlisted environment whose
  `PATH` contained only system directories. Pi uses `#!/usr/bin/env node`, while its matching Node
  binary is adjacent to Pi in the self-contained installation.
- Error signature: `could not determine Pi version`.
- Mutation check: the runner stopped in its version preflight with `model_invoked: false`; it did
  not call the model, change the existing SparkRun workload, write GitHub state, or retain a model
  transcript.
- Classification: runner executable-resolution defect, not a model, provider, container, or
  endpoint outage.
- Corrected path: run the supplied self-contained Pi installation inside a networkless Bubblewrap
  version preflight, mount the complete installation read-only, and select its adjacent Node through
  the sandbox `PATH`.
- Verification: a registration-free regression inspects the version command's networkless,
  read-only installation mount and recognizes the fixture's semantic version; the repaired live
  runner preflight reports Pi 0.84.1 before model execution.
- Prevention: `test_pi_version_uses_networkless_read_only_self_contained_installation` preserves
  the self-contained runtime contract, and the live command continues to require an explicit
  `--pi` path.

## LOCAL-RUNNER-005: first canary overstated prompt and oracle provenance

- Date: 2026-08-24.
- Workflow: independently verify the first paired Qwen canary and its durable smoke report.
- Provenance: exact local runner source and ignored result digest recorded in the Issue #21 report.
- Failed approach: hashed `task.prompt` into the result while sending a different hard-coded prompt;
  passed every hidden oracle case and expectation through `HARNESS_ORACLE`; buffered model output
  before checking its size; retained arbitrary tool names; and initialized some post-invocation
  error output as `model_invoked: false`.
- Error signature: recorded prompt digest did not identify the prompt Pi received, and generated
  code could read the hidden expected answers from its own environment.
- Mutation check: no additional model invocation, SparkRun/container mutation, GitHub write, or
  retained transcript occurred during correction. The original run remains only diagnostic history.
- Classification: runner provenance, isolation, resource-bound, sanitization, and reporting defect;
  not evidence of a Qwen, Pi, vLLM, Docker, or endpoint failure.
- Corrected path: pass the exact contract prompt; run each oracle case in a separate networkless
  child containing no expectation; bound stdout during execution and discard stderr; mount Pi
  configuration read-only; sanitize tool identities; validate cross-field relationships; freeze
  one resource bundle and seed repository for every lane/trial; and carry invocation state through
  every failure path. The historical report now labels the old `.git`-excluding scope observation
  and post-hoc event-length check precisely instead of treating either as a verified bound. Task
  and resource paths are opened component by component without following a symlinked root or nested
  ancestor, preventing a dirty checkout from redirecting model-visible input outside the root.
- Verification: focused regressions cover prompt equality, answer-free oracle environments,
  operative event-size limits, deep JSON, stable tool categories, strict result relationships,
  schema/custom length parity, frozen-seed identity after source mutation, root/ancestor symlink
  rejection, pre-invocation output validation, and truthful post-invocation failure output.
- Prevention: acceptance-candidate evidence must come from the repaired runner and independent
  review; the first smoke cannot be promoted or used as the accepted baseline.

## LOCAL-RUNNER-006: read-only Pi config triggered a credential-lock startup failure

- Date: 2026-08-24.
- Workflow: begin the three-task, three-trial paired Qwen acceptance-candidate run.
- Provenance: sanitized runner result, host vLLM access log, and disposable zero-tool Pi probes.
- Failed approach: relied only on the synthetic `apiKey` in generated `models.json` while mounting
  the generated Pi configuration read-only. Pi 0.84.1 still consulted its credential store and
  attempted to create `auth.json.lock`, then exited before contacting the provider.
- Error signature: all six initial diagnostic lanes returned exit 1 in under one second, produced
  no edits, usage, settled event, or stable tool error, and generated no request in the vLLM log.
- Mutation check: the invalidated runs changed no candidate file, container, model service, GitHub
  object, or external repository; their sanitized ignored result is diagnostic only.
- Classification: Pi startup/configuration incompatibility, not model quality or endpoint failure.
- Corrected path:
  1. Confirm the existing SparkRun job, container, listener, and `/v1/models` response from the host.
  2. Reproduce the failure in a disposable zero-tool Bubblewrap session using the same read-only
     generated configuration.
  3. Pass Pi the explicit synthetic `--api-key not-needed` argument so it need not consult a
     credential store; never substitute or expose a real credential.
  4. Require a zero-tool Bubblewrap probe to settle and reach the loopback provider before rerunning
     any scored task.
  5. Invalidate every trial produced by the failed startup path rather than counting it as model
     evidence or retrying it as though the model had answered.
- Verification: the direct provider probe and the matching read-only-config Bubblewrap probe both
  settled against `Intel/Qwen3-Coder-Next-int4-AutoRound`; the latter succeeded only after the
  explicit synthetic API-key argument was supplied.
- Prevention: the lane-command regression requires the synthetic argument while retaining the
  read-only config mount; future reports must distinguish a Pi process start from a provider-backed,
  settled model response.

## LOCAL-RUNNER-007: API-key control design conflicted with the authorized subscription boundary

- Date: 2026-08-24.
- Workflow: add a GPT-5.6 Sol control to the paired Pi model-stress runner.
- Provenance: human authorization and local design inspection in the agentic-project-template
  workspace.
- Failed approach: the first proposed control would have accepted an OpenAI API key through a
  credential-isolating proxy.
- Error signature: the human owner explicitly prohibited an OpenAI API key and required use of the
  existing ChatGPT Pro/Codex subscription.
- Mutation check: no OpenAI request or model invocation occurred; no API key was read, printed,
  passed to Pi, persisted, or added to retained evidence. Only uncommitted local runner design work
  existed when the approach was stopped.
- Classification: authorization and credential-boundary mismatch, not a provider outage,
  authentication rejection, model failure, or Pi catalog limitation.
- Corrected path:
  1. Use Pi's native `openai-codex` Responses provider and exact `gpt-5.6-sol` model.
  2. Validate the existing Codex ChatGPT login while rejecting any API-key auth field.
  3. Keep the short-lived OAuth token in a host relay and give Pi only a random per-run canary JWT.
  4. Resolve the exact Pi model in a credential-free, offline catalog preflight before a request.
  5. Run a bounded smoke before any repeated paired evaluation.
- Verification: focused tests prove API-key rejection, private bounded no-symlink auth loading,
  canary authentication, fixed upstream routing, credential substitution, request budgets,
  sanitized Pi catalog resolution, exact control provenance, and no inherited API-key environment.
- Prevention: ADR-0009 and the runner make the subscription target explicit and fail closed;
  control documentation states that Pi's `--api-key` flag carries only a non-secret canary value.

## LOCAL-RUNNER-008: Pi Codex credential synchronization required ephemeral state

- Date: 2026-08-24.
- Workflow: run the first bounded GPT-5.6 Sol subscription-control smoke through Pi 0.84.1.
- Provenance: sanitized paired result, loopback relay metrics, and a no-credential disposable Pi
  reproduction.
- Failed approach: mounted the complete generated Pi agent directory read-only, assuming the
  explicit non-secret canary argument would prevent all credential-store writes.
- Error signature: Pi attempted `setRuntimeApiKey` synchronization for `openai-codex` and exited on
  a read-only `models-store.json` before emitting JSON events or reaching the relay.
- Mutation check: both lanes exited in under one second, changed no disposable task file, reported
  no provider tokens, and the relay observed zero requests and zero bytes. No ChatGPT model request,
  API-key use, GitHub write, or host credential/configuration mutation occurred.
- Classification: Pi runtime-state mount incompatibility, not a ChatGPT authentication rejection,
  GPT-5.6 Sol result, relay transport failure, or subscription-usage event.
- Corrected path: keep generated `models.json` and `settings.json` individually read-only while
  giving Pi an empty, sandbox-local writable agent-state directory for lock and runtime-store
  files. Continue to mount no host auth store and pass only the random canary.
- Verification: a no-credential reproduction must progress beyond credential synchronization to
  the deliberately closed loopback endpoint; the corrected host safety tests and bounded live
  smoke must then pass their respective startup and relay boundaries.
- Prevention: lane-command regressions require both configuration files to remain read-only,
  forbid an auth-file mount, and preserve the ephemeral-state layout.

## LOCAL-RUNNER-009: subscription auth parsing accepted ambiguous or malformed structures

- Date: 2026-08-24.
- Workflow: independently verify the GPT-5.6 Sol subscription-control candidate before publication.
- Provenance: synthetic private auth files and JWTs containing no real credential or account data.
- Failed approach: parsed the bounded Codex auth file with ordinary JSON semantics and accessed the
  nested JWT auth claim before confirming it was an object.
- Error signature: duplicate top-level JSON keys were accepted by last-value-wins parsing, while a
  string or list at the auth-claim path raised an uncaught `AttributeError` in the CLI check path.
- Mutation check: the verifier used only disposable local files; no model, provider, credential,
  candidate, GitHub object, or external repository was invoked or mutated.
- Classification: fail-closed input-validation defect, not a ChatGPT authentication rejection or
  subscription outage.
- Corrected path: reject duplicate keys in both the auth document and decoded JWT claims, validate
  the nested claim as an object before reading its account ID, and translate malformed input into
  the runner's structured non-invocation result.
- Verification: loader regressions cover duplicate auth keys and string/list claim shapes; the CLI
  regression requires exit 2, empty stderr, no traceback, `ok: false`, and `model_invoked: false`.
- Prevention: all host credential metadata remains bounded, private, no-symlink, strictly parsed,
  shape-checked, and outside the Pi/model sandbox before any provider preflight or request.

## LOCAL-RUNNER-010: unsafe credential header values could reach exception text

- Date: 2026-08-24.
- Workflow: independently verify the GPT-5.6 Sol subscription-control credential boundary.
- Provenance: synthetic private auth files and a fake upstream connection; no real credential or
  provider request.
- Failed approach: validated JWT structure and account consistency without first restricting the
  token and account ID to bounded header-safe character sets; upstream header construction errors
  also did not catch `ValueError`.
- Error signature: a synthetic access token with a trailing line feed reached `http.client`, whose
  rejected-header exception could include the supplied bearer value; control characters in a
  synthetic account ID had the same disclosure class.
- Mutation check: the verifier and regression use only disposable synthetic values and a mocked
  connection; no model, provider, credential, candidate, GitHub object, or external repository is
  invoked or mutated.
- Classification: credential-metadata validation and exception-sanitization defect, not a ChatGPT
  authentication rejection or subscription outage.
- Corrected path: accept only bounded JWT-token characters and bounded account-ID characters before
  decoding or constructing a credential; apply the same check in the relay constructor; catch an
  upstream header `ValueError` and return only the fixed sanitized relay error.
- Verification: loader regressions reject newline/carriage-return cases without echo, and a host
  relay regression forces an exception containing the synthetic bearer while requiring HTTP 502,
  empty stderr, no traceback, and no token or account value in the response.
- Prevention: no credential-derived string reaches an HTTP header until strict syntax, size,
  identity, expiry, private-file, duplicate-key, and nested-claim checks all pass.

## LOCAL-RUNNER-011: Pi Codex ignored the configured output-token option

- Date: 2026-08-24.
- Workflow: independently compare the GPT-5.6 Sol control contract with installed Pi 0.84.1.
- Provenance: read-only inspection of Pi's installed OpenAI-compatible and Codex Responses provider
  implementations plus the retained sanitized results.
- Failed approach: treated the generated `maxTokens: 4096` model override as an enforced provider
  request limit for both local Qwen and Codex subscription targets.
- Error signature: Pi's OpenAI-compatible completions implementation transmits its max-token field,
  but the Codex Responses implementation does not read the option or send `max_output_tokens`.
- Mutation check: the finding used static local inspection only; no model, provider, credential,
  GitHub object, candidate repository, or external repository was invoked or mutated.
- Classification: evidence-provenance and comparison-contract defect, not a GPT-5.6 Sol failure,
  timeout, or subscription rejection.
- Corrected path: schema 1.3 records `output_token_limit_enforcement` in the provider boundary;
  local Qwen requires `provider-request`, while Codex Sol requires `runner-config-only`. The Sol
  report excludes output-token enforcement from the equal-limit claim and discloses the asymmetry.
- Verification: custom and Draft 2020-12 validators reject target/enforcement mismatches; retained
  Sol artifacts are transparently annotated without changing any trial, usage, scope, request,
  timing, tool-error, or oracle value, and both original and corrected hashes are reported.
- Prevention: future cross-provider comparisons must distinguish configuration intent from an
  observed or source-verified provider request boundary.

## GH-ACCESS-003: Dependency-review prerequisite and Projects OAuth scope

- Date: 2026-09-17 (America/New_York).
- Workflow: finish SciFact PR #14 and place template Issue #59 in Project #13.
- Evidence: SciFact run `35302453139` reports unsupported dependency review with a request to
  ensure Dependency graph is enabled. A subsequent dependency-diff read returns HTTP 403.
  Network-enabled `gh auth status` identifies the Mac keyring login with `repo`, `read:org`, and
  `gist`; `gh project view 13 --owner stauntonjr --format json` reports missing `read:project`.
  No environment-token override was present. The browser settings page was signed out.
- Failed approach: reported the graph as disabled without inspecting its live setting, and stopped
  at the read-scope error without documenting the write scope required for membership.
- Mutation status: Issue #59 exists; these diagnostics changed no credential, setting, or membership.
- Correction: follow [GitHub access recovery](github-access-recovery.md). An administrator checks
  the graph setting/eligibility; the account owner grants `project` for authorized membership work
  on the execution host. Then rerun the failed check and resume the existing item URL through
  `github_planning.py add-item`; verify both results.
- Verification boundary: error classification and official recovery commands were checked; live
  setting repair, OAuth refresh, and Project placement have not been completed by this entry.
- Durable prevention: the planning entry point links the prerequisite and recovery runbook.

## DeepAgent local execution corrections — 2026-10-04

- Failed path: sandboxed FastAPI TestClient stalled. Mutation: none from test.
  Corrected path: bounded host-permission tests; access suite passed4/4.
  Guard: use approved host runtime for local async/socket acceptance; do not infer outage.
- Failed path: legacy A2AClient import and removed Starlette middleware decorator.
  Signatures: ImportError / AttributeError. Mutation: local test simulator only.
  Corrected path: inspect installed SDK1.2.1 ClientFactory and FastAPI server APIs;
  SDK transport suite passed7/7. Guard: lock and inspect actual package API first.
- Failed path: DeepAgents default tools remained available despite restrictive prompt.
  Mutation: no external effects. Corrected path: enforced offered/invoked tool allowlist;
  actual graph regression passed. Guard: verify capability boundary in model requests.
- Failed path: Playwright browser revision missing, then string polling blocked by CSP.
  Mutation: test artifacts only. Corrected path: matching /tmp browser installation and
  locator assertions. Guard: preserve CSP; browser completion recorded separately.
- Browser reload assertion matched both the artifact and its final summary and failed
  strict locator selection. Mutation: test harness only. Corrected path: select the
  artifact region's first matching element; retain failure, do not reinterpret it as
  an application defect or completed browser check.

## Selected investigation context and review-batch boundaries

Failed approach: tool closures carried project/cutoff while model prompt omitted them.
Signature: live browser produced a missing-context reply without delegation. Mutation:
local candidate only. Correction: pass authoritative selected context in system prompt.
Deterministic regression failed before repair; live browser later delegated successfully.

Failed approach: MCP defaults followed same-origin redirects and enforced limits after
parsing; refresh saved only task rows; UI allowed history switching during streaming.
Correction: maintained HTTP factory with redirect rejection/bounded streams, persisted
owned refresh events, and one browser operation guard. Focused JSON/SSE/redirect,
working-to-completed export and delayed-stream browser checks passed after repair.

Failed loop command used guessed finding IDs; tool rejected dispositions before any
code mutation. Corrected path: inspect recorded review IDs and use full identifiers
review-001-finding-001 through003. Gate accepted all dispositions and independent
scope review before starting repair attempt2. Preserve actual tool-generated IDs.

## October 6 model timeout and reviewed resume

Failed approach: model requests used a hard-coded30second timeout while the enclosing
run allowed a validated deadline up to300seconds. Actual source-backed browser runs
saved completed procurement artifacts, then timed out generating the final brief.
An isolated same-prompt HTTP request using a saved task status read confirmed
OpenAITimeoutError without submitting another investigation. Correction: reuse
Settings.timeout_seconds in the maintained model constructor; retries remain0 and
the enclosing run deadline is unchanged. A custom90second constructor regression
failed before repair and passed afterward. Retain prior browser failures as failures.

Failed recovery approach: the structured resume handoff listed absolute temporary
artifact paths. Signature: invalid declared preserved path. The resume/revise gates
rejected the sequence; the runtime fix was not applied. A regression test was written
under the owner's approved scope before the loop boundary was successfully resumed.
Corrected path: retain sanitized diagnostics under the ignored loop directory and
list repository-relative preserved paths. Resume and scope revision then succeeded.
Guard: validate the handoff shape and use checked subprocess transitions before
subsequent mutations, rather than continue after a failed shell stage.

## October 6 unexecuted model delegation

Failed approach: the system prompt instructed tool use, but a fresh model response
claimed that investigation was delegated while the application recorded zero tool
calls and zero tasks. Mutation: temporary acceptance data only; no procurement task
was submitted. Verification: SQLite event/task counts and the browser's unmet artifact
condition; sanitized counts retained in the loop. Proposed correction is maintained
first-call tool choice plus rejecting final answers without verified tool results.
The proposal is not applied and is not claimed as a durable guard yet.


## October 6 — evidence enforcement and host MCP startup

A model final message claimed delegation without a tool event or task. Prompt-only
instructions failed; the approved repair now requires an initial approved tool and
rejects final messages without a successfully returned service result. Deterministic
no-tool and failed-service regressions pass. This establishes result presence, not
entailment of every generated claim.

Temporary host SciFact MCP was launched with container DNS defaults and failed with
ConnectError / temporary failure in name resolution. No source was mutated. Corrected
GENERATOR_BASE_URL and LATE_INTERACTION_BASE_URL point at existing host services.
Browser verification was restarted; original failure remains recorded.

Loop command correction: revise preserved a blocked terminal state; resume then refused
a non-retry-exhausted run. The owner already authorized continued repairs; applied
guard and regression were retained, then a continuation loop explicitly recorded its
post-patch baseline limitation. Future terminal recovery must inspect recovery-status
and command prerequisites before writing; no baseline is retroactively invented.
