"""Safe, dependency-free paired runner for the supplemental local-model canary."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
import resource
import shutil
import signal
import stat
import subprocess
import tempfile
import time
from contextlib import nullcontext
from functools import partial
from pathlib import Path, PurePosixPath
from typing import Any

from harness.runtime.codex_subscription_proxy import (
    CONTROL_MODEL,
    CONTROL_REASONING_EFFORT,
    CodexSubscriptionCredential,
    SubscriptionBudget,
    SubscriptionProxyMetrics,
    codex_subscription_proxy,
    create_model_canary_token,
    load_codex_subscription,
)

MAXIMUM_TASK_BYTES = 256 * 1024
MAXIMUM_TRIALS = 10
MAXIMUM_SNAPSHOT_FILES = 1000
MAXIMUM_SNAPSHOT_FILE_BYTES = 1024 * 1024
MAXIMUM_SNAPSHOT_TOTAL_BYTES = 16 * 1024 * 1024
MODEL_MAX_TOKENS = 4096
LANES = ("bare", "harness")
TOOLS = ["read", "edit"]
LOCAL_QWEN_TARGET = "local-qwen"
CODEX_SOL_CONTROL_TARGET = "codex-subscription-sol"
EXECUTION_TARGETS = {LOCAL_QWEN_TARGET, CODEX_SOL_CONTROL_TARGET}
LOCAL_BASE_URL = "http://127.0.0.1:8000/v1"
CODEX_SUBSCRIPTION_BASE_URL = "https://chatgpt.com/backend-api"
CODEX_SUBSCRIPTION_PROVIDER = "openai-codex"
IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")
TASK_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CORPUS_TASK_CLASSES = {
    "identifier-canonicalization-v1": "implementation",
    "retry-after-repair-v1": "defect-repair",
    "release-policy-integration-v1": "cross-file-integration",
}
TASK_CLASSES = set(CORPUS_TASK_CLASSES.values())
RESULT_DIRECTORY = Path(".harness/model-stress")
RESOURCE_PATHS = (
    "AGENTS.md",
    "harness/project.yaml",
    "harness/loops/engineering-loop.yaml",
    "harness/roles/implementer.md",
    "docs/project/handoff.md",
    ".agents/skills/execute-engineering-loop/SKILL.md",
    ".agents/skills/execute-engineering-loop/references/handoff-contract.md",
    ".pi/extensions/context-readiness.ts",
)
FORBIDDEN_RESULT_KEYS = {
    "prompt",
    "transcript",
    "reasoning",
    "message",
    "content",
    "stdout",
    "stderr",
    "secret",
    "token",
}


class RunnerError(ValueError):
    """A fail-closed input, capability, or execution error."""


class RunnerExecutionError(RunnerError):
    """An execution error carrying truthful model-invocation state."""

    def __init__(self, message: str, *, model_invoked: bool) -> None:
        super().__init__(message)
        self.model_invoked = model_invoked


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RunnerError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _has_control_character(value: str) -> bool:
    return any(ord(character) < 32 for character in value)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _open_directory_nofollow(path: Path, *, label: str) -> int:
    absolute = Path(os.path.abspath(path))
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(absolute.anchor, flags)
    try:
        for component in absolute.parts[1:]:
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except OSError as exc:
        os.close(descriptor)
        raise RunnerError(f"{label} contains a symlink or non-directory component") from exc


def _read_regular_at(
    root_descriptor: int,
    relative: Path,
    *,
    maximum: int,
    label: str,
) -> bytes:
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise RunnerError(f"{label} must stay beneath its declared root")
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    file_flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    parent_descriptor = os.dup(root_descriptor)
    file_descriptor: int | None = None
    try:
        for component in relative.parts[:-1]:
            next_descriptor = os.open(component, directory_flags, dir_fd=parent_descriptor)
            os.close(parent_descriptor)
            parent_descriptor = next_descriptor
        name = relative.parts[-1]
        before = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
            raise RunnerError(f"{label} must be a bounded regular file")
        file_descriptor = os.open(name, file_flags, dir_fd=parent_descriptor)
        opened = os.fstat(file_descriptor)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
            before.st_dev,
            before.st_ino,
        ):
            raise RunnerError(f"{label} changed while opening")
        chunks: list[bytes] = []
        observed = 0
        while True:
            chunk = os.read(file_descriptor, min(65536, maximum + 1 - observed))
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
            if observed > maximum:
                raise RunnerError(f"{label} exceeds {maximum} bytes")
        after = os.fstat(file_descriptor)
        if (
            after.st_size != before.st_size
            or after.st_mtime_ns != before.st_mtime_ns
            or after.st_ctime_ns != before.st_ctime_ns
            or observed != before.st_size
        ):
            raise RunnerError(f"{label} changed while reading")
        return b"".join(chunks)
    except OSError as exc:
        raise RunnerError(f"{label} contains a symlink or invalid path component") from exc
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        os.close(parent_descriptor)


def _regular_bounded_json(path: Path, *, root: Path | None = None) -> tuple[Any, bytes]:
    target = Path(os.path.abspath(path))
    boundary = Path(os.path.abspath(root if root is not None else path.parent))
    try:
        relative = target.relative_to(boundary)
    except ValueError as exc:
        raise RunnerError("task must stay beneath the repository root") from exc
    root_descriptor = _open_directory_nofollow(boundary, label="task root")
    try:
        raw = _read_regular_at(
            root_descriptor,
            relative,
            maximum=MAXIMUM_TASK_BYTES,
            label="task",
        )
    finally:
        os.close(root_descriptor)
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys), raw
    except (UnicodeError, json.JSONDecodeError, RecursionError, RunnerError) as exc:
        raise RunnerError(f"invalid task JSON: {exc}") from exc


def normalize_path(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or "\\" in value
        or _has_control_character(value)
    ):
        raise RunnerError("task paths must be non-empty normalized POSIX strings")
    path = PurePosixPath(value)
    if len(value) > 160:
        raise RunnerError("task paths must be at most 160 characters")
    if (
        path.is_absolute()
        or value.startswith("./")
        or ".." in path.parts
        or path.as_posix() in {"", "."}
    ):
        raise RunnerError(f"unsafe repository-relative path: {value!r}")
    if any(part == ".harness" or part.startswith(".git") for part in path.parts):
        raise RunnerError(f"reserved path in task: {value!r}")
    return path.as_posix()


def normalize_observed_path(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or "\\" in value
        or _has_control_character(value)
    ):
        raise RunnerError("observed paths must be non-empty normalized POSIX strings")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value.startswith("./")
        or ".." in path.parts
        or path.as_posix() in {"", "."}
    ):
        raise RunnerError(f"unsafe observed repository-relative path: {value!r}")
    return path.as_posix()


def _json_scalar(value: Any) -> bool:
    return value is None or (
        isinstance(value, (str, int, float, bool))
        and not (isinstance(value, float) and not math.isfinite(value))
    )


def _json_return_value(value: Any) -> bool:
    return _json_scalar(value) or (
        isinstance(value, list) and len(value) <= 8 and all(_json_scalar(item) for item in value)
    )


def validate_task(task: Any) -> list[str]:
    try:
        _validate_task(task)
    except (RunnerError, TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def _validate_task(task: Any) -> None:
    if not isinstance(task, dict):
        raise RunnerError("task must be an object")
    expected = {
        "schema_version",
        "id",
        "task_class",
        "prompt",
        "initial_files",
        "writable_paths",
        "oracle",
        "limits",
    }
    if set(task) != expected:
        raise RunnerError("task has missing or unknown top-level keys")
    if task["schema_version"] != "1.1":
        raise RunnerError("task schema_version must be 1.1")
    task_id = task["id"]
    if not isinstance(task_id, str) or len(task_id) > 80 or not TASK_ID.fullmatch(task_id):
        raise RunnerError("task id is invalid")
    if task["task_class"] not in TASK_CLASSES:
        raise RunnerError("task class is invalid")
    if task_id in CORPUS_TASK_CLASSES and task["task_class"] != CORPUS_TASK_CLASSES[task_id]:
        raise RunnerError("task id and class are inconsistent")
    prompt = task["prompt"]
    if (
        not isinstance(prompt, str)
        or not prompt.strip()
        or prompt != prompt.strip()
        or len(prompt) > 4000
        or "\x00" in prompt
    ):
        raise RunnerError(
            "task prompt must be a trimmed non-empty string of at most 4000 characters"
        )
    files = task["initial_files"]
    if not isinstance(files, list) or not 2 <= len(files) <= 20:
        raise RunnerError("initial_files must contain 2 to 20 entries")
    paths: list[str] = []
    total_bytes = 0
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "content"}:
            raise RunnerError("each initial file must define only path and content")
        path = normalize_path(item["path"])
        content = item["content"]
        if not isinstance(content, str):
            raise RunnerError(f"initial file content must be text: {path}")
        if "\x00" in content:
            raise RunnerError(f"initial file content cannot contain NUL: {path}")
        size = len(content.encode("utf-8"))
        if size > 65536:
            raise RunnerError(f"initial file exceeds 65536 bytes: {path}")
        total_bytes += size
        paths.append(path)
    if len(set(paths)) != len(paths) or total_bytes > 256 * 1024:
        raise RunnerError("initial files must be unique and total at most 256 KiB")
    for path in paths:
        if any(
            path == resource or path.startswith(resource + "/") or resource.startswith(path + "/")
            for resource in RESOURCE_PATHS
        ):
            raise RunnerError("initial files cannot replace lane harness resources")
    for left in paths:
        for right in paths:
            if left != right and right.startswith(left + "/"):
                raise RunnerError("initial file paths cannot contain file/directory collisions")
    writable = task["writable_paths"]
    if not isinstance(writable, list) or not 1 <= len(writable) <= 5:
        raise RunnerError("writable_paths must contain 1 to 5 paths")
    normalized_writable = [normalize_path(path) for path in writable]
    if len(set(normalized_writable)) != len(normalized_writable) or not set(
        normalized_writable
    ) <= set(paths):
        raise RunnerError("writable_paths must be unique initial-file paths")

    oracle = task["oracle"]
    if not isinstance(oracle, dict) or set(oracle) != {"targets"}:
        raise RunnerError("oracle must define only targets")
    targets = oracle["targets"]
    if not isinstance(targets, list) or not 1 <= len(targets) <= 5:
        raise RunnerError("oracle targets must contain 1 to 5 entries")
    case_ids: list[str] = []
    target_ids: list[tuple[str, str]] = []
    for target in targets:
        if not isinstance(target, dict) or set(target) != {
            "module",
            "function",
            "cases",
            "raises",
        }:
            raise RunnerError("each oracle target must define module, function, cases, and raises")
        for key in ("module", "function"):
            value = target[key]
            if not isinstance(value, str) or len(value) > 80 or not IDENTIFIER.fullmatch(value):
                raise RunnerError(f"oracle target {key} is invalid")
        target_id = (target["module"], target["function"])
        target_ids.append(target_id)
        module_path = target["module"] + ".py"
        if module_path not in paths:
            raise RunnerError("oracle target module must name an initial top-level Python file")
        if not target["cases"] and not target["raises"]:
            raise RunnerError("each oracle target must contain at least one case")
        for key, required_key in (("cases", "expected"), ("raises", "exception")):
            records = target[key]
            maximum = 50
            if not isinstance(records, list) or len(records) > maximum:
                raise RunnerError(f"oracle target {key} has an invalid count")
            expected_keys = {"id", "args", required_key}
            for record in records:
                if not isinstance(record, dict) or set(record) != expected_keys:
                    raise RunnerError(f"oracle target {key} entry has an invalid shape")
                if not isinstance(record["id"], str) or not TASK_ID.fullmatch(record["id"]):
                    raise RunnerError(f"oracle target {key} id is invalid")
                if len(record["id"]) > 80:
                    raise RunnerError(f"oracle target {key} id exceeds 80 characters")
                if (
                    not isinstance(record["args"], list)
                    or len(record["args"]) > 8
                    or not all(_json_scalar(arg) for arg in record["args"])
                ):
                    raise RunnerError(f"oracle target {key} args must be JSON scalars")
                if required_key == "expected" and not _json_return_value(record[required_key]):
                    raise RunnerError(
                        "oracle expected values must be JSON scalars or scalar arrays"
                    )
                if required_key == "exception" and record[required_key] not in {
                    "TypeError",
                    "ValueError",
                }:
                    raise RunnerError("oracle exception must be TypeError or ValueError")
                case_ids.append(record["id"])
    if len(set(target_ids)) != len(target_ids):
        raise RunnerError("oracle targets must be unique")
    if len(set(case_ids)) != len(case_ids):
        raise RunnerError("oracle case ids must be unique")
    if len(case_ids) > 70:
        raise RunnerError("oracle must contain at most 70 cases")

    limits = task["limits"]
    expected_limits = {
        "model_timeout_seconds",
        "oracle_timeout_seconds",
        "maximum_event_bytes",
        "maximum_changed_files",
    }
    if not isinstance(limits, dict) or set(limits) != expected_limits:
        raise RunnerError("task limits have an invalid shape")
    bounds = {
        "model_timeout_seconds": (30, 900),
        "oracle_timeout_seconds": (1, 30),
        "maximum_event_bytes": (65536, 8388608),
        "maximum_changed_files": (1, 5),
    }
    for key, (minimum, maximum) in bounds.items():
        value = limits[key]
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            raise RunnerError(f"task limit {key} must be between {minimum} and {maximum}")
    if limits["maximum_changed_files"] < len(normalized_writable):
        raise RunnerError("maximum_changed_files cannot be less than writable_paths")


def load_task(path: Path, *, root: Path | None = None) -> tuple[dict[str, Any], str]:
    task, raw = _regular_bounded_json(path, root=root)
    errors = validate_task(task)
    if errors:
        raise RunnerError(errors[0])
    return task, sha256_bytes(raw)


def validate_trials(value: int) -> str:
    if isinstance(value, bool) or value < 1 or value > MAXIMUM_TRIALS or value == 2:
        raise RunnerError("trials must be 1 for smoke or 3 to 10 for acceptance-candidate evidence")
    return "smoke" if value == 1 else "acceptance-candidate"


def trial_passed(record: dict[str, Any], required_paths: list[str]) -> bool:
    return (
        record["test_result"]["ok"]
        and record["scope_result"]["ok"]
        and set(record["changed_paths"]) == set(required_paths)
        and record["returncode"] == 0
        and record["settled"]
        and record["event_limit_ok"]
        and not record["timed_out"]
    )


def validate_result(payload: Any) -> list[str]:
    try:
        _validate_result(payload)
    except (RunnerError, TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def _validate_result(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise RunnerError("result must be an object")
    expected = {
        "schema_version",
        "authority",
        "evidence_level",
        "accepted_baseline",
        "model_invoked",
        "provenance",
        "provider_boundary",
        "task",
        "limits",
        "trial_count",
        "lanes",
        "comparison",
    }
    if set(payload) != expected:
        raise RunnerError("result has missing or unknown top-level keys")
    if payload["schema_version"] != "1.3" or payload["authority"] != "supplemental":
        raise RunnerError("result identity or authority is invalid")
    if payload["accepted_baseline"] is not False or payload["model_invoked"] is not True:
        raise RunnerError(
            "runner results cannot self-approve and must represent a model invocation"
        )
    trials = payload["trial_count"]
    level = validate_trials(trials)
    if payload["evidence_level"] != level:
        raise RunnerError("result evidence level does not match trial count")
    provenance = payload["provenance"]
    provenance_keys = {
        "model",
        "provider",
        "pi_version",
        "serving_runtime",
        "serving_recipe",
        "endpoint_class",
    }
    if not isinstance(provenance, dict) or set(provenance) != provenance_keys:
        raise RunnerError("result provenance is incomplete")
    for key, value in provenance.items():
        if (
            not isinstance(value, str)
            or not value
            or value != value.strip()
            or len(value) > 512
            or _has_control_character(value)
        ):
            raise RunnerError(f"result provenance {key} is invalid")
    if provenance["endpoint_class"] not in {
        "local-loopback-openai-compatible",
        "credential-isolated-chatgpt-codex-subscription",
    }:
        raise RunnerError("result endpoint class is invalid")
    if not re.fullmatch(r"\d+\.\d+\.\d+", provenance["pi_version"]):
        raise RunnerError("result Pi version is invalid")
    boundary = payload["provider_boundary"]
    boundary_keys = {
        "execution_target",
        "reasoning_effort",
        "credential_delivery",
        "output_token_limit_enforcement",
        "maximum_requests",
        "maximum_request_bytes",
        "observed_requests",
        "observed_request_bytes",
    }
    if not isinstance(boundary, dict) or set(boundary) != boundary_keys:
        raise RunnerError("result provider boundary is invalid")
    numeric_keys = boundary_keys - {
        "execution_target",
        "reasoning_effort",
        "credential_delivery",
        "output_token_limit_enforcement",
    }
    if any(
        isinstance(boundary[key], bool) or not isinstance(boundary[key], int) or boundary[key] < 0
        for key in numeric_keys
    ):
        raise RunnerError("result provider boundary counters are invalid")
    target = boundary["execution_target"]
    if target == LOCAL_QWEN_TARGET:
        if (
            provenance["endpoint_class"] != "local-loopback-openai-compatible"
            or boundary["reasoning_effort"] != "not-applicable"
            or boundary["credential_delivery"] != "synthetic-placeholder"
            or boundary["output_token_limit_enforcement"] != "provider-request"
            or any(boundary[key] != 0 for key in numeric_keys)
        ):
            raise RunnerError("result local provider boundary is inconsistent")
    elif target == CODEX_SOL_CONTROL_TARGET:
        if (
            provenance["endpoint_class"] != "credential-isolated-chatgpt-codex-subscription"
            or provenance["provider"] != CODEX_SUBSCRIPTION_PROVIDER
            or provenance["model"] != CONTROL_MODEL
            or boundary["reasoning_effort"] != CONTROL_REASONING_EFFORT
            or boundary["credential_delivery"] != "host-subscription-relay"
            or boundary["output_token_limit_enforcement"] != "runner-config-only"
            or not 1 <= boundary["maximum_requests"] <= 100
            or not 1024 <= boundary["maximum_request_bytes"] <= 8 * 1024 * 1024
            or boundary["observed_requests"] > boundary["maximum_requests"]
            or boundary["observed_request_bytes"] > boundary["maximum_request_bytes"]
        ):
            raise RunnerError("result Codex subscription boundary is inconsistent")
    else:
        raise RunnerError("result execution target is invalid")
    task = payload["task"]
    task_keys = {
        "id",
        "task_class",
        "task_digest",
        "prompt_digest",
        "tool_set",
        "oracle_case_count",
        "oracle_case_ids",
        "resource_bundle_digest",
        "writable_paths",
    }
    if not isinstance(task, dict) or set(task) != task_keys:
        raise RunnerError("result task identity is invalid")
    if not isinstance(task["id"], str) or len(task["id"]) > 80 or not TASK_ID.fullmatch(task["id"]):
        raise RunnerError("result task id is invalid")
    if task["task_class"] not in TASK_CLASSES:
        raise RunnerError("result task class is invalid")
    if task["id"] in CORPUS_TASK_CLASSES and task["task_class"] != CORPUS_TASK_CLASSES[task["id"]]:
        raise RunnerError("result task id and class are inconsistent")
    for key in ("task_digest", "prompt_digest"):
        if not isinstance(task[key], str) or not re.fullmatch(r"[0-9a-f]{64}", task[key]):
            raise RunnerError(f"result {key} is invalid")
    if not isinstance(task["resource_bundle_digest"], str) or not re.fullmatch(
        r"[0-9a-f]{64}", task["resource_bundle_digest"]
    ):
        raise RunnerError("result resource bundle digest is invalid")
    if task["tool_set"] != TOOLS:
        raise RunnerError("result tool set is invalid")
    oracle_case_count = task["oracle_case_count"]
    if (
        isinstance(oracle_case_count, bool)
        or not isinstance(oracle_case_count, int)
        or not 1 <= oracle_case_count <= 70
    ):
        raise RunnerError("result oracle case count is invalid")
    oracle_case_ids = task["oracle_case_ids"]
    if (
        not isinstance(oracle_case_ids, list)
        or len(oracle_case_ids) != oracle_case_count
        or len(oracle_case_ids) != len(set(oracle_case_ids))
        or not all(
            isinstance(case_id, str) and len(case_id) <= 80 and TASK_ID.fullmatch(case_id)
            for case_id in oracle_case_ids
        )
    ):
        raise RunnerError("result oracle case identities are invalid")
    writable_paths = task["writable_paths"]
    if not isinstance(writable_paths, list):
        raise RunnerError("result writable paths are invalid")
    try:
        normalized_writable = [normalize_path(path) for path in writable_paths]
    except RunnerError as exc:
        raise RunnerError("result writable paths are invalid") from exc
    if (
        not normalized_writable
        or normalized_writable != sorted(set(normalized_writable))
        or len(normalized_writable) > 5
    ):
        raise RunnerError("result writable paths are invalid")
    limits = payload["limits"]
    expected_limits = {
        "model_timeout_seconds": (30, 900),
        "oracle_timeout_seconds": (1, 30),
        "maximum_event_bytes": (65536, 8388608),
        "maximum_changed_files": (1, 5),
        "maximum_output_tokens": (1, MODEL_MAX_TOKENS),
    }
    if not isinstance(limits, dict) or set(limits) != set(expected_limits):
        raise RunnerError("result limits are invalid")
    for key, (minimum, maximum) in expected_limits.items():
        value = limits[key]
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            raise RunnerError(f"result limit {key} is invalid")
    if limits["maximum_output_tokens"] != MODEL_MAX_TOKENS:
        raise RunnerError("result model output-token limit is invalid")
    lanes = payload["lanes"]
    if not isinstance(lanes, dict) or set(lanes) != set(LANES):
        raise RunnerError("result must contain bare and harness lanes")
    for lane in LANES:
        summary = lanes[lane]
        if not isinstance(summary, dict) or set(summary) != {
            "passed_trials",
            "total_trials",
            "trials",
        }:
            raise RunnerError(f"result {lane} summary is invalid")
        records = summary["trials"]
        if (
            isinstance(summary["total_trials"], bool)
            or not isinstance(summary["total_trials"], int)
            or summary["total_trials"] != trials
            or not isinstance(records, list)
            or len(records) != trials
        ):
            raise RunnerError(f"result {lane} trial count is invalid")
        passed_trials = summary["passed_trials"]
        if (
            isinstance(passed_trials, bool)
            or not isinstance(passed_trials, int)
            or not 0 <= passed_trials <= trials
        ):
            raise RunnerError(f"result {lane} pass count is invalid")
        observed_trials: set[int] = set()
        for record in records:
            keys = {
                "returncode",
                "settled",
                "timed_out",
                "event_limit_ok",
                "elapsed_seconds",
                "changed_paths",
                "scope_result",
                "tool_errors",
                "usage",
                "trial",
                "test_result",
            }
            if not isinstance(record, dict) or set(record) != keys:
                raise RunnerError(f"result {lane} trial shape is invalid")
            if isinstance(record["trial"], bool) or record["trial"] not in range(1, trials + 1):
                raise RunnerError(f"result {lane} trial identity is invalid")
            observed_trials.add(record["trial"])
            if (
                isinstance(record["returncode"], bool)
                or not isinstance(record["returncode"], int)
                or type(record["settled"]) is not bool
                or type(record["timed_out"]) is not bool
                or type(record["event_limit_ok"]) is not bool
                or isinstance(record["elapsed_seconds"], bool)
                or not isinstance(record["elapsed_seconds"], (int, float))
                or not math.isfinite(record["elapsed_seconds"])
                or record["elapsed_seconds"] < 0
            ):
                raise RunnerError(f"result {lane} execution fields are invalid")
            if record["timed_out"] != (record["returncode"] == 124):
                raise RunnerError(f"result {lane} timeout state is inconsistent")
            changed_paths = record["changed_paths"]
            if not isinstance(changed_paths, list) or len(changed_paths) != len(set(changed_paths)):
                raise RunnerError(f"result {lane} changed paths are invalid")
            try:
                normalized_changed = [normalize_observed_path(path) for path in changed_paths]
            except RunnerError as exc:
                raise RunnerError(f"result {lane} changed paths are invalid") from exc
            scope = record["scope_result"]
            if not isinstance(scope, dict) or set(scope) != {"ok", "allowed_paths"}:
                raise RunnerError(f"result {lane} scope result is invalid")
            allowed_paths = scope["allowed_paths"]
            if type(scope["ok"]) is not bool or not isinstance(allowed_paths, list):
                raise RunnerError(f"result {lane} scope result is invalid")
            try:
                normalized_allowed = [normalize_path(path) for path in allowed_paths]
            except RunnerError as exc:
                raise RunnerError(f"result {lane} allowed paths are invalid") from exc
            if normalized_allowed != normalized_writable:
                raise RunnerError(f"result {lane} allowed paths are invalid")
            expected_scope = len(normalized_changed) <= limits["maximum_changed_files"] and set(
                normalized_changed
            ) <= set(normalized_allowed)
            if scope["ok"] is not expected_scope:
                raise RunnerError(f"result {lane} scope state is inconsistent")
            tool_errors = record["tool_errors"]
            if not isinstance(tool_errors, list) or not isinstance(record["usage"], dict):
                raise RunnerError(f"result {lane} sanitized metrics are invalid")
            observed_tools: set[str] = set()
            for error in tool_errors:
                if not isinstance(error, dict) or set(error) != {"tool", "category", "count"}:
                    raise RunnerError(f"result {lane} tool error is invalid")
                if (
                    error["tool"] not in {"read", "edit", "unavailable"}
                    or error["category"] != "tool-execution-error"
                    or isinstance(error["count"], bool)
                    or not isinstance(error["count"], int)
                    or error["count"] < 1
                    or error["tool"] in observed_tools
                ):
                    raise RunnerError(f"result {lane} tool error is invalid")
                observed_tools.add(error["tool"])
            usage = record["usage"]
            usage_keys = {
                "measurement_origin",
                "input_tokens",
                "output_tokens",
                "cache_read_tokens",
                "cache_write_tokens",
            }
            if set(usage) != usage_keys or usage["measurement_origin"] not in {
                "provider-reported",
                "unavailable",
            }:
                raise RunnerError(f"result {lane} usage provenance is invalid")
            numeric_values = [usage[key] for key in usage_keys - {"measurement_origin"}]
            if usage["measurement_origin"] == "unavailable":
                if any(value is not None for value in numeric_values):
                    raise RunnerError(f"result {lane} unavailable usage must be null")
            elif not all(
                isinstance(value, int) and not isinstance(value, bool) and value >= 0
                for value in numeric_values
            ):
                raise RunnerError(f"result {lane} provider usage must be nonnegative integers")
            test_result = record["test_result"]
            test_keys = {"ok", "passed", "failed_case_ids", "elapsed_seconds", "timed_out"}
            if not isinstance(test_result, dict) or set(test_result) != test_keys:
                raise RunnerError(f"result {lane} test result is invalid")
            failed_ids = test_result["failed_case_ids"]
            if (
                type(test_result["ok"]) is not bool
                or type(test_result["timed_out"]) is not bool
                or isinstance(test_result["passed"], bool)
                or not isinstance(test_result["passed"], int)
                or not 0 <= test_result["passed"] <= oracle_case_count
                or not isinstance(failed_ids, list)
                or len(failed_ids) != len(set(failed_ids))
                or not all(isinstance(item, str) and TASK_ID.fullmatch(item) for item in failed_ids)
                or not set(failed_ids) <= set(oracle_case_ids)
                or test_result["passed"] + len(failed_ids) != oracle_case_count
                or isinstance(test_result["elapsed_seconds"], bool)
                or not isinstance(test_result["elapsed_seconds"], (int, float))
                or not math.isfinite(test_result["elapsed_seconds"])
                or test_result["elapsed_seconds"] < 0
            ):
                raise RunnerError(f"result {lane} test result is invalid")
            expected_test_ok = (
                test_result["passed"] == oracle_case_count
                and not failed_ids
                and not test_result["timed_out"]
            )
            if test_result["ok"] is not expected_test_ok:
                raise RunnerError(f"result {lane} test state is inconsistent")
        if observed_trials != set(range(1, trials + 1)):
            raise RunnerError(f"result {lane} trial identities are incomplete")
        if passed_trials != sum(
            1 for record in records if trial_passed(record, normalized_writable)
        ):
            raise RunnerError(f"result {lane} pass count is inconsistent")
    comparison = payload["comparison"]
    if (
        not isinstance(comparison, dict)
        or set(comparison)
        != {
            "bare_passed_trials",
            "harness_passed_trials",
            "observed_pass_difference",
            "general_harness_lift_claim",
        }
        or type(comparison["bare_passed_trials"]) is not int
        or type(comparison["harness_passed_trials"]) is not int
        or type(comparison["observed_pass_difference"]) is not int
        or comparison["bare_passed_trials"] != lanes["bare"]["passed_trials"]
        or comparison["harness_passed_trials"] != lanes["harness"]["passed_trials"]
        or comparison["observed_pass_difference"]
        != lanes["harness"]["passed_trials"] - lanes["bare"]["passed_trials"]
        or comparison["general_harness_lift_claim"] is not False
    ):
        raise RunnerError("result comparison is invalid or overclaims harness lift")
    stack: list[Any] = [payload]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            for key, child in value.items():
                if key.lower() in FORBIDDEN_RESULT_KEYS:
                    raise RunnerError(f"result contains forbidden content key: {key}")
                stack.append(child)
        elif isinstance(value, list):
            stack.extend(value)


def safe_output_path(root: Path, output: Path) -> Path:
    root = root.resolve()
    candidate = output if output.is_absolute() else root / output
    try:
        relative = candidate.absolute().relative_to(root)
    except ValueError as exc:
        raise RunnerError("output must stay inside the repository") from exc
    value = relative.as_posix()
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or value in {"", "."} or "\\" in value:
        raise RunnerError("output must be a normalized repository-relative path")
    normalized = path.as_posix()
    if not (
        normalized == RESULT_DIRECTORY.as_posix()
        or normalized.startswith(RESULT_DIRECTORY.as_posix() + "/")
    ):
        raise RunnerError("output must stay under .harness/model-stress")
    current = root
    for part in PurePosixPath(normalized).parts[:-1]:
        current = current / part
        if current.exists() and (current.is_symlink() or not current.is_dir()):
            raise RunnerError(f"unsafe output ancestor: {current}")
    if candidate.exists() and (candidate.is_symlink() or not candidate.is_file()):
        raise RunnerError("output must be a regular file path")
    return candidate


def _bounded_file_digest(path: Path, maximum: int) -> tuple[str, int]:
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
        raise RunnerError(f"file is not a bounded regular file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    digest = hashlib.sha256()
    observed = 0
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
            before.st_dev,
            before.st_ino,
        ):
            raise RunnerError(f"file changed while opening: {path}")
        while True:
            chunk = os.read(descriptor, min(65536, maximum + 1 - observed))
            if not chunk:
                break
            observed += len(chunk)
            if observed > maximum:
                raise RunnerError(f"file exceeds {maximum} bytes: {path}")
            digest.update(chunk)
    finally:
        os.close(descriptor)
    return digest.hexdigest(), observed


def _snapshot(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    total_bytes = 0
    inspected_paths = 0
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        inspected_paths += 1
        if inspected_paths > MAXIMUM_SNAPSHOT_FILES:
            raise RunnerError(
                f"disposable repository exceeds {MAXIMUM_SNAPSHOT_FILES} inspectable paths"
            )
        if path.is_symlink():
            values[relative.as_posix()] = "symlink:" + os.readlink(path)
        elif path.is_file():
            digest, size = _bounded_file_digest(path, MAXIMUM_SNAPSHOT_FILE_BYTES)
            total_bytes += size
            if total_bytes > MAXIMUM_SNAPSHOT_TOTAL_BYTES:
                raise RunnerError("disposable repository exceeds the 16 MiB snapshot content bound")
            values[relative.as_posix()] = digest
    return values


def _changed_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))


def _load_resource_bundle(source_root: Path) -> tuple[dict[str, bytes], str]:
    resources: dict[str, bytes] = {}
    digest = hashlib.sha256()
    root_descriptor = _open_directory_nofollow(source_root, label="resource root")
    try:
        for relative in RESOURCE_PATHS:
            value = _read_regular_at(
                root_descriptor,
                Path(relative),
                maximum=MAXIMUM_TASK_BYTES,
                label=f"lane resource {relative}",
            )
            resources[relative] = value
            encoded_path = relative.encode("utf-8")
            digest.update(len(encoded_path).to_bytes(4, "big"))
            digest.update(encoded_path)
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
    finally:
        os.close(root_descriptor)
    return resources, digest.hexdigest()


def _write_initial_repository(
    task: dict[str, Any], repo: Path, resources: dict[str, bytes]
) -> None:
    if set(resources) != set(RESOURCE_PATHS) or not all(
        isinstance(value, bytes) and len(value) <= MAXIMUM_TASK_BYTES
        for value in resources.values()
    ):
        raise RunnerError("frozen lane resource bundle is invalid")
    repo.mkdir(parents=True)
    for item in task["initial_files"]:
        path = repo / item["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item["content"], encoding="utf-8")
    for relative in RESOURCE_PATHS:
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        value = resources[relative]
        target.write_bytes(value)
    environment = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(repo.parent / "git-home"),
        "LANG": "C.UTF-8",
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    Path(environment["HOME"]).mkdir()
    commands = (
        ["git", "init", "--quiet", "--template=", str(repo)],
        ["git", "-C", str(repo), "config", "user.name", "Harness Canary"],
        ["git", "-C", str(repo), "config", "user.email", "canary@example.invalid"],
        ["git", "-C", str(repo), "add", "--all"],
        ["git", "-C", str(repo), "commit", "--quiet", "-m", "canary baseline"],
    )
    for command in commands:
        completed = subprocess.run(command, check=False, capture_output=True, env=environment)
        if completed.returncode:
            raise RunnerError("could not initialize disposable repository")


def _pi_root(executable: Path) -> Path:
    supplied = executable.absolute()
    if supplied.name != "pi" or supplied.parent.name != "bin":
        raise RunnerError("Pi executable must be the bin/pi path of a self-contained installation")
    root = supplied.parent.parent
    if (
        not supplied.exists()
        or not os.access(supplied, os.X_OK)
        or not (root / "bin/node").is_file()
    ):
        raise RunnerError("Pi executable or adjacent Node runtime is unavailable")
    return root


def _write_pi_config(
    home: Path,
    provider: str,
    model: str,
    base_url: str,
    *,
    execution_target: str = LOCAL_QWEN_TARGET,
) -> None:
    agent = home / ".pi/agent"
    agent.mkdir(parents=True)
    if execution_target == LOCAL_QWEN_TARGET:
        provider_payload: dict[str, Any] = {
            "baseUrl": base_url,
            "api": "openai-completions",
            "apiKey": "not-needed",
            "compat": {
                "supportsDeveloperRole": False,
                "supportsReasoningEffort": False,
            },
            "models": [
                {
                    "id": model,
                    "name": "Harness model-stress target",
                    "input": ["text"],
                    "contextWindow": 262144,
                    "maxTokens": MODEL_MAX_TOKENS,
                }
            ],
        }
        settings: dict[str, Any] = {}
    elif execution_target == CODEX_SOL_CONTROL_TARGET:
        provider_payload = {
            "baseUrl": base_url,
            "apiKey": "not-needed",
            "modelOverrides": {model: {"maxTokens": MODEL_MAX_TOKENS}},
        }
        settings = {"transport": "sse"}
    else:
        raise RunnerError("unknown execution target")
    payload = {"providers": {provider: provider_payload}}
    (agent / "models.json").write_text(json.dumps(payload), encoding="utf-8")
    (agent / "settings.json").write_text(json.dumps(settings) + "\n", encoding="utf-8")


def codex_catalog_preflight(executable: Path) -> None:
    """Resolve the exact Sol model in isolated Pi config without a network call."""
    installation = _pi_root(executable)
    maximum_output_bytes = 64 * 1024
    with tempfile.TemporaryDirectory(prefix="harness-codex-catalog-") as temp_name:
        home = Path(temp_name)
        _write_pi_config(
            home,
            CODEX_SUBSCRIPTION_PROVIDER,
            CONTROL_MODEL,
            "http://127.0.0.1:9/backend-api",
            execution_target=CODEX_SOL_CONTROL_TARGET,
        )
        command = [
            str(executable.absolute()),
            "--offline",
            "--approve",
            "--api-key",
            create_model_canary_token(),
            "--provider",
            CODEX_SUBSCRIPTION_PROVIDER,
            "--no-extensions",
            "--no-skills",
            "--no-prompt-templates",
            "--no-themes",
            "--no-context-files",
            "--list-models",
            CONTROL_MODEL,
        ]
        environment = {
            "HOME": str(home),
            "PI_CODING_AGENT_DIR": str(home / ".pi/agent"),
            "PI_OFFLINE": "1",
            "PI_TELEMETRY": "0",
            "PATH": f"{installation / 'bin'}:/usr/bin:/bin",
            "LANG": "C.UTF-8",
        }
        with tempfile.TemporaryFile() as output_file:
            try:
                completed = subprocess.run(
                    command,
                    check=False,
                    stdin=subprocess.DEVNULL,
                    stdout=output_file,
                    stderr=subprocess.DEVNULL,
                    env=environment,
                    timeout=30,
                    preexec_fn=partial(_model_preexec, maximum_output_bytes),
                )
            except subprocess.TimeoutExpired as exc:
                raise RunnerError("Pi Codex catalog preflight timed out") from exc
            output_file.seek(0)
            output = output_file.read(maximum_output_bytes)
        if completed.returncode or len(output) >= maximum_output_bytes:
            raise RunnerError("Pi Codex catalog preflight failed")
        rows = [line.split() for line in output.decode("utf-8", errors="replace").splitlines()]
        if not any(
            len(row) >= 2 and row[0] == CODEX_SUBSCRIPTION_PROVIDER and row[1] == CONTROL_MODEL
            for row in rows
        ):
            raise RunnerError("Pi did not resolve the exact Codex subscription model")


def _base_bwrap(repo: Path, config_home: Path, pi_root: Path) -> list[str]:
    command = [
        "bwrap",
        "--die-with-parent",
        "--new-session",
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
        "--ro-bind",
        "/usr",
        "/usr",
        "--symlink",
        "usr/bin",
        "/bin",
        "--symlink",
        "usr/lib",
        "/lib",
    ]
    if Path("/usr/lib64").exists():
        command.extend(["--symlink", "usr/lib64", "/lib64"])
    command.extend(
        [
            "--ro-bind",
            str(pi_root),
            "/opt/pi-node",
            "--bind",
            str(repo),
            "/work",
            "--dir",
            "/home",
            "--dir",
            "/home/canary",
            "--dir",
            "/home/canary/.pi",
            "--dir",
            "/home/canary/.pi/agent",
            "--ro-bind",
            str(config_home / ".pi/agent/models.json"),
            "/home/canary/.pi/agent/models.json",
            "--ro-bind",
            str(config_home / ".pi/agent/settings.json"),
            "/home/canary/.pi/agent/settings.json",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
            "--chdir",
            "/work",
            "--clearenv",
            "--setenv",
            "HOME",
            "/home/canary",
            "--setenv",
            "PI_CODING_AGENT_DIR",
            "/home/canary/.pi/agent",
            "--setenv",
            "PI_OFFLINE",
            "1",
            "--setenv",
            "PI_TELEMETRY",
            "0",
            "--setenv",
            "NO_PROXY",
            "127.0.0.1,localhost",
            "--setenv",
            "PATH",
            "/opt/pi-node/bin:/usr/bin:/bin",
            "--setenv",
            "LANG",
            "C.UTF-8",
        ]
    )
    return command


def build_pi_command(
    *,
    lane: str,
    repo: Path,
    config_home: Path,
    pi_root: Path,
    provider: str,
    model: str,
    prompt: str,
    execution_target: str = LOCAL_QWEN_TARGET,
    auth_override: str = "not-needed",
) -> list[str]:
    if lane not in LANES:
        raise RunnerError(f"unknown lane: {lane}")
    command = _base_bwrap(repo, config_home, pi_root)
    command.extend(
        [
            "/opt/pi-node/bin/pi",
            "--provider",
            provider,
            "--model",
            model,
            "--api-key",
            auth_override,
            "--approve",
            "--offline",
            "--no-session",
            "--no-prompt-templates",
            "--no-themes",
            "--mode",
            "json",
            "--tools",
            ",".join(TOOLS),
        ]
    )
    if execution_target == CODEX_SOL_CONTROL_TARGET:
        command.extend(["--thinking", CONTROL_REASONING_EFFORT])
    elif execution_target != LOCAL_QWEN_TARGET:
        raise RunnerError("unknown execution target")
    if lane == "bare":
        command.extend(["--no-context-files", "--no-skills", "--no-extensions"])
    else:
        command.extend(
            [
                "--no-extensions",
                "--extension",
                "/work/.pi/extensions/context-readiness.ts",
                "--no-skills",
                "--skill",
                "/work/.agents/skills/execute-engineering-loop",
            ]
        )
    command.extend(["-p", prompt])
    return command


def _parse_events(output: bytes, maximum: int) -> tuple[list[dict[str, Any]], bool]:
    if len(output) >= maximum:
        return [], False
    events: list[dict[str, Any]] = []
    for line in output.decode("utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line, object_pairs_hook=_reject_duplicate_keys)
        except (json.JSONDecodeError, RecursionError, RunnerError):
            continue
        if isinstance(value, dict):
            events.append(value)
    return events, True


def _sanitized_event_metrics(
    events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], bool]:
    errors: dict[tuple[str, str], int] = {}
    usage_values = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
    }
    aliases = {
        "input": "input_tokens",
        "output": "output_tokens",
        "cacheRead": "cache_read_tokens",
        "cacheWrite": "cache_write_tokens",
    }
    usage_available = False
    settled = False
    for event in events:
        if event.get("type") == "agent_settled":
            settled = True
        if event.get("type") == "tool_execution_end" and event.get("isError") is True:
            observed_name = event.get("toolName")
            name = observed_name if observed_name in TOOLS else "unavailable"
            errors[(name, "tool-execution-error")] = (
                errors.get((name, "tool-execution-error"), 0) + 1
            )
        if event.get("type") == "message_end":
            message = event.get("message")
            candidate = message.get("usage") if isinstance(message, dict) else None
            if isinstance(candidate, dict):
                values: dict[str, int] = {}
                for source, target in aliases.items():
                    child = candidate.get(source)
                    if isinstance(child, int) and not isinstance(child, bool) and child >= 0:
                        values[target] = child
                if set(values) == set(usage_values):
                    usage_available = True
                    for key, value in values.items():
                        usage_values[key] += value
    sanitized = [
        {"tool": key[0], "category": key[1], "count": count}
        for key, count in sorted(errors.items())
    ]
    usage: dict[str, Any] = {
        "measurement_origin": "provider-reported" if usage_available else "unavailable"
    }
    usage.update(usage_values if usage_available else {key: None for key in usage_values})
    return sanitized, usage, settled


def _model_preexec(maximum_event_bytes: int) -> None:
    resource.setrlimit(
        resource.RLIMIT_FSIZE,
        (maximum_event_bytes, maximum_event_bytes),
    )


def _run_model_lane(
    *,
    lane: str,
    task: dict[str, Any],
    repo: Path,
    config_home: Path,
    pi_root: Path,
    provider: str,
    model: str,
    execution_target: str = LOCAL_QWEN_TARGET,
    auth_override: str = "not-needed",
) -> dict[str, Any]:
    before = _snapshot(repo)
    command = build_pi_command(
        lane=lane,
        repo=repo,
        config_home=config_home,
        pi_root=pi_root,
        provider=provider,
        model=model,
        prompt=task["prompt"],
        execution_target=execution_target,
        auth_override=auth_override,
    )
    started = time.monotonic()
    timed_out = False
    maximum_event_bytes = task["limits"]["maximum_event_bytes"]
    with tempfile.TemporaryFile() as event_file:
        try:
            completed = subprocess.run(
                command,
                check=False,
                stdout=event_file,
                stderr=subprocess.DEVNULL,
                env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
                timeout=task["limits"]["model_timeout_seconds"],
                preexec_fn=partial(_model_preexec, maximum_event_bytes),
            )
            returncode = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            returncode = 124
        event_file.seek(0)
        output = event_file.read(maximum_event_bytes)
    elapsed = round(time.monotonic() - started, 3)
    events, within_event_limit = _parse_events(output, maximum_event_bytes)
    if returncode == -signal.SIGXFSZ:
        within_event_limit = False
    tool_errors, usage, settled = _sanitized_event_metrics(events)
    after = _snapshot(repo)
    changed = _changed_paths(before, after)
    allowed = set(task["writable_paths"])
    scope_ok = len(changed) <= task["limits"]["maximum_changed_files"] and set(changed) <= allowed
    return {
        "returncode": returncode,
        "settled": settled,
        "timed_out": timed_out,
        "event_limit_ok": within_event_limit,
        "elapsed_seconds": elapsed,
        "changed_paths": changed,
        "scope_result": {"ok": scope_ok, "allowed_paths": sorted(allowed)},
        "tool_errors": tool_errors,
        "usage": usage,
    }


def _current_user_task_limit() -> int:
    current_uid = os.getuid()
    tasks = 0
    try:
        for process in Path("/proc").iterdir():
            if not process.name.isdigit():
                continue
            try:
                if process.stat().st_uid != current_uid:
                    continue
                tasks += sum(1 for task in (process / "task").iterdir() if task.name.isdigit())
            except (FileNotFoundError, PermissionError):
                continue
    except OSError as exc:
        raise RunnerError("cannot establish the oracle process bound") from exc
    hard = resource.getrlimit(resource.RLIMIT_NPROC)[1]
    requested = tasks + 64
    return requested if hard == resource.RLIM_INFINITY else min(requested, hard)


def _oracle_preexec(nproc_limit: int, maximum_output_bytes: int) -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    resource.setrlimit(
        resource.RLIMIT_FSIZE,
        (maximum_output_bytes, maximum_output_bytes),
    )
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    # RLIMIT_NPROC counts every host-UID thread, not only this PID namespace.
    # The parent measures current use and permits at most 64 additional tasks.
    resource.setrlimit(resource.RLIMIT_NPROC, (nproc_limit, nproc_limit))


def _oracle_records(
    task: dict[str, Any],
) -> list[tuple[dict[str, Any], dict[str, Any], str]]:
    records: list[tuple[dict[str, Any], dict[str, Any], str]] = []
    for target in task["oracle"]["targets"]:
        records.extend((target, record, "expected") for record in target["cases"])
        records.extend((target, record, "exception") for record in target["raises"])
    return records


def _run_oracle(task: dict[str, Any], repo: Path) -> dict[str, Any]:
    script = """
