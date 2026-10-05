from __future__ import annotations

import base64
import copy
import http.client
import io
import json
import math
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any
from unittest.mock import patch

from harness.runtime.codex_subscription_proxy import (
    CODEX_RESPONSES_PATH,
    MAXIMUM_CODEX_AUTH_BYTES,
    CodexSubscriptionCredential,
    CodexSubscriptionProxy,
    SubscriptionBudget,
    codex_subscription_proxy,
    load_codex_subscription,
)
from harness.runtime.model_stress_runner import (
    CODEX_SOL_CONTROL_TARGET,
    RESOURCE_PATHS,
    RunnerError,
    RunnerExecutionError,
    _changed_paths,
    _load_resource_bundle,
    _parse_events,
    _run_model_lane,
    _run_oracle,
    _sanitized_event_metrics,
    _snapshot,
    _write_initial_repository,
    _write_pi_config,
    build_pi_command,
    codex_catalog_preflight,
    codex_subscription_budget,
    load_task,
    pi_version,
    run_paired,
    safe_output_path,
    trial_passed,
    validate_result,
    validate_task,
    validate_trials,
)

ROOT = Path(__file__).resolve().parents[1]
TASK_PATH = ROOT / "harness/model-stress/tasks/identifier-canonicalization-v1.json"
TASK_DIRECTORY = ROOT / "harness/model-stress/tasks"
EXPECTED_TASK_CLASSES = {
    "identifier-canonicalization-v1": "implementation",
    "retry-after-repair-v1": "defect-repair",
    "release-policy-integration-v1": "cross-file-integration",
}


