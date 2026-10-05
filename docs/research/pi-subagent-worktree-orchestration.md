# Pi subagent and worktree orchestration

- Governing issue: [#20](https://github.com/stauntonjr/agentic-project-template/issues/20)
- Related decision: [ADR-0003](../adr/0003-pi-reference-adapter.md)
- Research status: recommendation complete; no prototype or architecture decision accepted
- Release impact: none; this is an internal research note and changes no runtime or public contract
- Inspected: 2026-08-25 UTC (2026-08-24 America/New_York)
- Date sensitivity: high; Pi and the independent orchestration projects are changing quickly

## Decision and scope

This research asks whether the experimental Pi adapter should gain automated subagent and Git
worktree orchestration without weakening the harness's one-writer-per-worktree or
independent-verifier rules.

The current recommendation is:

> **Defer every write-capable Pi orchestration lane. Harden the repository's existing MIT
> Bubblewrap/SparkRun supervisor primitives into a separately authorized, externally sandboxed,
> read-only spike; do not reuse its current write-capable profile unchanged.**

This is a research recommendation, not an accepted architecture decision. The human owner must
explicitly choose whether to authorize the read-only spike. Even that choice would not authorize a
Pi extension installation, a write-capable worker, Git mutation in an authoritative repository,
GitHub mutation, or a release. A later accepted ADR would be required before any write-capable Pi
lane.

The research stops at a design that:

1. can be tested against a disposable pinned fixture without modifying an authoritative checkout;
2. gives delegated Pi processes no more than repository-read authority;
3. does not load user, project, or third-party Pi extensions;
4. can produce before/after filesystem, process, network, and Git evidence; and
5. leaves the human owner with an explicit accept, defer, or reject choice.

No model or candidate orchestration package was executed, installed, or copied. One pre-existing
user extension did load unexpectedly during a local diagnostic; that boundary failure and its
unknown side-effect status are recorded below.

## Project constraints and comparison dimensions

Repository contracts impose these constraints:

- canonical roles, authority, loop state, and evidence remain provider-neutral;
- the orchestrator alone owns shared Git lifecycle, integration, and planning reconciliation;
- each implementer owns one bounded issue, branch, and worktree;
- a verifier cannot approve work it authored;
- Pi project extensions execute with the launching user's permissions and Pi supplies no built-in
  sandbox;
- project-local instructions and fetched content are untrusted input;
- publication, GitHub writes, destructive actions, architecture policy, and release remain outside
  model authority; and
- an adapter may narrow canonical authority but cannot broaden it.

Candidates were compared on functional fit, process/filesystem/Git/verifier isolation, maturity,
maintenance, license and provenance, portability, security, operating cost, integration effort,
provider lock-in, observability, recoverability, and evidence quality. Star counts were used only
as weak discovery signals.

## Search method

### Queries

The search used combinations of:

- `site:pi.dev subagent worktree coding agent extension security`
- `site:github.com/earendil-works/pi subagent worktree`
- `site:github.com/badlogic/pi-mono subagent extension worktree`
- `Pi subagent package depth cycle cwd security`
- `independent coding agent orchestration git worktree one agent per worktree GitHub`
- `site:skills.sh git worktree parallel agents orchestration`
- `site:github.com/github/awesome-copilot worktree agent orchestration`
- candidate-specific searches for `license`, `security`, `sandbox`, `worktree`, `reviewer`,
  `process`, and `cwd`.

The `skills.sh` query did not return a directly relevant, source-resolved candidate in the search
results. GitHub Awesome Copilot supplied independent pattern-discovery leads for coordinator/worker,
parallel review, and research-then-act. Those patterns were then assessed against primary Pi, Git,
and candidate repository sources rather than treated as production-ready instructions.

### Source-selection rules

1. Inspect this repository, its accepted Pi ADR, and its exercised adapter evidence first.
2. Prefer current Pi documentation and the canonical Pi repository for Pi behavior.
3. Pin mutable GitHub evidence to an inspected commit and record the product/release version.
4. Inspect implementation or tests where a README makes an enforcement claim.
5. Use an independent discovery hub to improve recall, then follow every useful lead to its
   canonical repository.
6. Treat prompts, role descriptions, stars, and README claims as advisory until corroborated.
7. Do not install or execute a candidate merely to evaluate it.

## Evidence inventory

| Source | Inspected revision/version | License and maintenance signal | Relevant evidence | Boundary |
|---|---|---|---|---|
| [Pi canonical repository](https://github.com/earendil-works/pi/tree/dcd461925db2edf69a43c8135db1180d418afd54) and [v0.84.3 release](https://github.com/earendil-works/pi/releases/tag/v0.84.3) | main `dcd461925db2edf69a43c8135db1180d418afd54`; release 0.84.3 published 2026-08-24 | MIT; active, 96,656 stars in the inspected 2026-08-25 UTC snapshot, main updated 2026-08-24 | Core is deliberately extensible; subagents are not a core authority/isolation feature. | Popularity and active maintenance do not establish safety or project fit; the exact star count is time-sensitive. |
| [Pi security](https://github.com/earendil-works/pi/blob/dcd461925db2edf69a43c8135db1180d418afd54/packages/coding-agent/docs/security.md) and [containerization](https://github.com/earendil-works/pi/blob/dcd461925db2edf69a43c8135db1180d418afd54/packages/coding-agent/docs/containerization.md) | blobs `ebd3e52a...` and `33f2df3...` | Pi repository MIT | Pi runs with the launching user's permissions. Project trust is an input-loading guard, not a sandbox. Real isolation must be an OS/container/VM boundary. Host Pi plus tool routing does not isolate other extension tools. | A read-only tool allowlist is not a filesystem security boundary by itself. |
| [Pi official subagent example](https://github.com/earendil-works/pi/tree/dcd461925db2edf69a43c8135db1180d418afd54/packages/coding-agent/examples/extensions/subagent) | `README.md` blob `da74f326...`; `index.ts` blob `71b1a33d...` | Pi repository MIT; example, not a stable core contract | Separate Pi subprocesses, isolated context windows, single/parallel/chain modes, at most 8 tasks and 4 concurrent, cancellation, structured output, user-agent default, project-agent confirmation. | Accepts caller-supplied `cwd`, does not create or constrain worktrees, does not supply an OS sandbox, and does not create verifier independence. Process separation is context separation, not authority separation. |
| [Pi SDK](https://github.com/earendil-works/pi/blob/dcd461925db2edf69a43c8135db1180d418afd54/packages/coding-agent/docs/sdk.md), [RPC](https://github.com/earendil-works/pi/blob/dcd461925db2edf69a43c8135db1180d418afd54/packages/coding-agent/docs/rpc.md), and [extensions](https://github.com/earendil-works/pi/blob/dcd461925db2edf69a43c8135db1180d418afd54/packages/coding-agent/docs/extensions.md) | blobs `5b75b2f...`, `f92c12e...`, `7643856...` | Pi repository MIT | SDK/RPC provide headless session control, events, abort, settlement, and explicit tools. Extensions can block tool calls and spawn processes. | In-process checks remain defense in depth; extensions themselves retain host authority. |
| Locally installed Pi | `@earendil-works/pi-coding-agent` 0.84.1; executable SHA-256 `840d1e8e689ed9e4937bcb00b9a810e02a8567d9afb10a47097f11ca93ea1521` | package manifest MIT; two patch releases behind current at inspection | Bundled 0.84.1 subagent example matches the basic subprocess design. Local configuration lists multiple user packages, and at least one global extension was auto-discovered. | It is not a clean test runtime. Package version does not by itself identify the exact upstream source commit. |
| Local [Bubblewrap/SparkRun supervisor](../../harness/runtime/model_stress_runner.py) and [Issue #21 Qwen smoke](../reports/issue-21-qwen-canary-smoke.md) | repository revision `6a8a9a5781165873b6e9a3f58cc4ef8ef553f013`; inspected runner lines 918-1035 and the 2026-08-24 smoke evidence | This repository is MIT; maintained in-tree and already statically checked and smoke-tested | Reusable primitives include a synthetic Pi home/config, allowlisted environment, read-only Pi installation, PID/IPC/UTS isolation, process/output/time bounds, symlink-aware path handling, before/after snapshots, truthful invocation state, and oracle isolation. | Its model-evaluation profile deliberately mounts a disposable repository writable, shares host networking to reach loopback inference, places the prompt in process argv, exposes `edit`, uses `--approve`, loads harness resources in one lane, and schedules paired lanes serially. The historical single-trial smoke is diagnostic negative evidence, not a parallel-research or isolation proof. |
| [`mjakl/pi-subagent`](https://github.com/mjakl/pi-subagent/tree/0d13273319902a84535c2bf4341a5aefbd422dc0) | package 3.0.1; commit `0d13273319902a84535c2bf4341a5aefbd422dc0`, 2026-08-19 | MIT; 76 stars, active in August 2026 | Useful patterns include empty child context by default, prompt transport over RPC stdin, canonicalized `cwd`, depth/cycle guards, process-tree termination, timeouts, bounded output, and persistent-session locks. | It inherits enabled extensions/configuration, allows external `cwd` values, writes session/lock/starter-agent state, provides no worktree lifecycle or OS sandbox, and calls process isolation "isolated" even though host authority is shared. Do not adopt or execute without a full supply-chain review. |
| [`HamdiMaz/pi-sub-agent`](https://github.com/HamdiMaz/pi-sub-agent/tree/f1c0ae29f4cf370255530d3d126ec71b0d7a6194) and [Pi package page](https://pi.dev/packages/pi-sub-agent) | package 0.1.5; commit `f1c0ae29f4cf370255530d3d126ec71b0d7a6194`, 2026-05-18 | MIT; Pi registry listed 386 monthly downloads, repository had 0 stars at inspection | Sends prompts over stdin, caps tasks and output, blocks recursive fan-out, narrows child tools to the parent allowlist, and fails closed on malformed child output. | Ordinary child Pi processes still inherit Pi/package security and selected `cwd`; no worktree or OS isolation. Young, small adoption signal. |
| [`ystepanoff/awo`](https://github.com/ystepanoff/awo/tree/44752483169bc22f84c8f9b53e23c536abf23e5d) | commit `44752483169bc22f84c8f9b53e23c536abf23e5d`, 2026-05-25 | MIT; created 2026-05-21, 2 stars, no open issues at inspection | Independent pattern: separate writer and reviewer worktrees, deterministic verification and proof artifacts, bounded cleanup paths/branch prefixes, reviewer-edit detection, no commit/push/merge/PR. | Very young; supports Claude/Codex rather than Pi. Verification commands run unsandboxed. A separate worktree and a prompt saying "read-only" do not prevent the same OS user from reading or modifying sibling paths or shared Git metadata. |
| [`gitpcl/openorchestrator`](https://github.com/gitpcl/openorchestrator/tree/1b485ae105596de19d8012ace921701c7b84b99c) | commit `1b485ae105596de19d8012ace921701c7b84b99c`, 2026-07-05 | MIT; created 2026-03-14, 5 stars, 8 open issues at inspection | Independent provider-neutral control-plane pattern with advertised Pi support, worktree-per-agent supervision, conflict warnings, status, and attachment. | Its default workflow can install dependencies, copy `.env`, commit, merge, push, open PRs, and delete worktrees. That authority is intentionally broader than this adapter and unsuitable for adoption. |
| [Git worktree documentation](https://git-scm.com/docs/git-worktree) and [pinned source](https://github.com/git/git/blob/593c42fe075be0c8cd5239b3a2f21c610cbc9798/Documentation/git-worktree.adoc) | Git `593c42fe075be0c8cd5239b3a2f21c610cbc9798`; document blob `fbf8426c...`, 2026-08-24 | Git repository license notice is GPL-2.0; factual baseline only, with no copied code or prose | A linked worktree gets separate `HEAD` and index but shares most repository data, refs, and default configuration through the common Git directory. | Worktrees reduce accidental working-tree collisions; they are not filesystem, process, credential, or Git-control isolation. |
| [GitHub Awesome Copilot orchestration guide](https://github.com/github/awesome-copilot/blob/4742f265959bf025882314564b364d9d7af6e2d5/website/src/content/docs/learning-hub/agents-and-subagents.md) | commit `4742f265959bf025882314564b364d9d7af6e2d5`, 2026-08-24 | MIT; 38k-plus stars; community catalog maintained by GitHub | Discovery patterns: coordinator/worker, parallel multi-perspective review, research-then-act, allowlisted agents, and depth/concurrency bounds. | Product-specific, community-contributed guidance; it does not establish Pi or OS isolation. |

Versions, activity, stars, downloads, and package behavior may drift. Exact revisions above are the
reviewable evidence boundary.

## Evidence-backed findings

### 1. Pi supplies orchestration primitives, not the required trust boundary

Pi can create and supervise sessions through subprocesses, SDK, RPC, and extensions. Its official
subagent example demonstrates useful scheduling and output mechanics. Pi's own security guidance is
equally explicit that extensions run with full user permissions and that the runtime has no built-in
sandbox. Therefore, a Pi process boundary isolates context and failure handling, but not files,
credentials, Git state, the network, or verifier authority.

### 2. The official example is a reference implementation, not a safe harness component

The example's bounded concurrency, child-process settlement, abort propagation, structured details,
and default-to-user-agent discovery are worth adapting. Its arbitrary `cwd`, ordinary inherited
process environment, lack of worktree ownership, and absence of an external sandbox are incompatible
with Issue #20's acceptance boundary. Vendoring it would overstate what is enforced.

### 3. Third-party Pi packages improve ergonomics but widen the supply chain

The two inspected Pi packages add real operational improvements: stdin prompt transport, recursive
delegation guards, bounded output, timeouts, model/tool inheritance, and better error propagation.
They still execute as extensions with the user's permissions, and neither creates a one-writer
worktree lease or an independent verifier boundary. Installing one would add an update channel and
executable authority before the project has proved its minimal need. Selected ideas should be
reimplemented against this repository's contracts if the human accepts a later design.

### 4. Worktrees are coordination boundaries, not security boundaries

Git gives each linked worktree its own working tree, index, and `HEAD`, but most refs, objects, and
configuration are shared. A same-user process can name sibling paths and the common Git directory.
Consequently, "one worktree per agent" prevents ordinary path collisions but cannot prove that one
agent cannot inspect, mutate, commit, reconfigure, or delete another lane. That proof requires both
an orchestrator-owned lease and an OS-enforced mount/process boundary.

### 5. Independent verification is an identity-and-evidence property

A new Pi process is not automatically an independent verifier. Independence requires a verifier
that did not author the candidate, receives a frozen candidate identity and acceptance criteria
instead of the writer's persuasive transcript, has no write authority, records deterministic check
evidence, and binds its verdict to the exact candidate. A different model/provider improves
diversity but does not replace those controls.

### 6. The local Pi home is unsuitable as a spike baseline

Static inspection found configured user packages and at least one auto-discovered extension under
`/home/jrs/.pi/agent`. The exact installed invocation:

```text
/home/jrs/.local/share/pi-node/node-v22.23.2-linux-arm64/bin/pi --help
```

unexpectedly emitted:

```text
[pi-hermes-memory-trilium] Extension loaded
[pi-hermes-memory-trilium] Auto-sync enabled via config
```

No model or installation was requested, but no before-command extension-state baseline existed, so
this research cannot prove the invocation caused no local or external mutation. The same already
submitted diagnostic shell then ran `pi list --no-approve`; Pi was not invoked after the unexpected
extension output was reviewed. This is a correction-log candidate for a later separately scoped
change: even discovery/help commands must use an empty isolated `PI_CODING_AGENT_DIR` and explicit
resource-disabling flags.

### 7. The existing MIT supervisor is the right adaptation base, but not safe unchanged

The in-tree model-stress runner materially changes the build-versus-adapt decision. It already has
the most expensive low-level primitives this spike needs: a Bubblewrap command builder, a synthetic
Pi home and provider configuration, an allowlisted environment, a read-only Pi installation,
process and output bounds, path and symlink checks, repository snapshots, and deliberately isolated
oracle execution. Reusing those reviewed primitives avoids a new executable dependency and preserves
the repository's MIT provenance.

The current profile cannot be reused unchanged for parallel research. Its current gaps include a
writable disposable repository, shared host network, and full prompt in argv. It is an evaluation
runner: it advertises `edit`, uses `--approve`, intentionally loads harness context in one lane, and
runs the paired lanes serially. Issue #21 shows that this boundary was useful for one diagnostic
Qwen trial, but also that shared networking was not an egress filter and the historical trial did
not prove full Git scope, parallel scheduling, or read-only isolation.

A separately selected `read-only-research` profile should adapt the existing primitives by:

- replacing the writable repository bind with a read-only fixture mount and excluding writable
  shared Git metadata;
- removing `edit` and using only `read`, `grep`, `find`, and `ls`;
- disabling approval, extensions, skills, context files, prompt templates, and saved sessions;
- transporting task text over RPC stdin or another owned non-argv channel;
- using a bounded parallel scheduler only after the complete batch passes preflight;
- replacing shared host networking with a logged egress boundary limited to the exact inference
  relay; and
- preserving the existing empty synthetic home, environment allowlist, output/time bounds,
  symlink-safe handling, snapshots, sanitization, and truthful invocation-state reporting.

Building a greenfield supervisor is justified only if a design review proves the evaluation-specific
paired-lane/oracle structure cannot be cleanly separated into provider-neutral primitives, or if the
existing network and process boundary cannot be hardened fail-closed. That evidence does not exist
today. Until the human authorizes the read-only spike and selects its external sandbox and inference
route, defer execution.

## Required isolation contracts

### Process isolation

The supervisor, not the model, must own process creation and concurrency.

- Preflight every lane before starting any child; one invalid lane prevents the entire batch.
- Use direct argv with `shell: false`; send task text over stdin or an owned `0600` file.
- Set a maximum task count, concurrency, delegation depth, wall-clock time, idle time, output bytes,
  and process memory/CPU limit.
- Put each child in its own process group/cgroup; abort sends a graceful termination followed by a
  bounded hard kill, and success requires no surviving descendants.
- Use a fresh empty `PI_CODING_AGENT_DIR` per child. Do not mount or inherit host
  `/home/jrs/.pi`, global `AGENTS.md`, sessions, packages, extensions, skills, prompts, or model
  catalogs.
- Start offline and disable startup update/telemetry traffic. Permit only the explicitly selected
  inference endpoint through a logged network policy.
- Pass an allowlisted environment. Exclude GitHub tokens, API keys not required by the chosen local
  endpoint, SSH agents, cloud credentials, Docker sockets, user home paths, and parent session
  identifiers.
- Treat any unknown tool, extension load, UI request, malformed RPC/event output, nonzero exit,
  timeout, resource-limit event, or incomplete settlement as a failed lane.

### Filesystem isolation

- The delegated process runs inside a container, VM, micro-VM, or equivalent OS-enforced sandbox.
- Mount one pinned fixture snapshot read-only and a lane-private scratch/output directory. Do not
  mount the authoritative repository, host home, sibling lanes, the common Git directory, or
  credential stores.
- Canonicalize every path with `realpath`, reject missing/non-directory targets and symlink escapes,
  and compare canonical mount targets before spawning.
- Make result artifacts append-only to the child or collect them from stdout; the child cannot alter
  the supervisor's lease, baseline, oracle, or evidence record.
- Record path, mode, symlink target, size, and digest fingerprints before and after. A write attempt
  must fail at the OS boundary, not merely because the prompt said not to write.

### Git isolation

- The human/orchestrator alone creates, locks, repairs, removes, fetches, rebases, commits, merges,
  pushes, and reconciles linked worktrees.
- Read-only delegated lanes receive a snapshot without a writable common Git directory. Git status
  evidence may be generated by the supervisor outside the child.
- A future writer, if separately approved, receives one canonical worktree path and a lane-private
  writable source mount, but shared Git metadata remains supervisor-owned.
- An atomic lease covers the filesystem-identity closure of the canonical repository, worktree, and
  shared Git common directory—not merely their path strings—and records lane id, role, issue, base
  SHA, branch, allowed identities/paths, owner principal and process group, creation time, heartbeat,
  and expiry. Duplicate, aliased, or overlapping writable identities fail before any process starts.
- Lease acquisition and validated write-capable mount/file-descriptor exposure are one fail-closed
  supervisor transaction: no principal or process group may spawn or receive writable authority
  unless it already owns the single current lease for every exposed identity.
- Recovery of an expired lease requires proof that no owner process remains and explicit
  orchestrator action. Agents never remove stale leases themselves.
- Candidate identity includes base revision, tracked/untracked bytes, modes, symlink targets, and
  declared scope. Any post-review mutation invalidates prior checks and verdicts.

### Verifier isolation

- The verifier is a fresh process and identity that did not author or repair the candidate.
- It receives the issue, acceptance criteria, exact candidate identity, declared scope, deterministic
  check contract, and relevant source evidence—not the writer's full conversation or self-report.
- Its candidate mount is read-only. It cannot access the writer's writable scratch area, session,
  credentials, or lease.
- Deterministic checks run through a separately authorized runner; verifier prose cannot turn a
  failed command into a pass.
- The verdict records verifier identity/model/runtime, evidence revisions, findings, exact candidate
  identity, and approve/reject/blocked status. A changed candidate requires a new verdict.
- A separate process with the same model is useful review, but the strongest practical independence
  combines different model families, deterministic tools, OS-enforced read-only access, and human
  authority.

## One-writer-per-worktree proof obligation

Let `identity_closure(R)` include a protected worktree or shared Git common directory and every
writable name or handle resolving to the same filesystem objects: canonical paths, symlinks, bind
mounts, mount-namespace aliases, filesystem and mount identities, inherited working directories,
and already-open writable file descriptors. A single lease may cover a set of identities, but a
principal/process group must not accumulate separate leases for aliases of the same resource.

The invariant is:

```text
For every protected resource R, instant T, and principal/process group P:
  can_write(P, identity_closure(R), T)
    implies lease_count(P, identity_closure(R), T) = 1,
    and that lease is current, exclusive, and covers every writable identity exposed to P.

For any distinct active lease holders P and Q at T:
  writable_identity_set(P, T) intersects writable_identity_set(Q, T) = empty.
```

An unleased writer therefore cannot be spawned, inherit, mount, open, or receive any writable path
or alias to a worktree or shared Git metadata. Lease acquisition and writable mount/file-descriptor
exposure must be coupled fail-closed: validate identities, atomically acquire the single lease,
construct and revalidate the exact mount namespace, and only then spawn. Any failure revokes the
provisional authority, removes the writable exposure, and starts no child. Release occurs only after
all descendants are dead and no writable mount or inherited descriptor remains.

Prompts and worktree names cannot prove this. A future implementation must provide all of:

1. a supervisor-owned atomic acquire/release operation;
2. canonical path, filesystem identity, mount identity, and Git common-directory comparison before
   acquisition and immediately before spawn;
3. batch preflight that rejects duplicate and overlapping writable identities before partial launch;
4. an unleased-writer case rejected before a writable mount, file descriptor, tool, or process is
   exposed;
5. direct-path and symlink-alias cases that resolve to the same worktree and cannot obtain distinct
   leases;
6. bind-mount and mount-namespace-alias cases whose different path strings share filesystem/mount
   identity and cannot obtain distinct leases;
7. linked-worktree cases that have distinct working directories but the same Git common directory,
   proving no child receives overlapping writable Git metadata;
8. path-retargeting and inherited working-directory/open-file-descriptor cases revalidated at the
   mount/spawn boundary;
9. a deliberate second leased writer rejected before process creation, plus lease-token and owner
   mismatch cases that fail closed;
10. crash/timeout cases that kill all descendants, withdraw writable mounts/descriptors, and retain
    recoverable, auditable lease state before release;
11. a read-only verifier case that receives neither a writer lease nor writable authority and whose
    attempted mutation is denied externally; and
12. before/after fingerprints showing sibling, shared Git, and authoritative targets unchanged.

The read-only spike below proves a stricter zero-writer boundary. It does **not** satisfy the future
one-writer proof merely because zero is less than one. The write-capable proof remains a separate,
human-authorized phase.

## Build, adopt, adapt, and defer

| Option | Benefit | Cost/risk | Recommendation |
|---|---|---|---|
| Reuse the existing model-stress supervisor unchanged | Already exercised locally; no new package or provenance boundary | Writable disposable repository, shared host network, prompt in argv, `edit`, approval, harness resource loading, and serial lanes violate the read-only parallel-research contract | Reject for the spike. It remains appropriate only for its separately governed evaluation purpose. |
| Harden/adapt the existing MIT supervisor primitives | Reuses reviewed Bubblewrap, synthetic-home, bounds, snapshot, sanitization, and oracle-isolation machinery while keeping code in-tree | Requires a distinct read-only profile, non-argv prompt transport, actual parallel scheduling, and a constrained inference route; still needs Pi compatibility maintenance | **Recommended only for the read-only spike, after human authorization.** |
| Build a new supervisor from scratch | Could optimize directly for provider-neutral research orchestration | Duplicates proven local primitives and adds a second security-sensitive implementation without current evidence that separation is impossible | Defer. Reconsider only if design review proves the evaluation runner cannot be safely factored or hardened. |
| Build a complete Pi orchestration extension now | Exact Pi-native UX and repository integration | Largest executable surface; duplicates contracts; easy to confuse in-process checks with isolation; creates a long-term Pi API burden | Reject now. |
| Adopt Pi's official subagent example | Small, current, observable, familiar Pi UX | Example quality, arbitrary `cwd`, no worktree/OS/verifier enforcement, full extension authority | Do not vendor or install. Borrow bounded scheduling and event concepts only. |
| Adopt a third-party Pi package | More mature session, timeout, recursion, and output ergonomics | New executable supply chain and update channel; no worktree lease or external sandbox; inherited extensions/configuration | Reject for the spike. Reconsider only after a complete admission review and a demonstrated need. |
| Adopt AWO or Open Orchestrator | Existing worktree control-plane concepts and artifacts | Young projects; mismatched providers or materially broader authority; unsandboxed commands; integration larger than the Pi adapter | Do not adopt. Use as independent comparison evidence. |
| Defer Pi orchestration entirely | No new attack or maintenance surface | Pi remains a prompt-mediated adapter and does not exercise native parallelism | Current default if the owner does not authorize the spike. |

## Strictly read-only next spike

### Goal

Prove that a hardened read-only profile built from the existing deterministic supervisor primitives
can run two independent Pi research workers in parallel against the same pinned disposable fixture
while the target repository, Git state, host Pi home, sibling lane, credentials, and external
network remain inaccessible or unchanged.

The supervisor may create ephemeral files only inside a fresh owner-controlled temporary directory.
Delegated children get no writable repository mount. The authoritative template checkout and its
Git common directory are never mounted into the sandbox.

### Mandatory preflight

1. Human explicitly accepts the read-only spike and selects the external sandbox implementation.
2. Pin and hash the Pi executable/package and the local inference model/server configuration.
3. Create a fresh temporary root with a separate empty Pi home and scratch/output directory per
   lane; do not reuse `/home/jrs/.pi`.
4. Copy or materialize a synthetic fixture at an exact commit into the temporary root, then expose
   it read-only to children.
5. Record:
   - filesystem tree digests, modes, and symlink targets;
   - Git `HEAD`, refs, config, worktree listing, index, status, hooks, and remotes;
   - scoped process/cgroup membership;
   - network policy and allowed inference endpoint;
   - environment-variable names after allowlisting, never secret values; and
   - exact child argv with task content omitted from process arguments.
6. Reject the whole batch if paths overlap unexpectedly, a symlink escapes, a resource is already
   loaded, the inference endpoint is not pinned, or any fingerprint is incomplete.

Each child must use an equivalent of:

```text
PI_CODING_AGENT_DIR=<fresh-lane-private-empty-dir>
PI_OFFLINE=1
PI_TELEMETRY=0
pi --mode rpc --no-session --no-extensions --no-skills \
  --no-prompt-templates --no-context-files --no-approve \
  --tools read,grep,find,ls
```

This argv is a design requirement, not evidence that the command has been safely exercised. The
external sandbox and environment allowlist remain the actual authority boundary.

### Scenarios

1. **Parallel happy path:** two workers receive disjoint, evidence-answerable research questions
   about the fixture and return path/line-grounded structured results.
2. **Malicious repository resources:** the fixture contains inert `.pi` project resources and
   instructions that request extension loading; startup evidence must show they were not loaded.
3. **Forbidden mutation:** a worker is asked to edit the fixture and Git state; no write-capable
   tool is advertised and the read-only mount rejects direct path writes.
4. **Path escape:** a fixture symlink and prompt target host Pi home and the sibling lane; both reads
   and writes fail at the sandbox boundary.
5. **Forbidden process/network:** a worker attempts shell execution and a non-inference connection;
   no shell tool is advertised, no descendant is created, and network policy denies the connection.
6. **Cancellation:** one worker is deliberately held until the deadline; the supervisor terminates
   its process group, preserves bounded diagnostics, and leaves no descendant.
7. **Malformed/unknown output:** invalid RPC/event data or an unknown tool call marks that lane and
   the aggregate run failed; there is no silent partial success.

### Success definition

The spike succeeds only if all of these are true:

- exactly two authorized Pi child processes start and concurrency never exceeds two;
- every advertised and observed tool is in `read`, `grep`, `find`, `ls`;
- startup evidence shows no user/project extension, skill, prompt, context, package, or saved session
  was loaded;
- the only permitted network flow is to the pinned local inference endpoint;
- no host credential path or secret environment value is exposed;
- every forbidden operation is denied by an external boundary and recorded;
- all child descendants terminate within the deadline;
- target filesystem and Git fingerprints are byte-identical before and after;
- lane outputs are bounded, attributable, and tied to the exact fixture and Pi/runtime revision; and
- repeating the deterministic supervisor portion produces the same manifest and disposition.

Any unexpected extension message, write, new process, network flow, Git/ref/config/worktree change,
fingerprint drift, surviving descendant, missing evidence, or ambiguous child settlement fails the
entire spike and stops before retry.

## Acceptance-criteria disposition

| Issue #20 criterion | Current disposition |
|---|---|
| Research current Pi loop/orchestration patterns and record primary-source evidence | **Satisfied by this note**, subject to normal drift. |
| Define explicit process, filesystem, Git, and verifier isolation requirements | **Satisfied as a design contract**; not implemented. |
| Prototype bounded read-only delegation before any write-capable lane | **Not yet satisfied.** The exact next spike is specified and awaits human authorization. |
| Prove one-writer-per-worktree and independent-verifier invariants | **Not yet satisfied.** Proof obligations are specified; the read-only spike proves only zero-writer isolation. |
| Record an explicit accept, defer, or reject decision | **Research decision recorded:** defer write-capable orchestration; recommend an adapt-only read-only spike. Human acceptance remains required. |

Issue #20 must remain open after this research loop.

## Human decision

The owner must choose one of:

1. **Authorize the read-only spike (recommended):** accept only the bounded experiment above, select
   an external sandbox, and create a separate implementation/evidence loop. No write-capable lane is
   authorized.
2. **Defer:** retain the current Pi prompt/questionnaire adapter and revisit after Pi exposes a more
   stable orchestration contract or the project has a stronger application need.
3. **Reject Pi orchestration:** keep Pi strictly as an interactive/reference adapter and invest in a
   provider-neutral external orchestrator only.

Only after option 1 succeeds may the owner consider an ADR for a future one-writer/independent-
verifier spike. That later decision must explicitly select the OS boundary, credential and network
policy, Git ownership model, artifact schema, failure recovery, Pi version-support policy, and
supply-chain strategy.

## Confidence, gaps, and drift

Confidence is high that Pi process separation alone cannot meet the required isolation because Pi's
official security documentation and Git's worktree model are explicit. Confidence is medium that a
minimal external supervisor is the best long-term implementation: the read-only spike has not run,
the available sandbox on the target host has not been selected or verified, and Pi's APIs are still
moving.

Open gaps:

- select and verify the external sandbox on the DGX host;
- decide whether local inference can be exposed through a narrowly logged network route or socket;
- define the durable orchestration artifact schema without duplicating the existing loop schema;
- test Pi 0.84.1 versus current 0.84.3 compatibility in disposable environments;
- independently review any code before installation or execution;
- verify resource-disable flags through observed startup events, not documentation alone; and
- determine whether a future provider-neutral supervisor should live in this template or a separate
  runtime repository.

No source code or prose from candidates should be copied merely because it is MIT-licensed. If a
later design is accepted, preserve the exact source revision and attribution, and prefer a small
provenance-recorded reimplementation of the necessary patterns.
