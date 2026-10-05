# ADR-0010: Batch independent review and tier verification gates

- Status: accepted
- Date: 2026-08-24
- Deciders: Jack Rory Staunton
- Governing issue: #46

## Context

The Issue #21 GPT-5.6 Sol control loop took about 84 minutes. The live model work consumed roughly
ten minutes; most of the remaining time was implementation, repeated complete gates, and six serial
review/repair cycles. The verifier returned a valid finding, the orchestrator invalidated the
candidate immediately, and review restarted after each repair. Several repairs did not change the
accepted objective, criteria, or write scope, but were recorded as contract revisions. This was
safe but unnecessarily repeated candidate pinning, broad checks, and review setup.

Observed evidence supports preserving independent review, candidate identity, scope enforcement,
and a complete final gate. It does not support treating every ordinary finding as an emergency or
rerunning expensive immutable model evidence after unrelated documentation/provenance repairs.

## Decision

Independent review is a bounded collection phase over one stable candidate. Ordinary findings are
deduplicated into one batch containing severity, criterion, reproduction, and minimum repair.
Implementation resumes only after the batch closes and one repair decision is recorded. Immediate
interruption is reserved for critical active secret exposure, destructive effect, or uncontrolled
external effect.

Verification uses five recorded tiers: `static`, `targeted`, `affected`, `external`, and `full`.
Implementation uses cheap and targeted checks; a closed repair batch receives affected-contract
checks; reported completion requires exactly one executed passing full gate on the final current
attempt. Expensive retained evidence may be reused only with source, immutable SHA-256 artifact
digest, and applicability rationale, and never as the final full gate.

Objective, acceptance-criterion, or declared-scope changes increment the run revision.
Implementation repairs under the unchanged contract increment the attempt. Review-cycle and check
durations are recorded and surfaced in the final report.

This decision does not weaken verifier independence, criterion coverage, candidate identity,
write-scope enforcement, retry ceilings, or human release authority.

## Consequences

### Positive

- One review setup and one repair batch replace serial one-finding review restarts.
- Cheap feedback runs during editing, while the complete gate remains current and authoritative.
- Expensive model/service evidence can be reused transparently when its boundary is demonstrably
  unchanged.
- Reports expose where verification time and repeated work were spent.

### Negative

- A reviewer may hold several findings before the implementer can begin repairs.
- Review-cycle and evidence-reuse metadata add schema and CLI complexity.
- Applicability of retained evidence still requires engineering judgment; a digest alone does not
  prove relevance.

### Risks and mitigations

- Delayed response to a dangerous finding: the explicit critical emergency-stop categories permit
  immediate containment.
- Candidate drift during review: non-emergency close and verdict recording compare the pinned
  candidate identity and fail closed.
- Over-reuse of stale evidence: source, digest, and rationale are mandatory; instructions require a
  rerun whenever an applicable input or behavior changed.
- A narrow check mistaken for completion: reported completion requires exactly one current,
  executed, passing full gate.

## Alternatives considered

| Alternative | Evidence | Reason not selected |
|---|---|---|
| Keep one-finding-at-a-time review | Issue #21 remained safe and ultimately reached approval | It produced six serial review repairs and repeated broad work for one bounded candidate |
| Remove independent adversarial review | Would reduce elapsed time | It would discard the mechanism that found real safety, provenance, and contract defects |
| Run the full suite after every edit | Produces frequent broad feedback | It repeats the most expensive deterministic boundary while the candidate is still moving |
| Trust retained external results without provenance | Avoids expensive reruns | It can silently apply evidence to changed prompts, tools, resources, or behavior |

## Verification and revisit trigger

Unit tests must cover batch closure, duplicate findings, stable-candidate enforcement, emergency
stop, tier/evidence validation, and the final full-gate requirement. Plugin synchronization,
schema validation, `make smoke`, and an independent verifier must pass.

Revisit if three completed loops show batching increases escaped high-severity defects, if emergency
categories are repeatedly insufficient, or if measured review/gate time does not improve without a
drop in final acceptance quality.
