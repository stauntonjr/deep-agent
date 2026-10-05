# GitHub access and dependency-review recovery

Use this before declaring a GitHub planning or CI blocker. Repository files cannot provision
account OAuth scopes or guarantee that live repository security settings were copied from a
template. These are separate setup prerequisites. Use the existing planning tool; no token files,
custom credential fallback, disabled checks, or administrator merge bypass are needed.

## Establish the actual failure

1. Use the approved network execution path. Follow `GH-AUTH-002` in
   [the correction log](correction-log.md) if the sandbox cannot reach GitHub.
2. Inspect `gh auth status` and `gh api user --jq .login`. Check whether `GH_TOKEN` or
   `GITHUB_TOKEN` is set without printing values. An environment credential can override the
   keyring credential. Do not print `gh auth token`, rotate credentials, or remove an override
   merely to obtain broader access.
3. Read `.github/planning.json` for the exact repository, Project owner, and number. Read the
   failed job log or API error, not just its check name. Record the host, commit/run, and sanitized
   error. Successful repository access does not establish Projects access.

## Dependency review says it is unsupported

The Action error `Dependency review is not supported on this repository. Please ensure that
Dependency graph is enabled` is a diagnostic hint, not proof of the setting. A dependency-diff
API 403 alone also does not prove that the graph is disabled. Check repository eligibility,
permissions, and the live setting before assigning a cause.

An authorized repository administrator should open the repository's **Settings → Advanced
Security → Dependency graph** (older interfaces call this Code security and analysis). Inspect
its state and, if disabled, enable Dependency graph. This is a persistent repository setting;
editing the workflow or setting `HARNESS_DEPENDENCY_REVIEW=enabled` does not enable it. If already
enabled, inspect the exact API/job error and GitHub availability or eligibility instead of
repeatedly changing settings. Private/internal repository entitlement is a separate prerequisite.

After an authorized repair, rerun only the failed workflow jobs using the actual run ID:

```bash
gh run rerun RUN_ID --repo OWNER/REPOSITORY --failed
gh run view RUN_ID --repo OWNER/REPOSITORY
gh pr checks PR_NUMBER --repo OWNER/REPOSITORY
```

Require the dependency-review job to pass on the current PR commit. An empty dependency diff is
legitimate for a documentation change; it is not a reason to skip the check. Do not add
`continue-on-error`, disable the public-repository job, weaken its severity threshold, or merge
with an administrator bypass to conceal a prerequisite failure. Enabling Dependabot security
updates is a different operation and must not be substituted for checking Dependency graph.

Sources: [GitHub enablement procedure](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/enable-dependency-graph),
[dependency review requirements](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-review).

## Projects v2 scope is missing

For GitHub CLI OAuth credentials, `read:project` permits read-only inspection; `project` is
needed for membership writes. A repository-admin `repo` credential does not imply either scope.
Use a live read to establish access on the execution host:

```bash
gh project view PROJECT_NUMBER --owner PROJECT_OWNER --format json
```

If the credential really lacks the required scope, the account owner completes the interactive
refresh on that same host. For the current create/add-item workflow, request the write scope
once, rather than fixing reads and immediately failing on the membership write:

```bash
gh auth refresh --hostname github.com --scopes project
gh auth status
gh project view PROJECT_NUMBER --owner PROJECT_OWNER --format json
```

For a strictly read-only task, request `read:project` instead. An environment-provided credential
must be fixed at its authorized source; refreshing a different stored token does not replace it.
Fine-grained tokens and GitHub App credentials have their own permission model: verify the actual
Project operation rather than blindly translating OAuth scope names. If interactive approval is
unavailable, report the exact host and missing permission and stop at the authentication boundary.
Do not copy a token from another machine or put credentials into a repository or workflow.

After access is verified, resume the existing membership procedure; preserve the already-created
Issue or PR and its URL:

```bash
python3 tools/github_planning.py add-item --url EXISTING_ITEM_URL
python3 tools/github_planning.py add-item --url EXISTING_ITEM_URL --yes
```

The second command requires authorized membership work. The wrapper verifies exact membership
and avoids duplicate writes. Do not recreate the issue, use the classic `--project` shortcut, or
claim board placement from issue creation alone. Inspect resulting Status separately; membership
is not evidence that work is In Progress or Done.

Sources: [GitHub CLI Projects permissions](https://cli.github.com/manual/gh_project),
[credential refresh](https://cli.github.com/manual/gh_auth_refresh).

## Handoff and prevention

Before a repository's first PR, verify dependency-review prerequisites on the live repository.
Before creating planning objects, verify Project access on the actual execution host and identify
whether writes are needed. Recheck after changing hosts or credential sources. Keep exact object
URLs if the task stops so a later agent resumes reconciliation instead of creating duplicates.
Link this runbook from the planning entry point and preserve observed failures in the correction
log; a documented remedy must not be reported as an executed repair.
