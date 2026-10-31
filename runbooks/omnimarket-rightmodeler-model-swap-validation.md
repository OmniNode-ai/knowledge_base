---
type: runbook
status: draft
date: "2026-10-30"
title: "OmniMarket RightModeler model-swap validation"
topics: [omnimarket, onex-runtime, rightmodeler, operations]
refs:
  - guides/omnimarket-rightmodeler-validation.md
summary: "Configure the proposed HTTP evidence boundary and durable recovery state. A compatible operator-provided service and aligned package releases remain prerequisites."
---

# Model-swap validation service effect

This experimental effect calls an operator-configured service endpoint. It does
not execute RightModeler, start containers, install packages or call model
providers in the OmniMarket runtime. Every result remains `evidence_only: true`;
the platform retains responsibility for routing decisions.

## Availability and installation

The HTTP protocol below is a proposed integration boundary. The published
[RightModeler CLI](https://github.com/elm-os/rightmodeler/tree/v0.6.2) does not
expose this endpoint. These changes do not deploy a service or establish live compatibility. An operator
must supply a service implementing the request/result contract before a live
pilot can run. Local HTTP fixture tests establish client behavior only.

This draft documents a proposed OmniMarket contribution, not the current
upstream development branch. Confirm that the contribution has landed before
installing it from normal package pins.

The shared models must land in `omnibase_core`, followed by the validator
protocol in `omnibase_spi`. Maintainers handle their releases and dependency
floors. Until those releases are available, normal installation from the current
dependency pins cannot import the new APIs. Source-built sibling wheels are
used only for local validation, without committed source-path overrides.

## Service protocol

Configure one **complete endpoint URL**, including its path. There is no default
hostname, inferred route, polling URL or cancellation endpoint.

- The client sends one `POST` with `Content-Type: application/json` and a bearer
  service credential resolved through the platform secret store.
- The JSON body is `ModelModelSwapValidationRequest` from
  `omnibase_core.models.model_swap_validation`, serialized in JSON mode.
- HTTP 200 must contain one `ModelModelSwapValidationResult` from the same
  package, with explicit JSON boolean `evidence_only: true`. The client validates
  the schema, correlation, judge mode, quality floor, candidate binding, cost
  receipts and recommendation eligibility before publishing it.
- A completed `recommend` must explicitly name the requested candidate, set
  `recommendation_effective: true`, report a lower bound at or above the request's
  floor, and contain no explicitly failed gate. Missing eligibility is refused.
- Responses must use identity content encoding. The client requests identity,
  rejects other encodings before reading, and enforces its bound on raw bytes.
- Responses other than HTTP 200, redirects, malformed or oversized bodies and transport
  errors produce typed failures. The client does not follow redirects or retry
  the POST. HTTP 202 is unsupported; asynchronous jobs need a separately agreed
  protocol before they can be used.

The service must independently resolve the request's `replay_set_digest` to an
approved replay bundle. The request does not upload traces, labels, repository
files or host paths. Provision approved bundles, recorded answers, model/judge
routes, provider credentials and repository authorization on the service side.
The service must enforce the request's budget and return actual provenance and
receipts. Completed results currently require `tool_commit` and `image_digest`
under the shared Core schema; the client never fabricates those fields.

Service authentication is distinct from a model-provider API key. Never place
credential values in command payloads, contracts, URLs or source files. The
transport supplies the resolved value only in the authorization header.

## Rendered operator contract

Copy the packaged `contract.yaml` and change only its operational settings.
Preserve the handler binding, declared topics and terminal mappings. The
following blocks are examples. Render the approved placeholder tokens as actual
values before validation. Replace the entire example endpoint, including its
path, with the operator-provided endpoint; `/validate` is not a published route:

```yaml
state:
  directory: <runner-home>/model-swap/state
  sqlite_timeout_seconds: 30.0
  lock_poll_interval_seconds: 0.01
service:
  endpoint_ref: https://<onex-host>/validate
  secret_ref: validation.rightmodeler.service_key
  secret_resolver_config_path: <repo-root>/config/model-swap/secret-resolver.yaml
  deadline_seconds: 240.0
  connect_timeout_seconds: 10.0
  read_timeout_seconds: 240.0
  write_timeout_seconds: 30.0
  pool_timeout_seconds: 10.0
  max_request_bytes: 65536
  max_response_bytes: 8388608
  response_chunk_bytes: 65536
descriptor:
  # Retain the other packaged descriptor fields.
  timeout_ms: 300000
```

All limits and timeouts come from the contract; the client owns no listening
port. The state directory must be a rendered absolute path on persistent storage.
In these examples, `<runner-home>` is the home directory of the account running
the worker; its state subdirectory must be shared by the workers and survive
restarts. `<repo-root>` is the operator configuration checkout. Packaged state and
service settings are intentionally unconfigured. Handler discovery needs no
environment variables, credentials, network or filesystem writes. Missing
configuration returns `failed/needs_input` on the first request.

Inject `ProtocolSecretStore` when constructing the handler, or supply an explicit
resolver configuration. A file-backed resolver can be configured as follows:

```yaml
enable_convention_fallback: false
mappings:
  - logical_name: validation.rightmodeler.service_key
    source:
      source_type: file
      source_path: <runner-home>/model-swap/secrets/service-key
```

Provision that file through the operator's secret-management system. This
minimal resolver configuration declares one explicit file mapping. The adapter
requires the logical credential when the call begins and refuses a missing
value; it does not use an environment-variable credential fallback.

## Invoke and receive evidence

The package registers `node_model_swap_validation_effect` in `onex.nodes`.
Pass the full rendered contract path explicitly when constructing the handler:

```python
import asyncio
import json
from pathlib import Path

from omnibase_core.models.model_swap_validation import ModelModelSwapValidationRequest
from omnimarket.nodes.node_model_swap_validation_effect import HandlerModelSwapValidation

request = ModelModelSwapValidationRequest.model_validate(
    json.loads(Path("<runner-home>/model-swap/request.json").read_text())
)
handler = HandlerModelSwapValidation(
    contract_path=Path("<repo-root>/config/model-swap/contract.yaml"),
)
terminal = asyncio.run(handler.handle(request))
print(terminal.model_dump_json())
```

For runtime operation, read the command topic from
`event_bus.subscribe_topics` and both terminal topics from
`runtime_dispatch.terminal_events` in the packaged contract. Subscribe before
publishing a typed command envelope with the same correlation ID in envelope
and payload. The runtime result applier publishes the concrete completed or
failed terminal class. Read back a terminal for that correlation ID; successful
publication alone is not proof of completion.

The operator's runtime composition must load the rendered contract and pass
constructor dependencies through the public `wire_from_manifest` API:

```python
dependencies = {
    "HandlerModelSwapValidation": {
        "contract_path": rendered_contract_path,
        "secret_store": operator_secret_store,
    }
}
```

Supply that map as `materialized_explicit_dependencies`, with the rendered
manifest's contract result applier in `result_appliers_by_contract`, then freeze
the dispatch engine and call `subscribe_wired_contract_topics`. This constructs
the registered handler through the normal resolver. Discovery or copying a
contract alone does not supply these dependencies: stock `ServiceKernel` does
not currently derive this node's operator contract path automatically. The
runtime proof covers this supported explicit composition.

## Redelivery and interrupted calls

All workers for a command must share the same durable state directory with
SQLite transactions and OS file-lock semantics. This is not a distributed
lease across unrelated hosts. The handler records start intent before calling
the service, persists its validated terminal, and replays that immutable
terminal on duplicate delivery or process restart.

An interrupted call after start intent is never resubmitted. Recovery returns
`failed/timeout` with `interrupted_service_call`. A local deadline or cancellation
likewise leaves the remote outcome unknown; it does not prove the remote
service stopped or incurred zero cost. There is no invented cancellation API.
Provider charges are known only from returned service receipts. Preserve state
across restarts and use a new correlation ID for a genuinely new request.

Unreadable or corrupt state returns a typed `needs_input` refusal without a
host-path disclosure. Treat `state_unavailable` as an operational repair: it may
mean a remote outcome could not be stored. Do not delete state and retry an old
ID; reconcile the service's record and restore durable state first.

## Validation and pilot prerequisites

Run the focused node tests, the existing all-node in-process auto-wiring gate,
metadata checks, strict typing, lint and package builds using the repository's
Python 3.12 and `uv` tooling. Focused tests use real local HTTP servers for
bounded I/O, authentication, malformed evidence, timeouts and cancellation, plus
durable state and a real local event-bus dispatch.

Live validation still requires a compatible deployed service endpoint, its
provisioned service credential, and the operator-labelled public replay bundle.
The service must have approved access to that bundle and a real judge backend.
After those exist, report per-case joins, refusals and missing cases, agreement
and Cohen's kappa with 95% intervals, separate measured/estimated judge cost,
and service-side egress evidence. Client tests and synthetic replies do not
establish model accuracy or production routing benefit.

See the [validation guide](../guides/omnimarket-rightmodeler-validation.md) for
local checks and the evidence required before a live pilot. The implementation
is maintained in the public [OmniMarket repository](https://github.com/OmniNode-ai/omnimarket).
