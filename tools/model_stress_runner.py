#!/usr/bin/env python3
"""Validate or run the bounded paired local-model canary."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.runtime.codex_subscription_proxy import (  # noqa: E402
    SubscriptionProxyError,
    load_codex_subscription,
)
from harness.runtime.model_stress_runner import (  # noqa: E402
    CODEX_SOL_CONTROL_TARGET,
    EXECUTION_TARGETS,
    LOCAL_QWEN_TARGET,
    RunnerError,
    RunnerExecutionError,
    codex_catalog_preflight,
    load_task,
    run_paired,
    safe_output_path,
    validate_result,
    validate_trials,
    write_result,
)

DEFAULT_TASK = Path("harness/model-stress/tasks/identifier-canonicalization-v1.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "run"))
    parser.add_argument("--root", type=Path)
    parser.add_argument("--task", type=Path, default=DEFAULT_TASK)
    parser.add_argument("--pi", type=Path)
    parser.add_argument("--provider")
    parser.add_argument("--model")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument(
        "--execution-target",
        choices=sorted(EXECUTION_TARGETS),
        default=LOCAL_QWEN_TARGET,
    )
    parser.add_argument("--serving-runtime")
    parser.add_argument("--serving-recipe")
    parser.add_argument(
        "--codex-auth-path",
        type=Path,
        default=Path.home() / ".codex/auth.json",
    )
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.absolute() if args.root else ROOT
    task_path = args.task if args.task.is_absolute() else root / args.task
    model_invoked = False
    try:
        task, digest = load_task(task_path, root=root)
        level = validate_trials(args.trials)
        if args.action == "check":
            check_ok = True
            subscription_ready = False
            subscription_error = None
            if args.execution_target == CODEX_SOL_CONTROL_TARGET:
                try:
                    load_codex_subscription(args.codex_auth_path)
                    if args.pi is None:
                        raise RunnerError("subscription preflight requires the exact Pi executable")
                    codex_catalog_preflight(args.pi)
                    subscription_ready = True
                except (RunnerError, SubscriptionProxyError) as exc:
                    check_ok = False
                    subscription_error = str(exc)
            print(
                json.dumps(
                    {
                        "ok": check_ok,
                        "model_invoked": False,
                        "task_id": task["id"],
                        "task_class": task["task_class"],
                        "task_digest": digest,
                        "evidence_level_if_run": level,
                        "capabilities": {
                            "bubblewrap": shutil.which("bwrap") is not None,
                            "pi_argument_required_for_run": True,
                            "codex_chatgpt_subscription_ready": subscription_ready,
                            "codex_chatgpt_subscription_error": subscription_error,
                        },
                    },
                    indent=2,
                )
            )
            return 0 if check_ok else 2
        missing = [
            name
            for name, value in (
                ("pi", args.pi),
                ("provider", args.provider),
                ("model", args.model),
                ("serving-runtime", args.serving_runtime),
                ("serving-recipe", args.serving_recipe),
            )
            if value is None
        ]
        if missing:
            raise RunnerError("run requires explicit " + ", ".join(missing))
        output_path = safe_output_path(root, args.output) if args.output else None
        payload = run_paired(
            source_root=root,
            task=task,
            task_digest=digest,
            executable=args.pi,
            provider=args.provider,
            model=args.model,
            base_url=args.base_url,
            serving_runtime=args.serving_runtime,
            serving_recipe=args.serving_recipe,
            trials=args.trials,
            execution_target=args.execution_target,
            codex_auth_path=args.codex_auth_path,
        )
        model_invoked = True
        errors = validate_result(payload)
        if errors:
            raise RunnerError(errors[0])
        if output_path:
            write_result(output_path, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return (
            0
            if all(
                payload["lanes"][lane]["passed_trials"] == args.trials
                for lane in ("bare", "harness")
            )
            else 1
        )
    except RunnerExecutionError as exc:
        print(
            json.dumps(
                {"ok": False, "model_invoked": exc.model_invoked, "errors": [str(exc)]},
                indent=2,
            )
        )
        return 2
    except (OSError, RunnerError, TypeError, ValueError, RecursionError) as exc:
        print(
            json.dumps(
                {"ok": False, "model_invoked": model_invoked, "errors": [str(exc)]},
                indent=2,
            )
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
