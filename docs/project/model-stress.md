# Local model-diversity canary

The harness uses a local Qwen coding model as supplemental evidence that repository instructions,
skills, loop contracts, and tool guards help a less-capable model perform engineering work. It does
not make Qwen a project default and does not replace tests, independent review, or human authority.

Check the contract and whether a canary is due without invoking a model:

```bash
python3 tools/model_stress.py check
python3 tools/model_stress.py status \
  --accepted-evidence \
  --reported-loops-since 4 \
  --changed-path harness/roles/verifier.md \
  --release-impact patch
```

The status command is pure local evaluation. It reports `model_invoked: false`. A canary is due
when no accepted evidence exists, ten loops have elapsed, an agent-control path changed, or a minor
or major release is assessed.

The paired runner validates its held-out task without invoking a model:

```bash
python3 tools/model_stress_runner.py check
```

Each task freezes one validated resource bundle, records that bundle's SHA-256 digest, builds
one seed Git repository, and clones that exact seed for every lane and trial. Both lanes therefore
receive the same initial bytes, public requirements, exact contract prompt, `read`/`edit` tools,
token configuration, and executable oracle even if the source worktree changes during a long run. Oracle
expectations remain outside the model-visible repository. The bare lane disables context files,
skills, and extensions. The harness lane enables the repository `AGENTS.md`, canonical
engineering-loop skill, and Pi context extension. Both lanes run in Bubblewrap with a sanitized
environment, no credentials, a read-only host system runtime, a read-only Pi installation, a
read-only generated Pi configuration, an explicit non-secret `not-needed` API-key placeholder that
prevents Pi from consulting a credential store, and no shell tool. The host home and source repository are
not mounted. Only the disposable repository and ephemeral virtual filesystems are writable. Model
event output is capped while the process runs, stderr is discarded, and the model output-token
configuration is fixed at 4,096 tokens. Result schema 1.3 separately records whether the selected
Pi provider sends that value in its provider request. Pi 0.84.1 source shows that the local Qwen
OpenAI-compatible path transmits it; future schema-1.3 Qwen results classify that as
`provider-request`. Historical schema-1.1 Qwen artifacts do not contain the field. Pi's Codex
Responses path ignores the option, so Sol records `runner-config-only` and must not be described as
having the same provider output-token bound.

Generated code is evaluated one case at a time in separate resource-bounded Bubblewrap processes.
Each oracle process receives only the current arguments plus the module and function names; hidden
expected values, exception names, other cases, and host environment are not provided. Its network
namespace is unshared, the disposable repository is mounted read-only, and observed return or
exception data is compared with the hidden expectation only in the host runner. Direct snapshots
include Git metadata and also bound path count and file bytes before hashing generated state. Every
seed clone must match the frozen seed snapshot before Pi is invoked.

The repository root, held-out task, and every resource ancestor/final component are opened without
following symlinks. The task must remain beneath that root. A symlinked root or nested ancestor is
rejected before any model invocation so an adopted or dirty checkout cannot redirect model-visible
inputs to host-external files.

Live execution requires explicit Pi, provider, model, serving-runtime, and serving-recipe values.
Results may be written only below ignored `.harness/model-stress/`; stdout and the result contain
aggregate token counts, stable tool-error categories, changed paths, oracle case IDs, and timing,
but never raw model text, prompts, transcripts, reasoning, or provider error bodies. One trial is
always labeled `smoke`; two trials are rejected; three to ten trials produce only
`acceptance-candidate` evidence and still require independent review and human acceptance.

Accepted live evidence requires the same disposable engineering task in bare and harness-enabled
Qwen lanes, at least three trials per lane, independent write-scope inspection, exact runtime
provenance, and the deterministic gates. The runner never promotes its own output to an accepted
baseline and never makes a general harness-lift claim.

## Optional ChatGPT subscription frontier control