import importlib, json, os, sys
decode=json.loads; encode=json.dumps; write=os.write
call=decode(os.environ['HARNESS_CALL'])
sys.path.insert(0, '/work')
try:
    function=getattr(importlib.import_module(call['module']),call['function'])
    try:
        value=function(*call['args'])
        result={'kind':'return','value':value}
    except BaseException as error:
        result={'kind':'raise','exception':type(error).__name__}
except BaseException as error:
    result={'kind':'harness-error','exception':type(error).__name__}
write(1,(encode(result,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8'))
"""
    started = time.monotonic()
    nproc_limit = _current_user_task_limit()
    maximum_output_bytes = 64 * 1024
    failed: list[str] = []
    passed = 0
    timed_out = False
    records = _oracle_records(task)
    deadline = started + task["limits"]["oracle_timeout_seconds"]
    for index, (target, record, expectation) in enumerate(records):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            failed.extend(item[1]["id"] for item in records[index:])
            break
        call = json.dumps(
            {
                "module": target["module"],
                "function": target["function"],
                "args": record["args"],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        command = [
            "bwrap",
            "--die-with-parent",
            "--new-session",
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
        ]
        if Path("/usr/lib64").exists():
            command.extend(["--symlink", "usr/lib64", "/lib64"])
        command.extend(
            [
                "--ro-bind",
                str(repo),
                "/work",
                "--dir",
                "/proc",
                "--dev",
                "/dev",
                "--tmpfs",
                "/tmp",
                "--chdir",
                "/work",
                "--clearenv",
                "--setenv",
                "HARNESS_CALL",
                call,
                "/usr/bin/python3",
                "-I",
                "-c",
                script,
            ]
        )
        with tempfile.TemporaryFile() as output_file:
            try:
                completed = subprocess.run(
                    command,
                    check=False,
                    stdout=output_file,
                    stderr=subprocess.DEVNULL,
                    env={"PATH": "/usr/bin:/bin"},
                    timeout=remaining,
                    preexec_fn=partial(
                        _oracle_preexec,
                        nproc_limit,
                        maximum_output_bytes,
                    ),
                )
            except subprocess.TimeoutExpired:
                timed_out = True
                failed.extend(item[1]["id"] for item in records[index:])
                break
            output_file.seek(0)
            output = output_file.read(maximum_output_bytes)
        observed: Any = None
        if completed.returncode == 0 and len(output) < maximum_output_bytes:
            lines = [line for line in output.splitlines() if line.strip()]
            try:
                observed = json.loads(lines[-1]) if lines else None
            except (UnicodeError, json.JSONDecodeError, RecursionError):
                observed = None
        valid = isinstance(observed, dict)
        if expectation == "expected":
            matches = (
                valid
                and set(observed) == {"kind", "value"}
                and observed["kind"] == "return"
                and observed["value"] == record["expected"]
            )
        else:
            matches = (
                valid
                and set(observed) == {"kind", "exception"}
                and observed["kind"] == "raise"
                and observed["exception"] == record["exception"]
            )
        if matches:
            passed += 1
        else:
            failed.append(record["id"])
    elapsed = round(time.monotonic() - started, 3)
    total = len(records)
    return {
        "ok": passed == total and not failed,
        "passed": passed,
        "failed_case_ids": failed,
        "elapsed_seconds": elapsed,
        "timed_out": timed_out,
    }


def pi_version(executable: Path) -> str:
    installation = _pi_root(executable)
    command = [
        "bwrap",
        "--die-with-parent",
        "--new-session",
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
    ]
    if Path("/usr/lib64").exists():
        command.extend(["--symlink", "usr/lib64", "/lib64"])
    command.extend(
        [
            "--ro-bind",
            str(installation),
            "/opt/pi-node",
            "--dir",
            "/home",
            "--dir",
            "/home/canary",
            "--tmpfs",
            "/tmp",
            "--clearenv",
            "--setenv",
            "HOME",
            "/home/canary",
            "--setenv",
            "PATH",
            "/opt/pi-node/bin:/usr/bin:/bin",
            "--setenv",
            "PI_OFFLINE",
            "1",
            "/opt/pi-node/bin/pi",
            "--version",
        ]
    )
    maximum_output_bytes = 64 * 1024
    with tempfile.TemporaryFile() as output_file:
        try:
            completed = subprocess.run(
                command,
                check=False,
                stdout=output_file,
                stderr=subprocess.DEVNULL,
                env={"PATH": "/usr/bin:/bin"},
                timeout=15,
                preexec_fn=partial(_model_preexec, maximum_output_bytes),
            )
        except subprocess.TimeoutExpired as exc:
            raise RunnerError("Pi version check timed out") from exc
        output_file.seek(0)
        output = output_file.read(maximum_output_bytes)
    if completed.returncode:
        raise RunnerError("could not determine Pi version")
    if len(output) >= maximum_output_bytes:
        raise RunnerError("Pi version output exceeded its bound")
    match = re.search(rb"\b\d+\.\d+\.\d+\b", output)
    if not match:
        raise RunnerError("Pi version output was not recognized")
    return match.group(0).decode("ascii")


def codex_subscription_budget(*, trials: int, model_timeout_seconds: int) -> SubscriptionBudget:
    """Return the fixed per-task budget for a paired Sol subscription run."""
    lane_trials = trials * len(LANES)
    return SubscriptionBudget(
        maximum_requests=lane_trials * 5,
        maximum_request_bytes=lane_trials * 256 * 1024,
        upstream_timeout_seconds=model_timeout_seconds,
    )


def run_paired(
    *,
    source_root: Path,
    task: dict[str, Any],
    task_digest: str,
    executable: Path,
    provider: str,
    model: str,
    base_url: str,
    serving_runtime: str,
    serving_recipe: str,
    trials: int,
    execution_target: str = LOCAL_QWEN_TARGET,
    codex_auth_path: Path | None = None,
) -> dict[str, Any]:
    model_invoked = False
    try:
        level = validate_trials(trials)
        task_errors = validate_task(task)
        if task_errors:
            raise RunnerError(task_errors[0])
        task = copy.deepcopy(task)
        if not isinstance(task_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", task_digest):
            raise RunnerError("task digest must be a lowercase SHA-256 value")
        if not isinstance(executable, Path):
            raise RunnerError("Pi executable must be supplied as a path")
        if shutil.which("bwrap") is None:
            raise RunnerError("bubblewrap is required for live model-stress execution")
        if execution_target not in EXECUTION_TARGETS:
            raise RunnerError("execution target is invalid")
        for label, value in (
            ("provider", provider),
            ("model", model),
            ("base URL", base_url),
            ("serving runtime", serving_runtime),
            ("serving recipe", serving_recipe),
        ):
            if (
                not isinstance(value, str)
                or not value.strip()
                or value != value.strip()
                or _has_control_character(value)
            ):
                raise RunnerError(f"{label} must be a trimmed non-empty string")
            if len(value) > 512:
                raise RunnerError(f"{label} exceeds 512 characters")
        control_budget: SubscriptionBudget | None = None
        credential: CodexSubscriptionCredential | None = None
        if execution_target == LOCAL_QWEN_TARGET:
            if base_url != LOCAL_BASE_URL:
                raise RunnerError("the local Qwen target requires the approved loopback endpoint")
        else:
            if provider != CODEX_SUBSCRIPTION_PROVIDER or model != CONTROL_MODEL:
                raise RunnerError(
                    "the Codex subscription control requires its exact provider and model"
                )
            if base_url != CODEX_SUBSCRIPTION_BASE_URL:
                raise RunnerError("the Codex subscription control requires the ChatGPT backend")
            if not isinstance(codex_auth_path, Path):
                raise RunnerError("the Codex subscription control requires an explicit auth path")
            credential = load_codex_subscription(
                codex_auth_path,
                minimum_lifetime_seconds=(
                    task["limits"]["model_timeout_seconds"] * trials * len(LANES) + 600
                ),
            )
            control_budget = codex_subscription_budget(
                trials=trials,
                model_timeout_seconds=task["limits"]["model_timeout_seconds"],
            )
        installation = _pi_root(executable)
        version = pi_version(executable)
        resources, resource_bundle_digest = _load_resource_bundle(source_root)
        lane_results: dict[str, list[dict[str, Any]]] = {lane: [] for lane in LANES}
        proxy_context = (
            codex_subscription_proxy(credential=credential, budget=control_budget)
            if control_budget is not None and credential is not None
            else nullcontext(None)
        )
        control_metrics = SubscriptionProxyMetrics(0, 0)
        with proxy_context as proxy:
            effective_base_url = proxy.base_url if proxy is not None else base_url
            with tempfile.TemporaryDirectory(prefix="harness-model-stress-") as temp_name:
                temp = Path(temp_name)
                seed_repo = temp / "seed-repo"
                _write_initial_repository(task, seed_repo, resources)
                seed_snapshot = _snapshot(seed_repo)
                for trial in range(1, trials + 1):
                    for lane in LANES:
                        lane_root = temp / f"trial-{trial}-{lane}"
                        repo = lane_root / "repo"
                        home = lane_root / "home"
                        shutil.copytree(seed_repo, repo, symlinks=True)
                        if _snapshot(repo) != seed_snapshot:
                            raise RunnerError(
                                "disposable repository clone differs from frozen seed"
                            )
                        _write_pi_config(
                            home,
                            provider,
                            model,
                            effective_base_url,
                            execution_target=execution_target,
                        )
                        model_invoked = True
                        result = _run_model_lane(
                            lane=lane,
                            task=task,
                            repo=repo,
                            config_home=home,
                            pi_root=installation,
                            provider=provider,
                            model=model,
                            execution_target=execution_target,
                            auth_override=(
                                proxy.model_token if proxy is not None else "not-needed"
                            ),
                        )
                        result["trial"] = trial
                        result["test_result"] = _run_oracle(task, repo)
                        lane_results[lane].append(result)
            if proxy is not None:
                control_metrics = proxy.metrics
        lane_summary: dict[str, Any] = {}
        for lane, results in lane_results.items():
            passed = sum(1 for item in results if trial_passed(item, task["writable_paths"]))
            lane_summary[lane] = {
                "passed_trials": passed,
                "total_trials": trials,
                "trials": results,
            }
        bare_passed = lane_summary["bare"]["passed_trials"]
        harness_passed = lane_summary["harness"]["passed_trials"]
        return {
            "schema_version": "1.3",
            "authority": "supplemental",
            "evidence_level": level,
            "accepted_baseline": False,
            "model_invoked": True,
            "provenance": {
                "model": model,
                "provider": provider,
                "pi_version": version,
                "serving_runtime": serving_runtime,
                "serving_recipe": serving_recipe,
                "endpoint_class": (
                    "credential-isolated-chatgpt-codex-subscription"
                    if execution_target == CODEX_SOL_CONTROL_TARGET
                    else "local-loopback-openai-compatible"
                ),
            },
            "provider_boundary": {
                "execution_target": execution_target,
                "reasoning_effort": (
                    CONTROL_REASONING_EFFORT
                    if execution_target == CODEX_SOL_CONTROL_TARGET
                    else "not-applicable"
                ),
                "credential_delivery": (
                    "host-subscription-relay"
                    if execution_target == CODEX_SOL_CONTROL_TARGET
                    else "synthetic-placeholder"
                ),
                "output_token_limit_enforcement": (
                    "runner-config-only"
                    if execution_target == CODEX_SOL_CONTROL_TARGET
                    else "provider-request"
                ),
                "maximum_requests": control_budget.maximum_requests if control_budget else 0,
                "maximum_request_bytes": (
                    control_budget.maximum_request_bytes if control_budget else 0
                ),
                "observed_requests": control_metrics.requests,
                "observed_request_bytes": control_metrics.request_bytes,
            },
            "task": {
                "id": task["id"],
                "task_class": task["task_class"],
                "task_digest": task_digest,
                "prompt_digest": sha256_bytes(task["prompt"].encode("utf-8")),
                "tool_set": TOOLS,
                "oracle_case_count": len(_oracle_records(task)),
                "oracle_case_ids": [record["id"] for _, record, _ in _oracle_records(task)],
                "resource_bundle_digest": resource_bundle_digest,
                "writable_paths": sorted(task["writable_paths"]),
            },
            "limits": {**task["limits"], "maximum_output_tokens": MODEL_MAX_TOKENS},
            "trial_count": trials,
            "lanes": lane_summary,
            "comparison": {
                "bare_passed_trials": bare_passed,
                "harness_passed_trials": harness_passed,
                "observed_pass_difference": harness_passed - bare_passed,
                "general_harness_lift_claim": False,
            },
        }
    except RunnerExecutionError:
        raise
    except (
        OSError,
        RunnerError,
        subprocess.SubprocessError,
        TypeError,
        ValueError,
        RecursionError,
    ) as exc:
        raise RunnerExecutionError(str(exc), model_invoked=model_invoked) from exc


def write_result(path: Path, payload: dict[str, Any]) -> None:
    errors = validate_result(payload)
    if errors:
        raise RunnerError(errors[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)
