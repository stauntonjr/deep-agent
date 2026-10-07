# DeepAgent

A browser evidence assistant built with [LangChain DeepAgents](https://github.com/langchain-ai/deepagents), powered by a locally hosted DGX model. It delegates procurement investigations through an authenticated A2A bridge and checks scientific claims through SciFact MCP.

**Working local demo.** The real DGX → A2A → procurement and SciFact browser journeys have passed, including evidence downloads and isolation between viewers. Procurement uses the admitted **synthetic** corpus from `procurement-intelligence-lab`. OCI deployment and procurement human review/save are not enabled.

## What you can try

- **Investigate a discrepancy:** compare GPU-A requirements against purchase orders, identify the 8-required / 6-ordered discrepancy, and inspect its 12 source records.
- **Check a claim:** ask whether evidence establishes that vitamin D reduces multiple-sclerosis risk in humans; distinguish animal evidence, association and causal claims.
- Download evidence, reload investigation history, and use separate viewer accounts with isolated sessions and tasks.

The agent must call an approved evidence tool before answering. Unsupported final answers are rejected. A returned tool result establishes evidence availability; it does not guarantee that every generated claim is correct. This first slice supports evidence investigations; unrestricted personal-assistant and coding tools remain future work.

## Install

Python 3.12 and [uv](https://docs.astral.sh/uv/) are required.

```sh
uv sync --frozen
make smoke
```

## Run locally on DGX

Run from this repository. Keep the existing model server running; it must expose an OpenAI-compatible `/v1` endpoint with tool calling. For the verified DGX setup that endpoint is `http://172.17.0.1:8000/v1`, serving `nvidia/Qwen3.6-35B-A3B-NVFP4`. Check your host's binding before using that address elsewhere.

Create a private viewer credential file and a shared bridge token outside Git. This prompts for your own password; it never prints the token. For another viewer, repeat the password block with a different username and append a record to the same file.

```sh
export DEEPAGENT_USERS_FILE="$HOME/.local/state/deep-agent/users"
export DEEPAGENT_SERVICE_TOKEN_FILE="$HOME/.local/state/deep-agent/service-token"
mkdir -p "$(dirname "$DEEPAGENT_USERS_FILE")"
.venv/bin/python - <<'PY'
import getpass, os, secrets
import bcrypt

username = os.environ.get("DEEPAGENT_VIEWER", getpass.getuser())
print(f"Creating viewer: {username} (set DEEPAGENT_VIEWER to choose another name)")
if not username or ":" in username or "\n" in username:
    raise ValueError("Use a nonempty username without colons or newlines")
password = getpass.getpass("Viewer password: ").encode()
hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode()
with open(os.environ["DEEPAGENT_USERS_FILE"], "a", opener=lambda path, flags: os.open(path, flags, 0o600)) as handle:
    handle.write(f"{username}:{hashed}\n")
os.chmod(os.environ["DEEPAGENT_USERS_FILE"], 0o600)
try:
    fd = os.open(os.environ["DEEPAGENT_SERVICE_TOKEN_FILE"], os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    pass  # Preserve the token shared by the running bridge and assistant.
else:
    with os.fdopen(fd, "w") as handle:
        handle.write(secrets.token_urlsafe(48))
PY
```

Keep the following services in separate terminals. Export the same credential/token paths in each relevant terminal. Do not start a second copy if a port is already occupied.

**1. Procurement inspector** — requires the sibling repository and its installed dependencies:

```sh
PYTHONPATH=../procurement-intelligence-lab/src \
  ../procurement-intelligence-lab/.venv/bin/python \
  -m procurement_intelligence_lab.interfaces.web --port 8092
```

**2. Read-only A2A bridge** — uses that inspector, never its approval/save workflow:

```sh
export DEEPAGENT_PROCUREMENT_URL=http://127.0.0.1:8092
.venv/bin/python -m deep_agent.bridge
```

**3. SciFact MCP** — requires the sibling repository, its populated PostgreSQL database on port 5432, and its late-interaction service on port 8082. Set `DATABASE_URL` to your existing database credentials outside Git. Host processes need host URLs rather than container DNS names:

```sh
export GENERATOR_BASE_URL=http://172.17.0.1:8000/v1
export LATE_INTERACTION_BASE_URL=http://127.0.0.1:8082
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 \
  ../scifact-rag/.venv/bin/python -c \
  'from scifact_rag.mcp_server import build_mcp_server; build_mcp_server().run(transport="streamable-http", host="127.0.0.1", port=8091, streamable_http_path="/mcp", stateless_http=True, json_response=True)'
```

**4. Assistant:**

```sh
export DEEPAGENT_MODEL_URL=http://172.17.0.1:8000/v1
export DEEPAGENT_SPECIALIST_URL=http://127.0.0.1:8101
export DEEPAGENT_SCIFACT_URL=http://127.0.0.1:8091/mcp
export DEEPAGENT_DATABASE="$HOME/.local/state/deep-agent/history.sqlite"
unset DEEPAGENT_SIMULATED
.venv/bin/python -m deep_agent
```

Open **http://127.0.0.1:8100** and sign in with the viewer account you created. When connected through VS Code Remote SSH, forward DGX port **8100** in the Ports panel. Keep the model, bridge, database and MCP ports private.

For a protocol-only procurement fixture, follow the [operator instructions](docs/project/deployment.md). The fixture is explicitly labeled simulated and still requires model inference; it does not certify procurement findings. `.env.example` is a reference and is not automatically loaded.

## Verification and limits

```sh
make smoke
# Optional live check: disposable alice/bob accounts with the test password
# defined in this script, Chromium installed, and all real services running:
.venv/bin/python tests/app/browser_bridge_acceptance.py
```

The current suite contains 30 tests covering viewer ownership, bounded transports, A2A contracts, service failures and answer enforcement. The latest completed live browser journey took 76.16 seconds. See the [acceptance record](docs/project/acceptance.md).

Use one application worker. SQLite task/history records survive restart; process-local conversation context does not. Automatic model retries are disabled. Stopping a local run does not prove remote cancellation; inspect task history before retrying an unknown outcome.

No arbitrary shell execution, automatic approval/purchasing, private-repository access or external tracing is provided. Docker/Compose and Traefik files are deployment starting points; their presence does not establish OCI readiness. See [deployment and rollback](docs/project/deployment.md), [bridge contract](docs/project/bridge.md), and [project handoff](docs/project/handoff.md).

Application code is MIT; dependencies retain their licenses.
