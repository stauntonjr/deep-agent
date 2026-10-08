# DeepAgent VPS edge / DGX runtime

Owner-authorized hostname: `deepagent.ediacarian.dedyn.io`.
The VPS terminates TLS using its existing Traefik `desecresolver` and watched file
provider. `traefik.deepagent.yaml` forwards to DGX tailnet port18100; Tailscale Serve
forwards that private listener to127.0.0.1:8100. Host headers are preserved for the
application's fixed HTTPS origin. No model, A2A, database or MCP port is public.

The ARM app runs on DGX from the existing Dockerfile and frozen lock. Build an image
from an exact committed source archive, tag it with that complete revision, and record
its Docker image ID. `compose.dgx.yaml` is a separate production profile: non-root
host UID/GID, read-only root, no capabilities, one worker, loopback bind, bounded
resources/logs, explicit tracing off and private credential/token mounts. Host networking
lets the fixed tools reach existing loopback services. It gives the app host-network
reachability; fixed endpoint/tool validation still constrains model authority.

## Start or update

Preserve private state under `.harness/runs/vps-deployment/private` (ignored by Git).
It contains `users` (BCrypt records), `service-token`, private operator/test login files,
`bridge.env`, `scifact.env` and the persistent `data` directory. Credential files must
be owned by the configured UID and mode0600. Never use the public local-test password.
Set `PYTHONPATH` in `bridge.env` to the archived release's `src` directory so a workspace
edit cannot change the bridge on restart. Its locked dependency runtime is the project
virtual environment. The SciFact environment uses the existing populated database and
host generator/late-interaction URLs. Source repos are not mutated by these units.

```sh
# After checking listener/process ownership, install the three provided user units.
install -m 0644 deploy/systemd/*.service "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now deepagent-procurement deepagent-scifact deepagent-bridge

export DEEPAGENT_REVISION=<full-source-revision>
export DEEPAGENT_STATE_DIR=/home/jrs/deep-agent/.harness/runs/vps-deployment/private
export DEEPAGENT_UID=$(id -u) DEEPAGENT_GID=$(id -g)
docker compose -f deploy/compose.dgx.yaml up -d --no-deps assistant
tailscale serve --bg --http=18100 http://127.0.0.1:8100
```

DGX user lingering and Docker/Tailscale restart behavior retain services across logout.
Existing model, database and retrieval workloads keep their existing supervisors.
Install only `deepagent.yml` in the VPS watched dynamic directory; preserve other files.
Add only the `deepagent` A record to the existing deSEC DDNS settings and refresh only
its updater. The existing ACME300second DNS wait can delay trusted TLS issuance.

## Verify and recover

Authenticated health is `/healthz`; unauthenticated requests must receive401, including
health. The container health probe checks that authentication boundary, not model/tool
readiness. Use the browser acceptance with private randomized credentials to verify
actual DGX/A2A/MCP, source counts, downloads/reload and cross-viewer404 over trusted TLS:

```sh
DEEPAGENT_BROWSER_URL=https://deepagent.ediacarian.dedyn.io \
DEEPAGENT_BROWSER_CREDENTIALS="$DEEPAGENT_STATE_DIR/browser-credentials.json" \
DEEPAGENT_BROWSER_PREFIX=/tmp/deepagent-vps \
PLAYWRIGHT_BROWSERS_PATH=/tmp/deepagent-playwright \
  .venv/bin/python tests/app/browser_bridge_acceptance.py
```

Verify HTTP→HTTPS, normal certificate validation, app/edge health, foreign Origin403,
no public backend listeners, service restart/persisted history and existing sibling
pages. The browser fixture accounts are for acceptance only; remove them from `users`
after verification. Owner login lives in `owner-login.txt`; distribute invitations
only when instructed. LangSmith upload remains disabled without separate consent.

Back up SQLite with its online backup API before later updates. Retain the data and
private users/token on rollback. Recreate only this app with the previous recorded
image; restore the bridge release PYTHONPATH if applicable. On a first failed deployment,
move only the DeepAgent route out of the watched VPS directory, disable only Tailscale
port18100, and stop only the DeepAgent app/units. Do not reset all Tailscale Serve routes,
restart Traefik or change other applications. DNS may remain reserved for this hostname.
