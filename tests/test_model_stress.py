from __future__ import annotations

import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from harness.runtime.model_stress import (
    MAXIMUM_CONTRACT_BYTES,
    due_reasons,
    normalize_repository_path,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]


class ModelStressTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads((ROOT / "harness/model-stress.json").read_text())

    def test_repository_contract_is_valid_and_supplemental(self) -> None:
        self.assertEqual([], validate_contract(self.contract))
        self.assertEqual("supplemental", self.contract["authority"])
        self.assertFalse(self.contract["execution"]["network_writes"])
        self.assertFalse(self.contract["execution"]["model_self_approval"])

    def test_decision_research_and_auth_correction_are_durable(self) -> None:
        correction = (ROOT / "docs/project/correction-log.md").read_text(encoding="utf-8")
        self.assertIn("GH-AUTH-002", correction)
        self.assertIn("unavailable network validation misclassified", correction)
        self.assertIn("Treat an unreachable API as indeterminate", correction)
        self.assertIn("gh api user", correction)
        self.assertIn("LOCAL-RUNTIME-003", correction)
        self.assertIn("restricted loopback visibility misclassified", correction)
        for boundary in ("sparkrun status", "docker inspect", "`ss`", "/v1/models"):
            self.assertIn(boundary, correction)
        self.assertIn("Never start a replacement workload before checking", correction)

        decision = (ROOT / "docs/adr/0008-model-diversity-canary.md").read_text(encoding="utf-8")
        self.assertIn("Status: accepted", decision)
        self.assertIn("Deciders: Jack Rory Staunton", decision)
        self.assertIn("same task and oracle in paired", decision)
        self.assertIn("supplemental evidence", decision)

        research = (ROOT / "docs/research/model-robustness-evaluation.md").read_text(
            encoding="utf-8"
        )
        for source in ("SWE-bench", "SWE-Lancer", "Agent Skills", "Pi settings"):
            self.assertIn(source, research)
        self.assertNotIn("endpoint was unavailable", research)
        self.assertIn("That result was\nindeterminate", research)

        execution_skill = (ROOT / ".agents/skills/execute-engineering-loop/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("failed network or loopback probe", execution_skill)
        self.assertIn("supervisor", execution_skill)
        self.assertIn("never launch a possible duplicate first", execution_skill)

    def test_contract_rejects_weakened_authority_and_execution_boundaries(self) -> None:
        mutations = (
            ("authority", "authoritative"),
            ("network_writes", True),
            ("raw_transcript_retention", True),
            ("model_self_approval", True),
            ("disposable_repository", False),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                candidate = copy.deepcopy(self.contract)
                if key == "authority":
                    candidate[key] = value
                else:
                    candidate["execution"][key] = value
                self.assertTrue(validate_contract(candidate))

    def test_contract_rejects_disabled_objective_triggers(self) -> None:
        mutations = (
            (("canary", "family"), "not-qwen"),
            (("triggers", "maximum_reported_loops_between_runs"), 999999),
            (("triggers", "release_impacts"), ["none"]),
            (("triggers", "path_prefixes"), ["never/"]),
            (("execution", "minimum_trials_for_acceptance"), 2),
        )
        for path, value in mutations:
            with self.subTest(path=path):
                candidate = copy.deepcopy(self.contract)
                candidate[path[0]][path[1]] = value
                self.assertTrue(validate_contract(candidate))

    def test_due_reasons_cover_absence_cadence_change_and_release(self) -> None:
        reasons = due_reasons(
            self.contract,
            has_accepted_evidence=False,
            reported_loops_since=10,
            changed_paths=["harness/roles/verifier.md", "src/unrelated.py"],
            release_impact="minor",
        )
        self.assertEqual(4, len(reasons))
        self.assertIn("no accepted", reasons[0])
        self.assertTrue(any("cadence" in reason for reason in reasons))
        self.assertTrue(any("harness/roles/verifier.md" in reason for reason in reasons))
        self.assertTrue(any("minor" in reason for reason in reasons))

    def test_clean_status_is_not_due_and_never_invokes_a_model(self) -> None:
        result = subprocess.run(
            [
                "python3",
                "tools/model_stress.py",
                "status",
                "--accepted-evidence",
                "--reported-loops-since",
                "2",
                "--changed-path",
                "src/unrelated.py",
                "--release-impact",
                "patch",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["due"])
        self.assertFalse(payload["model_invoked"])

    def test_changed_paths_are_normalized_and_matched_segment_safely(self) -> None:
        self.assertEqual(
            "harness/roles/verifier.md",
            normalize_repository_path("./harness/roles/verifier.md"),
        )
        reasons = due_reasons(
            self.contract,
            has_accepted_evidence=True,
            reported_loops_since=0,
            changed_paths=[normalize_repository_path("./harness/roles/verifier.md")],
            release_impact="none",
        )
        self.assertEqual(1, len(reasons))
        self.assertIn("harness/roles/verifier.md", reasons[0])
        directory_reasons = due_reasons(
            self.contract,
            has_accepted_evidence=True,
            reported_loops_since=0,
            changed_paths=["harness/roles"],
            release_impact="none",
        )
        self.assertEqual(1, len(directory_reasons))
        self.assertEqual(
            [],
            due_reasons(
                self.contract,
                has_accepted_evidence=True,
                reported_loops_since=0,
                changed_paths=["tools/loop.py.evil"],
                release_impact="none",
            ),
        )

    def run_contract_cli(self, contract: object) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "harness").mkdir()
            (root / "harness/model-stress.json").write_text(json.dumps(contract), encoding="utf-8")
            return subprocess.run(
                ["python3", str(ROOT / "tools/model_stress.py"), "check", "--root", str(root)],
                check=False,
                text=True,
                capture_output=True,
            )

    def test_nested_malformed_contract_values_fail_closed_without_traceback(self) -> None:
        for section, key, value in (
            (None, "required_evidence", [[]]),
            ("triggers", "release_impacts", [{}]),
        ):
            with self.subTest(key=key):
                candidate = copy.deepcopy(self.contract)
                target = candidate if section is None else candidate[section]
                target[key] = value
                result = self.run_contract_cli(candidate)
                self.assertEqual(1, result.returncode)
                self.assertEqual("", result.stderr)
                self.assertFalse(json.loads(result.stdout)["ok"])

    def test_deep_json_fails_closed_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "harness").mkdir()
            (root / "harness/model-stress.json").write_text(
                "[" * 10_000 + "]" * 10_000, encoding="utf-8"
            )
            result = subprocess.run(
                ["python3", str(ROOT / "tools/model_stress.py"), "check", "--root", str(root)],
                check=False,
                text=True,
                capture_output=True,
            )
        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        self.assertFalse(json.loads(result.stdout)["ok"])

    def test_oversized_contract_fails_closed_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "harness").mkdir()
            (root / "harness/model-stress.json").write_bytes(b" " * (MAXIMUM_CONTRACT_BYTES + 1))
            result = subprocess.run(
                ["python3", str(ROOT / "tools/model_stress.py"), "check", "--root", str(root)],
                check=False,
                text=True,
                capture_output=True,
            )
        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        self.assertFalse(json.loads(result.stdout)["ok"])

    def test_sparse_oversized_contract_is_rejected_before_reading(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "harness").mkdir()
            contract = root / "harness/model-stress.json"
            with contract.open("wb") as handle:
                handle.seek(MAXIMUM_CONTRACT_BYTES * 1_000)
                handle.write(b"x")
            result = subprocess.run(
                ["python3", str(ROOT / "tools/model_stress.py"), "check", "--root", str(root)],
                check=False,
                text=True,
                capture_output=True,
            )
        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        self.assertIn("exceeds", json.loads(result.stdout)["errors"][0])

    def test_symlink_and_fifo_contracts_fail_closed_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            harness = root / "harness"
            harness.mkdir()
            outside = root / "outside.json"
            outside.write_text(json.dumps(self.contract), encoding="utf-8")
            contract = harness / "model-stress.json"
            contract.symlink_to(outside)
            symlink_result = subprocess.run(
                ["python3", str(ROOT / "tools/model_stress.py"), "check", "--root", str(root)],
                check=False,
                text=True,
                capture_output=True,
                timeout=2,
            )
            contract.unlink()
            os.mkfifo(contract)
            fifo_result = subprocess.run(
                ["python3", str(ROOT / "tools/model_stress.py"), "check", "--root", str(root)],
                check=False,
                text=True,
                capture_output=True,
                timeout=2,
            )
        for result in (symlink_result, fifo_result):
            self.assertEqual(1, result.returncode)
            self.assertEqual("", result.stderr)
            self.assertFalse(json.loads(result.stdout)["ok"])

    def test_invalid_changed_path_fails_closed_without_traceback(self) -> None:
        result = subprocess.run(
            [
                "python3",
                "tools/model_stress.py",
                "status",
                "--accepted-evidence",
                "--changed-path",
                "../outside",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stderr)
        self.assertFalse(json.loads(result.stdout)["ok"])

    def test_malformed_contract_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "harness").mkdir()
            (root / "harness/model-stress.json").write_text("[]", encoding="utf-8")
            result = subprocess.run(
                ["python3", str(ROOT / "tools/model_stress.py"), "check", "--root", str(root)],
                check=False,
                text=True,
                capture_output=True,
            )
        self.assertEqual(1, result.returncode)
        self.assertFalse(json.loads(result.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
