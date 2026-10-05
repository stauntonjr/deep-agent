# ADR-0012: Bind scope, solution selection, and proportionality before repair

- Status: accepted
- Date: 2026-08-25
- Decider: human owner Jack Rory Staunton
- Governing issue: #49

## Context

Issue #16 began with a bounded, read-only GitHub security and settings objective. Independent review
found legitimate defects, but successive repair cycles expanded from GitHub API and workflow
boundaries into general YAML semantics and hostile concurrent filesystem mutation. The Issue form
had one combined scope-and-exclusions textarea, and the loop treated a verifier's minimum repair as
the next implementation plan without a separate product-alignment decision.

The loop already binds candidate identity, acceptance evidence, write scope, review batches,
revisions, attempts, and verifier decisions. GitHub Issue forms already support required textareas.
Research in `docs/research/issue-49-scope-and-proportionality-controls.md` found no justification for
a new runtime dependency or second orchestration engine.

## Decision

Every new loop run binds non-empty included scope, explicit exclusions, assurance boundary,
complexity/budget constraints, and scope-revision triggers. Feature and Defect forms collect those
fields separately; Decision forms separately identify what is and is not being decided.

Before planning, the orchestrator records one current-revision `build`, `adopt`, `adapt`, or
`defer` solution assessment. Material research records source provenance and is mandatory before
bespoke implementation of standardized, ecosystem-provided, or security-sensitive capability.
Dependency-free implementation is a decision, not a default assumption. Each trigger has one
active assessment per revision and candidate. Blocked research cannot advance to planning; a later
evidence-backed assessment can explicitly supersede blocked evidence or a candidate-stale completed
assessment while retaining the original record. A duplicate for the same current candidate fails.

An adversarial reviewer owns technical evidence, not repair authority. After a finding batch and
matching verdict, the orchestrator dispositions every finding as `repair-in-scope`, `simplify`,
`narrow-claim`, `defer`, `accept-risk`, `revise-contract`, or `emergency-stop`. Before mutation, one
proportionality record captures objective alignment, scope delta, complexity delta, budget status,
alternatives, solution disposition, and a recommendation of `proceed`, `simplify`, `defer`,
`revise-contract`, or `escalate-to-owner`.

A parser, sandbox, protocol, cryptography, concurrency-control, filesystem-security, material
dependency, write-scope-growth, threat-model, or budget trigger requires a scope reviewer distinct
from both implementer and technical verifier. The same independence is required before a third
implementation attempt. Contract-expanding work cannot proceed through an ordinary new attempt.
Human provenance remains required for accepted risk, policy changes, and external authority.
Every trigger also requires a current completed solution assessment. In-scope repair,
simplification, and narrowed claims enter a new attempt; `revise-contract` enters a new revision;
and deferral, human-accepted risk, or emergency stop may close through an explicit candidate-bound
no-code resolution followed, when completion is still sought, by a fresh clean technical review.
Mixed emergency batches retain every disposition and record one enforceable next transition:
`contract-revision` if any finding requires contract revision, otherwise `new-attempt`.

## Consequences

### Positive

- Issues state non-goals and assurance limits before implementation.
- Existing solutions are considered before bespoke complexity accumulates.
- Verifiers can report adjacent defects without silently changing product scope.
- Repair economics and alternatives become durable evidence rather than conversation recollection.
- Expensive secondary scope review is conditional instead of universal.

### Negative

- Starting a loop requires more explicit fields.
- Finding batches require a disposition step before repair.
- Schema 1.4 adds migration work for in-flight 1.2 and 1.3 records; migrated records cannot report
  completion until a real scope contract and current solution assessment are supplied.
- Tooling validates record consistency but cannot prove that an agent identified every material
  complexity trigger honestly.

### Risks and mitigations

- Agents may mechanically enter vague exclusions: Issue-form tests require separate fields, while
  independent review checks whether they are specific enough for the candidate.
- Metrics may be gamed: time, tokens, path counts, and code size are decision signals only and are
  never acceptance evidence by themselves.
- The new checkpoint may become bureaucracy: ordinary in-contract repairs use one lightweight
  orchestrator record; a second independent reviewer is required only at declared triggers.
- Research may introduce supply-chain risk: discovery remains read-only and no candidate may be
  installed or executed without its own authority and review.

## Alternatives considered

| Alternative | Evidence | Reason not selected |
|---|---|---|
| Keep the current combined Issue scope field | Issue #16 history | It did not enumerate the assurance and complexity boundaries needed to stop expansion. |
| Let the adversarial verifier choose the repair | Existing review contract | It conflates technical defect discovery with product, risk, dependency, and budget authority. |
| Require another reviewer after every review | Independent review experience | It would add latency even when the candidate is clean or the repair is plainly in contract. |
| Install a general agent methodology | Awesome Copilot and Superpowers research | Useful patterns exist, but neither replaces the repository's exact evidence and authority contracts. |
| Use prose only | Existing instructions | Prose did not prevent repair transition after scope-expanding findings. |

## Verification and revisit trigger

Tests must reject missing Issue exclusions, missing initial solution assessment, undispositioned
finding batches, absent proportionality decisions, non-independent triggered review, and ordinary
attempts that expand the contract. They must preserve clean review and bounded repair paths,
candidate identity, retry ceilings, telemetry, plugin provenance, and exactly one final full gate.

Revisit when authenticated risk acceptance, organization-wide enforcement, reliable automatic
complexity classification, or a maintained external platform can replace rather than duplicate the
local transition contract.
