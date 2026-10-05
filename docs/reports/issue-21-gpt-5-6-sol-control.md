# Issue #21: GPT-5.6 Sol subscription control

- Date: 2026-08-24
- Governing decisions: ADR-0008 and ADR-0009
- Engineering-loop run: `20260824T195906Z-fc9ec02f`, revision 9
- Evidence class: supplemental control; human acceptance only
- Accepted baseline: no
- General harness-lift claim: no

## Purpose and success definition

This control asks whether exact `openai-codex/gpt-5.6-sol`, invoked through Pi with the existing
ChatGPT Pro/Codex subscription, can execute the same frozen task definitions for the implementation,
defect-repair, and cross-file-integration challenges previously run against local Qwen. Success is
defined before looking at outcomes:

- the exact same task bytes, contract prompts, `read`/`edit` tools, task-level time/event/scope
  limits, writable paths, and hidden oracles are used, while one Sol resource bundle is frozen
  across its own lanes and trials;
- each scored task runs three bare and three harness-enabled trials;
- a trial passes only when Pi exits zero, settles, stays within event and changed-path bounds,
  changes every required writable file, and passes every hidden oracle case;
- custom and Draft 2020-12 result validation agree on the retained artifact;
- provider, model, Pi version, medium reasoning, runtime, resource digest, request budgets, observed
  requests, timings, tool-error categories, and provider-reported token counts are preserved; and
- neither result can accept itself or support a causal/general harness-lift claim.

Security success additionally requires no OpenAI API key, no OAuth value or account identifier in
Pi arguments/configuration/sandbox/evidence, no host auth-store mount, fixed loopback/upstream
routing, and fail-closed request-count, cumulative request-byte, and timeout bounds.

## Preflight and smoke

The no-model preflight validated the existing Codex ChatGPT login and resolved exact
`openai-codex/gpt-5.6-sol` through installed Pi 0.84.1 with startup networking disabled and a
minimal environment that omitted `OPENAI_API_KEY` and Codex home state.

The first attempted smoke is invalid startup evidence, not a GPT-5.6 Sol result. Pi tried to create
`models-store.json` inside a wholly read-only generated agent directory. Both lanes exited before
events or edits; the relay recorded zero requests and zero bytes. Its ignored sanitized artifact is
SHA-256 `28a14958ef917fb0333b3a69acbda2f900a8a0bd2e47241a70efdb6113f381c6`.
`LOCAL-RUNNER-008` records the correction.

After mounting `models.json` and `settings.json` individually read-only over an otherwise empty
ephemeral state directory, the corrected identifier smoke passed both lanes 7/7. Bare settled in
13.417 seconds with 3,281 input and 466 output tokens; harness settled in 19.982 seconds with
19,596 input, 9,216 cache-read, and 731 output tokens. Both changed only `identifier.py`. The relay
recorded 7 requests and 73,501 request bytes. Its schema-1.3 annotated ignored result SHA-256 is
`a9df32a80edceea4ca08fc5035090b2910d7fed0aab5864e3a22792408ad5d1a`; the original pre-annotation
hash was `fd4288611e42439974e23761a834668190eb0647b034b837d2e8ddd99baed2aa`.

## Three-task acceptance-candidate results

GPT-5.6 Sol passed all 18 scored trials: 9 of 9 bare and 9 of 9 harness-enabled. Every trial
returned zero, settled, stayed within its event and changed-path bounds, changed every required
writable file, avoided timeout, and passed every hidden case. Across all trials that is 360 of 360
oracle calls. The observed bare-versus-harness pass difference is zero.

| Task | Class | Oracle cases per trial | Bare | Harness | Difference | Relay requests / bound | Request bytes / bound |
|---|---|---:|---:|---:|---:|---:|---:|
| `identifier-canonicalization-v1` | implementation | 7 | 3/3 | 3/3 | 0 | 22 / 30 | 247,633 / 1,572,864 |
| `retry-after-repair-v1` | defect-repair | 13 | 3/3 | 3/3 | 0 | 27 / 30 | 395,041 / 1,572,864 |
| `release-policy-integration-v1` | cross-file integration | 40 | 3/3 | 3/3 | 0 | 29 / 30 | 373,082 / 1,572,864 |
| **Total** | three classes | — | **9/9** | **9/9** | **0** | **78 / 90** | **1,015,756 / 4,718,592** |

All three results bind Pi 0.84.1, `openai-codex/gpt-5.6-sol`, medium reasoning, ChatGPT Pro via
Codex OAuth, the same tool set and task/prompt digests as the Qwen run, and Sol resource-bundle
digest `1db98b6051cae2261b3ce916aaf2ec04c8eef1ca55c69ed402966c8d09ce0e12`.

