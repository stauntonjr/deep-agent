.PHONY: check test compile actions-supply-chain project-check smoke template-smoke application-smoke planning-audit challenge-validate challenges recovery-check harness-version product-version harness-lock harness-eval-validate model-stress-check model-stress-runner-check pi-runtime-check plugin-check plugin-sync

check:
	python3 tools/harness_check.py

test:
	@python3 -c 'import json, subprocess, sys; project = json.load(open("harness/project.yaml", encoding="utf-8")); sys.exit(subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]) if project.get("template_mode") else 0)'

compile:
	python3 -m compileall -q tools

actions-supply-chain:
	python3 tools/check_actions_supply_chain.py

project-check:
	python3 tools/run_quality.py

smoke:
	@python3 -c 'import json, subprocess; project = json.load(open("harness/project.yaml", encoding="utf-8")); target = "template-smoke" if project.get("template_mode") else "application-smoke"; subprocess.run(["make", target], check=True)'

template-smoke: check actions-supply-chain compile test project-check challenge-validate recovery-check model-stress-check model-stress-runner-check

application-smoke: check compile project-check

planning-audit:
	python3 tools/github_planning.py audit --offline

challenge-validate:
	python3 tools/run_challenges.py

challenges:
	python3 tools/run_challenges.py --run

recovery-check:
	python3 tools/recovery_scenarios.py

harness-version:
	python3 tools/harness_upgrade.py status

product-version:
	python3 tools/product_version.py

harness-lock:
	python3 tools/harness_upgrade.py lock --yes

harness-eval-validate:
	python3 tools/evaluate_harness.py

model-stress-check:
	python3 tools/model_stress.py check

model-stress-runner-check:
	python3 tools/model_stress_runner.py check

pi-runtime-check:
	python3 tools/pi_adapter_check.py

plugin-check:
	python3 tools/skill_plugin.py check

plugin-sync:
	python3 tools/skill_plugin.py sync --yes
