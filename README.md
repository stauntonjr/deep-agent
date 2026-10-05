# Agentic Project Template

A small, provider-neutral foundation for projects developed substantially by coding agents.
It keeps intent, authority, planning, verification, optional capabilities, and handoff state in
repository artifacts that humans and different agent runtimes can inspect.

This is a working v0.5 template, not a claim of autonomous delivery. Humans retain product intent,
capability activation, risk acceptance, external writes, and release authority.

## Create a greenfield project

Use this repository as the generator and choose a new target directory that does not already
contain the template or another harness:

```bash
python3 tools/project_intake.py \
  --interactive \
  --mode new \
  --target /path/to/new-project \
  --apply
make -C /path/to/new-project smoke
```

Template-mode greenfield generation requires an explicit `--target`. Running `new --apply` in
place is rejected before mutation because it would retain the template-maintenance files and
bypass the lean generation profile. Initialize and publish the generated target as the new
project repository after its smoke check passes.

For a dependency-free local proof:

```bash
python3 tools/project_intake.py \
  --answers harness/fixtures/intake.answers.json \
  --target /tmp/example-agent-project \
  --apply
make -C /tmp/example-agent-project smoke
```

Greenfield generation is controlled by `harness/generation.json`. The `greenfield-core` profile
has a hard ceiling of 90 copied files; intake adds its generated record, producing 91 files in the
current proof. The generated project includes the agent-facing core and excludes the template's
own maintenance tests, plugin distribution, historical reports, model stress, telemetry,
recovery, challenge/evaluation fixtures, and CI workflows.

## Generated core

| Surface | Purpose |
|---|---|
| `AGENTS.md` | Authority, context-readiness, capability, and workflow routing rules |
| `harness/project.yaml` | Project intent, constraints, lifecycle, and quality contract |
| `harness/capabilities.json` | Visible inactive capabilities and duplicate-prevention ownership |
| `harness/roles/` | Provider-neutral planner, implementer, verifier, and release roles |
| `harness/loops/` | Evidence-producing engineering state machine |
| `.agents/skills/` | Seven repository-local workflows |
| `.codex/` and `.pi/` | Thin runtime adapters; neither is installed globally by generation |
| `harness/adapters/` | Provider mappings and limitations |
| `tools/` | Intake, validation, loop, planning, upgrade, and quality entrypoints |
| `.github/planning.json` | Desired GitHub planning topology; no live writes occur automatically |
| `harness.lock` and `harness/ownership.json` | Pinned upgrade provenance and ownership classes |

The source template retains additional maintenance assets so the template itself can be tested and
released. Those assets are not application features and are not copied into a greenfield project.

## Capability policy

All optional capabilities begin as empty skeletons. They stay visible so agents know what can be
activated later and do not reinvent a competing implementation. Before planning work, an agent
must search the catalog and record one disposition:

- `use-active`: use the existing implementation;
- `propose-activation`: adapt the existing skeleton after explicit human approval;
- `not-applicable`: explain why the responsibility is outside the current slice.

The catalog currently preserves selected ideas from S3NTINEL, Kortex, Procurement Intelligence
Lab, and Macro Technical Pulse: AST/LOC and complexity analysis, validation challenges, durable
memory and governed reflection, semantic evidence, a shared composition root for CLI/API/MCP/web,
point-in-time provenance, and role-separated analysis. See
`docs/project/capability-matrix.md` for the source and activation cues.

## Engineering flow

```text
Intake -> Understand -> Plan -> Authorize -> Implement -> Verify
       -> Review -> Proportionality -> Integrate -> Report -> Learn
```

The agent asks only material unresolved questions before planning, records explicit scope and a
complexity budget, and checks for an existing capability before building. Verification is
proportional to the current product slice. A new project with no application code validates the
harness core; once code is added, intake or project configuration must name the real format, lint,
test, integration, and package commands that apply.

Start a bounded loop with:

```bash
python3 tools/loop.py start \
  --issue 123 \
  --objective "Deliver the smallest accepted slice" \
  --criterion "AC1=The accepted behavior is demonstrated" \
  --in-scope "The first vertical slice" \
  --out-of-scope "Deployment and unrelated infrastructure" \
  --assurance-boundary "One local candidate" \
  --budget-constraint "Focused checks; no new framework" \
  --scope-revision-trigger "A new dependency or expanded product boundary" \
  --write-path src/example.py \
  --implementer codex/implementer
```

The loop is a coordination record, not the product. If maintaining the loop takes more effort than
the accepted implementation and evidence, stop and revise the scope or process.

## Existing repositories

Adoption is separate from greenfield generation and remains ownership-driven:

```bash
python3 tools/project_intake.py \
  --answers /path/to/answers.json \
  --target /path/to/existing-application \
  --mode adopt \
  --adoption-check 'make check' \
  --apply
```

The adopter preserves existing files, copies only missing upstream-owned paths, and writes
`docs/project/adoption-gaps.md` for deliberate reconciliation. It never infers or runs an
application command unless `--adoption-check` is supplied. `refresh` and `gap-only` retain the same
ownership and context boundaries.

## Runtime and installation boundary

Repository-local skills and adapters are part of the template. Generating a project does not
install a Codex plugin or make these skills globally active in unrelated threads. The Pi adapter is
retained as an experimental runtime option, but model-effectiveness evaluation is deferred until
the template and its applications are useful.

## First proof

The [SciFact RAG prototype](https://github.com/stauntonjr/scifact-rag) has completed its DGX-local
scope: evaluated retrieval and generation plus accepted CLI, HTTP, MCP, and web interfaces.
Its downstream capability activations do not change this template's inactive defaults.

The [program roadmap](docs/project/roadmap.md) and
[Issue #59](https://github.com/stauntonjr/agentic-project-template/issues/59) now own the transferred
template/Pi effectiveness evaluation. Completion of the application is case-study evidence;
a prospective matched comparison is needed to assess the template's effect.

The template and that application are MIT licensed. Third-party datasets, models, and services keep
their own terms.
