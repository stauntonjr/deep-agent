---
name: release-readiness
description: Assess an exact revision for release or deployment readiness using build, package, acceptance, security, migration, observability, recovery, documentation, and GitHub evidence. Use before tagging, publishing, deploying, migrating, or promoting; this skill recommends but never authorizes a release.
---

# Release readiness

Read `harness/roles/release-steward.md` and `references/checklist.md`.

## Procedure

1. Resolve the exact commit, branch, version, artifact, target environment, and governing release Issue.
2. Reject an ambiguous or dirty release boundary.
3. Inspect required checks from the selected profile and project contract.
4. Validate the built artifact and real public entrypoint, not only the source checkout.
5. Confirm dependency, secret, static-analysis, provenance, license, and supply-chain evidence appropriate to risk.
6. Inspect migrations, compatibility, observability, rollback, backup, recovery, and operator documentation.
7. Reconcile the harness version separately from the product version. Validate the canonical product-version source, public compatibility contract, loop release-impact assessments, changelog, migrations, Issues, Project state, and release notes.
   Use `python3 tools/product_version.py --tag TAG` when the product has a release tag.
8. Run `python3 tools/model_stress.py status` when the repository contains the model-stress
   contract. If a canary is due, require accepted paired local-model evidence before a minor or
   major harness release; keep the result supplemental and never substitute it for deterministic
   checks or independent review. Before a live run, inspect the existing supervisor/container,
   listener, and model-discovery response through an approved host boundary; never infer that a
   sandbox-local loopback failure means the model is offline, and never start a possible duplicate
   workload first. Validate the held-out task with `python3 tools/model_stress_runner.py check`.
   One paired trial is smoke only; require at least three trials per lane, a current independent
   review, and explicit human acceptance before treating evidence as an accepted baseline. A
   missing local model makes readiness conditional, not falsely green.
9. Return `ready`, `conditional`, or `not-ready` with exact missing evidence, residual risk, and required human authorization.

Do not tag, publish, deploy, migrate, or create a release unless a separate user request explicitly authorizes that external action.
