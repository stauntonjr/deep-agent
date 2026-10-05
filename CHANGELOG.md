# Changelog

All notable changes to the harness are recorded here. The harness version and a derived project's product version are independent release streams.

## [0.5.0] - Unreleased

### Changed

- Replaced broad greenfield copying with a validated `greenfield-core` manifest capped at 90
  copied files. The current generated repository is 91 files including intake, retains capability
  awareness and both Codex/Pi adapters, and excludes source-template maintenance subsystems.
- Reduced generated README and handoff guidance to current project boundaries and made the generic
  no-code quality contract explicit instead of requiring an absent or empty test suite.
- Stopped new-project intake from copying the template-maintenance root `tests/` suite into derived
  applications. The raw template unittest stage now runs only in template mode; generated
  repositories retain the portable executable harness checks and run application tests through
  their selected quality profile.
- Feature-froze the harness around its implemented original core and made one time-boxed ordinary
  greenfield application the sole active proof target. Later security, provider, orchestration,
  analytics, and semantic-merge work is explicitly deferred rather than implied by the MVP.

### Added

- A dependency-free inactive-capability catalog derived from S3NTINEL, Kortex, Procurement
  Intelligence Lab, and Macro Technical Pulse. Agents must check its IDs, aliases, and claimed
  responsibilities before planning; initial activation requires human approval, and inactive
  skeletons add no implementation, runtime dependency, or CI check.
- Required, separate Issue-form fields for included scope, exclusions, assurance boundary,
  complexity and budget constraints, and scope-revision triggers.
- Loop schema 1.4 with revision-bound build/adopt/adapt/defer solution assessments, per-finding
  repair dispositions, and a candidate-bound proportionality gate before repair. Parser, sandbox,
  protocol, cryptography, concurrency, filesystem-security, dependency, write-scope, threat-model,
  budget, and repeated-repair triggers require a reviewer independent of both implementer and
  technical verifier.
- Superseding resolution for blocked or candidate-stale solution research and an explicit no-code
  finding-batch resolution for deferral, human-accepted risk, and emergency stop. Mixed emergency
  batches retain every disposition and bind exactly one deterministic next attempt or contract
  revision.
- A primary-source build-versus-adopt research note and ADR-0012, which adapt native GitHub Issue
  forms and existing loop primitives without adding an orchestration dependency.
- Batched stable-candidate independent review cycles with deduplicated findings, explicit critical
  emergency stops, tiered verification timing, immutable expensive-evidence reuse provenance, and
  exactly one executed final full gate per completed attempt.
- An explicit schema-1.2 or schema-1.3 to schema-1.4 in-flight loop migration that preserves the
  original dirty baseline instead of recreating evidence after implementation.

- Accepted shared-program versus dedicated-application GitHub Project topology, with
  Project #13 as the canonical field/view copy source.
- Live, non-destructive Project title, saved-view, and repository-link drift auditing.
- Idempotent creation of missing basic saved views through GitHub's typed API.
- Fail-closed validation for every supported write-bearing planning value and explicit
  drift for ambiguous duplicate live identities.
- A reproducible live-model Pi tool-call probe covering strict questionnaire sampling, valid reads,
  unavailable-tool ceilings, zero-tool sessions, and least-authority continuations.
- A credential-isolated ChatGPT Pro/Codex subscription control for GPT-5.6 Sol, with strict
  duplicate-key, JWT-claim, and credential-header validation; fixed loopback routing; sanitized
  upstream errors; non-secret canary substitution; and bounded request evidence without OpenAI
  API-key use.
- A layered domain-routing forward scenario and pinned S3NTINEL evaluation that keep repository
  Spark rules local while exercising reusable loop, verifier, release-steward, and Project
  ownership boundaries.
- Six sanitized disposable recovery fixtures covering dirty worktrees, partial loops, stale
  branches, agent crashes, retry exhaustion, and reviewed resumable handoffs.
- Candidate-versus-approved challenge provenance with explicit human-review promotion and two
  minimized dogfood-derived executable candidates.
- A read-only Kortex provenance and governed-learning evaluation that separates evidence tiers,
  keeps learned policy changes proposed pending human review, uses sanitized durable handoffs, and
  replays interrupted-session recovery without application or memory-store mutation.
- Opt-in, content-free per-loop outcome telemetry with explicit measurement provenance, strict
  local schemas, stdout-only defaults, retrospective observation timestamps, and a de-identified
  aggregation boundary that preserves unavailable values and unlike units.
- A SemVer-versioned `agentic-engineering-harness` Codex plugin containing the seven reusable
  workflow skills, generated from repository-local canonical sources with per-file provenance,
  collision-safe namespacing, and a repository marketplace entry.
- A sanitized failure-correction log and dry-run-first Projects v2 work-item membership command
  that verifies exact post-write membership with bounded read-only retries for visibility lag.
- An accepted local Qwen model-diversity canary policy, machine-readable cadence and evidence
  contract, and dependency-free due-status command that never invokes a model by default.
- A fail-closed held-out task contract and paired Qwen runner that freezes one resource bundle and
  clones one byte-verified seed Git repository for every lane and trial, with explicit bare versus
  harness resource loading, `read`/`edit`-only Pi authority,
  sanitized evidence, and a separate networkless resource-bounded executable oracle.
- A schema-1.1 three-class held-out corpus covering bounded implementation, defect repair, and
  cross-file integration, with task-class provenance in every sanitized runner result and
  multi-entrypoint oracle coverage that directly tests both modules in the cross-file task.