The recorded `limits.maximum_output_tokens` value of 4,096 is the runner's generated Pi
configuration, not an enforced Sol provider request bound. Inspection of installed Pi 0.84.1 found
that its OpenAI-compatible completions path transmits the configured token cap for Qwen, while its
Codex Responses path does not read that option or send `max_output_tokens`. Schema 1.3 therefore
records Sol `output_token_limit_enforcement` as `runner-config-only` and classifies a future Qwen
run as `provider-request`. The published Qwen artifacts use schema 1.1 and do not contain this
field; their provider-request classification comes from read-only Pi 0.84.1 source inspection, not
from their JSON. No output-token-limit equivalence is claimed.

### Provider-reported usage

| Task | Bare input | Bare cache read | Bare output | Harness input | Harness cache read | Harness output |
|---|---:|---:|---:|---:|---:|---:|
| Identifier | 10,056 | 0 | 1,553 | 41,451 | 56,320 | 2,396 |
| Retry-After | 15,477 | 2,560 | 6,240 | 63,354 | 86,016 | 5,818 |
| Release policy | 16,213 | 3,072 | 3,542 | 42,480 | 98,304 | 3,918 |
| **Total** | **41,746** | **5,632** | **11,335** | **147,285** | **240,640** | **12,132** |

These are provider-reported tokens, not API-billing records. The ChatGPT subscription path does not
produce or justify an API-price estimate. Harness input and cache-read totals are higher because
that lane intentionally loads repository instructions, the loop skill, handoff material, and the Pi
context extension.

### Per-trial evidence

| Task | Lane | Trial | Oracle | Seconds | Changed paths | Tool errors | Input / cache-read / output |
|---|---|---:|---:|---:|---|---|---:|
| Identifier | bare | 1 | 7/7 | 18.150 | `identifier.py` | none | 3,385 / 0 / 540 |
| Identifier | bare | 2 | 7/7 | 13.716 | `identifier.py` | none | 3,347 / 0 / 533 |
| Identifier | bare | 3 | 7/7 | 12.849 | `identifier.py` | none | 3,324 / 0 / 480 |
| Identifier | harness | 1 | 7/7 | 17.475 | `identifier.py` | none | 19,028 / 10,240 / 694 |
| Identifier | harness | 2 | 7/7 | 19.882 | `identifier.py` | none | 9,821 / 19,456 / 735 |
| Identifier | harness | 3 | 7/7 | 25.896 | `identifier.py` | `read`: 3 | 12,602 / 26,624 / 967 |
| Retry-After | bare | 1 | 13/13 | 36.592 | `retry_after.py` | none | 4,708 / 0 / 1,820 |
| Retry-After | bare | 2 | 13/13 | 53.050 | `retry_after.py` | none | 5,894 / 2,560 / 2,483 |
| Retry-After | bare | 3 | 13/13 | 38.556 | `retry_after.py` | none | 4,875 / 0 / 1,937 |
| Retry-After | harness | 1 | 13/13 | 40.952 | `retry_after.py` | `read`: 3 | 22,228 / 18,944 / 1,737 |
| Retry-After | harness | 2 | 13/13 | 62.436 | `retry_after.py` | `read`: 1 | 25,475 / 31,232 / 2,257 |
| Retry-After | harness | 3 | 13/13 | 45.969 | `retry_after.py` | `read`: 1 | 15,651 / 35,840 / 1,824 |
| Release policy | bare | 1 | 40/40 | 27.195 | `policy.py`, `release.py` | none | 6,217 / 0 / 1,086 |
| Release policy | bare | 2 | 40/40 | 21.989 | `policy.py`, `release.py` | none | 4,205 / 0 / 980 |
| Release policy | bare | 3 | 40/40 | 34.046 | `policy.py`, `release.py` | none | 5,791 / 3,072 / 1,476 |
| Release policy | harness | 1 | 40/40 | 33.765 | `policy.py`, `release.py` | `read`: 1 | 18,944 / 30,720 / 1,226 |
| Release policy | harness | 2 | 40/40 | 34.521 | `policy.py`, `release.py` | none | 10,679 / 30,208 / 1,322 |
| Release policy | harness | 3 | 40/40 | 37.185 | `policy.py`, `release.py` | `read`: 3 | 12,857 / 37,376 / 1,370 |

