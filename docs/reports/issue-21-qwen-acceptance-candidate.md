# Issue #21: three-class Qwen acceptance candidate

- Date: 2026-08-24
- Governing decision: ADR-0008
- Engineering-loop run: `20260824T174031Z-6a8a9a57`, revision 6
- Evidence class: acceptance candidate; three trials per lane and task
- Accepted baseline: no
- General harness-lift claim: no

## Executive result

The repaired paired runner completed 18 scored, provider-backed trials across implementation,
defect-repair, and cross-file-integration tasks. Bare passed 0 of 9 trials; harness-enabled passed 1
of 9, an observed difference of +1 confined to the implementation task. This small local corpus
does not establish a general harness lift. It is useful negative evidence: both lanes struggled
with strict type/error contracts, and one bare cross-file trial entered an unavailable-tool loop
and reached the 300-second timeout.

Every scored trial used the same Qwen model, Pi version, task bytes, frozen harness-resource bundle,
tool allowlist, limits, and hidden oracle for its pair. All 18 stayed within their declared changed
paths and event-size bound. Seventeen settled normally; the one timeout is retained as a failed
trial. This report remains supplemental and unaccepted pending a separate human decision.

## Exact runtime provenance

| Field | Value |
|---|---|
| Model | `Intel/Qwen3-Coder-Next-int4-AutoRound` |
| Provider | `local-vllm` |
| Pi | 0.84.1 |
| Serving runtime | SparkRun job `8337765ded59`; vLLM; container `sparkrun_8337765ded59_solo`; image `sparkrun-eugr-vllm-tf5` |
| Recipe | `@official/qwen3-coder-next-int4-autoround-vllm` |
| Endpoint class | local-loopback OpenAI-compatible |
| Tools | `read`, `edit` |
| Trial count | 3 per lane and task; 18 total |
| Model timeout | 300 seconds per trial |
| Oracle timeout | 10 seconds per trial |
| Maximum event bytes | 4,194,304 per trial |
| Maximum output tokens | 4,096 per model response |
| Frozen resource-bundle digest | `b51ea4c7788db7229b7a2ab6e5eb225324d913240a878a81ba9e0e0c628cba9e` |

The host preflight found one existing SparkRun job and did not start, stop, restart, or reconfigure
it. Docker reported the container running since `2026-08-24T02:12:31.934623255Z`, with no restart,
OOM, pause, or dead state. vLLM owned port 8000 and `/v1/models` returned the exact model above.

## Task provenance and paired summary

| Task | Class | Task digest | Prompt digest | Oracle cases | Bare | Harness | Difference |
|---|---|---|---|---:|---:|---:|---:|
| `identifier-canonicalization-v1` | implementation | `66224d4af69cab2b5a936bf393700d1710fb2814a7b15af5688881bd94ae4db9` | `ce88510a5978640c1f3a69fa9c4edf07253fcf8bc9186dccf8d5b8384b1142b8` | 7 | 0/3 | 1/3 | +1 |
| `retry-after-repair-v1` | defect-repair | `90f9ae5fd79a00ae33fc59faa632eae2416d3ed91654f6af851140b00fc9cc9e` | `2b65e7b0e788121c5d4b85e626faeec89df66463a0de4ac601b32fb9cd0070f6` | 13 | 0/3 | 0/3 | 0 |
| `release-policy-integration-v1` | cross-file-integration | `76c9035a93db91b8bbc0e52032b57016496b97568f263f6a60b23bb788bc2a81` | `e2cd1cceec598957c9e74be82a680140907a93584a0fcb17710cb3e2850f174e` | 40 | 0/3 | 0/3 | 0 |
| **Total** | three classes | — | — | — | **0/9** | **1/9** | **+1** |

The cross-file oracle directly exercised both `release.release_decision` and
`policy.parse_version`; a trial could pass only if both declared Python files changed and all 40
calls passed. This is stronger than inferring helper correctness from a cosmetic second-file edit,
but changed-path equality remains structural and does not prove every edit was semantically
necessary.

## All scored trials