def codex_access_token(
    account: str,
    expires: int,
    *,
    auth_claim: Any | None = None,
) -> str:
    def encoded(value: dict[str, Any]) -> str:
        raw = json.dumps(value, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

    return ".".join(
        (
            encoded({"alg": "none"}),
            encoded(
                {
                    "exp": expires,
                    "https://api.openai.com/auth": (
                        {"chatgpt_account_id": account} if auth_claim is None else auth_claim
                    ),
                }
            ),
            "",
        )
    )


def valid_result() -> dict[str, Any]:
    trial = {
        "returncode": 0,
        "settled": True,
        "timed_out": False,
        "event_limit_ok": True,
        "elapsed_seconds": 1.0,
        "changed_paths": ["identifier.py"],
        "scope_result": {"ok": True, "allowed_paths": ["identifier.py"]},
        "tool_errors": [],
        "usage": {
            "measurement_origin": "unavailable",
            "input_tokens": None,
            "output_tokens": None,
            "cache_read_tokens": None,
            "cache_write_tokens": None,
        },
        "trial": 1,
        "test_result": {
            "ok": False,
            "passed": 6,
            "failed_case_ids": ["runs"],
            "elapsed_seconds": 0.1,
            "timed_out": False,
        },
    }
    return {
        "schema_version": "1.3",
        "authority": "supplemental",
        "evidence_level": "smoke",
        "accepted_baseline": False,
        "model_invoked": True,
        "provenance": {
            "model": "model",
            "provider": "provider",
            "pi_version": "1.2.3",
            "serving_runtime": "runtime",
            "serving_recipe": "recipe",
            "endpoint_class": "local-loopback-openai-compatible",
        },
        "provider_boundary": {
            "execution_target": "local-qwen",
            "reasoning_effort": "not-applicable",
            "credential_delivery": "synthetic-placeholder",
            "output_token_limit_enforcement": "provider-request",
            "maximum_requests": 0,
            "maximum_request_bytes": 0,
            "observed_requests": 0,
            "observed_request_bytes": 0,
        },
        "task": {
            "id": "identifier-canonicalization-v1",
            "task_class": "implementation",
            "task_digest": "a" * 64,
            "prompt_digest": "b" * 64,
            "tool_set": ["read", "edit"],
            "oracle_case_count": 7,
            "oracle_case_ids": [
                "plain",
                "runs",
                "casefold",
                "unicode",
                "digits",
                "empty",
                "wrong-type",
            ],
            "resource_bundle_digest": "c" * 64,
            "writable_paths": ["identifier.py"],
        },
        "limits": {
            "model_timeout_seconds": 300,
            "oracle_timeout_seconds": 10,
            "maximum_event_bytes": 65536,
            "maximum_changed_files": 1,
            "maximum_output_tokens": 4096,
        },
        "trial_count": 1,
        "lanes": {
            "bare": {
                "passed_trials": 0,
                "total_trials": 1,
                "trials": [copy.deepcopy(trial)],
            },
            "harness": {
                "passed_trials": 0,
                "total_trials": 1,
                "trials": [copy.deepcopy(trial)],
            },
        },
        "comparison": {
            "bare_passed_trials": 0,
            "harness_passed_trials": 0,
            "observed_pass_difference": 0,
            "general_harness_lift_claim": False,
        },
    }


def bubblewrap_available() -> bool:
    if shutil.which("bwrap") is None:
        return False
    result = subprocess.run(
        [
            "bwrap",
            "--unshare-all",
            "--ro-bind",
            "/usr",
            "/usr",
            "--symlink",
            "usr/bin",
            "/bin",
            "--symlink",
            "usr/lib",
            "/lib",
            "--symlink",
            "usr/lib64",
            "/lib64",
            "/usr/bin/true",
        ],
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


class ModelStressRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = json.loads(TASK_PATH.read_text(encoding="utf-8"))

    def test_repository_task_is_valid_and_oracle_is_not_an_initial_file(self) -> None:
        task, digest = load_task(TASK_PATH)
        self.assertEqual([], validate_task(task))
        self.assertEqual(64, len(digest))
        visible = {item["path"] for item in task["initial_files"]}
        self.assertNotIn("oracle.json", visible)
        self.assertEqual(["identifier.py"], task["writable_paths"])

    def test_repository_corpus_has_three_distinct_valid_task_classes(self) -> None:
        observed = {}
        for path in sorted(TASK_DIRECTORY.glob("*.json")):
            task, digest = load_task(path, root=ROOT)
            self.assertEqual([], validate_task(task), path.name)
            self.assertEqual(64, len(digest))
            self.assertEqual(path.stem, task["id"])
            observed[task["id"]] = task["task_class"]
            self.assertNotIn("oracle.json", {item["path"] for item in task["initial_files"]})
        self.assertEqual(EXPECTED_TASK_CLASSES, observed)
        self.assertEqual(3, len(set(observed.values())))

    def test_malformed_and_unsafe_tasks_fail_closed(self) -> None:
        mutations = []
        candidate = copy.deepcopy(self.task)
        candidate["unknown"] = True
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["task_class"] = "algorithm"
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["initial_files"][0]["path"] = "../escape"
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["writable_paths"] = ["missing.py"]
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["oracle"]["targets"][0]["module"] = "pkg.module"
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["oracle"]["targets"] = []
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["oracle"]["targets"].append(copy.deepcopy(candidate["oracle"]["targets"][0]))
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["oracle"]["targets"][0]["cases"] = []
        candidate["oracle"]["targets"][0]["raises"] = []
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["oracle"]["targets"][0]["cases"][0]["args"] = [[]]
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["initial_files"][0]["path"] = "AGENTS.md"
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["initial_files"][0]["path"] = ".gitattributes"
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["initial_files"][0]["path"] = "nested/.git/config"
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["initial_files"][0]["path"] = "AGENTS.md/child"
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["initial_files"][0]["path"] = "bad\x00name.py"
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["prompt"] = "bad\x00prompt"
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["oracle"]["targets"][0]["cases"][0]["expected"] = math.nan
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["initial_files"][0]["path"] = "a" * 158 + ".py"
        mutations.append(candidate)
        candidate = copy.deepcopy(self.task)
        candidate["oracle"]["targets"][0]["cases"][0]["id"] = "a" * 81
        mutations.append(candidate)
        for value in mutations:
            with self.subTest(value=value):
                self.assertTrue(validate_task(value))

    def test_duplicate_task_json_keys_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "task.json"
            path.write_text('{"schema_version":"1.0","schema_version":"1.0"}', encoding="utf-8")
            with self.assertRaisesRegex(RunnerError, "duplicate JSON object key"):
                load_task(path)

    def test_task_loader_rejects_symlink_root_ancestor_and_outside_path(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            base = Path(name)
            root = base / "root"
            root.mkdir()
            outside = base / "outside"
            outside.mkdir()
            task = outside / "task.json"
            shutil.copy2(TASK_PATH, task)

            root_link = base / "root-link"
            root_link.symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(RunnerError, "task root"):
                load_task(root_link / "task.json", root=root_link)

            (root / "nested").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(RunnerError, "symlink|invalid path"):
                load_task(root / "nested/task.json", root=root)

            with self.assertRaisesRegex(RunnerError, "beneath the repository root"):
                load_task(task, root=root)

    def test_trial_levels_reject_ambiguous_two_trial_evidence(self) -> None:
        self.assertEqual("smoke", validate_trials(1))
        self.assertEqual("acceptance-candidate", validate_trials(3))
        for value in (0, 2, 11):
            with self.assertRaises(RunnerError):
                validate_trials(value)

    def test_output_is_confined_and_rejects_symlink_ancestors(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            path = safe_output_path(root, Path(".harness/model-stress/result.json"))
            self.assertEqual(root / ".harness/model-stress/result.json", path)
            with self.assertRaises((RunnerError, ValueError)):
                safe_output_path(root, Path("outside.json"))
            (root / ".harness").mkdir()
            outside = root / "outside"
            outside.mkdir()
            (root / ".harness/model-stress").symlink_to(outside)
            with self.assertRaises(RunnerError):
                safe_output_path(root, Path(".harness/model-stress/result.json"))

    def test_lane_commands_are_identical_except_harness_resources(self) -> None:
        common = {
            "repo": Path("/tmp/repo"),
            "config_home": Path("/tmp/home"),
            "pi_root": Path("/tmp/pi"),
            "provider": "local-vllm",
            "model": "model",
            "prompt": self.task["prompt"],
        }
        bare = build_pi_command(lane="bare", **common)
        harness = build_pi_command(lane="harness", **common)
        for command in (bare, harness):
            self.assertIn("read,edit", command)
            self.assertNotIn("bash", command)
            self.assertNotIn("write", command)
            self.assertIn("--no-session", command)
            self.assertIn("--offline", command)
            self.assertEqual("not-needed", command[command.index("--api-key") + 1])
            self.assertEqual(self.task["prompt"], command[-1])
        self.assertIn("--no-context-files", bare)
        self.assertNotIn("--no-context-files", harness)
        self.assertIn("--skill", harness)
        self.assertIn("--extension", harness)
        self.assertNotIn("--skill", bare)
        for name in ("models.json", "settings.json"):
            destination = f"/home/canary/.pi/agent/{name}"
            mount = bare.index(destination)
            self.assertEqual("--ro-bind", bare[mount - 2])
        self.assertNotIn("/home/jrs/.codex", bare)
        correction = (ROOT / "docs/project/correction-log.md").read_text(encoding="utf-8")
        self.assertIn("LOCAL-RUNNER-006", correction)

    def test_codex_subscription_config_uses_only_a_nonsecret_model_token(self) -> None:
        expires = int(time.time()) + 7200
        credential = CodexSubscriptionCredential(
            access_token=codex_access_token("real-test-account", expires),
            account_id="real-test-account",
            expires_at=expires,
        )
        with tempfile.TemporaryDirectory() as name:
            home = Path(name)
            _write_pi_config(
                home,
                "openai-codex",
                "gpt-5.6-sol",
                "http://127.0.0.1:12345/backend-api",
                execution_target=CODEX_SOL_CONTROL_TARGET,
            )
            models_text = (home / ".pi/agent/models.json").read_text(encoding="utf-8")
            settings = json.loads((home / ".pi/agent/settings.json").read_text(encoding="utf-8"))
            budget = SubscriptionBudget(
                maximum_requests=1,
                maximum_request_bytes=1024,
                upstream_timeout_seconds=60,
            )
            proxy = CodexSubscriptionProxy(credential=credential, budget=budget)
            command = build_pi_command(
                lane="bare",
                repo=Path("/tmp/repo"),
                config_home=home,
                pi_root=Path("/tmp/pi"),
                provider="openai-codex",
                model="gpt-5.6-sol",
                prompt=self.task["prompt"],
                execution_target=CODEX_SOL_CONTROL_TARGET,
                auth_override=proxy.model_token,
            )
            model_token = proxy.model_token
        self.assertNotIn(credential.access_token, models_text)
        self.assertNotIn(credential.account_id, models_text)
        self.assertNotIn(credential.access_token, command)
        self.assertNotIn(credential.account_id, command)
        self.assertEqual("sse", settings["transport"])
        self.assertEqual(
            model_token,
            command[command.index("--api-key") + 1],
        )
        self.assertNotEqual("not-needed", model_token)
        self.assertEqual(
            "medium",
            command[command.index("--thinking") + 1],
        )
        self.assertIn("/home/canary/.pi/agent/models.json", command)
        self.assertIn("/home/canary/.pi/agent/settings.json", command)
        self.assertNotIn("auth.json", command)

    def test_codex_subscription_budget_is_bounded_for_every_allowed_trial_count(self) -> None:
        smoke = codex_subscription_budget(trials=1, model_timeout_seconds=300)
        self.assertEqual(10, smoke.maximum_requests)
        self.assertEqual(512 * 1024, smoke.maximum_request_bytes)
        maximum = codex_subscription_budget(trials=10, model_timeout_seconds=300)
        maximum.validate()
        self.assertEqual(100, maximum.maximum_requests)
        self.assertEqual(5 * 1024 * 1024, maximum.maximum_request_bytes)

    def test_codex_subscription_loader_requires_private_current_chatgpt_oauth(self) -> None:
        account = "account-test"
        access = codex_access_token(account, int(time.time()) + 7200)
        payload = {
            "auth_mode": "chatgpt",
            "OPENAI_API_KEY": None,
            "tokens": {
                "access_token": access,
                "refresh_token": "refresh-test",
                "account_id": account,
            },
        }
        with tempfile.TemporaryDirectory() as name:
            auth = Path(name) / "auth.json"
            auth.write_text(json.dumps(payload), encoding="utf-8")
            auth.chmod(0o600)
            credential = load_codex_subscription(auth)
            self.assertEqual(account, credential.account_id)

            payload["OPENAI_API_KEY"] = "prohibited"
            auth.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "prohibited"):
                load_codex_subscription(auth)
            payload["OPENAI_API_KEY"] = None
            payload["auth_mode"] = "apikey"
            auth.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not logged in with ChatGPT"):
                load_codex_subscription(auth)

    def test_codex_subscription_loader_rejects_unsafe_auth_files(self) -> None:
        account = "account-test"
        expires = int(time.time()) + 7200
        payload = {
            "auth_mode": "chatgpt",
            "OPENAI_API_KEY": None,
            "tokens": {
                "access_token": codex_access_token(account, expires),
                "refresh_token": "refresh-test",
                "account_id": account,
            },
        }
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            auth = root / "auth.json"
            auth.write_text(json.dumps(payload), encoding="utf-8")
            auth.chmod(0o644)
            with self.assertRaisesRegex(ValueError, "private bounded regular file"):
                load_codex_subscription(auth)

            auth.chmod(0o600)
            linked = root / "linked-auth.json"
            linked.symlink_to(auth)
            with self.assertRaisesRegex(ValueError, "unavailable"):
                load_codex_subscription(linked)

            actual = root / "actual"
            actual.mkdir()
            nested_auth = actual / "auth.json"
            nested_auth.write_text(json.dumps(payload), encoding="utf-8")
            nested_auth.chmod(0o600)
            linked_directory = root / "linked-directory"
            linked_directory.symlink_to(actual, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "unavailable"):
                load_codex_subscription(linked_directory / "auth.json")

            oversized = root / "oversized.json"
            with oversized.open("wb") as stream:
                stream.truncate(MAXIMUM_CODEX_AUTH_BYTES + 1)
            oversized.chmod(0o600)
            with self.assertRaisesRegex(ValueError, "private bounded regular file"):
                load_codex_subscription(oversized)

    def test_codex_subscription_loader_rejects_ambiguous_or_malformed_json(self) -> None:
        account = "account-test"
        expires = int(time.time()) + 7200
        with tempfile.TemporaryDirectory() as name:
            auth = Path(name) / "auth.json"
            valid_tail = json.dumps(
                {
                    "OPENAI_API_KEY": None,
                    "tokens": {
                        "access_token": codex_access_token(account, expires),
                        "account_id": account,
                    },
                }
            )[1:]
            auth.write_text(
                '{"auth_mode":"apikey","auth_mode":"chatgpt",' + valid_tail,
                encoding="utf-8",
            )
            auth.chmod(0o600)
            with self.assertRaisesRegex(ValueError, "duplicate JSON object key"):
                load_codex_subscription(auth)

            for bad_claim in ("not-an-object", ["not-an-object"]):
                payload = {
                    "auth_mode": "chatgpt",
                    "OPENAI_API_KEY": None,
                    "tokens": {
                        "access_token": codex_access_token(
                            account,
                            expires,
                            auth_claim=bad_claim,
                        ),
                        "account_id": account,
                    },
                }
                auth.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "auth claim is invalid"):
                    load_codex_subscription(auth)

    def test_codex_subscription_loader_rejects_unsafe_header_values_without_echo(self) -> None:
        account = "account-test"
        expires = int(time.time()) + 7200
        access = codex_access_token(account, expires)
        cases = (
            (access + "\nsecret-suffix", account, "access token"),
            (access, account + "\rsecret-suffix", "account identity"),
        )
        with tempfile.TemporaryDirectory() as name:
            auth = Path(name) / "auth.json"
            for candidate_access, candidate_account, expected in cases:
                payload = {
                    "auth_mode": "chatgpt",
                    "OPENAI_API_KEY": None,
                    "tokens": {
                        "access_token": candidate_access,
                        "account_id": candidate_account,
                    },
                }
                auth.write_text(json.dumps(payload), encoding="utf-8")
                auth.chmod(0o600)
                with self.assertRaisesRegex(ValueError, expected) as raised:
                    load_codex_subscription(auth)
                self.assertNotIn("secret-suffix", str(raised.exception))

    def test_codex_subscription_proxy_rejects_inconsistent_credentials(self) -> None:
        expires = int(time.time()) + 7200
        credential = CodexSubscriptionCredential(
            access_token=codex_access_token("claimed-account", expires),
            account_id="different-account",
            expires_at=expires,
        )
        budget = SubscriptionBudget(
            maximum_requests=1,
            maximum_request_bytes=1024,
            upstream_timeout_seconds=60,
        )
        with self.assertRaisesRegex(ValueError, "identity is inconsistent"):
            CodexSubscriptionProxy(credential=credential, budget=budget)

    def test_codex_subscription_relay_replaces_fake_auth_and_enforces_budget(self) -> None:
        observed: list[dict[str, Any]] = []

        class FakeResponse:
            status = 200

            def __init__(self) -> None:
                self.chunks = [b"data: done\n\n", b""]

            def getheader(self, name: str):
                return "text/event-stream" if name.lower() == "content-type" else None

            def read(self, _size: int) -> bytes:
                return self.chunks.pop(0)

        class FakeHTTPSConnection:
            def __init__(self, host: str, timeout: int) -> None:
                self.host = host
                self.timeout = timeout

            def request(self, method: str, path: str, *, body: bytes, headers: dict) -> None:
                observed.append(
                    {
                        "method": method,
                        "path": path,
                        "body": body,
                        "headers": headers,
                        "host": self.host,
                    }
                )

            def getresponse(self) -> FakeResponse:
                return FakeResponse()

            def close(self) -> None:
                return

        expires = int(time.time()) + 7200
        access_token = codex_access_token("real-test-account", expires)
        credential = CodexSubscriptionCredential(
            access_token=access_token,
            account_id="real-test-account",
            expires_at=expires,
        )
        budget = SubscriptionBudget(
            maximum_requests=1,
            maximum_request_bytes=1024,
            upstream_timeout_seconds=60,
        )
        with patch(
            "harness.runtime.codex_subscription_proxy.http.client.HTTPSConnection",
            FakeHTTPSConnection,
        ):
            manager = codex_subscription_proxy(credential=credential, budget=budget)
            try:
                proxy = manager.__enter__()
            except PermissionError:
                self.skipTest("loopback sockets unavailable in this test boundary")
            try:
                model_token = proxy.model_token
                host, port_text = proxy.base_url.removeprefix("http://").split(":", 1)
                port = int(port_text.split("/", 1)[0])
                connection = http.client.HTTPConnection(host, port, timeout=5)
                connection.request(
                    "POST",
                    CODEX_RESPONSES_PATH,
                    body=b"opaque-zstd-request",
                    headers={
                        "Authorization": f"Bearer {proxy.model_token}",
                        "chatgpt-account-id": "harness-canary",
                        "Content-Encoding": "zstd",
                    },
                )
                response = connection.getresponse()
                self.assertEqual(200, response.status)
                self.assertEqual(b"data: done\n\n", response.read())
                connection.close()

                unauthorized = http.client.HTTPConnection(host, port, timeout=5)
                unauthorized.request(
                    "POST",
                    CODEX_RESPONSES_PATH,
                    body=b"rejected",
                    headers={
                        "Authorization": "Bearer fixed-known-token",
                        "chatgpt-account-id": "harness-canary",
                    },
                )
                rejected = unauthorized.getresponse()
                self.assertEqual(401, rejected.status)
                rejected.read()
                unauthorized.close()

                second = http.client.HTTPConnection(host, port, timeout=5)
                second.request(
                    "POST",
                    CODEX_RESPONSES_PATH,
                    body=b"second",
                    headers={
                        "Authorization": f"Bearer {proxy.model_token}",
                        "chatgpt-account-id": "harness-canary",
                    },
                )
                exhausted = second.getresponse()
                self.assertEqual(429, exhausted.status)
                exhausted.read()
                second.close()
                metrics = proxy.metrics
            finally:
                manager.__exit__(None, None, None)

        self.assertEqual(1, len(observed))
        self.assertEqual(CODEX_RESPONSES_PATH, observed[0]["path"])
        self.assertEqual(
            f"Bearer {access_token}",
            observed[0]["headers"]["Authorization"],
        )
        self.assertEqual("real-test-account", observed[0]["headers"]["chatgpt-account-id"])
        self.assertNotIn(model_token, repr(observed))
        self.assertEqual(1, metrics.requests)
        self.assertEqual(len(b"opaque-zstd-request"), metrics.request_bytes)

    def test_codex_subscription_relay_sanitizes_header_construction_errors(self) -> None:
        class RejectingHTTPSConnection:
            def __init__(self, _host: str, timeout: int) -> None:
                self.timeout = timeout

            def request(self, _method: str, _path: str, *, body: bytes, headers: dict) -> None:
                raise ValueError(f"Invalid header value {headers['Authorization']}")

            def close(self) -> None:
                return

        expires = int(time.time()) + 7200
        credential = CodexSubscriptionCredential(
            access_token=codex_access_token("real-test-account", expires),
            account_id="real-test-account",
            expires_at=expires,
        )
        budget = SubscriptionBudget(
            maximum_requests=1,
            maximum_request_bytes=1024,
            upstream_timeout_seconds=60,
        )
        stderr = io.StringIO()
        with (
            patch(
                "harness.runtime.codex_subscription_proxy.http.client.HTTPSConnection",
                RejectingHTTPSConnection,
            ),
            redirect_stderr(stderr),
        ):
            manager = codex_subscription_proxy(credential=credential, budget=budget)
            try:
                proxy = manager.__enter__()
            except PermissionError:
                self.skipTest("loopback sockets unavailable in this test boundary")
            try:
                host, port_text = proxy.base_url.removeprefix("http://").split(":", 1)
                connection = http.client.HTTPConnection(
                    host,
                    int(port_text.split("/", 1)[0]),
                    timeout=5,
                )
                connection.request(
                    "POST",
                    CODEX_RESPONSES_PATH,
                    body=b"opaque-zstd-request",
                    headers={
                        "Authorization": f"Bearer {proxy.model_token}",
                        "chatgpt-account-id": "harness-canary",
                    },
                )
                response = connection.getresponse()
                response_body = response.read().decode("utf-8")
                connection.close()
            finally:
                manager.__exit__(None, None, None)
        self.assertEqual(502, response.status)
        self.assertIn("upstream request failed", response_body)
        self.assertEqual("", stderr.getvalue())
        self.assertNotIn(credential.access_token, response_body)
        self.assertNotIn(credential.account_id, response_body)

    def test_sanitized_metrics_never_retain_transcript_or_error_text(self) -> None:
        events = [
            {
                "type": "message_end",
                "message": {
                    "content": [{"type": "text", "text": "RAW_PRIVATE_TEXT"}],
                    "usage": {"input": 12, "output": 4, "cacheRead": 2, "cacheWrite": 1},
                },
            },
            {
                "type": "tool_execution_end",
                "toolName": "edit",
                "isError": True,
                "result": {"content": [{"type": "text", "text": "SECRET_ERROR_DETAIL"}]},
            },
            {"type": "agent_settled"},
        ]
        errors, usage, settled = _sanitized_event_metrics(events)
        rendered = json.dumps({"errors": errors, "usage": usage})
        self.assertNotIn("RAW_PRIVATE_TEXT", rendered)
        self.assertNotIn("SECRET_ERROR_DETAIL", rendered)
        self.assertEqual(
            [{"tool": "edit", "category": "tool-execution-error", "count": 1}],
            errors,
        )
        self.assertEqual(12, usage["input_tokens"])
        self.assertEqual("provider-reported", usage["measurement_origin"])
        self.assertTrue(settled)

        secret_name = "private-provider-tool-name"
        secret_errors, _, _ = _sanitized_event_metrics(
            [
                {
                    "type": "tool_execution_end",
                    "toolName": secret_name,
                    "isError": True,
                }
            ]
        )
        self.assertEqual(
            [{"tool": "unavailable", "category": "tool-execution-error", "count": 1}],
            secret_errors,
        )
        self.assertNotIn(secret_name, json.dumps(secret_errors))

        _, unavailable, _ = _sanitized_event_metrics([{"type": "agent_settled"}])
        self.assertEqual("unavailable", unavailable["measurement_origin"])
        self.assertIsNone(unavailable["input_tokens"])

    def test_result_validator_rejects_raw_content_and_self_approval(self) -> None:
        payload = valid_result()
        self.assertEqual([], validate_result(payload))
        payload["accepted_baseline"] = True
        self.assertTrue(validate_result(payload))
        payload = valid_result()
        payload["raw"] = {"transcript": "private"}
        self.assertTrue(validate_result(payload))

    def test_result_validator_binds_codex_subscription_identity_and_budget(self) -> None:
        payload = valid_result()
        payload["provenance"].update(
            {
                "model": "gpt-5.6-sol",
                "provider": "openai-codex",
                "endpoint_class": "credential-isolated-chatgpt-codex-subscription",
            }
        )
        payload["provider_boundary"] = {
            "execution_target": "codex-subscription-sol",
            "reasoning_effort": "medium",
            "credential_delivery": "host-subscription-relay",
            "output_token_limit_enforcement": "runner-config-only",
            "maximum_requests": 10,
            "maximum_request_bytes": 524288,
            "observed_requests": 2,
            "observed_request_bytes": 2048,
        }
        self.assertEqual([], validate_result(payload))
        for key, value in (
            ("model", "gpt-5.6"),
            ("provider", "openai"),
            ("endpoint_class", "local-loopback-openai-compatible"),
        ):
            invalid = copy.deepcopy(payload)
            invalid["provenance"][key] = value
            with self.subTest(key=key):
                self.assertTrue(validate_result(invalid))
        invalid = copy.deepcopy(payload)
        invalid["provider_boundary"]["observed_requests"] = 11
        self.assertTrue(validate_result(invalid))
        invalid = copy.deepcopy(payload)
        invalid["provider_boundary"]["output_token_limit_enforcement"] = "provider-request"
        self.assertTrue(validate_result(invalid))

        local = valid_result()
        local["provider_boundary"]["output_token_limit_enforcement"] = "runner-config-only"
        self.assertTrue(validate_result(local))

    def test_result_validator_rejects_inconsistent_shapes_and_relationships(self) -> None:
        mutations = []
        payload = valid_result()
        payload["provenance"]["endpoint_class"] = "local"
        mutations.append(payload)
        payload = valid_result()
        payload["task"]["task_digest"] = "not-a-digest"
        mutations.append(payload)
        payload = valid_result()
        payload["task"]["task_class"] = "unknown"
        mutations.append(payload)
        payload = valid_result()
        payload["task"]["id"] = "a" * 81
        mutations.append(payload)
        payload = valid_result()
        payload["task"]["id"] = "retry-after-repair-v1"
        mutations.append(payload)
        payload = valid_result()
        payload["lanes"]["bare"]["trials"][0]["settled"] = 1
        mutations.append(payload)
        payload = valid_result()
        payload["lanes"]["bare"]["trials"][0]["scope_result"]["ok"] = False
        mutations.append(payload)
        payload = valid_result()
        payload["lanes"]["bare"]["trials"][0]["tool_errors"] = [
            {"tool": "secret-tool", "category": "tool-execution-error", "count": 1}
        ]
        mutations.append(payload)
        payload = valid_result()
        payload["lanes"]["bare"]["trials"][0]["usage"]["input_tokens"] = 0
        mutations.append(payload)
        payload = valid_result()
        payload["lanes"]["bare"]["trials"][0]["test_result"]["passed"] = 7
        mutations.append(payload)
        payload = valid_result()
        payload["lanes"]["bare"]["trials"][0]["test_result"]["failed_case_ids"] = ["invented-case"]
        mutations.append(payload)
        payload = valid_result()
        payload["lanes"]["bare"]["trials"][0]["scope_result"]["allowed_paths"] = ["other.py"]
        mutations.append(payload)
        payload = valid_result()
        payload["comparison"]["observed_pass_difference"] = 1
        mutations.append(payload)
        for value in mutations:
            with self.subTest(value=value):
                self.assertTrue(validate_result(value))

    def test_deep_event_json_is_discarded_without_recursion_failure(self) -> None:
        output = ('{"nested":' + "[" * 10000 + "0" + "]" * 10000 + "}\n").encode()
        events, within_limit = _parse_events(output, 65536)
        self.assertFalse(events)
        self.assertTrue(within_limit)
        duplicate_events, duplicate_within_limit = _parse_events(
            b'{"type":"agent_settled","type":"message_end"}\n', 65536
        )
        self.assertFalse(duplicate_events)
        self.assertTrue(duplicate_within_limit)

    def test_model_event_stream_is_bounded_while_subprocess_runs(self) -> None:
        task = copy.deepcopy(self.task)
        task["limits"]["maximum_event_bytes"] = 65536
        with tempfile.TemporaryDirectory() as name:
            repo = Path(name) / "repo"
            repo.mkdir()

            def fake_run(command, **kwargs):
                self.assertIs(subprocess.DEVNULL, kwargs["stderr"])
                self.assertIn("preexec_fn", kwargs)
                kwargs["stdout"].write(b"x" * 65536)
                return subprocess.CompletedProcess(command, -signal.SIGXFSZ)

            with patch("harness.runtime.model_stress_runner.subprocess.run", side_effect=fake_run):
                result = _run_model_lane(
                    lane="bare",
                    task=task,
                    repo=repo,
                    config_home=Path(name) / "home",
                    pi_root=Path(name) / "pi",
                    provider="provider",
                    model="model",
                )
        self.assertFalse(result["event_limit_ok"])
        self.assertEqual(-signal.SIGXFSZ, result["returncode"])

    def test_direct_snapshot_detects_scope_changes_without_git_filters(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "identifier.py").write_text("before", encoding="utf-8")
            (root / "TASK.md").write_text("task", encoding="utf-8")
            before = _snapshot(root)
            (root / "identifier.py").write_text("after", encoding="utf-8")
            (root / "extra.txt").write_text("extra", encoding="utf-8")
            (root / ".git").mkdir()
            (root / ".git/config").write_text("changed metadata", encoding="utf-8")
            self.assertEqual(
                [".git/config", "extra.txt", "identifier.py"],
                _changed_paths(before, _snapshot(root)),
            )

    def test_frozen_resource_bundle_builds_identical_seed_clones(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = root / "source"
            for relative in RESOURCE_PATHS:
                target = source / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
            resources, digest = _load_resource_bundle(source)
            seed = root / "seed"
            _write_initial_repository(self.task, seed, resources)
            seed_snapshot = _snapshot(seed)

            changed_resource = source / RESOURCE_PATHS[0]
            changed_resource.write_bytes(
                changed_resource.read_bytes() + b"\nchanged after freeze\n"
            )
            _, changed_digest = _load_resource_bundle(source)
            self.assertNotEqual(digest, changed_digest)

            for lane in ("bare", "harness"):
                clone = root / lane
                shutil.copytree(seed, clone, symlinks=True)
                self.assertEqual(seed_snapshot, _snapshot(clone))

    def test_resource_bundle_rejects_symlink_root_and_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            base = Path(name)
            source = base / "source"
            outside = base / "outside"
            for relative in RESOURCE_PATHS:
                parent = outside if relative.startswith(".agents/") else source
                target = parent / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
            (source / ".agents").symlink_to(outside / ".agents", target_is_directory=True)

            with self.assertRaisesRegex(RunnerError, "symlink|invalid path"):
                _load_resource_bundle(source)

            source_link = base / "source-link"
            source_link.symlink_to(source, target_is_directory=True)
            with self.assertRaisesRegex(RunnerError, "resource root"):
                _load_resource_bundle(source_link)

    def test_run_paired_reuses_frozen_seed_after_source_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = root / "source"
            for relative in RESOURCE_PATHS:
                target = source / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
            _, original_digest = _load_resource_bundle(source)
            observed_snapshots: list[dict[str, str]] = []
            changed_resource = source / RESOURCE_PATHS[0]

            def fake_lane(**kwargs):
                observed_snapshots.append(_snapshot(kwargs["repo"]))
                if len(observed_snapshots) == 1:
                    changed_resource.write_bytes(
                        changed_resource.read_bytes() + b"\nchanged after first lane\n"
                    )
                return {
                    "returncode": 0,
                    "settled": True,
                    "timed_out": False,
                    "event_limit_ok": True,
                    "elapsed_seconds": 0.01,
                    "changed_paths": [],
                    "scope_result": {"ok": True, "allowed_paths": ["identifier.py"]},
                    "tool_errors": [],
                    "usage": {
                        "measurement_origin": "unavailable",
                        "input_tokens": None,
                        "output_tokens": None,
                        "cache_read_tokens": None,
                        "cache_write_tokens": None,
                    },
                }

            oracle = {
                "ok": False,
                "passed": 0,
                "failed_case_ids": [
                    record["id"]
                    for target in self.task["oracle"]["targets"]
                    for record in target["cases"] + target["raises"]
                ],
                "elapsed_seconds": 0.01,
                "timed_out": False,
            }
            with (
                patch("harness.runtime.model_stress_runner.shutil.which", return_value="bwrap"),
                patch("harness.runtime.model_stress_runner._pi_root", return_value=root / "pi"),
                patch("harness.runtime.model_stress_runner.pi_version", return_value="0.84.1"),
                patch(
                    "harness.runtime.model_stress_runner._run_model_lane",
                    side_effect=fake_lane,
                ),
                patch("harness.runtime.model_stress_runner._run_oracle", return_value=oracle),
            ):
                result = run_paired(
                    source_root=source,
                    task=self.task,
                    task_digest="a" * 64,
                    executable=root / "pi/bin/pi",
                    provider="local-vllm",
                    model="model",
                    base_url="http://127.0.0.1:8000/v1",
                    serving_runtime="runtime",
                    serving_recipe="recipe",
                    trials=3,
                )

            self.assertEqual(6, len(observed_snapshots))
            self.assertTrue(
                all(snapshot == observed_snapshots[0] for snapshot in observed_snapshots)
            )
            self.assertEqual(original_digest, result["task"]["resource_bundle_digest"])
            _, changed_digest = _load_resource_bundle(source)
            self.assertNotEqual(original_digest, changed_digest)

    def test_snapshot_rejects_oversized_model_output_without_loading_it(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            oversized = root / "oversized.py"
            with oversized.open("wb") as handle:
                handle.truncate(1024 * 1024 + 1)
            with self.assertRaises(RunnerError):
                _snapshot(root)

    @unittest.skipUnless(
        bubblewrap_available(), "unprivileged Bubblewrap unavailable in this test boundary"
    )
    def test_oracle_runs_in_networkless_bubblewrap(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            repo = Path(name) / "repo"
            resources, _ = _load_resource_bundle(ROOT)
            _write_initial_repository(self.task, repo, resources)
            bad = _run_oracle(self.task, repo)
            self.assertFalse(bad["ok"])
            (repo / "identifier.py").write_text(
                """def canonical_identifier(value):
    if not isinstance(value, str):
        raise TypeError
    result = []
    separator = False
    for character in value.casefold():
        if character.isalnum():
            if separator and result:
                result.append('-')
            result.append(character)
            separator = False
        else:
            separator = True
    if not result:
        raise ValueError
    return ''.join(result)
""",
                encoding="utf-8",
            )
            good = _run_oracle(self.task, repo)
            self.assertTrue(good["ok"], good)
            self.assertEqual(7, good["passed"])
            self.assertFalse(good["timed_out"])

    @unittest.skipUnless(
        bubblewrap_available(), "unprivileged Bubblewrap unavailable in this test boundary"
    )
    def test_every_corpus_oracle_rejects_seed_and_accepts_reference_solution(self) -> None:
        reference_solutions = {
            "identifier-canonicalization-v1": {
                "identifier.py": """def canonical_identifier(value):
    if not isinstance(value, str):
        raise TypeError
    result = []
    separator = False
    for character in value.casefold():
        if character.isalnum():
            if separator and result:
                result.append('-')
            result.append(character)
            separator = False
        else:
            separator = True
    if not result:
        raise ValueError
    return ''.join(result)
""",
            },
            "retry-after-repair-v1": {
                "retry_after.py": """from datetime import datetime, timezone
import re


def retry_delay(value, now_epoch):
    if not isinstance(value, str) or type(now_epoch) is not int:
        raise TypeError
    value = value.strip()
    if re.fullmatch(r'[0-9]+', value):
        return int(value)
    try:
        parsed = datetime.strptime(value, '%a, %d %b %Y %H:%M:%S GMT')
    except ValueError:
        raise ValueError from None
    if parsed.strftime('%a, %d %b %Y %H:%M:%S GMT') != value:
        raise ValueError
    return max(0, int(parsed.replace(tzinfo=timezone.utc).timestamp()) - now_epoch)
""",
            },
            "release-policy-integration-v1": {
                "policy.py": """import re


def parse_version(value):
    if not isinstance(value, str):
        raise TypeError
    if not re.fullmatch(r'(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)', value):
        raise ValueError
    return tuple(int(part) for part in value.split('.'))
""",
                "release.py": """from policy import parse_version


def release_decision(current, candidate, checks_passed, approved):
    if type(checks_passed) is not bool or type(approved) is not bool:
        raise TypeError
    current_version = parse_version(current)
    candidate_version = parse_version(candidate)
    if not checks_passed:
        return 'deny:checks'
    if candidate_version <= current_version:
        return 'deny:not-forward'
    if candidate_version[0] != current_version[0] and not approved:
        return 'deny:approval'
    return 'allow'
""",
            },
        }
        resources, _ = _load_resource_bundle(ROOT)
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for path in sorted(TASK_DIRECTORY.glob("*.json")):
                task, _ = load_task(path, root=ROOT)
                repo = root / task["id"] / "repo"
                _write_initial_repository(task, repo, resources)
                bad = _run_oracle(task, repo)
                self.assertFalse(bad["ok"], task["id"])
                if task["id"] == "release-policy-integration-v1":
                    (repo / "policy.py").write_text(
                        (repo / "policy.py").read_text(encoding="utf-8") + "\n# touched only\n",
                        encoding="utf-8",
                    )
                    (repo / "release.py").write_text(
                        """import re


def release_decision(current, candidate, checks_passed, approved):
    pattern = r'(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)'
    if not isinstance(current, str) or not isinstance(candidate, str):
        raise TypeError
    if not re.fullmatch(pattern, current) or not re.fullmatch(pattern, candidate):
        raise ValueError
    current_version = tuple(int(part) for part in current.split('.'))
    candidate_version = tuple(int(part) for part in candidate.split('.'))
    if not checks_passed:
        return 'deny:checks'
    if candidate_version <= current_version:
        return 'deny:not-forward'
    if candidate_version[0] != current_version[0] and not approved:
        return 'deny:approval'
    return 'allow'
""",
                        encoding="utf-8",
                    )
                    bypass = _run_oracle(task, repo)
                    self.assertFalse(bypass["ok"], bypass)
                    (repo / "policy.py").write_text(
                        """def parse_version(value):
    if not isinstance(value, str):
        raise TypeError
    parts = value.split('.')
    if any(len(part) > 1 and part.startswith('0') for part in parts):
        raise ValueError
    return tuple(int(part) for part in parts)
""",
                        encoding="utf-8",
                    )
                    (repo / "release.py").write_text(
                        """from policy import parse_version


def release_decision(current, candidate, checks_passed, approved):
    if type(checks_passed) is not bool or type(approved) is not bool:
        raise TypeError
    current_version = parse_version(current)
    candidate_version = parse_version(candidate)
    if not checks_passed:
        return 'deny:checks'
    if candidate_version <= current_version:
        return 'deny:not-forward'
    if candidate_version[0] != current_version[0] and not approved:
        return 'deny:approval'
    return 'allow'
""",
                        encoding="utf-8",
                    )
                    shape_bypass = _run_oracle(task, repo)
                    self.assertFalse(shape_bypass["ok"], shape_bypass)
                    (repo / "policy.py").write_text(
                        reference_solutions[task["id"]]["policy.py"], encoding="utf-8"
                    )
                    (repo / "release.py").write_text(
                        """import re


def release_decision(current, candidate, checks_passed, approved):
    if not isinstance(current, str) or not isinstance(candidate, str):
        raise TypeError
    if type(checks_passed) is not bool or type(approved) is not bool:
        raise TypeError
    if not re.fullmatch(r'[0-9]+(?:\\.[0-9]+)+', current):
        raise ValueError
    if not re.fullmatch(r'[0-9]+(?:\\.[0-9]+)+', candidate):
        raise ValueError
    current_version = tuple(int(part) for part in current.split('.'))
    candidate_version = tuple(int(part) for part in candidate.split('.'))
    if not checks_passed:
        return 'deny:checks'
    if candidate_version <= current_version:
        return 'deny:not-forward'
    if candidate_version[0] != current_version[0] and not approved:
        return 'deny:approval'
    return 'allow'
""",
                        encoding="utf-8",
                    )
                    seam_bypass = _run_oracle(task, repo)
                    self.assertFalse(seam_bypass["ok"], seam_bypass)
                for relative, content in reference_solutions[task["id"]].items():
                    (repo / relative).write_text(content, encoding="utf-8")
                good = _run_oracle(task, repo)
                self.assertTrue(good["ok"], {"task": task["id"], "result": good})

    def test_cross_file_trial_requires_every_declared_writable_path_to_change(self) -> None:
        record = valid_result()["lanes"]["bare"]["trials"][0]
        record["changed_paths"] = ["release.py"]
        record["scope_result"] = {
            "ok": True,
            "allowed_paths": ["policy.py", "release.py"],
        }
        record["test_result"] = {
            "ok": True,
            "passed": 10,
            "failed_case_ids": [],
            "elapsed_seconds": 0.1,
            "timed_out": False,
        }
        self.assertFalse(trial_passed(record, ["policy.py", "release.py"]))
        record["changed_paths"] = ["policy.py", "release.py"]
        self.assertTrue(trial_passed(record, ["policy.py", "release.py"]))

    @unittest.skipUnless(
        bubblewrap_available(), "unprivileged Bubblewrap unavailable in this test boundary"
    )
    def test_oracle_does_not_expose_hidden_expectations_to_generated_code(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            repo = Path(name) / "repo"
            resources, _ = _load_resource_bundle(ROOT)
            _write_initial_repository(self.task, repo, resources)
            (repo / "identifier.py").write_text(
                """import os


def canonical_identifier(value):
    if 'HARNESS_ORACLE' in os.environ:
        return 'would-game-hidden-expectations'
    raise RuntimeError('hidden expectations unavailable')
""",
                encoding="utf-8",
            )
            result = _run_oracle(self.task, repo)
            self.assertFalse(result["ok"])
            self.assertEqual(0, result["passed"])
            self.assertEqual(7, len(result["failed_case_ids"]))

    def test_cli_check_never_invokes_a_model(self) -> None:
        result = subprocess.run(
            ["python3", "tools/model_stress_runner.py", "check"],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["model_invoked"])

    def test_cli_subscription_check_fails_closed_without_chatgpt_login(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            result = subprocess.run(
                [
                    "python3",
                    "tools/model_stress_runner.py",
                    "check",
                    "--execution-target",
                    CODEX_SOL_CONTROL_TARGET,
                    "--codex-auth-path",
                    str(Path(name) / "missing-auth.json"),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                capture_output=True,
            )
        self.assertEqual(2, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertFalse(payload["model_invoked"])
        self.assertFalse(payload["capabilities"]["codex_chatgpt_subscription_ready"])

    def test_cli_subscription_check_rejects_malformed_claim_without_traceback(self) -> None:
        account = "account-test"
        payload = {
            "auth_mode": "chatgpt",
            "OPENAI_API_KEY": None,
            "tokens": {
                "access_token": codex_access_token(
                    account,
                    int(time.time()) + 7200,
                    auth_claim="not-an-object",
                ),
                "account_id": account,
            },
        }
        with tempfile.TemporaryDirectory() as name:
            auth = Path(name) / "auth.json"
            auth.write_text(json.dumps(payload), encoding="utf-8")
            auth.chmod(0o600)
            result = subprocess.run(
                [
                    "python3",
                    "tools/model_stress_runner.py",
                    "check",
                    "--execution-target",
                    CODEX_SOL_CONTROL_TARGET,
                    "--codex-auth-path",
                    str(auth),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                capture_output=True,
            )
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        self.assertNotIn("Traceback", result.stdout)
        output = json.loads(result.stdout)
        self.assertFalse(output["ok"])
        self.assertFalse(output["model_invoked"])
        self.assertIn(
            "auth claim is invalid",
            output["capabilities"]["codex_chatgpt_subscription_error"],
        )

    def test_codex_catalog_preflight_uses_sanitized_environment(self) -> None:
        executable = Path("/opt/pi/bin/pi")
        fake_root = Path("/opt/pi")
        with (
            patch("harness.runtime.model_stress_runner._pi_root", return_value=fake_root),
            patch("harness.runtime.model_stress_runner.subprocess.run") as run,
        ):
            run.return_value.returncode = 0

            def populate_output(command, **kwargs):
                kwargs["stdout"].write(
                    b"provider model context max-out thinking images\n"
                    b"openai-codex gpt-5.6-sol 272K 4.1K yes yes\n"
                )
                return run.return_value

            run.side_effect = populate_output
            codex_catalog_preflight(executable)
        command = run.call_args.args[0]
        environment = run.call_args.kwargs["env"]
        self.assertNotIn("OPENAI_API_KEY", environment)
        self.assertNotIn("CODEX_HOME", environment)
        self.assertIn("--offline", command)
        self.assertIn("--no-extensions", command)
        self.assertEqual("openai-codex", command[command.index("--provider") + 1])
        self.assertEqual("gpt-5.6-sol", command[-1])

    def test_cli_check_rejects_symlink_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            base = Path(name)
            actual = base / "actual"
            task = actual / "harness/model-stress/tasks/identifier-canonicalization-v1.json"
            task.parent.mkdir(parents=True)
            shutil.copy2(TASK_PATH, task)
            linked = base / "linked"
            linked.symlink_to(actual, target_is_directory=True)
            result = subprocess.run(
                [
                    "python3",
                    "tools/model_stress_runner.py",
                    "check",
                    "--root",
                    str(linked),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                capture_output=True,
            )
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertFalse(payload["model_invoked"])

    def test_pi_version_uses_networkless_read_only_self_contained_installation(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            binary = Path(name) / "bin"
            binary.mkdir()
            node = binary / "node"
            node.write_text("#!/bin/sh\n", encoding="utf-8")
            node.chmod(0o755)
            pi = binary / "pi"
            pi.write_text("#!/usr/bin/env node\n", encoding="utf-8")
            pi.chmod(0o755)
            completed = subprocess.CompletedProcess([], 0)

            def fake_run(*args, **kwargs):
                kwargs["stdout"].write(b"pi 9.8.7\n")
                return completed

            with patch(
                "harness.runtime.model_stress_runner.subprocess.run",
                side_effect=fake_run,
            ) as run:
                self.assertEqual("9.8.7", pi_version(pi))
            command = run.call_args.args[0]
            self.assertIn("--unshare-all", command)
            mount = command.index("/opt/pi-node")
            self.assertEqual("--ro-bind", command[mount - 2])
            self.assertEqual(str(Path(name)), command[mount - 1])

    def test_cli_rejects_output_before_model_invocation(self) -> None:
        from tools import model_stress_runner as cli

        argv = self._run_argv() + ["--output", "outside.json"]
        stream = io.StringIO()
        with (
            patch.object(sys, "argv", argv),
            patch.object(cli, "run_paired") as run,
            redirect_stdout(stream),
        ):
            self.assertEqual(2, cli.main())
        run.assert_not_called()
        self.assertFalse(json.loads(stream.getvalue())["model_invoked"])

    def test_cli_preserves_invocation_state_on_execution_failure(self) -> None:
        from tools import model_stress_runner as cli

        stream = io.StringIO()
        with (
            patch.object(sys, "argv", self._run_argv()),
            patch.object(
                cli,
                "run_paired",
                side_effect=RunnerExecutionError("after invocation", model_invoked=True),
            ),
            redirect_stdout(stream),
        ):
            self.assertEqual(2, cli.main())
        self.assertTrue(json.loads(stream.getvalue())["model_invoked"])

    @staticmethod
    def _run_argv() -> list[str]:
        return [
            "model_stress_runner.py",
            "run",
            "--root",
            str(ROOT),
            "--task",
            str(TASK_PATH),
            "--pi",
            "/tmp/pi/bin/pi",
            "--provider",
            "provider",
            "--model",
            "model",
            "--serving-runtime",
            "runtime",
            "--serving-recipe",
            "recipe",
        ]


if __name__ == "__main__":
    unittest.main()
