---
name: execute-engineering-loop
description: Run a non-trivial repository change through intake, evidence gathering, planning, authorization, implementation, independent verification, integration, reporting, and learning. Use for features, defects, refactors, migrations, or documentation changes that alter durable project state; do not use for a read-only answer.
---

# Execute engineering loop

Read `harness/loops/engineering-loop.yaml`, the relevant role contracts, and
`references/verification-efficiency.md` before acting.

## Start

1. Read `AGENTS.md`, `harness/project.yaml`, the handoff, governing Issue, and linked ADRs.
2. Inspect Git status and resolve the exact branch/worktree boundary.
3. Assess context readiness: do you have enough intent, evidence, authority, acceptance criteria, and current-state knowledge to excel? Inspect discoverable facts first. Ask focused follow-ups only for material gaps; record safe assumptions.
4. Bind the smallest useful included work, explicit exclusions, assurance boundary, complexity and budget constraints, and conditions requiring scope revision. Do not begin with a combined or implicit scope statement.
5. Record a `build`, `adopt`, `adapt`, or `defer` assessment before planning. Invoke `$research-existing-solutions` when novelty, standards, licensing, current external behavior, security sensitivity, ecosystem-provided capability, or buy-versus-build materially affects the plan. Do not assume dependency-free implementation when the project has not chosen it.
6. Start the evidence boundary:

   ```bash
   python3 tools/loop.py start --issue NUMBER \
     --objective "ACCEPTED OBJECTIVE" \
     --criterion "AC1=MECHANICALLY VERIFIABLE RESULT" \
     --in-scope "SMALLEST ACCEPTED SLICE" \
     --out-of-scope "EXPLICIT EXCLUSION" \
     --assurance-boundary "ACTORS, ENVIRONMENT, AND GUARANTEE" \
     --budget-constraint "TIME, TOKEN, DEPENDENCY, OR COMPLEXITY LIMIT" \
     --scope-revision-trigger "DISCOVERY THAT REQUIRES REPLANNING" \
     --write-path path/to/exact-file \
     --write-prefix path/to/owned-directory \
     --implementer PROVIDER/SESSION-ID
   ```

Do not invent a start commit or dirty baseline after implementation begins. The baseline binds worktree content, staged index identity, and dirty gitlinks. Use stable criterion IDs. Declare exact files with `--write-path` and directory subtrees with `--write-prefix`; never use the repository root as a catch-all.

Before entering `plan`, record the disposition and evidence:

```bash
python3 tools/loop.py record-solution-assessment --run RUN_ID \
  --trigger initial --disposition adapt --research-status completed \
  --source https://example.com/canonical-source \
  --rationale "WHY THIS IS PROPORTIONATE"
```

Use `not-material` only when the repository already supplies an authoritative, stable solution and
the work does not cross a standardized, ecosystem-provided, or security-sensitive boundary.
Keep one active assessment per trigger, revision, and current candidate. A `blocked` research
status stops the transition to planning, but a later evidence-backed record may explicitly
supersede it while preserving both records. Candidate changes likewise permit a refreshed
same-trigger assessment to supersede stale evidence; duplicate same-candidate records fail. Every
proportionality trigger requires its own current, completed assessment before repair.

When upgrading an in-flight schema-1.2 or schema-1.3 run to tooling that writes schema 1.4, preserve its original
baseline with `python3 tools/loop.py migrate-run --run RUN_ID`. Do not restart the run after edits
or rewrite the baseline manually.

## Execute the states

Follow the state order and gates in the loop contract.

- Keep the orchestrator as sole owner of shared Git lifecycle, integration, and GitHub planning state.
- Delegate only independent, bounded lanes. Use one write-capable owner per worktree.
- Give every implementer an issue, branch, worktree, path scope, acceptance evidence, and stop condition.
- Use a verifier who did not author the reviewed work.
- Stop after three consecutive failures at the same boundary and escalate with preserved evidence.
- Obtain required human approval before external side effects.
- Treat a failed network or loopback probe inside a restricted runtime as indeterminate, not as
  proof that a credential, API, container, or host service is unavailable. Before classifying a
  local service outage, use the approved host-permission path to inspect its supervisor, candidate
  container/process, listener, and health or discovery endpoint. If host verification is not
  available, report the boundary as unverified. Inspect before starting or restarting a workload;
  never launch a possible duplicate first, especially for GPU- or port-exclusive services.

