import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.loop import (
    close_review,
    finish_run,
    load_run,
    make_scope_contract,
    make_write_set,
    migrate_run,
    new_attempt,
    parse_criteria,
    record_check,
    record_finding,
    record_finding_disposition,
    record_proportionality_review,
    record_release_impact,
    record_solution_assessment,
    record_verdict,
    recovery_status,
    resolve_finding_batch,
    resume_run,
    revise_run,
    set_state,
    start_review,
    start_run,
    waive_criterion,
)
from tools.project_intake import mark_adoption_state

ROOT = Path(__file__).resolve().parents[1]


def test_scope_contract() -> dict[str, object]:
    return make_scope_contract(
        in_scope=["Change artifact.txt"],
        out_of_scope=["Repository deployment"],
        assurance_boundary="One local disposable Git repository",
        budget_constraints=["Use existing loop primitives"],
        revision_triggers=["New dependency or subsystem"],
    )


def record_fixture_solution(root: Path, run_id: str) -> None:
    record_solution_assessment(
        root,
        run_id,
        trigger="initial",
        disposition="adapt",
        research_status="not-material",
        rationale="The fixture exercises existing loop primitives",
        sources=[],
    )


def init_repository(root: Path, *, commit: bool = True) -> Path:
    subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Harness Test"], cwd=root, check=True)
    tracked = root / "artifact.txt"
    tracked.write_text("before\n", encoding="utf-8")
    if commit:
        subprocess.run(["git", "add", "--", "artifact.txt"], cwd=root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "baseline"], cwd=root, check=True, stdout=subprocess.PIPE
        )
    return tracked


