# Project handoff

This is the short orientation index for a fresh human or agent. It is not a transcript or a second
roadmap.

## Read first

1. `AGENTS.md`.
2. `harness/project.yaml`.
3. `harness/capabilities.json`.
4. The active Issue and its acceptance criteria.
5. The relevant repository-local skill.

## Current template state

- Harness version: 0.5.0.
- License: MIT.
- Greenfield profile: `greenfield-core` in `harness/generation.json`.
- Current generation proof: 90 copied files plus one generated intake record, 91 total.
- Generated smoke status: passing with dependency-free harness validation and Python compilation.
- Adoption behavior: separate and ownership-driven; existing application files remain authoritative.
- Program planning: [roadmap](roadmap.md); transferred template-effectiveness work is tracked in
  [Issue #59](https://github.com/stauntonjr/agentic-project-template/issues/59).

## Product priority

The SciFact RAG DGX-local prototype is complete, including evaluated retrieval/generation and
accepted CLI, HTTP, MCP, and web interfaces. Its retained acceptance reports provide application
proof, not a causal estimate of the template's benefit. The former SciFact Phase 7 is now owned by
this program's [roadmap](roadmap.md) and [Issue #59](https://github.com/stauntonjr/agentic-project-template/issues/59).
First synthesize the case-study evidence, then design a bounded matched comparison. No model calls
or new evaluation framework are authorized by the handoff.

## Capability boundary

The catalog contains 13 inactive skeletons derived from S3NTINEL, Kortex, Procurement Intelligence
Lab, and Macro Technical Pulse. An inactive capability owns its responsibility but contributes no
implementation, dependency, or CI check. Agents must use the catalog before planning and may not
create a duplicate implementation. Initial activation or supersession requires explicit human
approval.

SciFact's application-specific catalog activates composition, CLI, HTTP, MCP, web presentation,
and product validation. These are downstream activations: this template's 13 skeletons remain
inactive defaults for newly generated projects. The handoff does not activate any skeleton here.

## Runtime boundary

The repository contains both Codex and Pi adapters. They are optional project-local instructions,
not globally active skills. The Pi adapter remains available; smaller-model effectiveness is a
prospective step in Issue #59 after a matched protocol is accepted, not an automatic continuation.

## Next useful work

1. Complete Issue #59's evidence retrospective and comparison design using the program roadmap.
2. Reuse #20 for Pi isolation, #21 for live scoring, and #56 for lifecycle enforcement; do not
   duplicate their responsibilities or treat them as automatic scope for this evaluation.
3. Retain useful application work as the priority; activate capabilities only for demonstrated need.

## Refresh rule

Update this file only when the current product priority, active capability set, verified generation
result, or recommended next step changes materially. Link to durable evidence instead of adding
historical narrative.