Record exact checks as they finish. Use `static` and `targeted` during implementation,
`affected` after a closed repair batch, `external` for model/service evidence, and one `full` gate
on the final current attempt:

```bash
python3 tools/loop.py record-check --run RUN_ID --name NAME \
  --command "EXACT COMMAND" --status passed --evidence "BOUNDARY PROVEN" \
  --criterion AC1 --tier targeted --duration-seconds 1.25
```

When reusing an expensive retained result, also pass `--evidence-origin reused`,
`--reuse-source`, `--artifact-digest sha256:...`, and `--applicability`. Rerun instead if the
candidate changes an applicable input, tool, environment, oracle, or behavior. Reused evidence
cannot be the final full gate.

Before independent approval, record the recommended product release impact. Base it on the public compatibility contract in `harness/project.yaml`, not commit-message syntax:

```bash
python3 tools/loop.py record-release-impact --run RUN_ID \
  --level patch --reason "SEMANTIC COMPATIBILITY RATIONALE" \
  --public-contract-change "OPTIONAL CHANGED CONTRACT"
```

Use `none`, `patch`, `minor`, or `major`. `none` means the project contract does not require a product release for this change. This assessment is a recommendation and never authorizes a version bump or publication.

Record release impact before the final `full` check because that check is bound to the exact
candidate identity, including impact. Any later candidate or impact change makes the full gate
stale and requires a new attempt.

If objective, acceptance, or write scope changes, use `loop.py revise`; if implementation repairs
without changing the contract, use `loop.py new-attempt`. A verifier finding is not itself a
contract revision. Prior checks and approvals do not satisfy the new revision or attempt, and a
contract revision invalidates prior criterion waivers. `new-attempt` persists each failed repair
attempt and blocks after the third without creating attempt four.

Inspect a preserved run without changing Git state:

```bash
python3 tools/loop.py recovery-status --run RUN_ID --integration-ref main
```

After retry exhaustion, do not delete partial work or continue under a fourth attempt. Prepare a
structured handoff containing `schema_version`, `summary`, `failure_boundary`, `preserved_paths`,
and `next_action`. Only a human-reviewed resume starts a new revision:

```bash
python3 tools/loop.py resume --run RUN_ID --handoff /path/to/handoff.json \
  --by human:IDENTITY
```

The `human:` marker is auditable provenance, not authentication. Resume preserves the working tree,
returns to `understand`, and invalidates the old revision's checks, waivers, impact, and verdict.

After verification, the independent reviewer opens a stable-candidate review cycle:

```bash
python3 tools/loop.py start-review --run RUN_ID --reviewer PROVIDER/SEPARATE-SESSION-ID
```

Collect ordinary findings through the whole bounded review. Record each with severity, criterion,
reproduction, and minimum repair; duplicates are rejected. Close once as `batch-ready`, or as
`clean` when there are no findings. Use `emergency-stop` only for a critical active secret
exposure, destructive effect, or uncontrolled external effect. An open review blocks `revise` and
`new-attempt`; a non-emergency close fails if the candidate changed.

```bash
python3 tools/loop.py record-finding --run RUN_ID --review review-001 \
  --severity high --title "BOUNDARY" --criterion AC1 \
  --reproduction "BOUNDED REPRODUCTION" --minimum-repair "SMALLEST REPAIR"
python3 tools/loop.py close-review --run RUN_ID --review review-001 \
  --outcome batch-ready --summary "ONE DEDUPLICATED REPAIR BATCH"
```

The reviewer then records a matching verdict. `approve` requires the latest review to be clean;
`revise` or `reject` requires a batch or emergency stop:

```bash
python3 tools/loop.py record-verdict --run RUN_ID \
  --reviewer PROVIDER/SEPARATE-SESSION-ID --verdict approve \
  --criterion AC1 --evidence "RAW REVIEW EVIDENCE"
```

The reviewer identity must differ from every recorded implementer. The approval is bound to the current revision, attempt, commit, and baseline-relative working-tree digest.

For a finding batch, do not mutate after the verdict. The orchestrator first dispositions every
finding, then records one proportionality review for the unchanged candidate. A finding may be an
in-scope repair, simplification, narrowed claim, deferral, accepted risk, contract revision, or
emergency stop. `accept-risk` requires `human:IDENTITY` provenance.

```bash
python3 tools/loop.py record-finding-disposition --run RUN_ID \
  --review review-001 --finding review-001-finding-001 \
  --disposition simplify --by orchestrator/SESSION \
  --rationale "WHY THIS DISPOSITION MATCHES THE ACCEPTED SCOPE"
python3 tools/loop.py record-proportionality-review --run RUN_ID \
  --review review-001 --reviewed-by scope-reviewer/SESSION \
  --objective-alignment "TRACE TO THE GOVERNING OBJECTIVE" \
  --scope-change within-contract --complexity-change reduced \
  --budget-status at-risk --trigger new-parser \
  --alternative "ADOPT A MAINTAINED PARSER" --alternative "NARROW THE CLAIM" \
  --recommendation simplify --solution-disposition adapt \
  --rationale "REUSE THE EXISTING NARROW CONTRACT"
```

The scope reviewer must be independent of both implementer and technical verifier when any parser,
sandbox, protocol, cryptography, concurrency, filesystem-security, dependency, write-scope,
threat-model, or budget trigger is present, or when the candidate is on its second failed repair.
Contract expansion cannot proceed through `new-attempt`; revise the contract, defer the work, or
escalate to the owner.

The transition table is explicit: `repair-in-scope`, `simplify`, and `narrow-claim` enter a new
attempt; `revise-contract` enters a new revision; and candidate-bound `defer`, human `accept-risk`,
or `emergency-stop` batches use `resolve-finding-batch` without pretending code changed. Mixed
emergency batches preserve every disposition and bind `contract-revision` when any finding requires
it, otherwise `new-attempt`; the other transition must fail:

```bash
python3 tools/loop.py resolve-finding-batch --run RUN_ID \
  --review review-001 --by orchestrator/SESSION \
  --rationale "WHY NO CANDIDATE MUTATION IS AUTHORIZED OR REQUIRED"
```

Only an explicit human decision may waive a criterion. Record its provenance and rationale with `loop.py waive-criterion --criterion AC1 --by human:IDENTITY --reason "..."`; the label is auditable evidence, not authentication.

Use `references/handoff-contract.md` for every agent handoff.

## Finish

1. Reconcile implementation, tests, docs, ADRs, handoff, Issue, and Project state.
2. Run exactly one complete final gate for the current attempt (normally `make smoke`), then
   `git diff --check` and `git status --short`. Record the complete gate with `--tier full`.
3. Invoke `$loop-report` or run `python3 tools/loop.py finish --run RUN_ID`. A `reported` finish refuses missing criterion evidence, missing or stale release impact, stale or non-independent approval, and writes outside the declared scope. Use `--state blocked` or `--state abandoned` to preserve an incomplete run truthfully.
4. In Learn, inspect every failed command, rejected approach, retry, and human correction. For a
   repeatable failure, add a sanitized entry to `docs/project/correction-log.md` containing the
   failed path, short error signature, mutation status, corrected path, verification, and durable
   prevention surface. Preserve the original failure even after correction. Never retain secrets,
   raw transcripts, private prompts, or hidden reasoning.
5. Convert deterministic escaped defects into challenge candidates when possible. Use a skill,
   test, or tool guard for command-routing mistakes that cannot be replayed safely without live
   side effects. Do not apply policy changes without human review.

A loop is not complete because code exists. It is complete only when the accepted boundary is verified, independently reviewed where required, reconciled, and reported.
