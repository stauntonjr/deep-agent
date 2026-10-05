# ADR-0009: Use credential-isolated ChatGPT subscription controls through Pi

- Status: accepted
- Date: 2026-08-24
- Deciders: Jack Rory Staunton
- Governing issue: #21

## Context

ADR-0008 makes a local Qwen coding model the recurring model-diversity canary. Its first accepted
candidate is mostly negative: bare passed 0 of 9 trials and the harness-enabled lane passed 1 of
9. Those results do not reveal whether the task corpus is merely difficult for the selected local
model or whether the paired runner and harness can support a stronger model on the same bounded
work. A one-off frontier control is therefore useful, but it must exercise Pi rather than a
different agent client and must not weaken the local-Qwen policy.

Pi 0.84.1 includes an `openai-codex` provider using the Codex Responses protocol and catalogs exact
model `gpt-5.6-sol`. The installed provider targets the ChatGPT backend and supports ChatGPT
Plus/Pro OAuth. Codex CLI is already logged in through ChatGPT, while Pi has no global
`openai-codex` credential configured. The human owner explicitly prohibited using an OpenAI API
key. Copying Codex OAuth material into Pi's normal credential store would also place a reusable
credential beside configuration used by a model process.

## Decision

Run an optional, explicitly selected `codex-subscription-sol` control through Pi's native
`openai-codex` provider and exact `gpt-5.6-sol` model. Use the existing Codex ChatGPT subscription
login only. Do not read, accept, inherit, forward, or persist an OpenAI API key.

The host runner opens the private Codex auth file without following symlinks, validates ChatGPT
mode, rejects a populated API-key field, checks token account identity and remaining lifetime, and
keeps the short-lived access token only in process memory. A loopback-only relay accepts the fixed
Codex Responses path, requires a random per-run canary bearer and dummy account identity, enforces
request-count, cumulative request-byte, and timeout bounds, and replaces only those inbound dummy
headers with the real subscription OAuth values when forwarding to the fixed ChatGPT host and
path.

Pi receives only the random non-secret canary JWT on its command line. Its generated `models.json`
and `settings.json` remain individually read-only and contain only a `not-needed` placeholder, a
loopback base URL, the exact model override, and forced SSE transport. Pi may create lock and
credential-cache files in an otherwise empty ephemeral agent-state directory; that state can hold
only the canary, is not host-backed, and disappears with the sandbox. Bubblewrap clears the
inherited environment, does not mount the Codex auth file or host home, and gives the model only
the same disposable task repository and `read`/`edit` tools as the Qwen evaluation. The relay never
emits tokens, account identifiers, request bodies, model text, or upstream errors into retained
evidence.

Before a live request, a no-model check must validate the ChatGPT login and resolve exact
`openai-codex/gpt-5.6-sol` from the installed Pi catalog in a separate minimal environment without
`OPENAI_API_KEY`, Codex home, extensions, skills, context files, sessions, or startup networking.
Then run one paired smoke before any three-trial evidence. Cloud submission is limited to the
public synthetic benchmark prompt, generated harness context, and disposable repository content.

This control is supplemental and one-off unless a later human decision schedules it. It does not
replace the recurring local-Qwen canary, establish a default model/provider, authorize unrelated
cloud use, approve either baseline, or create a general harness-lift claim.

## Consequences

### Positive

- The same Pi runner, tools, frozen tasks, hidden oracles, and lanes can be compared against a
  stronger model without creating OpenAI API-key handling.
- The real subscription credential is absent from Pi configuration, Pi arguments, the model
  sandbox, generated repositories, result JSON, and tracked reports.
- Exact provider, model, reasoning effort, relay bounds, observed request counts, and provider
  token measurements are retained as sanitized provenance.

### Negative

- A host relay is additional security-critical code and holds a short-lived OAuth access token in
  process memory for the duration of a run.
- ChatGPT subscription usage, rate limits, and service behavior are externally managed and do not
  provide an API-price accounting boundary.
- Pi 0.84.1's Codex Responses provider ignores the generated 4,096-token option; results must record
  it as runner configuration only, not as an enforced provider output bound or Qwen-equivalent limit.
- Requests leave the DGX host and send the synthetic task plus applicable harness context to
  ChatGPT; this path is unsuitable for private repository data without a separate decision.

### Risks and mitigations

- Local relay misuse: bind only to loopback, require a random per-run bearer and dummy account,
  expose one fixed path, stop the relay after the run, and test rejection before forwarding.
- Credential disclosure: no credential file mount, no inherited environment, no real token on the
  command line or generated config, bounded private-file loading, strict header-safe token/account
  validation, sanitized upstream exceptions, and content-free retained metrics.
- Endpoint or model drift: the runner and read-only Pi configuration hard-code and validate the
  provider, exact model, SSE transport, and medium reasoning; the relay independently hard-codes
  the upstream host/path and canary boundary. Pi 0.84.1 sends zstd-compressed request bodies, so the
  relay treats the body as opaque and does not claim independent model-field validation.
- Unexpected subscription consumption: require explicit target selection, a no-model preflight,
  one-trial smoke, and fixed request and timeout budgets before repeated trials.
- Misleading comparison: use identical frozen tasks and disclose task-authoring exposure, small
  sample size, provider differences, and the absence of a causal or general lift claim.

## Alternatives considered

| Alternative | Evidence | Reason not selected |
|---|---|---|
| OpenAI API key through a proxy | Conventional Responses integration | Explicitly prohibited by the human owner; creates separate secret and billing boundaries |
| Copy Codex OAuth into Pi auth storage | Pi supports ChatGPT Plus/Pro OAuth | Creates a second reusable credential store that could become visible inside a future model boundary |
| Pass the real OAuth bearer directly to Pi | Pi accepts a highest-priority command-line credential | Exposes reusable OAuth material in process arguments and the model process |
| Invoke Codex CLI instead of Pi | Existing ChatGPT login already works | Would not test the same Pi adapter, tools, lane configuration, or failure modes |
| Run no frontier control | Avoids cloud exposure and relay complexity | Leaves task difficulty and harness portability under a stronger model unmeasured |

## Verification and revisit trigger

Require hostile loader/relay/config/result tests, a sanitized no-model catalog preflight, a bounded
one-trial paired smoke, custom and Draft 2020-12 result validation, full repository checks, and
independent revision-bound verification. Revisit or supersede this ADR if Pi provides an equally
isolated subscription-token broker, the Codex Responses protocol or ChatGPT endpoint changes, the
control becomes recurring, private application content is proposed, or the relay cannot enforce
its documented boundary.
