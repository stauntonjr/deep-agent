#!/usr/bin/env python3
"""Validate the model-stress policy and report whether a live canary is due."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any

RELEASE_IMPACTS = {"none", "patch", "minor", "major"}
CANARY = {
    "family": "qwen-coder",
    "provider": "runtime-selected",
    "model": "runtime-selected",
}
MAXIMUM_REPORTED_LOOPS = 10
RELEASE_TRIGGER_IMPACTS = ["minor", "major"]
CONTROL_PATH_PREFIXES = [
    ".agents/skills/",
    ".pi/",
    "harness/adapters/",
    "harness/loops/",
    "harness/roles/",
    "tools/loop.py",
]
MINIMUM_ACCEPTED_TRIALS = 3
MAXIMUM_CONTRACT_BYTES = 256 * 1024
REQUIRED_EVIDENCE = [
    "model",
    "provider",
    "pi_version",
    "serving_runtime",
    "serving_recipe",
    "task_id",
    "prompt_digest",
    "tool_set",
    "limits",
    "trial_count",
    "test_result",
    "scope_result",
    "tool_errors",
    "elapsed_seconds",
]


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def load_contract(path: Path) -> Any:
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("model-stress contract must be a regular file, not a symlink or device")
    if before.st_size > MAXIMUM_CONTRACT_BYTES:
        raise ValueError(f"model-stress contract exceeds {MAXIMUM_CONTRACT_BYTES} bytes")

    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError("model-stress contract must be a regular file")
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise ValueError("model-stress contract changed while it was being opened")
        if opened.st_size > MAXIMUM_CONTRACT_BYTES:
            raise ValueError(f"model-stress contract exceeds {MAXIMUM_CONTRACT_BYTES} bytes")
        chunks: list[bytes] = []
        remaining = MAXIMUM_CONTRACT_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
    finally:
        os.close(descriptor)
    raw = b"".join(chunks)
    if len(raw) > MAXIMUM_CONTRACT_BYTES:
        raise ValueError(f"model-stress contract exceeds {MAXIMUM_CONTRACT_BYTES} bytes")
    return json.loads(raw.decode("utf-8"))


def default_repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def normalize_repository_path(value: Any) -> str:
    if not nonempty_string(value):
        raise ValueError("changed paths must be non-empty normalized strings")
    if "\\" in value:
        raise ValueError(f"changed path must use POSIX separators: {value!r}")
    while value.startswith("./"):
        value = value[2:]
    if not value:
        raise ValueError("changed path cannot resolve to the repository root")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"changed path must stay repository-relative: {value!r}")
    normalized = path.as_posix()
    if normalized in {"", "."}:
        raise ValueError("changed path cannot resolve to the repository root")
    return normalized


def path_matches_prefix(path: str, prefix: str) -> bool:
    if prefix.endswith("/"):
        return path == prefix.rstrip("/") or path.startswith(prefix)
    return path == prefix


def validate_contract(contract: Any) -> list[str]:
    if not isinstance(contract, dict):
        return ["model-stress contract must be an object"]
    errors: list[str] = []
    expected = {
        "schema_version",
        "authority",
        "canary",
        "triggers",
        "execution",
        "required_evidence",
    }
    if set(contract) != expected:
        errors.append("model-stress contract has missing or unknown top-level keys")
    if contract.get("schema_version") != "1.0":
        errors.append("model-stress schema_version must be 1.0")
    if contract.get("authority") != "supplemental":
        errors.append("model-stress authority must remain supplemental")

    canary = contract.get("canary")
    if not isinstance(canary, dict) or set(canary) != {"family", "provider", "model"}:
        errors.append("model-stress canary must define only family, provider, and model")
    elif canary != CANARY:
        errors.append("model-stress canary must retain the canonical Qwen runtime selection")

    triggers = contract.get("triggers")
    trigger_keys = {"maximum_reported_loops_between_runs", "release_impacts", "path_prefixes"}
    if not isinstance(triggers, dict) or set(triggers) != trigger_keys:
        errors.append("model-stress triggers have an invalid shape")
    else:
        maximum = triggers.get("maximum_reported_loops_between_runs")
        if maximum != MAXIMUM_REPORTED_LOOPS or isinstance(maximum, bool):
            errors.append(
                f"maximum reported loops between runs must remain {MAXIMUM_REPORTED_LOOPS}"
            )
        impacts = triggers.get("release_impacts")
        if impacts != RELEASE_TRIGGER_IMPACTS:
            errors.append("model-stress release impacts must remain minor then major")
        prefixes = triggers.get("path_prefixes")
        if prefixes != CONTROL_PATH_PREFIXES:
            errors.append("model-stress path prefixes must match the canonical control paths")

    execution = contract.get("execution")
    execution_keys = {
        "lanes",
        "minimum_trials_for_acceptance",
        "disposable_repository",
        "network_writes",
        "raw_transcript_retention",
        "model_self_approval",
    }
    if not isinstance(execution, dict) or set(execution) != execution_keys:
        errors.append("model-stress execution has an invalid shape")
    else:
        if execution.get("lanes") != ["bare", "harness"]:
            errors.append("model-stress lanes must be bare then harness")
        trials = execution.get("minimum_trials_for_acceptance")
        if trials != MINIMUM_ACCEPTED_TRIALS or isinstance(trials, bool):
            errors.append(f"minimum accepted trials must remain {MINIMUM_ACCEPTED_TRIALS}")
        for key, expected_value in (
            ("disposable_repository", True),
            ("network_writes", False),
            ("raw_transcript_retention", False),
            ("model_self_approval", False),
        ):
            if execution.get(key) is not expected_value:
                errors.append(
                    f"model-stress execution requires {key}={str(expected_value).lower()}"
                )

    evidence = contract.get("required_evidence")
    if not isinstance(evidence, list) or evidence != REQUIRED_EVIDENCE:
        errors.append("model-stress required evidence does not match the canonical set")
    return errors


def due_reasons(
    contract: dict[str, Any],
    *,
    has_accepted_evidence: bool,
    reported_loops_since: int,
    changed_paths: list[str],
    release_impact: str,
) -> list[str]:
    reasons: list[str] = []
    if not has_accepted_evidence:
        reasons.append("no accepted model-stress evidence exists")
    maximum = contract["triggers"]["maximum_reported_loops_between_runs"]
    if reported_loops_since >= maximum:
        reasons.append(
            f"{reported_loops_since} reported loops reached the cadence limit of {maximum}"
        )
    prefixes = contract["triggers"]["path_prefixes"]
    matched = sorted(
        path
        for path in changed_paths
        if any(path_matches_prefix(path, prefix) for prefix in prefixes)
    )
    if matched:
        reasons.append("agent-control paths changed: " + ", ".join(matched))
    if release_impact in contract["triggers"]["release_impacts"]:
        reasons.append(f"{release_impact} release assessment requires a canary")
    return reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "status"))
    parser.add_argument("--root", type=Path)
    parser.add_argument("--accepted-evidence", action="store_true")
    parser.add_argument("--reported-loops-since", type=int, default=0)
    parser.add_argument("--changed-path", action="append", default=[])
    parser.add_argument("--release-impact", choices=sorted(RELEASE_IMPACTS), default="none")
    args = parser.parse_args()
    root = args.root.resolve() if args.root else default_repository_root()
    try:
        contract = load_contract(root / "harness/model-stress.json")
        errors = validate_contract(contract)
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        errors = [f"cannot read model-stress contract: {exc}"]
        contract = {}
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    if args.action == "check":
        print(json.dumps({"ok": True, "authority": contract["authority"]}, indent=2))
        return 0
    if args.reported_loops_since < 0:
        print(
            json.dumps(
                {"ok": False, "errors": ["reported loops since cannot be negative"]}, indent=2
            )
        )
        return 1
    try:
        changed_paths = [normalize_repository_path(path) for path in args.changed_path]
        reasons = due_reasons(
            contract,
            has_accepted_evidence=args.accepted_evidence,
            reported_loops_since=args.reported_loops_since,
            changed_paths=changed_paths,
            release_impact=args.release_impact,
        )
    except (TypeError, ValueError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        return 1
    print(
        json.dumps(
            {
                "ok": True,
                "due": bool(reasons),
                "reasons": reasons,
                "model_invoked": False,
                "authority": contract["authority"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
