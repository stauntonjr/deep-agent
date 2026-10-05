# Project charter

Status: draft

## Purpose

TBD. Describe the system, its users, the problem it solves, and why it should exist.

## Outcomes and success measures

- TBD

## Scope

### In

- TBD

### Out

- TBD

## Constraints

- Security and data classification: TBD
- Delivery and deployment: TBD
- Budget and schedule: TBD
- Licensing and provenance: TBD

## Authority

Humans own product intent, risk acceptance, architecture approval, external side effects, and release authorization. The current autonomy contract is recorded in `harness/project.yaml`.

## Engineering and release contract

- Harness version: 0.5.0.
- Product versioning, current version, public compatibility contract, and canonical source: TBD during intake.
- Primary local/CI check: `make smoke` for the template; derived-project commands are profile-selected.
- Dependency lock: required when dependencies exist.
- Coverage: ratchet from an observed baseline or record an explicit reviewed exception.
- GitHub security expectations: dependency updates and review, CodeQL, secret scanning, push protection, least privilege, and full-SHA Action references.

Generated from: `harness/project.yaml` and the accepted intake record.