- The first one-trial paired Qwen smoke as explicitly negative evidence: neither lane passed the
  oracle; bare timed out in an unavailable-tool loop while the harness lane settled without that
  loop. No accepted baseline or general harness-lift claim is recorded.
- Independent review downgraded that first smoke to diagnostic history because its recorded prompt
  digest described an unsent field and its oracle exposed hidden answers. The runner now sends the
  exact contract prompt, evaluates one answer-free oracle case per process, bounds output while it
  is produced, closes result relationships, sanitizes tool identities, records the frozen resource
  digest, rejects symlinked task/resource roots and ancestors, and reports invocation truthfully;
  the model was not rerun as part of the repair.
- A provider-backed three-class acceptance candidate with three trials per lane and task: bare
  passed 0/9 and harness-enabled passed 1/9, an observed +1 confined to implementation. The result
  stays supplemental, unaccepted, and explicitly makes no general harness-lift claim. A Pi 0.84.1
  read-only-config credential-lock startup failure is preserved as invalidated diagnostic evidence;
  the runner now supplies an explicit non-secret synthetic API-key override.
- An optional exact `openai-codex/gpt-5.6-sol` frontier control using the existing Codex ChatGPT
  Pro subscription without an OpenAI API key. A loopback-only canary-authenticated relay keeps OAuth
  out of Pi's sandbox, fixes the upstream host and path, bounds requests and request bytes, and
  retains only sanitized provider and relay metrics. Result schema 1.3 distinguishes a token cap
  sent in the provider request from Pi Codex's runner-configuration-only value.

### Changed

- Derived intake now clears the template's live Project identity and prepares a dedicated
  one-time copy bootstrap; adopters may explicitly select a shared Project instead.
- The planning contract now requires `topology` and `canonical_source`. Existing derived
  repositories must review and add these keys before upgrading.
- Existing-repository adoption now copies only upstream-owned harness internals and records
  merge-required, workflow, test, license, changelog, and dependency-lock paths
  for explicit reconciliation instead of silently overwriting application policy.
- Engineering-loop retries now persist the third consecutive failure as `blocked` without creating
  attempt four. A retry-exhausted resume preserves partial work and starts a new evidence revision
  only from a structured `human:IDENTITY` handoff.
- Plugin packaging now deterministically qualifies cross-skill references while retaining
  progressively disclosed `SKILL.md` and reference files. Repository policy and application state
  remain outside the user-installed bundle.
- GitHub planning instructions now reject the deprecated classic-Projects shortcut and document
  the supported `gh project` versus typed Projects v2 GraphQL boundary.
- Release readiness now treats due Qwen canary evidence as supplemental and conditional for
  minor/major harness releases without weakening deterministic checks or human authority.
- Model-stress evidence now labels one paired trial as smoke, rejects ambiguous two-trial runs,
  treats three or more trials only as acceptance candidates, and cannot self-approve a baseline.
- Pi model-stress configuration is mounted as individually read-only files over an ephemeral
  writable agent-state directory, allowing Pi 0.84.1 to synchronize only its non-secret runtime
  canary without exposing a host credential store.

### Fixed

- The installable plugin now uses a new patch/cache identity, and its isolated lifecycle probe
  byte-verifies the installed GitHub planning skill and safety reference against the reviewed
  generated distribution.

- Adopted harness validation now imports the Actions supply-chain implementation from the
  harness-owned `harness.runtime` namespace. An incompatible application-owned
  `tools/check_actions_supply_chain.py` remains byte-for-byte intact, is reported as a
  reconciliation collision, and no longer causes the copied validator to crash during import.
- Adopt-mode dry runs and applies now record an `adopt` lifecycle, exact reconciliation disposition
  counts, `context_readiness`, and separate reconciliation and overall activation states. Project
  activation remains `provisional` until both adoption gaps and essential intake context are
  resolved; harness validation and reported loop completion fail closed until then.
- Harness validation can use a trusted application-owned GitHub planning loader when the
  application intentionally retains its own planning implementation.
- Adoption preflights every target path, rejects symlink traversal and non-directory ancestors
  before copying, preserves existing generated artifacts under non-overwriting proposal names,
  and refuses a second proposal collision.
- Greenfield template copies apply the same lexical target-root preflight before creating any
  project files.
- The Pi adapter requests strict JSON-schema tool sampling when supported and aborts after three
  consecutive unavailable-tool calls before a fourth sibling can be preflighted, while active calls
  reset the counter.
- Existing-repository adoption can explicitly run an application's authoritative quality command
  before and after copying harness files. It records the command, exit codes, compatibility, and
  implicated copied paths; missing, indeterminate, or incompatible evidence keeps activation
  provisional.
- Universal copied Python harness sources now satisfy Procurement Intelligence Lab's locked Ruff
  0.16.3 format and lint discovery without changing its configuration, lock, or ignore rules.

## [0.4.1] - 2026-08-22

### Fixed

- Live GitHub planning audit now works with supported GitHub CLI versions that do not
  provide `gh api --slurp`, while retaining zero-, single-, and multi-page JSON parsing.

## [0.4.0] - 2026-08-22

### Added

- Provider-neutral roles, skills, engineering loop, evidence reports, intake, GitHub planning, and project profiles.
- Codex and experimental Pi adapters.
- Integrity-checked write scopes, independent verifier verdicts, and provenance-locked harness upgrades.
- Configurable product-version, engineering-quality, and GitHub security contracts.
- Dependabot, dependency review, CodeQL, and immutable GitHub Actions validation.

### Security

- Completion fingerprints worktree, index, hidden index flags, submodules, and embedded repositories.
- Third-party GitHub Actions are pinned to reviewed full commit SHAs.
