# Project charter

Status: active

## Purpose

Invited evidence assistant with DGX-local inference and A2A specialist delegation.

Primary users:

- owner
- invited demonstration viewers

## Outcomes and success measures

Desired outcomes:

- Evidence-backed procurement delegation
- Scientific claim checking

Success measures:

- Two viewer ownership tests pass
- Actual DGX tool use and local browser acceptance recorded

## Scope

### In

- Scoped browser assistant
- A2A client
- SciFact MCP client
- Local simulator and deployment package

### Out

- Procurement repository changes
- OCI release until final approval
- Arbitrary shell execution
- Automatic human approval

## Constraints

- Security: No secrets in the repository
- Data classification: public synthetic demonstration data
- Deployment: OCI application with DGX inference; local acceptance first
- Budget: One-day showcase; one specialist and one retrieval service
- Licensing: MIT application; upstream dependencies retain their licenses

## Engineering and release contract

- Primary check: make smoke
- Dependency lock: uv.lock
- Coverage policy: Focused ownership, protocol, evidence and cancellation checks; no coverage percentage claim for first slice
- Product versioning: semver at 0.1.0
- Version source: pyproject.toml:project.version
- Public contract: Authenticated HTTP routes, Environment configuration, Task record schema
- Harness version: 0.5.0

## Authority

- Autonomy level: supervised
- Network writes: explicit-human-approval
- Destructive actions: explicit-human-approval
- Release: human-only
- Policy changes: human-review

Generated from `harness/project.yaml` and `harness/intake.json`.