The harness lane recorded twelve failed `read` tool executions across five trials, then recovered
without an unavailable-tool loop or oracle failure. Bare recorded no tool errors. Because the raw
tool arguments/results are deliberately not retained, this evidence supports only the stable
error-category counts—not a diagnosis of each failed read.

### Comparison with the Qwen candidate

| Model and lane | Implementation | Defect repair | Cross-file | Total |
|---|---:|---:|---:|---:|
| Qwen bare | 0/3 | 0/3 | 0/3 | 0/9 |
| Qwen harness | 1/3 | 0/3 | 0/3 | 1/9 |
| GPT-5.6 Sol bare | 3/3 | 3/3 | 3/3 | 9/9 |
| GPT-5.6 Sol harness | 3/3 | 3/3 | 3/3 | 9/9 |

The Sol result establishes that the bounded Pi runner, tasks, hidden oracles, and tool surface are
solvable by a stronger model. It does not demonstrate Sol-specific harness lift: both Sol lanes
were perfect. Conversely, it does not invalidate the harness; the corpus is ceiling-saturated for
this model at three trials. Qwen's observed +1 harness difference remains too small and task-local
for a general claim.

### Result artifacts

Each ignored result passed both the dependency-free custom validator and the tracked Draft 2020-12
schema:

| Result | SHA-256 |
|---|---|
| `.harness/model-stress/issue-21-gpt-5-6-sol-identifier-smoke-r2.json` | `a9df32a80edceea4ca08fc5035090b2910d7fed0aab5864e3a22792408ad5d1a` |
| `.harness/model-stress/issue-21-gpt-5-6-sol-identifier-3x.json` | `30dabf9c8d1e39329745e612a575c30e0abf16da4b185883fc21b962d02e7fac` |
| `.harness/model-stress/issue-21-gpt-5-6-sol-retry-after-3x.json` | `37756f981ece85630d250d267b798db77919d2f0aa1648bf36eb41043b3e1eac` |
| `.harness/model-stress/issue-21-gpt-5-6-sol-release-policy-3x.json` | `555204ec378094d2dddbdf41c7cf8b4ba8d728b7b42ac1f6d734e4662e0bf824` |

These are post-run provenance corrections: schema changed from 1.2 to 1.3 and the derived
`output_token_limit_enforcement: runner-config-only` field was added; no lane, trial, usage, timing,
tool-error, scope, request, or oracle value changed. The original pre-annotation hashes were
`fd4288611e42439974e23761a834668190eb0647b034b837d2e8ddd99baed2aa`,
`9fe0ae943fd200923820f65fbe7e6f93c6932f07add1283c63a073c3bd98f22b`,
`2b68632ef9ef4d069c34bfea0e45f72ceb0c059f6fd266d117f3664951442413`, and
`fafb4cba2171b0484b207645246acb34e09b4ae8bb3b9eaea502e0c90cce15a6`, respectively.

## Comparison boundary

The Qwen and Sol runs use the same public task bytes, prompt digests, tools, writable paths,
task-level time/event/scope limits, hidden oracles, and paired-lane semantics, but their
harness-resource bundles are not byte-identical and their output-token enforcement differs.
Qwen recorded `b51ea4c7788db7229b7a2ab6e5eb225324d913240a878a81ba9e0e0c628cba9e`;
Sol recorded `1db98b6051cae2261b3ce916aaf2ec04c8eef1ca55c69ed402966c8d09ce0e12`
after tracked harness context, including the handoff, evolved. Each run froze its own bundle across
bare/harness lanes and trials, but this is not a byte-identical replay of the Qwen harness context.

The comparison is also not a blinded model benchmark. The harness, tasks, and oracles were
developed with frontier-agent help, so GPT-5.6 Sol may be more familiar with the style of
requirements. Runtime, provider protocol, quantization, service implementation, and date also
differ. The small corpus measures concrete task outcomes only; it does not estimate general model
quality, statistical significance, causal harness lift, repository-scale performance, or API cost.

## Privacy and authorization

Only synthetic public benchmark prompts, generated source, and applicable public harness context
are sent to ChatGPT. The host's short-lived Codex subscription token stays in relay-process memory.
Pi sees a random per-run canary JWT and a dummy account identity; those values are non-secret and
accepted only by that relay instance. Raw responses, transcripts, reasoning, tool arguments,
generated file bodies, upstream error bodies, OAuth values, and account identifiers are not
retained. The run uses ChatGPT subscription capacity and makes no API-price claim.

## Human disposition

Pending. The runner and independent verifier may recommend a disposition, but only Jack Rory
Staunton can accept either Qwen or Sol evidence as a project baseline or change the recurring model
policy.