| Task | Lane | Trial | Oracle | Pass | Seconds | RC | Settled | Timeout | Changed paths | Tool errors | Input / output tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|
| `identifier-canonicalization-v1` | bare | 1 | 4/7 | no | 8.197 | 0 | yes | no | `identifier.py` | none | 4,465 / 517 |
| `identifier-canonicalization-v1` | bare | 2 | 4/7 | no | 65.526 | 0 | yes | no | `identifier.py` | `edit`: 1 | 65,540 / 4,319 |
| `identifier-canonicalization-v1` | bare | 3 | 5/7 | no | 9.300 | 0 | yes | no | `identifier.py` | none | 6,402 / 572 |
| `identifier-canonicalization-v1` | harness | 1 | 5/7 | no | 9.828 | 0 | yes | no | `identifier.py` | none | 11,719 / 586 |
| `identifier-canonicalization-v1` | harness | 2 | 7/7 | yes | 11.456 | 0 | yes | no | `identifier.py` | none | 12,314 / 706 |
| `identifier-canonicalization-v1` | harness | 3 | 5/7 | no | 8.448 | 0 | yes | no | `identifier.py` | none | 8,500 / 512 |
| `retry-after-repair-v1` | bare | 1 | 10/13 | no | 16.552 | 0 | yes | no | `retry_after.py` | none | 9,521 / 1,071 |
| `retry-after-repair-v1` | bare | 2 | 10/13 | no | 15.642 | 0 | yes | no | `retry_after.py` | none | 7,876 / 1,021 |
| `retry-after-repair-v1` | bare | 3 | 10/13 | no | 48.748 | 0 | yes | no | `retry_after.py` | `edit`: 1; unavailable: 22 | 98,291 / 2,938 |
| `retry-after-repair-v1` | harness | 1 | 10/13 | no | 30.379 | 0 | yes | no | `retry_after.py` | unavailable: 3 | 22,065 / 2,008 |
| `retry-after-repair-v1` | harness | 2 | 10/13 | no | 22.211 | 0 | yes | no | `retry_after.py` | `edit`: 1 | 16,395 / 1,442 |
| `retry-after-repair-v1` | harness | 3 | 10/13 | no | 15.806 | 0 | yes | no | `retry_after.py` | none | 13,102 / 1,002 |
| `release-policy-integration-v1` | bare | 1 | 35/40 | no | 16.192 | 0 | yes | no | `policy.py`, `release.py` | none | 10,032 / 1,034 |
| `release-policy-integration-v1` | bare | 2 | 35/40 | no | 300.006 | 124 | no | yes | `policy.py`, `release.py` | `edit`: 1; `read`: 1; unavailable: 89 | 987,126 / 18,649 |
| `release-policy-integration-v1` | bare | 3 | 29/40 | no | 18.027 | 0 | yes | no | `policy.py`, `release.py` | none | 10,590 / 1,154 |
| `release-policy-integration-v1` | harness | 1 | 35/40 | no | 49.130 | 0 | yes | no | `policy.py`, `release.py` | unavailable: 3 | 41,717 / 3,210 |
| `release-policy-integration-v1` | harness | 2 | 35/40 | no | 36.623 | 0 | yes | no | `policy.py`, `release.py` | unavailable: 3 | 26,950 / 2,404 |
| `release-policy-integration-v1` | harness | 3 | 35/40 | no | 29.765 | 0 | yes | no | `policy.py`, `release.py` | unavailable: 3 | 26,424 / 1,929 |

Provider-reported totals were 1,199,843 input and 31,275 output tokens for bare, versus 179,186
input and 13,799 output tokens for harness-enabled. The bare totals are dominated by the single
unavailable-tool timeout and should not be generalized into a cost ratio.

## Failure patterns

- Implementation: all bare trials missed separator-run handling; the two failing harness trials
  missed separator runs and empty-input behavior. Harness trial 2 passed all seven cases.
- Defect repair: all six trials missed the same three cases—weekday/date consistency,
  non-string `value`, and non-integer-or-boolean `now_epoch` handling.
- Cross-file integration: five settled trials commonly missed the five strict-type cases across
  `release_decision` and `parse_version`. Bare trial 3 also accepted plus signs and leading
  whitespace. Bare trial 2 timed out in an unavailable-tool loop but its generated files still
  passed 35 of 40 calls.

These patterns show that a lower-capability model can make substantial bounded progress under both
conditions, but the current harness did not reliably drive it to exact error-contract correctness.
The one passing harness trial is encouraging only as a concrete observation for this task and seed.

## Safety, privacy, and validation

- Pi ran with only `read` and `edit`; no shell tool, host home, host credential, Docker socket, or
  GitHub authority was mounted. The generated Pi configuration and Pi installation were read-only.
- The literal `--api-key not-needed` was synthetic and non-secret. It prevented Pi 0.84.1 from
  consulting a credential store; no real credential was supplied or persisted.
- Generated code ran one hidden case at a time in a separate networkless, resource-bounded
  Bubblewrap process. Expected values and other cases were not delivered to generated code.
- Direct snapshots included Git metadata, bounded file/path counts and bytes, and required exact
  changed-path equality. All 18 scored trials passed scope and event-limit checks.
- Each ignored JSON result passed both the dependency-free custom validator and the tracked Draft
  2020-12 schema. Raw assistant text, tool arguments/results, provider bodies, transcripts, and
  reasoning were not retained.

## Result artifacts

The local machine results are ignored working evidence, not tracked artifacts or an accepted
baseline:

| Result | SHA-256 |
|---|---|
| `.harness/model-stress/issue-21-identifier-canonicalization-v1-3x.json` | `d4d7d06809d081fc65a69582357b5baf8804a5663550099dfb64def49d1ae064` |
| `.harness/model-stress/issue-21-retry-after-repair-v1-3x.json` | `6eff3de9bd5a97c024a33ba5beafb49f950d565a56522a122780ec459e98b39c` |
| `.harness/model-stress/issue-21-release-policy-integration-v1-3x.json` | `adc76cd75550ca5143a0dd884fdf5bf8efa84f9cb05c1784283da4b16a295f02` |

Before the scored rerun, six identifier lanes exited before contacting the provider because Pi
could not create a credential lock beside its read-only config. Their preserved diagnostic has
SHA-256 `d506e2b98ad8bec15eaf23f0f3e20bfb8f49e325c80c8b6d963c3a2940e90acb` and is explicitly excluded
from every score above. `LOCAL-RUNNER-006` records the reproduction, correction, and prevention.

## Limitations and disposition

This is a three-task function-level corpus on one model, quantization, server, Pi version, prompt
family, and day. It does not measure repository-scale architecture, UI, dependencies, performance,
deployment, long-horizon recovery, or another model family. Trial count is sufficient only for an
acceptance candidate, not a causal or statistically stable estimate. Shared host networking permits
the constrained loopback provider path but is not a general network-egress filter.

Keep the results as reviewed acceptance-candidate evidence with `accepted_baseline: false` and
`general_harness_lift_claim: false`. A human may separately accept this as the first scheduled Qwen
baseline despite its mostly negative scores, reject it and revise the harness/tasks, or request a
larger follow-up. No deterministic engineering gate should be weakened based on these outcomes.
