# Model-robustness evaluation patterns

## Decision and scope

Determine how this harness should periodically test whether repository instructions, skills, loop
contracts, and tool safeguards make a local Qwen coding model more effective at engineering tasks.
The decision covers evaluation shape and evidence, not model deployment or organization analytics.

## Search method

- Inspected: 2026-08-24.
- Queries: reproducible coding-agent evaluation, executable patch oracles, Pi JSON/tool execution,
  Agent Skills evaluation, and local Qwen serving patterns.
- Selection: canonical repositories, official documentation, and original project publications;
  community catalogs were used only for discovery.
- Stop condition: enough evidence to choose a small paired local canary without adding a benchmark
  dependency or external service.

## Constraints and comparison dimensions

The design must be provider-neutral, dependency-free in its default validation path, local-first,
safe for public repositories, explicit about model/runtime versions, bounded in GPU time, and
unable to override deterministic tests or human authority. Options were compared on reproducibility,
oracle quality, harness-effect isolation, cost, privacy, portability, and integration effort.

## Candidate evidence

| Source | Revision/version inspected | License/provenance | Relevant pattern |
|---|---|---|---|
| [SWE-bench evaluation guide](https://github.com/SWE-bench/SWE-bench/blob/main/docs/guides/evaluation.md) | Current page, 2026-08-24 | MIT, canonical repository | Apply a patch in an isolated environment and score it with executable tests |
| [SWE-bench Verified introduction](https://openai.com/index/introducing-swe-bench-verified/) and [2026 reassessment](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/) | Publications, 2024-08-13 and 2026-02-23 | OpenAI publications and linked dataset | Historical human-validation pattern; no longer a current capability benchmark because of contamination and flawed tests |
| [SWE-Lancer](https://openai.com/index/swe-lancer/) | Updated dataset noted 2025-07-28 | OpenAI publication and open evaluation split | Realistic tasks, independently checked end-to-end tests, and removal of network variability |
| [Pi settings and resources](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/settings.md) | Current page inspected 2026-08-24 | Canonical Earendil Works Pi repository, MIT | Project resources and model selection are separable runtime inputs |
| [Agent Skills best practices](https://github.com/agentskills/agentskills/blob/main/docs/skill-creation/best-practices.mdx) | Current page, 2026-08-24 | Apache-2.0 code / CC-BY-4.0 docs | Refine from real executions, inspect traces, and test whether a skill adds value |
| Local Pi/SparkRun dogfood | Pi 0.84.1; Qwen3-Coder-Next INT4 | Repository reports and host configuration | Tool-name, research, and synthesis failures provide concrete canary dimensions |

## Findings

- Executable repository oracles are stronger than model-graded prose for engineering outcomes.
- A harness-only success cannot establish harness value. Paired lanes with the same model, task,
  tools, budget, and oracle provide the smallest credible ablation.
- Real model behavior varies. Accepted evidence needs repeated trials; a one-shot run remains smoke.
- Traces are useful for tool errors and wasted steps, but public evidence should retain sanitized
  metrics and identities rather than raw private prompts or hidden reasoning.
- Large public benchmarks are useful periodic external references, not suitable default gates for
  every template loop.
- SWE-bench Verified is retained here only for its historical human-review methodology. OpenAI's
  2026 audit says contamination and flawed tests have eroded its capability signal and recommends
  SWE-bench Pro instead. A future external comparison should therefore prefer current SWE-bench Pro
  guidance or privately authored held-out tasks, while rechecking benchmark fitness at run time.

## Options

- Build: a small local paired-task runner and due-policy contract. Best fit for harness-specific
  lift, privacy, and deterministic integration.
- Adopt: run a current external benchmark such as SWE-bench Pro directly. Credible external
  comparison, but high setup/runtime cost and weak isolation of this repository's guidance.
- Adapt: borrow isolated execution, exact provenance, repeated trials, and executable-oracle
  patterns while maintaining a small project-owned corpus. Recommended.
- Defer: continue one-off dogfood only. Lowest effort but does not make regressions or cadence
  visible.

## Recommendation

Adapt the benchmark patterns into a dependency-free contract plus a disposable paired Pi runner.
Use runtime-selected local Qwen as the recurring canary, require three trials per lane for release
evidence, and keep deterministic tests authoritative. Confidence is high for the evaluation shape
and moderate for thresholds until several paired runs establish a baseline.

## Unknowns and spike plan

A restricted-sandbox probe could not reach local port 8000 during this design loop. That result was
indeterminate: a later host-boundary check proved the existing official SparkRun Qwen container had
started before the probe and `/v1/models` was healthy. No model request or paired evaluation was run,
so no new model result is claimed. The next slice should implement one small held-out Python repair
task, run bare and harness lanes through Pi against the official SparkRun Qwen3-Coder-Next INT4
recipe, capture only sanitized metrics, and use those results to set provisional thresholds. Model,
Pi, SparkRun, and serving-recipe behavior may drift and must be re-read at execution time.
