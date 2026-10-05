# Issue #49 research: scope and proportionality controls

- Inspected: 2026-08-25
- Decision: whether to build, adopt, adapt, or defer the scope, existing-solution, and proportionality controls requested after Issue #16 expanded beyond its original product boundary.
- Scope: planning and engineering-loop governance only; no Issue #16 implementation, dependency installation, or external execution.
- Stop condition: enough primary evidence to decide whether native GitHub forms and existing loop primitives can express and enforce the required boundary without a new runtime dependency.

## Source selection and queries

Repository evidence was inspected first: current Issue forms, `AGENTS.md`, the engineering-loop
contract, loop schema/runtime/tests, ADR-0004, and ADR-0010. External discovery then used these
queries: GitHub Issue-form required textareas; agent planning explicit scope/non-goals; research
before implementation; and plan scope review. Only canonical documentation and original
repositories were admitted.

## Constraints and comparison dimensions

The correction must remain provider-neutral, preserve independent technical verification, add no
external execution authority, retain exact candidate and retry evidence, work without a new runtime
dependency, and make contract expansion fail closed. Candidates were compared for fitness,
maturity, maintenance, license, security boundary, portability, integration effort, lock-in, and
evidence quality.

## Candidates

| Candidate | Evidence inspected | License/provenance | Fitness and boundary | Disposition |
|---|---|---|---|---|
| GitHub Issue forms | [Official syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms), inspected 2026-08-25 | GitHub first-party platform contract | Native required textareas can separately collect included scope, exclusions, assurance, budget, and revision triggers. They collect declarations but do not enforce later repair transitions. | Adopt |
| Existing harness loop | `tools/loop.py`, loop schema 1.3, ADR-0004, ADR-0010 at repository base `7b1b8a24` | Project-owned MIT code and accepted decisions | Already provides candidate identity, revisions, attempts, closed review batches, verdicts, transitions, reports, and deterministic tests. Extending these records is lower risk than another orchestration engine. | Adapt |
| GitHub Awesome Copilot feature planner | [`one-shot-feature-issue-planner.agent.md`](https://github.com/github/awesome-copilot/blob/3b5e9191e449bf911b96fe05f0857bf2d0081a0d/agents/one-shot-feature-issue-planner.agent.md) | Canonical `github/awesome-copilot`, commit `3b5e9191`, MIT | Explicitly separates in-scope and out-of-scope work, repository research, assumptions, dependencies, risks, and testable acceptance. Useful design evidence; not an executable dependency for this harness. | Adapt pattern |
| Superpowers writing-plans workflow | [`writing-plans/SKILL.md`](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/writing-plans/SKILL.md) | Canonical `obra/superpowers`, commit `b36e0829`, MIT | Performs a pre-plan scope check, splits independent subsystems, maps exact files, and emphasizes YAGNI and reviewable task size. Its broader methodology is opinionated and unnecessary as a runtime dependency. | Adapt pattern |
| New third-party orchestration dependency | No candidate provides this repository's exact revision, candidate-identity, disposition, and Project authority contracts | Would require separate supply-chain and compatibility review | Adds integration and lock-in without replacing the project-specific transition logic. | Defer |
| Prompt-only policy | Existing instructions already requested bounded work but did not prevent the Issue #16 expansion | Project-owned prose | Useful for judgment but cannot prevent an undispositioned finding batch from starting another repair. | Reject as sole control |

## Findings

GitHub natively supports the required planning fields, so a custom Issue-templating dependency is
unnecessary. Current agent-planning patterns corroborate explicit non-goals and a scope check before
implementation. Neither external pattern supplies the harness's evidence-bound revision and review
semantics. The existing loop is therefore the correct enforcement point.

The primary escaped behavior was not absence of technical review. It was an authority error: a
valid adversarial finding and its suggested repair implicitly enlarged the product contract. The
minimum correction is to separate technical finding collection from repair disposition, record the
build/adopt/adapt/defer choice before planning, and require a proportionality decision before a
finding batch can transition to repair.

The assessment must remain recoverable: blocked or candidate-stale research is durable evidence,
not a permanent dead end, so later evidence explicitly supersedes rather than overwrites it while
same-candidate duplicates remain invalid. Likewise, the repair transition must cover all declared
dispositions. Deferral, human-accepted risk, and emergency stop need a candidate-bound no-code
resolution instead of a fictitious implementation attempt. A mixed emergency batch retains every
ordinary disposition and binds one existing next transition: contract revision takes precedence;
otherwise containment continues in a new attempt.

## Recommendation

**Adapt** the existing loop and **adopt** native required Issue-form fields. Add no runtime
dependency. Require one initial solution assessment and one finding-batch proportionality record.
Use an independent scope reviewer only when a defined complexity, scope, budget, dependency,
threat-model, or second-failed-repair trigger fires; ordinary bounded repair retains the lightweight
orchestrator checkpoint.

Tradeoff: the tooling can enforce that a record exists and reject internally contradictory
transitions, but it cannot prove that an agent truthfully recognized every complexity trigger.
Issue fields, roles, deterministic tests, and independent review provide defense in depth without
pretending that code can infer project intent.

Confidence is high for GitHub form capability and local loop integration, medium for cross-provider
behavioral compliance. Repository popularity and upstream instructions may drift; their pinned
revisions remain discovery evidence rather than installed code.

## Reopen conditions

Reassess this decision if the project needs organization-wide policy enforcement outside the
repository, machine-derived complexity classification, authenticated risk acceptance, or a
third-party orchestration platform whose maintained contract demonstrably replaces rather than
duplicates the local loop primitives.
