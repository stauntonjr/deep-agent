# Issue #21: first paired Qwen canary smoke

- Date: 2026-08-24
- Governing decision: ADR-0008
- Engineering-loop run: `20260824T144218Z-4c62716f`, revision 2
- Evidence class: smoke; one trial per lane
- Accepted baseline: no
- General harness-lift claim: no

## Executive result

The first bounded paired execution completed without changing the template worktree, GitHub, or
the existing model workload. Neither lane passed the executable oracle. The bare lane
timed out after repeatedly calling an unavailable tool; the harness lane terminated quickly without
that unavailable-tool loop but implemented fewer oracle cases correctly. This single observation
supports only a narrow finding: the loaded harness resources coincided with better termination and
tool discipline on this trial, not better task correctness. Subsequent review found that the first
runner did not send the contract prompt and exposed hidden oracle expectations to generated code,
so this run is diagnostic history rather than contract-valid baseline evidence.

## Exact provenance

| Field | Value |
|---|---|
| Model | `Intel/Qwen3-Coder-Next-int4-AutoRound` |
| Provider | `local-vllm` |
| Pi | 0.84.1 |
| Serving runtime | SparkRun job `8337765ded59`; vLLM; container `sparkrun_8337765ded59_solo` |
| Recipe | `@official/qwen3-coder-next-int4-autoround-vllm` |
| Task | `identifier-canonicalization-v1` |
| Task digest | `faa9aedd54a027c6fe9e996af59a2b0d03b088e810d5d081977623f54cc3b6f5` |
| Recorded contract-prompt digest; prompt was not sent | `ce88510a5978640c1f3a69fa9c4edf07253fcf8bc9186dccf8d5b8384b1142b8` |
| Actual runtime-prompt digest | `052e0c9078369e352eae66df845ff28f31eb24c8376a4b441d5ff186508f0552` |
| Tools | `read`, `edit` |
| Trial count | 1 per lane |
| Model timeout | 300 seconds per lane |
| Oracle timeout | 10 seconds |
| Maximum event bytes | 4,194,304 |

The ignored machine result created by the original runner has SHA-256
`f8b4754a90ec846fde2265e318820f185f980ac270689b70eb50b6ad54072c3e`. It is local working
evidence, not a tracked artifact or accepted baseline.

## Host preflight

Verified before invocation through the approved host boundary:

- `sparkrun status` reported only the intended job and one running container;
- Docker reported start time `2026-08-24T02:12:31.934623255Z`, restart count 0, no OOM, and host
  networking;
- `ss` reported vLLM listening on port 8000; and
- `/v1/models` returned the exact configured model.

No start, stop, restart, deployment, publication, credential, or GitHub operation was performed.

## Paired outcomes

| Observation | Bare | Harness-enabled |
|---|---:|---:|
| Runner return | 124, timed out | 0, settled |
| Elapsed model time | 300.006 s | 15.333 s |
| Oracle cases passed | 6 of 7 | 5 of 7 |
| Failed case IDs | `runs` | `runs`, `empty` |
| Non-`.git` worktree observation | only `identifier.py` observed | only `identifier.py` observed |
| `edit` errors | 1 | 1 |
| unavailable `run` errors | 79 | 0 |
| Post-hoc event-length check | within threshold; not an operative bound | within threshold; not an operative bound |

The old runner recorded zero passed trials because neither lane passed its complete oracle. Its
scope boolean is not accepted as full scope evidence: the old snapshot excluded `.git`, so changes
to Git metadata are unknowable after the disposable repositories were deleted. The actual
hard-coded runtime prompt, initial Git repository, public task, oracle, tools,
provider/model, and limits were fixed across lanes. The actual prompt was “Complete the engineering
task in TASK.md. Read TASK.md and identifier.py, edit only identifier.py, and finish after making
the requested change.” The bare lane disabled repository context, skills, and extensions; the
harness lane enabled the same repository's `AGENTS.md`, canonical engineering-loop skill, and Pi
context extension. The tracked task contract's more precise `prompt` field was hashed into the old
result but was not sent to Pi.

## Safety and privacy evidence

- Pi ran inside Bubblewrap with a synthetic home and model configuration, an allowlisted
  environment, and the self-contained Pi installation mounted read-only. The disposable repository
  and synthetic configuration home were writable; no host home was mounted.
- Pi shared host networking so the configured provider could reach the constrained loopback
  endpoint. Offline mode, the synthetic provider configuration, and the absence of credentials or
  shell tools limited the exercised path; the network namespace itself was not an egress filter.
  Pi had no GitHub, container, host-home, or credential authority.
- Generated Python ran separately with the disposable repository read-only, the network namespace
  unshared, CPU/address-space/file/task/file-descriptor limits, and a ten-second timeout. The old
  oracle nevertheless supplied all case arguments and hidden expected values in `HARNESS_ORACLE`
  to that same Python process. There is no evidence this trial exploited the exposure, but the
  secrecy boundary was invalid.
- Direct hashing observed non-`.git` worktree paths. The old snapshot excluded `.git`, so this
  historical run does not verify full changed-path scope.
- Raw assistant text, tool arguments/results, provider bodies, transcripts, and reasoning were not
  written to the result and were deleted with the disposable repositories.

## Corrections and limitations

The first command stopped before model invocation because the sanitized Pi-version subprocess did
not include Pi's adjacent Node binary on `PATH`. `LOCAL-RUNNER-004` records the failure and verified
repair. The successful paired invocation then exposed a second reporting ambiguity: Pi token usage
uses `input`, `output`, `cacheRead`, and `cacheWrite`, while the initial reducer looked for different
keys and emitted unqualified zeros. Because raw events were deliberately destroyed, the token
counts are now classified as unavailable and cannot be reconstructed. The reducer and result
schema now require either provider-reported numeric counts or explicit null values with
`measurement_origin: unavailable`.

Independent review then found that the recorded prompt digest described an unused contract field,
the oracle exposed its hidden answers, the event-length check happened only after unbounded output
buffering and therefore was not an operative resource bound, arbitrary
tool names could enter sanitized output, and some post-invocation failures could claim that no model
ran. The repaired runner now sends the exact contract prompt, isolates each oracle case without
expectations, bounds model output during execution, maps tool names to stable categories, validates
result relationships, mounts Pi configuration read-only, and preserves truthful invocation state.
No second model run was made during that repair.

One task and one trial cannot estimate variance, general correctness, or causal harness lift. The
bare lane's unavailable-call loop and the harness lane's quicker termination warrant additional
task classes and repeated trials, but neither outcome authorizes a release or an accepted baseline.

## Disposition

Keep the result as diagnostic negative smoke history, not accepted or contract-valid baseline
evidence. Before any acceptance-candidate run:

1. independently review the runner and this evidence boundary;
2. add at least two distinct held-out task classes so a single normalization pattern cannot dominate;
3. run at least three trials per lane; and
4. require a separate human decision to accept or reject the resulting baseline.
