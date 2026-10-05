# MVP reset

Date: 2026-08-25

Owner: Jack Rory Staunton

Governing Issue #51: [Reset to one time-boxed greenfield application proof](https://github.com/stauntonjr/agentic-project-template/issues/51)

## Decision

The harness foundation is sufficient. Stop expanding it until one small, ordinary greenfield
application demonstrates that the template accelerates delivery. “Complete agentic engineering
operating system” is not the current objective.

## Original-plan audit

| Original core | Status | Disposition |
|---|---|---|
| Repository contract and source precedence | Implemented | Keep |
| Project intake questionnaire | Implemented and dogfooded | Keep |
| One engineering loop | Implemented; more elaborate than necessary | Keep, freeze |
| Deterministic loop report | Implemented | Keep |
| GitHub desired-state audit and bounded reconciliation | Implemented | Keep |
| Python/data and agent-system profiles | Implemented | Keep |
| Tiered CI and historical challenges | Implemented | Keep |
| Harness self-tests | Implemented | Keep |
| Ordinary greenfield application proof | Missing | Do next |

## Removed from the MVP

The following remain preserved but are not prerequisites and receive no further work until the
greenfield proof is accepted:

- GitHub security/settings reconciliation (#16).
- Additional provider adapters (#19).
- Pi subagent/worktree orchestration (#20).
- Live-model scoring and organization analytics (#21).
- Semantic merge assistance (#5).
- Further Agentic Repo Auditor or Agentic Application Assessor expansion.

No current capability is deleted in this reset. Removal would create compatibility work without
helping the proof. “Remove” therefore means remove from the MVP and active roadmap; code deletion
requires separate evidence after the probe.

## Greenfield success definition

Create `stauntonjr/agentic-application-probe` from the current template and deliver one normal,
standard-library Python/data capability: read one local UTF-8 CSV file and emit deterministic JSON
with row count, column names, and missing-value counts.

The proof succeeds only if:

- application work finishes in one short session with one implementer and no subagents;
- there are at most five application-specific source, test, and configuration files;
- no template or harness feature is added to make the application pass;
- one focused test command and one final repository check pass;
- the report records elapsed time, human corrections, escaped defects, and harness friction;
- a failure stops the experiment instead of widening scope.

## After the proof

The owner chooses one of three outcomes:

1. Keep the template and resume one deferred item.
2. Simplify or remove specific harness machinery that obstructed the probe.
3. Stop the project if the template does not materially improve delivery.