def init_repository_with_submodule(base: Path) -> tuple[Path, Path]:
    child_source = base / "child-source"
    child_source.mkdir()
    child_file = init_repository(child_source)
    child_file.write_text("child baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "--", "artifact.txt"], cwd=child_source, check=True)
    subprocess.run(
        ["git", "commit", "-m", "child content"],
        cwd=child_source,
        check=True,
        stdout=subprocess.PIPE,
    )

    root = base / "parent"
    root.mkdir()
    init_repository(root)
    subprocess.run(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            str(child_source),
            "deps/child",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-am", "add child"], cwd=root, check=True, stdout=subprocess.PIPE
    )
    return root, root / "deps/child/artifact.txt"


def add_embedded_repository(root: Path) -> Path:
    nested = root / "vendor/nested"
    nested.mkdir(parents=True)
    return init_repository(nested)


def start_test_run(
    root: Path,
    *,
    run_id: str = "test-run",
    write_paths: tuple[str, ...] = ("artifact.txt",),
    implementers: tuple[str, ...] = ("implementer-1",),
):
    record = start_run(
        root,
        "Change the artifact",
        "123",
        run_id,
        acceptance_criteria=parse_criteria(["AC1=Artifact contains the accepted value"]),
        declared_write_set=make_write_set(write_paths, []),
        implementers=list(implementers),
        scope_contract=test_scope_contract(),
    )
    record_fixture_solution(root, run_id)
    record_release_impact(
        root,
        run_id,
        level="none",
        reason="Test fixture does not publish a product",
    )
    return record


def close_clean_review(root: Path, run_id: str, reviewer: str = "verifier-1") -> None:
    cycle = start_review(root, run_id, reviewer=reviewer)
    close_review(
        root,
        run_id,
        review_id=cycle["review_id"],
        outcome="clean",
        summary="No findings after bounded independent review",
    )


def disposition_review_batch(
    root: Path,
    run_id: str,
    review_id: str,
    finding_id: str,
    *,
    triggers: tuple[str, ...] = (),
    reviewed_by: str = "orchestrator-1",
    scope_change: str = "within-contract",
    complexity_change: str = "bounded",
    budget_status: str = "on-budget",
    recommendation: str = "proceed",
    finding_disposition: str = "repair-in-scope",
) -> None:
    for trigger in triggers:
        record_solution_assessment(
            root,
            run_id,
            trigger=trigger,
            disposition="adapt",
            research_status="completed",
            rationale="The fixture reopens the existing-solution comparison",
            sources=["https://example.com/canonical-source"],
        )
    record_finding_disposition(
        root,
        run_id,
        review_id=review_id,
        finding_id=finding_id,
        disposition=finding_disposition,
        rationale="The defect is inside the accepted criterion and threat boundary",
        decided_by="orchestrator-1",
    )
    record_proportionality_review(
        root,
        run_id,
        review_id=review_id,
        reviewed_by=reviewed_by,
        objective_alignment="The bounded repair directly restores AC1",
        scope_change=scope_change,
        complexity_change=complexity_change,
        budget_status=budget_status,
        triggers=triggers,
        alternatives=["Narrow the claim", "Defer the repair"],
        recommendation=recommendation,
        solution_disposition="adapt",
        rationale="Reuse the existing completion guard without a new subsystem",
    )


def approve_current(root: Path, run_id: str = "test-run") -> None:
    record_check(
        root,
        run_id,
        name="unit",
        command="python3 -m unittest",
        status="passed",
        evidence="targeted unit boundary",
        criteria=["AC1"],
        tier="full",
    )
    close_clean_review(root, run_id)
    record_verdict(
        root,
        run_id,
        reviewer="verifier-1",
        verdict="approve",
        criteria=["AC1"],
        evidence="Inspected the candidate and raw test result",
    )


class LoopTests(unittest.TestCase):
    def test_schema_12_and_13_runs_migrate_without_replacing_baseline(self) -> None:
        for source_version in ("1.2", "1.3"):
            with (
                self.subTest(source_version=source_version),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                init_repository(root)
                start_test_run(root)
                record_check(
                    root,
                    "test-run",
                    name="legacy",
                    command="python3 -m unittest",
                    status="passed",
                    evidence="legacy evidence",
                    criteria=["AC1"],
                )
                path, record = load_run(root, "test-run")
                baseline = record["baseline"]
                record["schema_version"] = source_version
                if source_version == "1.2":
                    record.pop("review_cycles")
                    record["checks"][0].pop("candidate")
                path.write_text(json.dumps(record), encoding="utf-8")

                migrated = migrate_run(root, "test-run")

                self.assertEqual("1.4", migrated["schema_version"])
                self.assertEqual(baseline, migrated["baseline"])
                self.assertEqual([], migrated["review_cycles"])
                if source_version == "1.2":
                    self.assertIsNone(migrated["checks"][0]["candidate"])
                self.assertIn("scope_contract", migrated)
                self.assertIn("solution_assessments", migrated)
                self.assertTrue(
                    migrated["telemetry"]["schema_migrations"][-1]["preserved_baseline"]
                )

    def test_migration_backfills_legacy_resolution_transition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            path, record = load_run(root, "test-run")
            record["review_cycles"] = [
                {"resolution": {"decision": "emergency-stopped"}, "findings": []}
            ]
            path.write_text(json.dumps(record), encoding="utf-8")

            migrated = migrate_run(root, "test-run")

            self.assertEqual(
                "new-attempt",
                migrated["review_cycles"][0]["resolution"]["next_transition"],
            )

    def test_three_consecutive_failures_block_without_starting_a_fourth_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)

            self.assertEqual(2, new_attempt(root, "test-run", "first failure")["attempt_id"])
            self.assertEqual(3, new_attempt(root, "test-run", "second failure")["attempt_id"])
            with self.assertRaisesRegex(RuntimeError, "retry ceiling reached after 3"):
                new_attempt(root, "test-run", "third failure")

            _, record = load_run(root, "test-run")
            self.assertEqual("blocked", record["state"])
            self.assertEqual(3, record["attempt_id"])
            self.assertEqual(3, len(record["attempt_history"]))
            self.assertEqual(
                ["failed", "failed", "failed"],
                [item["outcome"] for item in record["attempt_history"]],
            )
            self.assertEqual(3, record["telemetry"]["retry_exhaustion"]["limit"])

    def test_retry_exhaustion_resumes_only_with_human_reviewed_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = init_repository(root)
            start_test_run(root)
            tracked.write_text("preserved partial work\n", encoding="utf-8")
            new_attempt(root, "test-run", "first failure")
            new_attempt(root, "test-run", "second failure")
            with self.assertRaises(RuntimeError):
                new_attempt(root, "test-run", "third failure")
            handoff = {
                "schema_version": "1.0",
                "summary": "Change the recovery approach",
                "failure_boundary": "Three attempts failed at the same deterministic check",
                "preserved_paths": ["artifact.txt"],
                "next_action": "Re-enter understand and inspect the preserved candidate",
            }

            with self.assertRaisesRegex(ValueError, "human:IDENTITY"):
                resume_run(root, "test-run", handoff=handoff, authorized_by="agent:planner")
            with self.assertRaisesRegex(ValueError, "reviewed resume"):
                revise_run(root, "test-run", reason="Bypass reviewed recovery")
            loop_contract = root / "harness/loops/engineering-loop.yaml"
            loop_contract.parent.mkdir(parents=True)
            loop_contract.write_bytes((ROOT / "harness/loops/engineering-loop.yaml").read_bytes())
            with self.assertRaisesRegex(ValueError, "cannot leave terminal state blocked"):
                set_state(root, "test-run", "understand")
            resumed = resume_run(
                root,
                "test-run",
                handoff=handoff,
                authorized_by="human:owner",
            )

            self.assertEqual(2, resumed["revision"])
            self.assertEqual(1, resumed["attempt_id"])
            self.assertEqual("understand", resumed["state"])
            self.assertEqual("preserved partial work\n", tracked.read_text(encoding="utf-8"))
            self.assertEqual("human:owner", resumed["agent_handoffs"][-1]["authorized_by"])

    def test_invalid_resume_handoff_fails_before_mutating_blocked_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            new_attempt(root, "test-run", "first failure")
            new_attempt(root, "test-run", "second failure")
            with self.assertRaises(RuntimeError):
                new_attempt(root, "test-run", "third failure")
            before = (root / ".harness/runs/test-run/run.json").read_bytes()

            with self.assertRaisesRegex(ValueError, "forbidden"):
                resume_run(
                    root,
                    "test-run",
                    handoff={
                        "schema_version": "1.0",
                        "summary": "Unsafe handoff",
                        "failure_boundary": "retry",
                        "preserved_paths": [],
                        "next_action": "continue",
                        "transcript": "raw model history",
                    },
                    authorized_by="human:owner",
                )

            self.assertEqual(before, (root / ".harness/runs/test-run/run.json").read_bytes())
            with self.assertRaisesRegex(ValueError, "invalid declared preserved path"):
                resume_run(
                    root,
                    "test-run",
                    handoff={
                        "schema_version": "1.0",
                        "summary": "Escaping handoff",
                        "failure_boundary": "retry",
                        "preserved_paths": ["../outside"],
                        "next_action": "continue",
                    },
                    authorized_by="human:owner",
                )
            self.assertEqual(before, (root / ".harness/runs/test-run/run.json").read_bytes())

    def test_recovery_status_detects_branch_stale_against_integration_ref(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            subprocess.run(["git", "switch", "-c", "feature"], cwd=root, check=True)
            start_test_run(root)
            subprocess.run(["git", "branch", "integration", "main"], cwd=root, check=True)
            subprocess.run(["git", "switch", "integration"], cwd=root, check=True)
            (root / "integration.txt").write_text("advanced\n", encoding="utf-8")
            subprocess.run(["git", "add", "integration.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-m", "advance integration"],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            subprocess.run(["git", "switch", "feature"], cwd=root, check=True)

            status = recovery_status(root, "test-run", "integration")

            self.assertTrue(status["branch_stale"])
            self.assertEqual([], status["scope_violations"])

    def test_context_incomplete_zero_gap_adoption_cannot_report_completion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            project = {
                "project": {"lifecycle": "new", "status": "active"},
                "open_questions": ["Resolve intent.outcomes"],
            }
            intake = {"missing_essential_fields": ["intent.outcomes"]}
            dispositions = {
                "copied": [],
                "upstream_collisions": [],
                "adoption_deferred": [],
                "merge_required_existing": [],
                "merge_required_missing": [],
            }
            mark_adoption_state(project, intake, dispositions)
            project_path = root / "harness/project.yaml"
            project_path.parent.mkdir()
            project_path.write_text(json.dumps(project), encoding="utf-8")
            start_test_run(root)
            approve_current(root)

            self.assertEqual("complete", intake["adoption"]["reconciliation_status"])
            self.assertEqual("provisional", intake["context_readiness"])
            with self.assertRaisesRegex(ValueError, "harness project is provisional"):
                finish_run(root, "test-run", "reported")

    def test_provisional_adoption_cannot_report_completion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            project_path = root / "harness/project.yaml"
            project_path.parent.mkdir()
            project_path.write_text(
                json.dumps({"project": {"lifecycle": "adopt", "status": "provisional"}}),
                encoding="utf-8",
            )
            start_test_run(root)
            approve_current(root)

            with self.assertRaisesRegex(ValueError, "harness project is provisional"):
                finish_run(root, "test-run", "reported")

    def test_report_uses_real_git_boundary_and_acceptance_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = init_repository(root)
            record = start_test_run(root)
            tracked.write_text("after\n", encoding="utf-8")
            approve_current(root)

            report_path, evidence_path, finished = finish_run(root, record["run_id"], "reported")

            report = report_path.read_text(encoding="utf-8")
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            self.assertIn("Acceptance evidence matrix", report)
            self.assertIn("artifact.txt", report)
            self.assertIn("targeted unit boundary", report)
            self.assertIn("approve by verifier-1", report)
            self.assertIn("Recommended product release impact: none", report)
            self.assertIn("Efficiency telemetry: 1 review cycle(s)", report)
            self.assertIn('Review outcomes: {"batch-ready": 0, "clean": 1', report)
            self.assertIn("0 finding batch(es)", report)
            self.assertIn("Contract revision history:", report)
            self.assertIn("Implementation attempt history:", report)
            self.assertIn("Binding scope contract", report)
            self.assertIn("Explicitly out of scope", report)
            self.assertIn("Existing-solution assessments", report)
            self.assertIn("Check-tier time:", report)
            self.assertIn("| check-001 | unit | full |", report)
            self.assertEqual("none", evidence["release_impact"]["level"])
            self.assertEqual(["Repository deployment"], evidence["scope_contract"]["out_of_scope"])
            self.assertEqual("adapt", evidence["solution_assessments"][0]["disposition"])
            self.assertEqual("clean", evidence["review_cycles"][0]["outcome"])
            self.assertEqual([], evidence["boundary"]["scope"]["violations"])
            self.assertEqual("reported", finished["state"])

    def test_cli_records_criterion_linked_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            started = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools/loop.py"),
                    "--root",
                    str(root),
                    "start",
                    "--run-id",
                    "cli-run",
                    "--objective",
                    "Exercise CLI parsing",
                    "--criterion",
                    "AC1=CLI records evidence",
                    "--in-scope",
                    "Change artifact.txt",
                    "--out-of-scope",
                    "Deployment",
                    "--assurance-boundary",
                    "One local repository",
                    "--budget-constraint",
                    "Use existing loop primitives",
                    "--scope-revision-trigger",
                    "New dependency",
                    "--write-path",
                    "artifact.txt",
                    "--implementer",
                    "implementer-1",
                ],
                cwd=ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )
            self.assertEqual("cli-run", started.stdout.strip())
            recorded = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools/loop.py"),
                    "--root",
                    str(root),
                    "record-check",
                    "--run",
                    "cli-run",
                    "--name",
                    "smoke",
                    "--command",
                    "python3 -m unittest",
                    "--status",
                    "passed",
                    "--evidence",
                    "parser boundary",
                    "--criterion",
                    "AC1",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, recorded.returncode, recorded.stdout + recorded.stderr)
            run = json.loads((root / ".harness/runs/cli-run/run.json").read_text(encoding="utf-8"))
            self.assertEqual(["AC1"], run["checks"][0]["criterion_ids"])

    def test_unborn_report_uses_baseline_relative_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(
                ["git", "init", "-b", "main"], cwd=root, check=True, stdout=subprocess.PIPE
            )
            record = start_run(
                root,
                "Create the initial project",
                None,
                "unborn-run",
                acceptance_criteria=parse_criteria(["AC1=New file exists"]),
                declared_write_set=make_write_set(["new.txt"], []),
                implementers=["implementer-1"],
                scope_contract=test_scope_contract(),
            )
            record_fixture_solution(root, record["run_id"])
            (root / "new.txt").write_text("untracked\n", encoding="utf-8")
            record_release_impact(
                root,
                record["run_id"],
                level="minor",
                reason="The initial public file is a new pre-1.0 capability",
                public_contract_changes=["new.txt"],
            )
            record_check(
                root,
                record["run_id"],
                name="exists",
                command="test -f new.txt",
                status="passed",
                evidence="new.txt exists",
                criteria=["AC1"],
                tier="full",
            )
            close_clean_review(root, record["run_id"])
            record_verdict(
                root,
                record["run_id"],
                reviewer="verifier-1",
                verdict="approve",
                criteria=["AC1"],
                evidence="Inspected new.txt",
            )

            report_path, _, _ = finish_run(root, record["run_id"], "reported")
            report = report_path.read_text(encoding="utf-8")

            self.assertIn("baseline-relative changed paths", report)
            self.assertNotIn("tracked change entries", report)

    def test_stale_verdict_is_rejected_after_candidate_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = init_repository(root)
            start_test_run(root)
            tracked.write_text("reviewed\n", encoding="utf-8")
            approve_current(root)
            tracked.write_text("changed after review\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "verifier verdict is stale"):
                finish_run(root, "test-run", "reported")

    def test_release_impact_change_invalidates_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            approve_current(root)
            record_release_impact(
                root,
                "test-run",
                level="patch",
                reason="Changed after independent review",
                public_contract_changes=["artifact behavior"],
            )

            with self.assertRaisesRegex(ValueError, "verifier verdict is stale"):
                finish_run(root, "test-run", "reported")

    def test_staged_index_change_invalidates_verdict_when_status_and_worktree_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = init_repository(root)
            start_test_run(root)
            tracked.write_text("INDEX-A\n", encoding="utf-8")
            subprocess.run(["git", "add", "--", "artifact.txt"], cwd=root, check=True)
            tracked.write_text("WORKTREE\n", encoding="utf-8")
            approve_current(root)
            status_before = subprocess.run(
                ["git", "status", "--short"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout

            tracked.write_text("INDEX-C\n", encoding="utf-8")
            subprocess.run(["git", "add", "--", "artifact.txt"], cwd=root, check=True)
            tracked.write_text("WORKTREE\n", encoding="utf-8")
            status_after = subprocess.run(
                ["git", "status", "--short"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout

            self.assertEqual(status_before, status_after)
            with self.assertRaisesRegex(ValueError, "verifier verdict is stale"):
                finish_run(root, "test-run", "reported")

    def test_hidden_index_paths_cannot_escape_declared_scope(self) -> None:
        for flag in ("--assume-unchanged", "--skip-worktree"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                init_repository(root)
                hidden = root / "hidden.txt"
                hidden.write_text("hidden baseline\n", encoding="utf-8")
                subprocess.run(["git", "add", "--", "hidden.txt"], cwd=root, check=True)
                subprocess.run(
                    ["git", "commit", "-m", "add hidden path"],
                    cwd=root,
                    check=True,
                    stdout=subprocess.PIPE,
                )
                subprocess.run(["git", "update-index", flag, "hidden.txt"], cwd=root, check=True)
                start_test_run(root, write_paths=("artifact.txt",))
                hidden.write_text(f"changed under {flag}\n", encoding="utf-8")
                approve_current(root)

                ordinary_status = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=root,
                    check=True,
                    text=True,
                    stdout=subprocess.PIPE,
                ).stdout
                self.assertNotIn("hidden.txt", ordinary_status)
                with self.assertRaisesRegex(
                    ValueError, "writes outside declared scope: hidden.txt"
                ):
                    finish_run(root, "test-run", "reported")

    def test_assume_unchanged_content_change_invalidates_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            hidden = root / "hidden.txt"
            hidden.write_text("hidden baseline\n", encoding="utf-8")
            subprocess.run(["git", "add", "--", "hidden.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-m", "add hidden path"],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            subprocess.run(
                ["git", "update-index", "--assume-unchanged", "hidden.txt"],
                cwd=root,
                check=True,
            )
            start_test_run(root, write_paths=("hidden.txt",))
            hidden.write_text("reviewed hidden content\n", encoding="utf-8")
            approve_current(root)
            hidden.write_text("changed after review\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "verifier verdict is stale"):
                finish_run(root, "test-run", "reported")

    def test_dirty_submodule_change_invalidates_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, child_file = init_repository_with_submodule(Path(directory))
            child_file.write_text("dirty baseline\n", encoding="utf-8")
            record = start_run(
                root,
                "Change the nested repository",
                "123",
                "submodule-run",
                acceptance_criteria=parse_criteria(["AC1=Nested change is verified"]),
                declared_write_set=make_write_set(["deps/child"], []),
                implementers=["implementer-1"],
                scope_contract=test_scope_contract(),
            )
            record_fixture_solution(root, record["run_id"])
            child_file.write_text("reviewed nested content\n", encoding="utf-8")
            record_check(
                root,
                record["run_id"],
                name="nested",
                command="git -C deps/child diff --check",
                status="passed",
                evidence="Nested candidate inspected",
                criteria=["AC1"],
                tier="full",
            )
            close_clean_review(root, record["run_id"])
            record_verdict(
                root,
                record["run_id"],
                reviewer="verifier-1",
                verdict="approve",
                criteria=["AC1"],
                evidence="Reviewed nested candidate",
            )
            child_file.write_text("changed after review\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "verifier verdict is stale"):
                finish_run(root, record["run_id"], "reported")

    def test_baseline_dirty_submodule_change_is_a_scope_delta(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, child_file = init_repository_with_submodule(Path(directory))
            child_file.write_text("dirty baseline\n", encoding="utf-8")
            start_test_run(root, write_paths=("artifact.txt",))
            child_file.write_text("changed during run\n", encoding="utf-8")
            approve_current(root)

            with self.assertRaisesRegex(ValueError, "writes outside declared scope: deps/child"):
                finish_run(root, "test-run", "reported")

    def test_untracked_embedded_repository_change_invalidates_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            nested_file = add_embedded_repository(root)
            record = start_run(
                root,
                "Change an embedded repository",
                "123",
                "embedded-run",
                acceptance_criteria=parse_criteria(["AC1=Embedded change is verified"]),
                declared_write_set=make_write_set(["vendor/nested"], []),
                implementers=["implementer-1"],
                scope_contract=test_scope_contract(),
            )
            record_fixture_solution(root, record["run_id"])
            nested_file.write_text("reviewed nested content\n", encoding="utf-8")
            record_check(
                root,
                record["run_id"],
                name="nested",
                command="git -C vendor/nested diff --check",
                status="passed",
                evidence="Embedded candidate inspected",
                criteria=["AC1"],
                tier="full",
            )
            close_clean_review(root, record["run_id"])
            record_verdict(
                root,
                record["run_id"],
                reviewer="verifier-1",
                verdict="approve",
                criteria=["AC1"],
                evidence="Reviewed embedded candidate",
            )
            nested_file.write_text("changed after review\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "verifier verdict is stale"):
                finish_run(root, record["run_id"], "reported")

    def test_baseline_embedded_repository_change_is_a_scope_delta(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            nested_file = add_embedded_repository(root)
            start_test_run(root, write_paths=("artifact.txt",))
            nested_file.write_text("changed during run\n", encoding="utf-8")
            approve_current(root)

            with self.assertRaisesRegex(ValueError, "writes outside declared scope: vendor/nested"):
                finish_run(root, "test-run", "reported")

    def test_submodule_ignore_all_cannot_hide_scope_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, child_file = init_repository_with_submodule(Path(directory))
            subprocess.run(
                ["git", "config", "-f", ".gitmodules", "submodule.deps/child.ignore", "all"],
                cwd=root,
                check=True,
            )
            subprocess.run(["git", "add", "--", ".gitmodules"], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-m", "ignore child status"],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            start_test_run(root, write_paths=("artifact.txt",))
            child_file.write_text("hidden by configuration\n", encoding="utf-8")
            approve_current(root)

            ordinary_status = subprocess.run(
                ["git", "status", "--short"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout
            self.assertNotIn("deps/child", ordinary_status)
            with self.assertRaisesRegex(ValueError, "writes outside declared scope: deps/child"):
                finish_run(root, "test-run", "reported")

    def test_preexisting_dirty_path_is_subtracted_from_run_delta(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = init_repository(root)
            tracked.write_text("pre-existing user work\n", encoding="utf-8")
            start_test_run(root, write_paths=("output.txt",))
            (root / "output.txt").write_text("task output\n", encoding="utf-8")
            approve_current(root)

            _, evidence_path, _ = finish_run(root, "test-run", "reported")
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            changed = [item["path"] for item in evidence["boundary"]["scope"]["delta"]]
            self.assertEqual(["output.txt"], changed)
            self.assertEqual([], evidence["boundary"]["scope"]["violations"])

    def test_untracked_write_outside_declared_scope_blocks_completion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = init_repository(root)
            start_test_run(root)
            tracked.write_text("accepted\n", encoding="utf-8")
            (root / "escape.txt").write_text("undeclared\n", encoding="utf-8")
            approve_current(root)

            with self.assertRaisesRegex(ValueError, "writes outside declared scope: escape.txt"):
                finish_run(root, "test-run", "reported")

    def test_untracked_symlink_to_directory_is_fingerprinted_without_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "outside-target"
            target.mkdir()
            (target / "outside.txt").write_text("outside\n", encoding="utf-8")
            root = base / "repository"
            root.mkdir()
            init_repository(root)
            (root / "linked-directory").symlink_to(target, target_is_directory=True)

            record = start_run(
                root,
                "Preserve an existing symlink",
                "123",
                "symlink-run",
                acceptance_criteria=parse_criteria(["AC1=Symlink baseline is captured"]),
                declared_write_set=[],
                implementers=["implementer-1"],
                scope_contract=test_scope_contract(),
            )

            entry = next(
                item for item in record["baseline"]["entries"] if item["path"] == "linked-directory"
            )
            self.assertEqual("symlink", entry["kind"])
            self.assertNotIn("outside.txt", json.dumps(entry))

    def test_committed_write_outside_declared_scope_blocks_completion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = init_repository(root)
            start_test_run(root)
            tracked.write_text("accepted\n", encoding="utf-8")
            (root / "escape.txt").write_text("undeclared\n", encoding="utf-8")
            subprocess.run(["git", "add", "--", "artifact.txt", "escape.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-m", "candidate"],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            approve_current(root)

            with self.assertRaisesRegex(ValueError, "writes outside declared scope: escape.txt"):
                finish_run(root, "test-run", "reported")

    def test_approval_without_criterion_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            close_clean_review(root, "test-run")

            with self.assertRaisesRegex(
                ValueError, "lacks passed check evidence for criteria: AC1"
            ):
                record_verdict(
                    root,
                    "test-run",
                    reviewer="verifier-1",
                    verdict="approve",
                    criteria=["AC1"],
                    evidence="Unsupported approval",
                )

    def test_implementer_cannot_record_independent_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            record_check(
                root,
                "test-run",
                name="unit",
                command="python3 -m unittest",
                status="passed",
                evidence="targeted unit boundary",
                criteria=["AC1"],
            )

            with self.assertRaisesRegex(ValueError, "recorded as an implementer"):
                record_verdict(
                    root,
                    "test-run",
                    reviewer="implementer-1",
                    verdict="approve",
                    criteria=["AC1"],
                    evidence="Self approval",
                )

    def test_run_requires_an_implementer_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            with self.assertRaisesRegex(ValueError, "implementer identity"):
                start_run(
                    root,
                    "Unowned change",
                    None,
                    "unowned-run",
                    acceptance_criteria=parse_criteria(["AC1=Change is complete"]),
                    declared_write_set=[],
                    scope_contract=test_scope_contract(),
                )

    def test_criterion_waiver_requires_human_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            with self.assertRaisesRegex(ValueError, "human:IDENTITY"):
                waive_criterion(
                    root,
                    "test-run",
                    "AC1",
                    waived_by="implementer-1",
                    reason="Agent attempted waiver",
                )

    def test_human_waiver_can_satisfy_a_criterion_without_a_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            waive_criterion(
                root,
                "test-run",
                "AC1",
                waived_by="human:owner",
                reason="Owner accepted this boundary as out of scope",
            )
            record_check(
                root,
                "test-run",
                name="full",
                command="python3 -m unittest",
                status="passed",
                evidence="complete final gate",
                criteria=[],
                tier="full",
            )
            close_clean_review(root, "test-run")
            record_verdict(
                root,
                "test-run",
                reviewer="verifier-1",
                verdict="approve",
                criteria=[],
                evidence="Confirmed the explicit owner waiver and unchanged candidate",
            )
            _, _, finished = finish_run(root, "test-run", "reported")
            self.assertEqual("reported", finished["state"])

    def test_reported_completion_requires_current_release_impact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_run(
                root,
                "Change the artifact",
                "123",
                "impact-run",
                acceptance_criteria=parse_criteria(["AC1=Artifact is accepted"]),
                declared_write_set=make_write_set(["artifact.txt"], []),
                implementers=["implementer-1"],
                scope_contract=test_scope_contract(),
            )
            record_fixture_solution(root, "impact-run")
            record_check(
                root,
                "impact-run",
                name="unit",
                command="python3 -m unittest",
                status="passed",
                evidence="targeted boundary",
                criteria=["AC1"],
                tier="full",
            )
            close_clean_review(root, "impact-run")
            record_verdict(
                root,
                "impact-run",
                reviewer="verifier-1",
                verdict="approve",
                criteria=["AC1"],
                evidence="Reviewed the unchanged fixture",
            )
            with self.assertRaisesRegex(ValueError, "product release impact is not assessed"):
                finish_run(root, "impact-run", "reported")

    def test_revision_invalidates_prior_checks_and_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = init_repository(root)
            start_test_run(root)
            tracked.write_text("reviewed\n", encoding="utf-8")
            approve_current(root)
            revise_run(
                root,
                "test-run",
                reason="Acceptance wording changed",
                objective="Revised test objective",
            )

            with self.assertRaisesRegex(ValueError, "current revision and attempt"):
                finish_run(root, "test-run", "reported")

    def test_revision_invalidates_prior_human_waiver(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            waive_criterion(
                root,
                "test-run",
                "AC1",
                waived_by="human:owner",
                reason="Waived only for revision one",
            )
            revise_run(
                root, "test-run", reason="Objective contract changed", objective="New objective"
            )

            with self.assertRaisesRegex(ValueError, "criteria lack current passed checks: AC1"):
                finish_run(root, "test-run", "reported")

    def test_review_collects_one_deduplicated_batch_before_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            cycle = start_review(root, "test-run", reviewer="verifier-1")
            finding = {
                "review_id": cycle["review_id"],
                "severity": "high",
                "title": "Completion gate can be bypassed",
                "criterion": "AC1",
                "reproduction": "Run the bounded bypass fixture",
                "minimum_repair": "Fail closed and add the fixture as a regression",
            }
            record_finding(root, "test-run", **finding)
            with self.assertRaisesRegex(ValueError, "duplicate review finding"):
                record_finding(root, "test-run", **finding)
            with self.assertRaisesRegex(ValueError, "review cycle is open"):
                new_attempt(root, "test-run", "repair finding batch")
            with self.assertRaisesRegex(ValueError, "review cycle is open"):
                revise_run(root, "test-run", reason="change contract too early")

            closed = close_review(
                root,
                "test-run",
                review_id=cycle["review_id"],
                outcome="batch-ready",
                summary="One deduplicated repair batch",
            )
            self.assertEqual(1, len(closed["findings"]))
            record_verdict(
                root,
                "test-run",
                reviewer="verifier-1",
                verdict="revise",
                criteria=["AC1"],
                evidence="Bounded finding batch",
            )
            finding_id = closed["findings"][0]["finding_id"]
            with self.assertRaisesRegex(ValueError, "finding dispositions"):
                new_attempt(root, "test-run", "repair finding batch")
            record_finding_disposition(
                root,
                "test-run",
                review_id=cycle["review_id"],
                finding_id=finding_id,
                disposition="repair-in-scope",
                rationale="The failure is inside AC1",
                decided_by="orchestrator-1",
            )
            with self.assertRaisesRegex(ValueError, "proportionality review"):
                new_attempt(root, "test-run", "repair finding batch")
            record_proportionality_review(
                root,
                "test-run",
                review_id=cycle["review_id"],
                reviewed_by="orchestrator-1",
                objective_alignment="The repair directly restores AC1",
                scope_change="within-contract",
                complexity_change="bounded",
                budget_status="on-budget",
                triggers=[],
                alternatives=["Narrow the claim"],
                recommendation="proceed",
                solution_disposition="adapt",
                rationale="Reuse the existing completion guard",
            )
            self.assertEqual(2, new_attempt(root, "test-run", "repair finding batch")["attempt_id"])

    def test_finding_batch_blocks_second_review_and_late_repair_transition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = init_repository(root)
            start_test_run(root)
            cycle = start_review(root, "test-run", reviewer="verifier-1")
            record_finding(
                root,
                "test-run",
                review_id=cycle["review_id"],
                severity="high",
                title="Completion bypass",
                criterion="AC1",
                reproduction="Open a second review without repairing the first batch",
                minimum_repair="Require the finding-batch transition before another review",
            )
            closed = close_review(
                root,
                "test-run",
                review_id=cycle["review_id"],
                outcome="batch-ready",
                summary="One repair batch",
            )

            with self.assertRaisesRegex(ValueError, "requires a repair attempt"):
                start_review(root, "test-run", reviewer="verifier-1")
            with self.assertRaisesRegex(ValueError, "matching revise or reject verdict"):
                new_attempt(root, "test-run", "repair without a decision")

            record_verdict(
                root,
                "test-run",
                reviewer="verifier-1",
                verdict="revise",
                criteria=["AC1"],
                evidence="The bounded finding batch requires repair",
            )
            disposition_review_batch(
                root,
                "test-run",
                cycle["review_id"],
                closed["findings"][0]["finding_id"],
            )
            with self.assertRaisesRegex(ValueError, "requires a repair attempt"):
                start_review(root, "test-run", reviewer="verifier-1")
            tracked.write_text("mutated before transition\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "changed before the repair attempt"):
                new_attempt(root, "test-run", "late repair decision")
            tracked.write_text("before\n", encoding="utf-8")
            self.assertEqual(
                2,
                new_attempt(root, "test-run", "repair the reviewed finding batch")["attempt_id"],
            )

    def test_contract_revision_requires_a_delta_and_resolves_finding_batch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = init_repository(root)
            start_test_run(root)
            with self.assertRaisesRegex(ValueError, "contract revision must change"):
                revise_run(root, "test-run", reason="Nominal revision only")

            cycle = start_review(root, "test-run", reviewer="verifier-1")
            record_finding(
                root,
                "test-run",
                review_id=cycle["review_id"],
                severity="high",
                title="Revision escape",
                criterion="AC1",
                reproduction="Increment the revision without resolving the batch",
                minimum_repair="Bind revision transitions to the finding decision",
            )
            closed = close_review(
                root,
                "test-run",
                review_id=cycle["review_id"],
                outcome="batch-ready",
                summary="Revision escape requires repair",
            )
            with self.assertRaisesRegex(ValueError, "matching revise or reject verdict"):
                revise_run(
                    root,
                    "test-run",
                    reason="Genuine but unauthorized contract change",
                    objective="Changed before decision",
                )

            record_verdict(
                root,
                "test-run",
                reviewer="verifier-1",
                verdict="revise",
                criteria=["AC1"],
                evidence="Revise the reviewed contract",
            )
            disposition_review_batch(
                root,
                "test-run",
                cycle["review_id"],
                closed["findings"][0]["finding_id"],
                triggers=("threat-model-expansion",),
                reviewed_by="scope-reviewer-1",
                scope_change="expands-contract",
                complexity_change="material",
                recommendation="revise-contract",
                finding_disposition="revise-contract",
            )
            tracked.write_text("candidate drift\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "changed before the repair attempt"):
                revise_run(
                    root,
                    "test-run",
                    reason="Late contract repair",
                    objective="Changed after candidate drift",
                )
            tracked.write_text("before\n", encoding="utf-8")
            revised = revise_run(
                root,
                "test-run",
                reason="Reviewed contract repair",
                objective="Changed after reviewed decision",
            )
            self.assertEqual(2, revised["revision"])
            self.assertEqual(
                "review-002",
                start_review(root, "test-run", reviewer="verifier-1")["review_id"],
            )

    def test_blocked_report_does_not_count_stale_candidate_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = init_repository(root)
            start_test_run(root)
            record_check(
                root,
                "test-run",
                name="old candidate",
                command="python3 -m unittest old",
                status="passed",
                evidence="Passed before candidate mutation",
                criteria=["AC1"],
            )
            tracked.write_text("changed after check\n", encoding="utf-8")

            report_path, _, _ = finish_run(root, "test-run", "blocked")
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("| AC1 | missing |", report)
            self.assertNotIn("| AC1 | check-passed |", report)

    def test_non_emergency_review_fails_if_candidate_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = init_repository(root)
            start_test_run(root)
            cycle = start_review(root, "test-run", reviewer="verifier-1")
            tracked.write_text("changed during review\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "review candidate changed"):
                close_review(
                    root,
                    "test-run",
                    review_id=cycle["review_id"],
                    outcome="clean",
                    summary="Incorrectly clean",
                )

    def test_critical_emergency_can_stop_review_after_candidate_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = init_repository(root)
            start_test_run(root)
            cycle = start_review(root, "test-run", reviewer="verifier-1")
            tracked.write_text("removed exposed value\n", encoding="utf-8")
            record_finding(
                root,
                "test-run",
                review_id=cycle["review_id"],
                severity="critical",
                title="Active credential exposure",
                criterion="AC1",
                reproduction="A bounded secret scanner identified an active value",
                minimum_repair="Revoke and remove the value before continuing",
                emergency_boundary="secret-exposure",
            )
            closed = close_review(
                root,
                "test-run",
                review_id=cycle["review_id"],
                outcome="emergency-stop",
                summary="Stopped immediately to contain active exposure",
            )
            self.assertTrue(closed["candidate_changed"])

    def test_critical_emergency_cannot_be_downgraded_to_an_ordinary_batch(self) -> None:
        for boundary in (
            "secret-exposure",
            "destructive-effect",
            "uncontrolled-external-effect",
        ):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                init_repository(root)
                start_test_run(root)
                cycle = start_review(root, "test-run", reviewer="verifier-1")
                record_finding(
                    root,
                    "test-run",
                    review_id=cycle["review_id"],
                    severity="critical",
                    title=f"Critical {boundary}",
                    criterion="AC1",
                    reproduction="Exercise the declared emergency boundary",
                    minimum_repair="Stop the review immediately",
                    emergency_boundary=boundary,
                )
                with self.assertRaisesRegex(ValueError, "requires an emergency stop"):
                    close_review(
                        root,
                        "test-run",
                        review_id=cycle["review_id"],
                        outcome="batch-ready",
                        summary="Incorrect ordinary batch",
                    )

    def test_reused_evidence_requires_immutable_provenance_and_cannot_be_full_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            digest = "sha256:" + "a" * 64
            with self.assertRaisesRegex(ValueError, "requires an immutable sha256"):
                record_check(
                    root,
                    "test-run",
                    name="model evaluation",
                    command="reuse retained result",
                    status="passed",
                    evidence="retained result",
                    criteria=["AC1"],
                    tier="external",
                    evidence_origin="reused",
                    reuse_source="result.json",
                    applicability="model-visible resources are unchanged",
                )
            record = record_check(
                root,
                "test-run",
                name="model evaluation",
                command="reuse retained result",
                status="passed",
                evidence="retained result",
                criteria=["AC1"],
                tier="external",
                duration_seconds=0.25,
                evidence_origin="reused",
                reuse_source="result.json",
                artifact_digest=digest,
                applicability="model-visible resources and oracle are unchanged",
            )
            self.assertEqual("reused", record["checks"][-1]["evidence_origin"])
            with self.assertRaisesRegex(ValueError, "final full gate must be executed"):
                record_check(
                    root,
                    "test-run",
                    name="full",
                    command="make smoke",
                    status="passed",
                    evidence="reused full result",
                    tier="full",
                    evidence_origin="reused",
                    reuse_source="result.json",
                    artifact_digest=digest,
                    applicability="unchanged",
                )

    def test_reported_completion_requires_exactly_one_executed_full_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            record_check(
                root,
                "test-run",
                name="targeted",
                command="python3 -m unittest tests.test_loop",
                status="passed",
                evidence="criterion passes without complete gate",
                criteria=["AC1"],
                tier="targeted",
            )
            close_clean_review(root, "test-run")
            record_verdict(
                root,
                "test-run",
                reviewer="verifier-1",
                verdict="approve",
                criteria=["AC1"],
                evidence="Reviewed targeted evidence",
            )
            with self.assertRaisesRegex(ValueError, "exactly one current-attempt full gate"):
                finish_run(root, "test-run", "reported")

    def test_later_finding_batch_invalidates_earlier_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            approve_current(root)
            cycle = start_review(root, "test-run", reviewer="verifier-1")
            record_finding(
                root,
                "test-run",
                review_id=cycle["review_id"],
                severity="high",
                title="Later review found a bypass",
                criterion="AC1",
                reproduction="Run the later bounded review fixture",
                minimum_repair="Bind approval to the latest review",
            )
            close_review(
                root,
                "test-run",
                review_id=cycle["review_id"],
                outcome="batch-ready",
                summary="Later finding batch",
            )

            with self.assertRaisesRegex(ValueError, "latest independent review is not clean"):
                finish_run(root, "test-run", "reported")

    def test_full_gate_is_stale_after_candidate_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = init_repository(root)
            start_test_run(root)
            record_check(
                root,
                "test-run",
                name="full",
                command="make smoke",
                status="passed",
                evidence="complete gate before mutation",
                criteria=["AC1"],
                tier="full",
            )
            tracked.write_text("changed after full gate\n", encoding="utf-8")
            record_check(
                root,
                "test-run",
                name="current targeted",
                command="python3 -m unittest current-targeted",
                status="passed",
                evidence="AC1 passes on the changed candidate but the full gate is stale",
                criteria=["AC1"],
                tier="targeted",
            )
            close_clean_review(root, "test-run")
            record_verdict(
                root,
                "test-run",
                reviewer="verifier-1",
                verdict="approve",
                criteria=["AC1"],
                evidence="Reviewed changed candidate",
            )

            with self.assertRaisesRegex(ValueError, "full gate is stale"):
                finish_run(root, "test-run", "reported")

    def test_criterion_evidence_is_stale_after_candidate_changes(self) -> None:
        for evidence_origin in ("executed", "reused"):
            with (
                self.subTest(evidence_origin=evidence_origin),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                tracked = init_repository(root)
                start_test_run(root)
                kwargs = {}
                if evidence_origin == "reused":
                    kwargs = {
                        "reuse_source": "retained-result.json",
                        "artifact_digest": "sha256:" + "a" * 64,
                        "applicability": "The candidate was unchanged when evidence was recorded",
                    }
                record_check(
                    root,
                    "test-run",
                    name="criterion evidence",
                    command="run targeted evidence",
                    status="passed",
                    evidence="AC1 passed for the earlier candidate",
                    criteria=["AC1"],
                    tier="targeted" if evidence_origin == "executed" else "external",
                    evidence_origin=evidence_origin,
                    **kwargs,
                )
                tracked.write_text("changed after criterion evidence\n", encoding="utf-8")
                record_check(
                    root,
                    "test-run",
                    name="full",
                    command="make smoke",
                    status="passed",
                    evidence="Current full gate intentionally has no criterion link",
                    tier="full",
                )
                close_clean_review(root, "test-run")
                with self.assertRaisesRegex(ValueError, "lacks passed check evidence"):
                    record_verdict(
                        root,
                        "test-run",
                        reviewer="verifier-1",
                        verdict="approve",
                        criteria=["AC1"],
                        evidence="The stale criterion result must not count",
                    )

    def test_documentation_only_impact_classifier_is_fail_closed(self) -> None:
        contract = (
            ROOT / ".agents/skills/execute-engineering-loop/references/verification-efficiency.md"
        ).read_text(encoding="utf-8")
        self.assertIn("## Documentation-only impact classifier", contract)
        self.assertIn("Ambiguous changes are behavior-affecting", contract)
        self.assertIn("The final full gate remains mandatory", contract)

    def test_scope_contract_requires_explicit_boundaries(self) -> None:
        with self.assertRaisesRegex(ValueError, "out-of-scope"):
            make_scope_contract(
                in_scope=["One bounded change"],
                out_of_scope=[],
                assurance_boundary="One repository",
                budget_constraints=["No new subsystem"],
                revision_triggers=["New dependency"],
            )
        with self.assertRaisesRegex(ValueError, "budget constraints"):
            make_scope_contract(
                in_scope=["One bounded change"],
                out_of_scope=["Deployment"],
                assurance_boundary="One repository",
                budget_constraints=[],
                revision_triggers=["New dependency"],
            )

    def test_solution_assessment_is_required_before_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_run(
                root,
                "Change the artifact",
                "123",
                "solution-run",
                acceptance_criteria=parse_criteria(["AC1=Artifact is accepted"]),
                declared_write_set=make_write_set(["artifact.txt"], []),
                implementers=["implementer-1"],
                scope_contract=test_scope_contract(),
            )
            loop_path = root / "harness/loops/engineering-loop.yaml"
            loop_path.parent.mkdir(parents=True)
            loop_path.write_bytes((ROOT / "harness/loops/engineering-loop.yaml").read_bytes())
            with self.assertRaisesRegex(ValueError, "solution assessment"):
                set_state(root, "solution-run", "plan")
            with self.assertRaisesRegex(ValueError, "at least one source"):
                record_solution_assessment(
                    root,
                    "solution-run",
                    trigger="initial",
                    disposition="adopt",
                    research_status="completed",
                    rationale="A maintained dependency appears suitable",
                    sources=[],
                )
            record_solution_assessment(
                root,
                "solution-run",
                trigger="initial",
                disposition="adapt",
                research_status="completed",
                rationale="Reuse the current loop and native Issue forms",
                sources=["https://docs.github.com/issue-forms"],
            )
            self.assertEqual("plan", set_state(root, "solution-run", "plan")["state"])

    def test_blocked_solution_assessment_can_be_resolved_without_losing_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_run(
                root,
                "Change the artifact",
                "123",
                "blocked-solution-run",
                acceptance_criteria=parse_criteria(["AC1=Artifact is accepted"]),
                declared_write_set=make_write_set(["artifact.txt"], []),
                implementers=["implementer-1"],
                scope_contract=test_scope_contract(),
            )
            loop_path = root / "harness/loops/engineering-loop.yaml"
            loop_path.parent.mkdir(parents=True)
            loop_path.write_bytes((ROOT / "harness/loops/engineering-loop.yaml").read_bytes())
            record_solution_assessment(
                root,
                "blocked-solution-run",
                trigger="initial",
                disposition="defer",
                research_status="blocked",
                rationale="Authoritative dependency evidence is unavailable.",
                sources=[],
            )
            with self.assertRaisesRegex(ValueError, "blocked existing-solution research"):
                set_state(root, "blocked-solution-run", "plan")
            with self.assertRaisesRegex(ValueError, "only by completed research"):
                record_solution_assessment(
                    root,
                    "blocked-solution-run",
                    trigger="initial",
                    disposition="build",
                    research_status="not-material",
                    rationale="A blocked evidence gap cannot become immaterial by assertion.",
                    sources=[],
                )
            resolved = record_solution_assessment(
                root,
                "blocked-solution-run",
                trigger="initial",
                disposition="adapt",
                research_status="completed",
                rationale="Owner input resolved the prior evidence gap.",
                sources=["https://example.com/resolved"],
            )
            first, second = resolved["solution_assessments"]
            self.assertEqual(second["assessment_id"], first["superseded_by"])
            self.assertEqual(first["assessment_id"], second["supersedes"])
            self.assertEqual("plan", set_state(root, "blocked-solution-run", "plan")["state"])
            with self.assertRaisesRegex(ValueError, "already exists"):
                record_solution_assessment(
                    root,
                    "blocked-solution-run",
                    trigger="initial",
                    disposition="build",
                    research_status="not-material",
                    rationale="A second active assessment is ambiguous.",
                    sources=[],
                )

    def test_stale_completed_solution_assessment_can_be_refreshed_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            first_record = record_solution_assessment(
                root,
                "test-run",
                trigger="protocol",
                disposition="adapt",
                research_status="completed",
                rationale="The first candidate uses the existing protocol.",
                sources=["https://example.com/protocol-v1"],
            )
            first = first_record["solution_assessments"][-1]
            new_attempt(root, "test-run", "candidate repair changes the bound identity")
            refreshed_record = record_solution_assessment(
                root,
                "test-run",
                trigger="protocol",
                disposition="adapt",
                research_status="completed",
                rationale="The repaired candidate was reassessed against the protocol.",
                sources=["https://example.com/protocol-v2"],
            )
            refreshed = refreshed_record["solution_assessments"][-1]
            self.assertEqual(
                refreshed["assessment_id"],
                refreshed_record["solution_assessments"][-2]["superseded_by"],
            )
            self.assertEqual(first["assessment_id"], refreshed["supersedes"])
            self.assertNotEqual(first["candidate"], refreshed["candidate"])
            with self.assertRaisesRegex(ValueError, "current candidate"):
                record_solution_assessment(
                    root,
                    "test-run",
                    trigger="protocol",
                    disposition="adapt",
                    research_status="completed",
                    rationale="A duplicate current-candidate assessment is ambiguous.",
                    sources=["https://example.com/protocol-v3"],
                )

    def test_complexity_trigger_requires_independent_scope_reviewer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            cycle = start_review(root, "test-run", reviewer="verifier-1")
            record_finding(
                root,
                "test-run",
                review_id=cycle["review_id"],
                severity="high",
                title="Repair proposes a bespoke parser",
                criterion="AC1",
                reproduction="The minimum repair crosses a parser boundary",
                minimum_repair="Reassess build, adopt, adapt, or defer",
            )
            closed = close_review(
                root,
                "test-run",
                review_id=cycle["review_id"],
                outcome="batch-ready",
                summary="One complexity-triggering finding",
            )
            record_verdict(
                root,
                "test-run",
                reviewer="verifier-1",
                verdict="revise",
                criteria=["AC1"],
                evidence="The parser boundary needs disposition",
            )
            record_finding_disposition(
                root,
                "test-run",
                review_id=cycle["review_id"],
                finding_id=closed["findings"][0]["finding_id"],
                disposition="simplify",
                rationale="Use a narrower existing contract",
                decided_by="orchestrator-1",
            )
            missing_assessment_kwargs = {
                "review_id": cycle["review_id"],
                "reviewed_by": "scope-reviewer-1",
                "objective_alignment": "The simplified repair still satisfies AC1",
                "scope_change": "within-contract",
                "complexity_change": "reduced",
                "budget_status": "at-risk",
                "triggers": ["new-parser"],
                "alternatives": ["Adopt a maintained parser", "Narrow the claim"],
                "recommendation": "simplify",
                "solution_disposition": "adapt",
                "rationale": "Do not create a general parser",
            }
            with self.assertRaisesRegex(ValueError, "completed solution assessments"):
                record_proportionality_review(root, "test-run", **missing_assessment_kwargs)
            with self.assertRaisesRegex(ValueError, "completed or blocked research"):
                record_solution_assessment(
                    root,
                    "test-run",
                    trigger="new-parser",
                    disposition="build",
                    research_status="not-material",
                    rationale="A parser trigger cannot skip the research checkpoint",
                    sources=[],
                )
            record_solution_assessment(
                root,
                "test-run",
                trigger="new-parser",
                disposition="defer",
                research_status="blocked",
                rationale="Parser research is temporarily blocked",
                sources=[],
            )
            with self.assertRaisesRegex(ValueError, "completed solution assessments"):
                record_proportionality_review(root, "test-run", **missing_assessment_kwargs)
            record_solution_assessment(
                root,
                "test-run",
                trigger="new-parser",
                disposition="adapt",
                research_status="completed",
                rationale="Reassess the parser boundary before repair",
                sources=["https://example.com/parser"],
            )
            kwargs = {
                "review_id": cycle["review_id"],
                "objective_alignment": "The simplified repair still satisfies AC1",
                "scope_change": "within-contract",
                "complexity_change": "reduced",
                "budget_status": "at-risk",
                "triggers": ["new-parser"],
                "alternatives": ["Adopt a maintained parser", "Narrow the claim"],
                "recommendation": "simplify",
                "solution_disposition": "adapt",
                "rationale": "Do not create a general parser",
            }
            with self.assertRaisesRegex(ValueError, "independent scope reviewer"):
                record_proportionality_review(
                    root, "test-run", reviewed_by="implementer-1", **kwargs
                )
            with self.assertRaisesRegex(ValueError, "technical reviewer"):
                record_proportionality_review(root, "test-run", reviewed_by="verifier-1", **kwargs)
            record_proportionality_review(
                root, "test-run", reviewed_by="scope-reviewer-1", **kwargs
            )
            self.assertEqual(
                2,
                new_attempt(root, "test-run", "simplified bounded repair")["attempt_id"],
            )

    def test_every_finding_disposition_has_an_explicit_transition(self) -> None:
        cases = {
            "repair-in-scope": ("proceed", "attempt"),
            "simplify": ("simplify", "attempt"),
            "narrow-claim": ("simplify", "attempt"),
            "defer": ("defer", "resolve"),
            "accept-risk": ("proceed", "resolve"),
            "revise-contract": ("revise-contract", "revision"),
            "emergency-stop": ("escalate-to-owner", "resolve"),
        }
        for disposition, (recommendation, transition) in cases.items():
            with self.subTest(disposition=disposition), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                init_repository(root)
                start_test_run(root)
                cycle = start_review(root, "test-run", reviewer="verifier-1")
                emergency = disposition == "emergency-stop"
                record_finding(
                    root,
                    "test-run",
                    review_id=cycle["review_id"],
                    severity="critical" if emergency else "medium",
                    title=f"Exercise {disposition}",
                    criterion="AC1",
                    reproduction="The bounded test selects one documented disposition",
                    minimum_repair="Use the documented transition",
                    emergency_boundary="destructive-effect" if emergency else None,
                )
                closed = close_review(
                    root,
                    "test-run",
                    review_id=cycle["review_id"],
                    outcome="emergency-stop" if emergency else "batch-ready",
                    summary="One disposition transition",
                )
                record_verdict(
                    root,
                    "test-run",
                    reviewer="verifier-1",
                    verdict="reject" if emergency else "revise",
                    criteria=["AC1"],
                    evidence="Exercise the complete transition table",
                )
                record_finding_disposition(
                    root,
                    "test-run",
                    review_id=cycle["review_id"],
                    finding_id=closed["findings"][0]["finding_id"],
                    disposition=disposition,
                    rationale="The test binds the selected transition",
                    decided_by=(
                        "human:owner" if disposition == "accept-risk" else "orchestrator-1"
                    ),
                )
                record_proportionality_review(
                    root,
                    "test-run",
                    review_id=cycle["review_id"],
                    reviewed_by="orchestrator-1",
                    objective_alignment="The transition preserves explicit disposition semantics",
                    scope_change="within-contract",
                    complexity_change="bounded",
                    budget_status="on-budget",
                    triggers=[],
                    alternatives=["Repair", "Defer"],
                    recommendation=recommendation,
                    solution_disposition="adapt",
                    rationale="Use only the bounded transition table",
                )
                if transition == "attempt":
                    with self.assertRaisesRegex(ValueError, "require repair or contract revision"):
                        resolve_finding_batch(
                            root,
                            "test-run",
                            review_id=cycle["review_id"],
                            resolved_by="orchestrator-1",
                            rationale="A mutating repair cannot use no-code resolution",
                        )
                    self.assertEqual(
                        2,
                        new_attempt(root, "test-run", "bounded repair")["attempt_id"],
                    )
                elif transition == "revision":
                    with self.assertRaisesRegex(
                        ValueError, "implementation attempt|contract revision"
                    ):
                        new_attempt(root, "test-run", "incorrect implementation retry")
                    self.assertEqual(
                        2,
                        revise_run(
                            root,
                            "test-run",
                            reason="reviewed contract change",
                            objective="Revised accepted objective",
                        )["revision"],
                    )
                else:
                    with self.assertRaisesRegex(
                        ValueError,
                        "no-code finding batch|implementation attempt|contract revision, deferral, or escalation",
                    ):
                        new_attempt(root, "test-run", "incorrect no-code retry")
                    if disposition == "accept-risk":
                        result = subprocess.run(
                            [
                                sys.executable,
                                str(ROOT / "tools/loop.py"),
                                "--root",
                                str(root),
                                "resolve-finding-batch",
                                "--run",
                                "test-run",
                                "--review",
                                cycle["review_id"],
                                "--by",
                                "orchestrator-1",
                                "--rationale",
                                "No candidate mutation is authorized or required",
                            ],
                            check=True,
                            capture_output=True,
                            text=True,
                        )
                        self.assertIn("resolved finding batch", result.stdout)
                        _, resolved = load_run(root, "test-run")
                    else:
                        resolved = resolve_finding_batch(
                            root,
                            "test-run",
                            review_id=cycle["review_id"],
                            resolved_by="orchestrator-1",
                            rationale="No candidate mutation is authorized or required",
                        )
                    self.assertIsNotNone(resolved["review_cycles"][-1]["resolution"])
                    if emergency:
                        with self.assertRaisesRegex(ValueError, "emergency-stopped attempt"):
                            start_review(root, "test-run", reviewer="verifier-1")
                        self.assertEqual(
                            2,
                            new_attempt(root, "test-run", "repair after emergency stop")[
                                "attempt_id"
                            ],
                        )
                    else:
                        self.assertEqual(
                            "review-002",
                            start_review(root, "test-run", reviewer="verifier-1")["review_id"],
                        )

    def test_mixed_emergency_batches_preserve_dispositions_and_next_transition(self) -> None:
        cases = {
            "repair-in-scope": "new-attempt",
            "defer": "new-attempt",
            "revise-contract": "contract-revision",
        }
        for ordinary_disposition, expected in cases.items():
            with (
                self.subTest(disposition=ordinary_disposition),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                init_repository(root)
                start_test_run(root)
                cycle = start_review(root, "test-run", reviewer="verifier-1")
                record_finding(
                    root,
                    "test-run",
                    review_id=cycle["review_id"],
                    severity="medium",
                    title="Ordinary finding",
                    criterion="AC1",
                    reproduction="The batch contains a non-emergency disposition.",
                    minimum_repair="Preserve this disposition alongside the emergency.",
                )
                record_finding(
                    root,
                    "test-run",
                    review_id=cycle["review_id"],
                    severity="critical",
                    title="Emergency finding",
                    criterion="AC1",
                    reproduction="The same batch crosses a destructive-effect boundary.",
                    minimum_repair="Stop and require the deterministic owner-authorized transition.",
                    emergency_boundary="destructive-effect",
                )
                closed = close_review(
                    root,
                    "test-run",
                    review_id=cycle["review_id"],
                    outcome="emergency-stop",
                    summary="Mixed ordinary and emergency findings",
                )
                record_verdict(
                    root,
                    "test-run",
                    reviewer="verifier-1",
                    verdict="reject",
                    criteria=["AC1"],
                    evidence="The emergency batch requires owner escalation.",
                )
                record_finding_disposition(
                    root,
                    "test-run",
                    review_id=cycle["review_id"],
                    finding_id=closed["findings"][0]["finding_id"],
                    disposition=ordinary_disposition,
                    rationale="Preserve the ordinary finding's selected disposition.",
                    decided_by="orchestrator-1",
                )
                record_finding_disposition(
                    root,
                    "test-run",
                    review_id=cycle["review_id"],
                    finding_id=closed["findings"][1]["finding_id"],
                    disposition="emergency-stop",
                    rationale="The critical boundary requires owner escalation.",
                    decided_by="orchestrator-1",
                )
                record_proportionality_review(
                    root,
                    "test-run",
                    review_id=cycle["review_id"],
                    reviewed_by="scope-reviewer-1",
                    objective_alignment="Resolve the mixed batch without discarding either finding.",
                    scope_change="within-contract",
                    complexity_change="bounded",
                    budget_status="on-budget",
                    triggers=[],
                    alternatives=["Discard the ordinary finding", "Preserve both dispositions"],
                    recommendation="escalate-to-owner",
                    solution_disposition="adapt",
                    rationale="Use only an existing attempt or contract-revision transition.",
                )
                resolved = resolve_finding_batch(
                    root,
                    "test-run",
                    review_id=cycle["review_id"],
                    resolved_by="human:owner",
                    rationale="Authorize the deterministic transition while preserving the batch.",
                )
                resolution = resolved["review_cycles"][-1]["resolution"]
                self.assertEqual("emergency-stopped", resolution["decision"])
                self.assertEqual(expected, resolution["next_transition"])
                self.assertEqual(
                    {ordinary_disposition, "emergency-stop"},
                    {
                        finding["disposition"]["decision"]
                        for finding in resolved["review_cycles"][-1]["findings"]
                    },
                )
                if expected == "new-attempt":
                    with self.assertRaisesRegex(ValueError, "requires a new attempt"):
                        revise_run(
                            root,
                            "test-run",
                            reason="wrong transition",
                            objective="Wrong contract revision",
                        )
                    self.assertEqual(
                        2, new_attempt(root, "test-run", "contain emergency")["attempt_id"]
                    )
                else:
                    with self.assertRaisesRegex(ValueError, "requires a contract revision"):
                        new_attempt(root, "test-run", "wrong transition")
                    self.assertEqual(
                        2,
                        revise_run(
                            root,
                            "test-run",
                            reason="authorized contract revision",
                            objective="Revised objective after emergency",
                        )["revision"],
                    )

    def test_scope_expansion_cannot_be_dispositioned_as_proceed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            cycle = start_review(root, "test-run", reviewer="verifier-1")
            record_finding(
                root,
                "test-run",
                review_id=cycle["review_id"],
                severity="medium",
                title="Threat model would expand",
                criterion="AC1",
                reproduction="The proposed repair adds a new hostile actor",
                minimum_repair="Revise or defer the contract",
            )
            closed = close_review(
                root,
                "test-run",
                review_id=cycle["review_id"],
                outcome="batch-ready",
                summary="Scope decision required",
            )
            record_verdict(
                root,
                "test-run",
                reviewer="verifier-1",
                verdict="revise",
                criteria=["AC1"],
                evidence="The accepted threat model does not include this actor",
            )
            record_finding_disposition(
                root,
                "test-run",
                review_id=cycle["review_id"],
                finding_id=closed["findings"][0]["finding_id"],
                disposition="revise-contract",
                rationale="The owner must decide whether to expand the threat model",
                decided_by="orchestrator-1",
            )
            record_solution_assessment(
                root,
                "test-run",
                trigger="threat-model-expansion",
                disposition="defer",
                research_status="completed",
                rationale="Reassess the expanded threat boundary",
                sources=["https://example.com/threat-model"],
            )
            with self.assertRaisesRegex(ValueError, "cannot proceed"):
                record_proportionality_review(
                    root,
                    "test-run",
                    review_id=cycle["review_id"],
                    reviewed_by="scope-reviewer-1",
                    objective_alignment="The finding is adjacent to AC1",
                    scope_change="expands-contract",
                    complexity_change="material",
                    budget_status="exceeded",
                    triggers=["threat-model-expansion"],
                    alternatives=["Defer to a new Issue"],
                    recommendation="proceed",
                    solution_disposition="build",
                    rationale="Incorrectly continue the broader design",
                )

    def test_schema_14_requires_scope_and_governance_records(self) -> None:
        schema = json.loads((ROOT / "harness/schemas/loop-run.schema.json").read_text())
        self.assertEqual("1.4", schema["properties"]["schema_version"]["const"])
        for field in ("scope_contract", "solution_assessments"):
            self.assertIn(field, schema["required"])
        review = schema["$defs"]["reviewCycle"]
        self.assertIn("proportionality", review["required"])
        self.assertIn("resolution", review["required"])
        finding = schema["$defs"]["finding"]
        self.assertIn("disposition", finding["required"])
        assessment = schema["$defs"]["solutionAssessment"]
        self.assertIn("supersedes", assessment["required"])
        self.assertIn("superseded_by", assessment["required"])
        resolution = schema["$defs"]["findingBatchResolution"]
        self.assertIn("next_transition", resolution["required"])
        self.assertEqual(
            ["none", "new-attempt", "contract-revision"],
            resolution["properties"]["next_transition"]["enum"],
        )

    def test_schema_encodes_reused_evidence_invariants(self) -> None:
        schema = json.loads((ROOT / "harness/schemas/loop-run.schema.json").read_text())
        conditional = schema["$defs"]["check"]["allOf"][0]

        self.assertEqual("reused", conditional["if"]["properties"]["evidence_origin"]["const"])
        self.assertEqual(
            {"not": {"const": "full"}},
            conditional["then"]["properties"]["tier"],
        )
        for field in ("reuse_source", "artifact_digest", "applicability"):
            self.assertEqual("string", conditional["then"]["properties"][field]["type"])
            self.assertEqual({"const": None}, conditional["else"]["properties"][field])

    def test_report_distinguishes_contract_revisions_from_repair_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            new_attempt(root, "test-run", "repair one finding batch")
            record_release_impact(
                root,
                "test-run",
                level="none",
                reason="Current repair attempt has no product release",
            )
            approve_current(root)

            report_path, _, _ = finish_run(root, "test-run", "reported")
            report = report_path.read_text(encoding="utf-8")

            self.assertIn("1 superseded attempt(s)", report)
            self.assertIn("revision 1 attempt 1: repair one finding batch", report)

    def test_blocked_run_can_report_incomplete_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init_repository(root)
            start_test_run(root)
            report_path, _, finished = finish_run(root, "test-run", "blocked")
            self.assertTrue(report_path.is_file())
            self.assertEqual("blocked", finished["state"])


if __name__ == "__main__":
    unittest.main()
