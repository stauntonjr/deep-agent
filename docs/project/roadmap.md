# Template effectiveness program roadmap

Date: 2026-09-17

Owner: Jack Rory Staunton. Governing work: [Issue #59](https://github.com/stauntonjr/agentic-project-template/issues/59).
Status: planning; no evaluation execution or compute allocation implied.

## Handoff from the completed SciFact prototype

The former Phase 7 of SciFact RAG is program work owned here. The application sequencing guard is
satisfied: SciFact has evaluated retrieval/generation and accepted CLI, HTTP, MCP, and web
interfaces on its DGX-local boundary. Its scientific negative results remain negative results.
No template evaluation is a condition for declaring that prototype complete.

Start from SciFact [main at d399a2d](https://github.com/stauntonjr/scifact-rag/commit/d399a2d),
Issues [#10](https://github.com/stauntonjr/scifact-rag/issues/10),
[#11](https://github.com/stauntonjr/scifact-rag/issues/11),
[#12](https://github.com/stauntonjr/scifact-rag/issues/12), and
[#13](https://github.com/stauntonjr/scifact-rag/issues/13), and their retained reports.
The application activates composition, CLI, HTTP, MCP, web, and product validation; this
template's skeletons remain inactive defaults. Application success alone does not establish that
the harness improved cost, correctness, or agent capability.

## 1. Evidence retrospective

Issue #59 first produces a small evidence table: task/issue, capability used, artifact actually
consulted, failure caught or escaped, recovery, human intervention, and available cost/time evidence.
Missing historical measurements stay unavailable; do not estimate a counterfactual from chat or
compare unmatched model runs as an effectiveness result. Recommend retaining, simplifying, or
deferring artifacts based on observed use. Changes to template policy require separate review.

Exit: a traceable case study and one narrowly stated effectiveness question.

## 2. Matched protocol before model calls

Compare the same tasks using (A) the current template and (B) a minimal repository containing the
same product specification, dependencies, tests, tool access, and safety constraints. Hold runtime,
model revision, starting commit, resource budget, and evaluator fixed. Use fresh isolated sessions,
balanced task order, and multiple task/seed pairs. No arm can inherit another arm's solution.

Measure product correctness first, then scope violations, recovery success, human intervention,
elapsed time, and token/API or local-compute cost. Fix scoring and stop rules prospectively. Use
existing deterministic tooling where it suffices; do not build a general evaluation platform.
Select task count and budget from a measured setup-cost pilot before the comparative run, without
using comparison outcomes to enlarge the study. Report small-study uncertainty.

Exit: owner-accepted protocol with tasks, versions, task-specific oracles, budget, retained
artifacts, and a decision rule. Execution needs an explicit compute allocation.

## 3. Smaller-model Pi comparison, only if useful

Apply the stable protocol with one selected local model in Pi. Within each model, compare template
versus minimal repository using the same runtime; do not attribute a model/runtime change to the
template. A frontier-model reference is descriptive unless the matched study includes it. An
unfavorable or inconclusive result may terminate the lane.

Exit: a bounded adopt/adapt/defer result and a justified next decision, not an automatic model sweep.

## Existing ownership and exclusions

- [#20](https://github.com/stauntonjr/agentic-project-template/issues/20): Pi delegation/worktree isolation.
- [#21](https://github.com/stauntonjr/agentic-project-template/issues/21): live scoring and organization analytics.
- [#56](https://github.com/stauntonjr/agentic-project-template/issues/56): lifecycle enforcement.
- #59: application-level template effectiveness and the SciFact retrospective.

Use dependencies and shared evidence instead of parallel evaluators. Project #13 remains the
program's operational view; Issue #59 is the canonical work item. No new SciFact feature, Lattice
training, public-test access, scheduled calls, global telemetry, or Pi orchestration is authorized
by this roadmap. Lattice model science is distinct from evaluating agents that write its code.
