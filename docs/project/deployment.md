# DeepAgent operator instructions

The actual local DGX/A2A procurement and SciFact browser journeys have passed.
Procurement uses admitted synthetic corpus services through the read-only bridge;
human review/save remains unavailable. The owner-authorized VPS edge / DGX deployment uses the separate [production profile](../../deploy/README.md). See the README for complete
host startup commands and read the current handoff before changing services.

## Local startup

`uv sync --frozen`. Create a private credential file containing one
`username:BCrypt-hash` per viewer. Generate hashes interactively with `htpasswd -nB`
and save them outside Git; never put passwords in CLI arguments, URLs or environment
variables. File must be owned by the application user, regular/non-symlink and mode
0600. Revocation takes effect on the next request after removing the record.

Set the `.env.example` values in the process environment; the application does not
implicitly source a repository `.env`. For the local protocol fixture only:

```sh
.venv/bin/python tests/app/simulated_specialist.py
# Separate terminal, with private credential-file path exported:
DEEPAGENT_SIMULATED=1 .venv/bin/python -m deep_agent
```

Visit http://127.0.0.1:8100 and use the browser's authentication prompt.
The application binds loopback by default and checks Host/Origin against
DEEPAGENT_ORIGIN. Run exactly one Uvicorn worker; queue limits are process-local.
Health `/healthz` is authenticated. Task history survives restart; chat generation
is not resumed. Use demo data only. Download/reset controls operate on owned records.
Unknown remote outcome is not failure or success: inspect the existing task before
starting another investigation. Stop aborts local orchestration; remote cancellation
is not automatically established.

## Integration gates

SciFact must already expose its accepted streamable HTTP MCP endpoint at the configured
private URL. HTTP readiness alone does not establish MCP availability. Do not replace
MCP failures with fabricated evidence. The loaded DGX model must support actual tool use.

The owner-approved bridge wraps merged procurement main corpus endpoints, not its review workflow.
The client currently supports SDK protocol1.0 JSONRPC only; unsupported versions fail
closed. The RPC URL defaults to the configured service base plus /rpc;
set DEEPAGENT_SPECIALIST_RPC_URL for the exact accepted same-origin endpoint.
Human review/save is intentionally disabled pending a compatible trusted
contract. No new adapter is automatically deployed into procurement.

## OCI package and rollback

`uv build` creates wheel/sdist; Dockerfile uses locked dependencies. Compose requires
explicit HTTPS origin and private service URLs, binds app port to host loopback,
uses non-root UID10001, read-only root, no privileges and no Docker socket.
The credential file must be owned/readable by UID10001 when containerized.
Review the Traefik example against actual OCI network and certificate resolver;
its private address is a placeholder and is not a live route. No service-token mount
is configured yet; real specialist authentication is a release integration gate.

Before release: resolve accepted endpoints, viewer credentials and private ingress,
verify two-viewer isolation through HTTPS, execute both actual browser journeys, record
image digest/exact revision and independently review release readiness. Owner approval
is required for OCI mutation and invitation distribution. Keep current procurement
inspector unchanged.

Rollback recreates only the DeepAgent app at the previous recorded image/configuration.
Retain its database volume; do not migrate schemas or restart Traefik/other services as
inferred cleanup. First deployment has no prior image: disable its route and stop only
its app if acceptance fails.

Create a new investigation before changing project/cutoff; prior chat context is retained.

## Read-only A2A bridge

The accepted bridge uses procurement's admitted synthetic corpus over HTTP; it does
not wrap its LangGraph review/save workflow. Run the merged procurement inspector on
an unused loopback port (example8092) using that project's normal entrypoint, then
run from this workspace:

```sh
# Export a private service token file path, never the token itself.
export DEEPAGENT_SERVICE_TOKEN_FILE=/absolute/private/service-token
export DEEPAGENT_PROCUREMENT_URL=http://127.0.0.1:8092
.venv/bin/python -m deep_agent.bridge
```

The token file must be regular, owned by the launching account and mode0600; generate
at least32random non-whitespace characters using a secret manager or Python secrets,
without printing it or including it in shell history. The same private file path is
used by the assistant process. Keep DEEPAGENT_SIMULATED unset for actual domain calls.
Bridge listens only on127.0.0.1:8101, requires Bearer authentication even for discovery,
checks Host, bounds request/response bytes and rejects upstream redirects. Card RPC
endpoint is /rpc. Do not expose this port publicly. In-memory remote tasks are lost
on restart; inspect retained local artifacts without automatically resubmitting.
The browser labels the real integration read-only; this bridge does not establish procurement review/save. Public hosting is verified separately through its production acceptance.
