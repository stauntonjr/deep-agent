# ADR-0008: Use a local Qwen canary to measure harness lift

- Status: accepted
- Date: 2026-08-24
- Deciders: Jack Rory Staunton
- Governing issue: #21

## Context

The deterministic scenario, challenge, contract, and repository test suites verify known behavior,
but they do not show whether a less-capable coding model can use the harness to complete an
engineering task. Existing Pi/SparkRun dogfood used local Qwen successfully for narrow reads,
intake, reporting, and tool-call probes, while also exposing unsupported tool names, inaccurate
research claims, and weak broad synthesis. Those observations are valuable but one-off.

External engineering benchmarks reinforce two boundaries. SWE-bench evaluates patches by applying
them in containerized repositories and running executable tests. The historical SWE-bench Verified
work and SWE-Lancer also emphasize well-specified tasks, reproducible execution, and independently
reviewed oracles. OpenAI's 2026 reassessment says contamination and flawed tests mean SWE-bench
Verified should no longer be used as a current capability benchmark; it recommends SWE-bench Pro.
The Agent Skills guidance recommends comparing real executions and inspecting tool traces rather
than judging only final prose. None of those sources establishes a project-specific pass threshold.

## Decision

Use a runtime-selected local Qwen coding model as the recurring model-diversity canary. The canary
is supplemental evidence; deterministic checks, independent verification, human risk decisions,
and release authorization remain authoritative.

The canary is due when any of these conditions holds:

- no accepted canary evidence exists;
- ten reported engineering loops have completed since the last accepted run;
- a role, loop, reusable skill, provider adapter, Pi surface, or core loop tool changed; or
- a minor or major harness release is being assessed.

Each accepted evaluation must use a disposable repository and the same task and oracle in paired
lanes: Qwen without repository harness context and Qwen with the harness enabled. Capture exact
model, provider, Pi, serving recipe/runtime, task, prompt, tool set, limits, trial count, test
result, scope result, tool-call errors, elapsed time, and sanitized evidence identity. Run at least
three trials per lane for release evidence. A single trial is a smoke result only.

The template selects no default provider or model. Running or starting a model remains an explicit
operator action. The canary may not write GitHub state, deploy, publish, retain raw private prompts
or reasoning, approve its own output, or weaken a deterministic gate. A failed or unavailable
canary is reported as such; it is never converted into a deterministic pass.

## Consequences

### Positive

- The project can measure whether repository infrastructure closes part of the model-capability
  gap instead of celebrating an unpaired model success.
- Fixed tasks, executable oracles, exact provenance, and repeated trials make regressions visible.
- Local Qwen runs avoid mandatory external model spend and exercise provider portability.

### Negative

- Paired repeated runs consume GPU time and remain statistically noisy.
- A small corpus can overfit the harness or the model and is not a general coding benchmark.
- Keeping the serving recipe, Pi adapter, prompts, and task corpus reproducible requires upkeep.

### Risks and mitigations

- Benchmark gaming: keep held-out tasks and immutable oracles; review corpus changes separately.
- False confidence: report task-level results and variance, never a universal model-quality claim.
- Model drift: record exact model and serving runtime instead of relying on a friendly alias.
- Unsafe agent actions: run in a disposable repository without credentials or network-write
  authority and verify changed-path scope independently.

## Alternatives considered

| Alternative | Evidence | Reason not selected |
|---|---|---|
| Deterministic tests only | Fast and authoritative for known contracts | Cannot measure real model use of instructions and tools |
| Qwen harness-only runs | Existing dogfood found meaningful failures | Cannot distinguish harness value from raw model ability |
| Frontier-model comparison only | Useful reference ceiling | Does not answer whether the harness improves a weaker local model |
| Adopt SWE-bench as the only gate | Mature containerized patch oracle | Too costly for frequent template checks and does not isolate this harness's lift |
| Scheduled cloud model calls | Easy centralized execution | Adds spend, credentials, privacy, and external-side-effect policy before needed |

## Verification and revisit trigger

Validate `harness/model-stress.json` and its due-status command in `make smoke`. The subsequent
runner slice must demonstrate paired disposable execution through Pi and local SparkRun Qwen before
any result is called accepted. Revisit this ADR if the local canary no longer represents a useful
lower-capability model, Pi's execution boundary changes materially, or accumulated results show the
paired design does not distinguish harness effects.