ADR-0009 defines a separate one-off positive control using Pi's native `openai-codex` provider and
exact `gpt-5.6-sol`. It uses the same frozen tasks, prompts, tools, lanes, limits, and hidden oracles
as the local Qwen run except for the disclosed provider output-token enforcement asymmetry. Each
evaluation freezes its own harness-resource bundle; the Sol report must
compare its digest with Qwen and disclose any byte difference rather than implying an identical
harness-context replay. It does not replace the Qwen cadence, select a project default, accept a
baseline, or authorize routine cloud execution.

This control uses the existing Codex CLI ChatGPT Pro login. OpenAI API-key authentication is
prohibited. The host runner rejects Codex auth containing an API key, keeps the short-lived ChatGPT
OAuth access token in host-process memory, and exposes only a random non-secret canary JWT to Pi.
A loopback relay verifies that canary, accepts only the Codex Responses path, enforces per-task
request-count, cumulative request-byte, and timeout bounds, and substitutes the real subscription
headers only for the fixed upstream request. Pi's read-only generated configuration, command
evidence, disposable repository, result JSON, and tracked report never contain the OAuth token or
account identifier. Pi receives an otherwise empty ephemeral writable agent-state directory
because version 0.84.1 synchronizes even the canary credential into a runtime store; that directory
is not host-backed and disappears after the sandbox exits. The auth file and host home are not
mounted in Bubblewrap, and `--clearenv` prevents an ambient `OPENAI_API_KEY` or other host
credential from reaching Pi.

The preflight validates the private ChatGPT login and resolves the exact model from the supplied Pi
installation without a model request or startup networking:

```bash
python3 tools/model_stress_runner.py check \
  --execution-target codex-subscription-sol \
  --codex-auth-path "$HOME/.codex/auth.json" \
  --pi /absolute/path/to/pi
```

The live path must then begin with `--trials 1`. Only after the smoke result is structurally valid
may an operator select three trials for each tracked task. The explicit live arguments are
`--execution-target codex-subscription-sol`, `--provider openai-codex`, `--model gpt-5.6-sol`, and
`--base-url https://chatgpt.com/backend-api`; the runner rejects alternatives. The literal Pi flag
name `--api-key` carries the random canary JWT required by Pi's local account parser, not an API key
or reusable OAuth credential.

The public synthetic task, generated source files, and lane-specific harness context leave the
host for ChatGPT processing. Do not use this route for private application content without a new
privacy and authorization decision. Subscription usage has no API-price claim; retain only
provider-reported token counts and the relay's sanitized request metrics.

## Held-out corpus

Task schema 1.1 requires one of three machine-readable classes, and the repository validator
requires exactly one tracked task in each class:

| Class | Task | Boundary |
|---|---|---|
| `implementation` | `identifier-canonicalization-v1` | Implement a Unicode-aware normalization contract in one file. |
| `defect-repair` | `retry-after-repair-v1` | Repair a broken standard-library Retry-After parser while preserving strict error behavior. |
| `cross-file-integration` | `release-policy-integration-v1` | Reconcile strict version parsing and release decisions across two writable modules. |

The function-level scalar oracle is intentionally small enough for frequent local execution. It
does not represent repository-scale architecture, UI, dependency, performance, or deployment work.
Corpus changes require deterministic seed-failure and reference-pass checks before a live run. A
trial counts as passed only when the oracle and scope checks pass and every declared writable path
changed. For the cross-file task this establishes the structural two-file boundary; it does not by
itself prove that every edit was semantically necessary, so the oracle results and changed-path
evidence must still be reviewed together. Oracle schema 1.1 supports multiple named module/function
targets in one task; the cross-file corpus therefore tests both `release.release_decision` and
`policy.parse_version` directly instead of inferring the helper's correctness from a cosmetic file
change.

Before a live run, inspect the host's existing SparkRun/container state, listener, and `/v1/models`
response through an approved host boundary. A loopback failure observed only inside a restricted
sandbox is indeterminate. Do not start or restart a model workload until this preflight confirms
that no suitable instance is already running. The runner shares only the host network so it can
reach the explicitly constrained `http://127.0.0.1:8000/v1` endpoint; it cannot start, stop, or
inspect a container and performs no GitHub operation.
