# DeepAgent

A browser evidence assistant built with [LangChain DeepAgents](https://github.com/langchain-ai/deepagents), powered by a locally hosted DGX model. It delegates procurement investigations through an authenticated A2A bridge and checks scientific claims through SciFact MCP.

[Open the invited demo](https://deepagent.ediacarian.dedyn.io/) (sign-in required; best-effort availability).

**Verified local demo.** The real DGX → A2A → procurement and SciFact browser journeys have passed, including evidence downloads and isolation between viewers. Procurement uses the admitted **synthetic** corpus from `procurement-intelligence-lab`. The VPS edge / DGX hosting profile is described in [deployment instructions](deploy/README.md). Procurement human review/save is not enabled.

## What you can try

- **Investigate a discrepancy:** compare GPU-A requirements against purchase orders, identify the 8-required / 6-ordered discrepancy, and inspect its 12 source records.
- **Check a claim:** ask whether evidence establishes that vitamin D reduces multiple-sclerosis risk in humans; distinguish animal evidence, association and causal claims.
- Watch the observed A2A request/reply, model milestones and service timings. Inspect compact evidence cards, download the complete local trace, and reload viewer-owned history.

The agent must call an approved evidence tool before answering. Unsupported final answers are rejected. A returned tool result establishes evidence availability; it does not guarantee that every generated claim is correct. This first slice supports evidence investigations; unrestricted personal-assistant and coding tools remain future work.

## Showcase in two minutes

Open the app, choose **Investigate a discrepancy**, and send the prepared GPU-A prompt.
Point out the progression: your request → DGX model → scoped A2A `SendMessage` →
procurement reply → evidence → generated reviewer brief. The request/reply carry the
same correlation ID. The reply reports the actual investigation read and 12 source reads.
The evidence card shows **8 required / 6 ordered**; expand the raw artifact to inspect
source records. Download the trace to retain the observed sequence, then reload the
investigation to show persistence. Use **Check a claim** for the SciFact MCP example.

Explain the actors accurately: the DeepAgents graph uses a DGX LLM; the procurement
specialist is a deterministic, read-only A2A bridge to the existing corpus services.
This demonstrates agent delegation and evidence transfer. Procurement LangGraph human
review/save remains in the procurement application. The UI presents observed actions,
not a second LLM conversation or private model reasoning.

### Optional LangSmith tree

External export is **off by default**, even if a global `LANGSMITH_TRACING` variable
is set. To opt in, approve exporting demonstration prompts, generated answers and tool
results, then set these variables in **both** the assistant and bridge terminals before
starting them. Store a key in an owned private regular file with mode `0600` outside Git;
`LANGSMITH_API_KEY` is also supported when no key file is configured.

```sh
export DEEPAGENT_LANGSMITH_TRACING=1
export DEEPAGENT_LANGSMITH_PROJECT=deepagent-showcase
export DEEPAGENT_LANGSMITH_KEY_FILE=/absolute/private/langsmith-key
```

Open the `deepagent-showcase` project in LangSmith and match the UI's trace ID to
**DeepAgent investigation**. Expand the LangGraph/model/tool spans, then **A2A SendMessage**,
**Procurement A2A task**, **Procurement investigation read**, and **Procurement source read**.
The bridge joins the parent through maintained SDK trace headers in A2A metadata.
Both processes must have export enabled for the server spans to appear. Trace IDs do
not grant app access; LangSmith access follows its own workspace permissions. SciFact
service internals are not instrumented by this repository. Local downloads include
visible prompts/results and evidence, so share them intentionally.

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

The current suite contains 35 tests covering viewer ownership, bounded transports, A2A contracts, service failures and answer enforcement. The October 6 live browser journey took 76.16 seconds; current showcase acceptance is recorded separately. See the [acceptance record](docs/project/acceptance.md).

Use one application worker. SQLite task/history records survive restart; process-local conversation context does not. Automatic model retries are disabled. Stopping a local run does not prove remote cancellation; inspect task history before retrying an unknown outcome.

No arbitrary shell execution, automatic approval/purchasing, private-repository access is provided. Optional LangSmith export requires explicit configuration as described above. The production profile reuses the existing VPS TLS/Tailscale edge; deployment verification is recorded separately from local tests. See [deployment and rollback](docs/project/deployment.md), [bridge contract](docs/project/bridge.md), and [project handoff](docs/project/handoff.md).

Application code is MIT; dependencies retain their licenses.
