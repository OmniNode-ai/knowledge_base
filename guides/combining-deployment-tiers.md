---
type: guide
status: current
date: "2026-08-26"
title: "Combining Deployment Tiers"
topics:
  - getting-started
  - local
  - self-hosting
  - cloud
  - event-bus
  - runtime
  - configuration
refs:
  - guides/getting-started-local.md
  - guides/getting-started-self-hosted.md
  - guides/connecting-to-the-cloud.md
---

# Combining Deployment Tiers

The three preceding guides each describe one way to run ONEX. Almost nobody runs
exactly one.

The realistic shape is a **combination**: you author and test on tier-0 because the
loop is fast and needs nothing, you keep a self-hosted stack up because that is
where cross-process behaviour is actually provable, and you may also talk to a
hosted deployment as a client. This chapter is about the seams between those tiers
— which knob moves you across one, what changes when you cross it, and what
stays exactly the same.

It **composes** the three guides and does not restate them. Read them first:

- [Building on the ONEX runtime](getting-started-local.md) — tier-0: the in-process bus, the local file-backed store, zero external infrastructure.
- [Self-hosting the full stack](getting-started-self-hosted.md) — the broker, the database, the cache, the identity provider, the runtime services.
- [Connecting to the cloud](connecting-to-the-cloud.md) — the hosted deployment as a client.

Current source audit: 2026-10-20, against public `omnibase-core v0.47.49` and
`omnibase-infra v0.38.75`. The examples below describe those revisions. Earlier
execution reports are attributed and dated in [verification posture](#verification-posture-for-this-page);
this update did not run inference, access credentials or deploy a stack.

---

## The one thing that makes combining tiers possible

Before the patterns, the property they all rest on.

The event bus is chosen at **runtime construction**, from one small set of
values, behind a protocol. `omnibase_core.runtime.runtime_local` declares the
whole accepted set in one place:

```python
SUPPORTED_EVENT_BUS_VALUES: frozenset[str] = frozenset({"inmemory", "kafka"})
```

— [runtime_local.py](https://github.com/OmniNode-ai/omnibase_core/blob/v0.47.49/src/omnibase_core/runtime/runtime_local.py)

`RuntimeLocal._create_event_bus()`
([runtime_local.py](https://github.com/OmniNode-ai/omnibase_core/blob/v0.47.49/src/omnibase_core/runtime/runtime_local.py)) reads
`backend_overrides["event_bus"]`, defaults it to `"inmemory"`, and returns either
`EventBusInmemory(environment="local", group="runtime-local")` or — for `"kafka"` —
a bus class discovered through an entry-point group. Your nodes, contracts and
models are on the other side of that call and never see which one won.

That adapter boundary is the basis for reusing node code across configurations.
A distributed run also needs declared transport/addressing, matching credentials,
and the services and migrations described in guide 2. Changing one argument alone
does not establish deployment readiness or full behavioral parity.

### Why the Kafka bus is an entry point and not an import

`omnibase_core` cannot import `omnibase_infra` — the dependency layering runs
compat → core → spi → infra, and core importing infra would invert it. So core
resolves the Kafka bus by name at runtime instead:

```python
_BACKEND_ENTRY_POINT_GROUP: str = "onex.backends"
_KAFKA_EVENT_BUS_ENTRY_POINT: str = "event_bus_kafka"
```

— [runtime_local.py](https://github.com/OmniNode-ai/omnibase_core/blob/v0.47.49/src/omnibase_core/runtime/runtime_local.py)

and `omnibase_infra` supplies it from its own `pyproject.toml`:

```toml
[project.entry-points."onex.backends"]
event_bus_kafka = "omnibase_infra.event_bus.event_bus_kafka:EventBusKafka"
state_postgres = "omnibase_infra.backends.backend_probe:probe_postgres"
```

— [pyproject.toml](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/pyproject.toml)

The practical consequence is the first rule of a hybrid setup: **asking for the
Kafka bus in an environment where `omnibase-infra` is not installed is an error,
not a downgrade.** The original authors reported this refusal in a clean core-only environment
on 2026-08-26; the checked runtime still declares the missing-entry-point error:

```
[ONEX_CORE_044_CONFIGURATION_ERROR] Requested event_bus=kafka but no entry point
named 'event_bus_kafka' is registered under 'onex.backends'. Install
omnibase-infra to provide EventBusKafka.
```

A typo is refused on the same terms, rather than silently falling back to
in-memory — the checked source declares this error (also historically reported):

```
[ONEX_CORE_044_CONFIGURATION_ERROR] Unsupported backend override
event_bus='kafak'. Supported values: inmemory, kafka.
```

Silent fallback would be the worst possible behaviour here: you would believe you
were proving cross-process behaviour while running everything in one process.

### The CLI grows through installed entry points

The `onex` command comes from core and discovers extensions under `onex.cli`.
The pinned [infra package declaration](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/pyproject.toml)
registers `auth`, `delegate`, `identity`, `kafka`, `ledger`, `node`, `occ`, `profile`
and `skill`. These are registration declarations, not a freshly executed install test.
The older seven-command inventory on this page is obsolete.

`onex run` is a core command in the checked release; it is not an alias registered
by infra for `onex node`. Use `onex node` for the backend examples below. Local
product delegation also needs `omnimarket` in the same environment, as the
[quickstart](onex-plugin-quickstart.md) specifies.

---

## Pattern A — tier-0 dev loop, self-hosted stack for integration proof

The most common combination. You iterate on tier-0 all day because it starts
instantly and proves the contract chain; you cross to your self-hosted broker only
to prove the things tier-0 structurally cannot.

### When to flip

Guide 2 already lists the reasons to stand a full stack up at all. The narrower
question here — *when does an individual run need to cross?* — has a short answer:
flip when the property you are trying to prove **only exists between processes.**

| Prove this | Tier |
|---|---|
| The contract resolves, the handler chain runs, a terminal event closes it, the projection materialises | tier-0 |
| Replay determinism from a recorded completion | tier-0 |
| A validation or refusal fires | tier-0 |
| A second process sees the event | self-hosted |
| Consumer groups, partitioning, ordering across processes | self-hosted |
| Broker-backed event persistence and recovery across a restart | self-hosted |
| A deployed runtime consumer picks the command up and dispatches it | self-hosted |

Anything in the top half that you run on the broker is a slower version of a test
you already had.

### How transport selection is expressed

The command surfaces differ; do not treat their defaults as interchangeable.

**`onex node`: explicit runtime backend overrides.** The checked
[core runtime](https://github.com/OmniNode-ai/omnibase_core/blob/v0.47.49/src/omnibase_core/runtime/runtime_local.py)
reads `backend_overrides["event_bus"]`, defaulting to `inmemory`. The infra
[node CLI](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/src/omnibase_infra/cli/cli_node.py)
accepts repeated `--backend key=value` arguments:

```bash
onex node <node-name> --backend event_bus=inmemory
onex node <node-name> --backend event_bus=kafka --backend kafka_bootstrap=<host:port>
```

Only `inmemory` and `kafka` are supported here. The explicit Kafka address reaches
the provider's `from_bootstrap` factory. Without that address, this generic node
path uses the Kafka provider's default configuration, which can read
`KAFKA_BOOTSTRAP_SERVERS`. That is address configuration after selecting Kafka,
not a broker probe choosing the transport.

**`onex delegate`: explicit flag or declared runtime configuration.** The checked
[delegate CLI](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/src/omnibase_infra/cli/cli_delegate.py)
accepts `--bus inmemory|kafka`. For example, after the quickstart's model/key setup:

```bash
onex delegate "<task>" --bus inmemory
onex delegate "<task>" --bus kafka --kafka-bootstrap <host:port>
```

For Kafka, supply a declared lane with `--lane <lane-id>` or state the broker
address with `--kafka-bootstrap`; those two addressing options are mutually
exclusive. A configured lane can supply the address when `--bus` is omitted.
The delegate path does not take its broker address from ambient
`KAFKA_BOOTSTRAP_SERVERS`. A Kafka selection without resolved addressing refuses;
`--kafka-bootstrap` alongside `--bus inmemory` also refuses.

### Current resolution authority

The shared [transport resolver](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/src/omnibase_infra/backends/auto_configure.py)
uses this order:

1. An explicit caller argument (`--bus` for delegation, `bus_type=` for a selector caller).
2. Declared `config.event_bus.type`, supplied by a config-resolved runtime caller.
3. A broker probe, only for callers that supply neither argument nor configuration.

The shared resolver also normalizes a declared `cloud` value to Kafka transport;
that alias does not select the hosted API. The CLI flags above still accept only
`inmemory` and `kafka`.

`ONEX_EVENT_BUS_TYPE` is ignored. A nonempty value produces a warning to remove
it; even an invalid value does not select a transport or fail validation. It is
not a shell-wide transport override.

Omitting `--bus` on the current delegate CLI calls `resolve_default_bus`, which
always resolves embedded runtime configuration first through
[service_kernel.py](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/src/omnibase_infra/runtime/service_kernel.py).
Its authority is a contracts-directory bootstrap pointer (`ONEX_CONTRACTS_DIR`),
then a developer lane binding, then a bound workspace's materialized or working-tree
runtime config, otherwise the shipped
[tier-0 default](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/src/omnibase_infra/runtime/tier0_runtime_config.yaml)
(`event_bus.type: inmemory`, local profile). A bound workspace missing its required
config refuses instead of silently becoming tier-0.

Consequently the broker-probe tier is unreachable on this config-resolved delegate
path. An ambient broker appearing or disappearing cannot choose its transport.
If the declared transport is Kafka and that broker is unreachable, execution fails
downstream; it does not silently switch to in-memory. Read the reported resolution
provenance to identify which configuration answered, or pass `--bus` for a one-run
override. For a persistent selection, update the owning runtime configuration;
bootstrap variables name where it is found, not which transport to invent.

The deployed kernel also passes its configured event-bus type to the shared
resolver. Its broker connection settings are distinct from selecting that type.
The generic `onex node --backend` construction path above is not the delegate
config loader and should not be described as that same ladder.

### Probe-only callers and historical observations

A caller that directly invokes the shared resolver without either an explicit
bus or `config_bus` can still reach the probe. `HEALTHY` and `AUTHORITATIVE` select
Kafka, `DISCOVERED` selects in-memory, and indeterminate `REACHABLE` raises
`EventBusResolutionAmbiguousError`. Declare configuration or an explicit argument
to resolve that ambiguity; exporting `ONEX_EVENT_BUS_TYPE` cannot fix it.

**Historical author report (2026-08-26):** the earlier guide reported fourteen
Kafka selections and six in-memory selections over twenty unchanged-environment
probe calls, illustrating the old probe-driven behavior. That observation predates
the current config-first delegate path, was not repeated for this update, and is
not a current CLI selection rule or a portable failure-rate estimate.

### Crossing back: what your self-hosted stack must already be

One asymmetry to plan around. Tier-0 needs nothing. The moment a run crosses to
the broker it inherits **every** precondition in guide 2 — most sharply the
migration gate, which the runtime will not start without, and the broker's
advertised address, which is what makes an off-box client fail on the second hop
rather than the first. Neither is visible from the tier-0 side of the flip, and
both will present as "my run hangs" rather than as a configuration error.

The practical sequencing is therefore: bring the stack up and verify it *on its
own terms* using guide 2's step 5, and only then start flipping individual runs
onto it. Debugging a flipped run against a stack you have not independently
verified means debugging two things at once.

---

## Pattern B — self-hosted stack, hosted API as a client

Here the hosted deployment is not a replacement for your stack. It is another
service your stack talks to, the same way it talks to any external API.

### The documented connection surface

The platform's own REST connection configuration is
`ModelRestApiConnectionConfig`
([model_rest_api_connection_config.py](https://github.com/OmniNode-ai/omnibase_core/blob/v0.47.49/src/omnibase_core/models/configuration/model_rest_api_connection_config.py)).
Its `apply_environment_overrides()` method
(the linked file) declares the exact variable-to-field mapping:

| Variable | Field |
|---|---|
| `ONEX_API_BASE_URL` | `base_url` |
| `ONEX_API_KEY` | `api_key` |
| `ONEX_API_BEARER_TOKEN` | `bearer_token` |
| `ONEX_API_TIMEOUT_SECONDS` | `timeout_seconds` |
| `ONEX_API_MAX_RETRIES` | `max_retries` |

These are bindings for this connection model. The `onex cloud` client has its
own documented credential-file setup in guide 3; do not assume that constructing
this model configures that CLI. Three details that guide 3 does not cover, and that matter as soon as
you are wiring this into your own stack rather than typing `curl`:

- **The overrides are applied, not absorbed.** `apply_environment_overrides()` is
  an explicit method call returning a **new** config object. Nothing reads these
  variables at import time or at construction. Exporting `ONEX_API_KEY` and
  constructing the model does not pick the key up; the calling code has to invoke
  the method. If you are embedding this, call it.
- **`base_url` is required on the model.** Construct it with an explicit gateway
  origin; the field does not provide a default public service address.
- **`timeout_seconds` and `max_retries` are parsed as integers, and a value that
  does not parse is skipped rather than raising** (the linked file). A typo in
  `ONEX_API_TIMEOUT_SECONDS` leaves the previous timeout in force silently. This
  is the one place in this chapter where a bad input is absorbed instead of
  refused, so check the value you set.

The credential shapes themselves — `X-API-Key` versus `Authorization: Bearer` —
are selected at `get_request_headers()` (the linked file), matching the two
header shapes guide 3 documents.

### Other credential commands in the public package

The checked [auth CLI](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/src/omnibase_infra/cli/cli_auth.py)
registers `login`, `status`, `token`, `logout`, `lane-login` and `lane-logout`.
For the hosted customer path, follow guide 3's `onex cloud` instructions.

`onex auth login` requires `--tenant-slug` and `--base-url`, plus exactly one of
`--api-key-stdin` or `--client-secret-stdin`. The client-secret mode additionally
requires `--client-id` and `--token-endpoint`; API-key mode does not. Secrets arrive
on stdin and are stored by reference under `~/.onex`.

`login` and `logout` are local storage operations. `status` verifies API-key
credentials against the gateway by default; use `status --no-verify` for a local
inspection. For a client credential, status does not claim verification and points
to `token`, which performs the token request. These are source-inspected behaviors;
this documentation update did not access a credential or exercise authentication.

### The genuinely composable piece: verify a hosted receipt on your own machine

This is the most useful thing in this pattern, and it is available to you offline.

Guide 3's receipt section documents the receipt a completed workflow returns, including a
`terminal_event_hash` presented as the receipt's integrity claim. That hash is
recomputable, and the function that computes it ships in `omnibase-infra`:

`omnibase_infra/src/omnibase_infra/verification/workflow_receipt/receipt_hash.py`
exposes `terminal_event_payload()` (line 30) and `sha256_of()` (line 26). The
payload shape is five fields, and they are exactly five fields the receipt hands
back to you. Run it yourself:

```python
from omnibase_infra.verification.workflow_receipt.receipt_hash import (
    sha256_of,
    terminal_event_payload,
)

payload = terminal_event_payload(
    correlation_id="11111111-2222-3333-4444-555555555555",
    status="completed",
    terminal_model_used="a-model",
    terminal_total_tokens=456,
    terminal_latency_ms=1234,
)
print(list(payload))
print(sha256_of(payload))
```

```
['correlation_id', 'status', 'terminal_model_used', 'terminal_total_tokens', 'terminal_latency_ms']
179e74b0877198fd9165181f801f364192e5b54fb0534aac375d9722489eabf5
```

Those exact inputs produce that exact digest — 64 hex characters, byte-stable
across repeated runs, both confirmed here. Note that the payload's own key order
is deliberately *not* the order that gets hashed: the encoding is
`json.dumps(payload, sort_keys=True, default=str)` UTF-8 encoded, SHA-256
hexdigest, so the keys are sorted on the way in. That is what makes the hash
independent of field order — and it is why you can rebuild the payload out of a
receipt's fields in whatever order you read them and still reproduce the digest.

So the hybrid pattern is: **the hosted service executes the work and issues the
receipt; your own machine independently recomputes the hash from the receipt's own
fields and compares.** A receipt whose `terminal_event_hash` does not reproduce
from its own `correlation_id`, `status`, `terminal_model_used`,
`terminal_total_tokens` and `terminal_latency_ms` is not internally consistent,
and you can establish that without asking the service to confirm anything about
itself.

The hashes cover different field sets, but comparing them for inequality is only a
sanity check. Recomputing a hash from the receipt's own fields establishes internal
consistency with those fields; it is not an independent attestation of execution,
model identity or answer correctness. Someone who replaces the data can recompute
these unkeyed hashes too. See guide 3's [receipt limits](connecting-to-the-cloud.md#what-a-receipt-says)
for the distinction between hashes, signatures and authentication.

> **Unverified.** The recomputation was proven against synthetic field values, not
> against a receipt issued by the production API. Guide 3 states that the workflow
> routes are not currently listed in the production OpenAPI document, so no live
> receipt was available to check. The hash function is described in its own
> module docstring as a pinned mirror of the renderer that issues these receipts,
> with a parity test asserting they agree; that is a strong claim but it is a
> claim about the code, not a live end-to-end comparison.

### Hosted availability is a dated report

Guide 3's [availability table](connecting-to-the-cloud.md#availability-of-each-step-stated-honestly)
preserves author reports dated 2026-09-23. The earlier version of this chapter
reported unauthenticated checks on 2026-08-26: workflow routes were absent from
the production OpenAPI document and real/invented `/v1/` paths both returned `401`.
Those observations were not repeated in this update and do not establish the
current deployment. Recheck `GET /openapi.json` before depending on a route;
even an advertised route does not establish successful authenticated execution.

---

## Pattern C — author locally, execute in the cloud

The documented hosted workflow API does not provide an arbitrary node-upload
procedure. Local authoring is a separate capability: the pinned core source
supports project/node scaffolding, but that is not hosted deployment authorization
or a custom workflow registration API.

The submission side does not connect to it, for two independent reasons:

1. **The hosted API takes a declared `workflow_type`, not a node.** Guide 3 step 4
   documents that a `workflow_type` the gateway has not declared is refused at
   ingress with `400`, and that the refusal lists the types that *are* accepted.
   There is no route that accepts a contract, a node package, or a handler. A node
   you scaffolded on your laptop is not a `workflow_type` the gateway knows.
2. **Current production availability is not established by this source audit.**
   Guide 3's dated availability report says submission routes were not advertised;
   repeat its route-discovery check before relying on the hosted path.

The public sources linked here do not establish a supported procedure to submit
and deploy your locally authored node to the hosted service. Do not infer one
from the ability to execute a packaged workflow locally.

### Local authoring and the scaffold boundary

The older author report on this page described a missing `default_handler` binding
and terminal event, preventing a freshly generated scaffold from running. That
source mismatch is fixed in the checked
[core scaffold template](https://github.com/OmniNode-ai/omnibase_core/blob/v0.47.49/src/omnibase_core/cli/cli_new.py):
it emits `handler_routing.default_handler` in `module_ref:ClassName` form, a typed
handler class, input/output model modules and a terminal event. Its handler returns
an empty typed response pending your implementation. The public
[scaffold execution tests](https://github.com/OmniNode-ai/omnibase_core/blob/v0.47.49/tests/unit/cli/test_cli_new_scaffold_runnable.py)
exercise generated nodes through `RuntimeLocal`; they were inspected, not executed
in this documentation audit.

A default `onex node <name>` lookup still targets packaged nodes. For your own
project, make its Python package importable and point `--contract` at its contract;
consult the pinned CLI and test source for that invocation shape. The two built-in
harness workflows in guide 1 do not dynamically discover your project. A runnable
empty scaffold establishes wiring, not your application's behavior, and it does
not upload a new workflow type to a hosted service.

---

## Which tier for which activity

The decision table. "Author" means writing contracts and handlers; "test" means
proving your own logic; "integrate" means proving behaviour between components;
"operate" means running something others depend on.

| Activity | Tier | Why |
|---|---|---|
| **Author** a contract or handler | tier-0 | Nothing about writing a contract needs a broker. The scaffold and the contract read are offline operations. |
| **Test** handler logic, refusals, replay determinism | tier-0 | Fastest loop, and these properties are fully present in-process. A recorded completion makes the run deterministic and offline. |
| **Integrate** — second consumer, cross-process ordering, broker-backed event persistence/recovery, consumer groups | self-hosted | The tier-0 event bus is in-memory and per-process; it does not retain events across a restart. |
| **Integrate** — a deployed runtime consumer dispatching your command | self-hosted | Requires the runtime services and the migration gate from guide 2. |
| **Operate** with distributed event persistence and recovery | self-hosted, or hosted where supported | tier-0 has no durable event transport or cross-process consumers. Local SQLite projection files and saved run artifacts can persist without a broker. |
| **Operate** without running infrastructure yourself | hosted | The entire reason the hosted tier exists. |
| **Verify** a hosted receipt's integrity | tier-0 | The hash function runs offline, on the receipt's own fields. |
| **Evaluate** the platform | tier-0 | Guide 1 is the whole evaluation. |

### What changes when you cross a tier, and what does not

This is the part worth internalising, because it determines how much of your work
survives a move.

**Designed to remain stable across configurations (not a full parity test):**

| | Why it is invariant |
|---|---|
| Your `contract.yaml` | The contract is the specification the runtime resolves against. Nothing in it names a transport. |
| Your typed input and output models | Referenced by the contract by import path; the bus carries them, it does not define them. |
| Your handler code | It sits behind the runtime, on the far side of `_create_event_bus()`. It cannot observe which bus was constructed. |
| Topic names | Declared in the contract's `event_bus.subscribe_topics` / `publish_topics`. The same strings appear in the tier-0 evidence packet's `emitted_topics` and on the broker. |
| The `onex` entry point | Installed distributions extend its command registry; inspect the pinned package entry points rather than assuming the surface is identical. |
| The three-primitive model — contract, node, handler | Architectural, not deployment-specific. |

**Changes when you cross:**

| | tier-0 | self-hosted | hosted |
|---|---|---|---|
| Bus construction argument | `event_bus=inmemory` (default) | `event_bus=kafka` + a bootstrap address | not yours to set |
| Packages required | Core for the harness; the quickstart lists all three packages for product delegation | Relevant node packages plus infra and a checkout for `scripts/` and `docker/` | the documented client and a credential |
| Preconditions before a run | none | migration gate healthy, secrets present, broker advertising a reachable address | an account and an API key |
| Failure surface | one process, one traceback | dependency ordering, gate health, broker reachability | HTTP status codes |
| What proves success | the evidence packet plus an independent read of the projection row | the same, plus behaviour visible only between processes | a terminal status, then a receipt |
| Configuration required | The harness uses explicit arguments; product delegation resolves its runtime config | per guide 2 and the selected runtime/lane | guide 3's client login and base URL |

The row that matters most is the first one, and it is deliberately one row.

---

## Troubleshooting

Rows marked **expected** are correct behaviour, not defects. Confirming them is
how you tell a working hybrid setup from a broken one.

| Symptom | Cause and what to do |
|---|---|
| `Requested event_bus=kafka but no entry point named 'event_bus_kafka' is registered` | **Expected** in a `omnibase-core`-only environment. The Kafka bus ships in `omnibase-infra`. Install it; do not treat this as a fallback path. |
| `Unsupported backend override event_bus='...'` | **Expected** for a typo. Only `inmemory` and `kafka` are accepted, and no other value silently degrades. Fix the spelling. |
| `Invalid --backend format '...'. Expected key=value` | **Expected.** `--backend` takes `key=value`, e.g. `--backend event_bus=inmemory`. |
| `--kafka-bootstrap is only valid with --bus kafka` | **Expected**, and a useful refusal — it catches the case where you would have run in-process while believing you were on the broker. Pick one. |
| `onex delegate` selected Kafka when you expected in-process | Inspect the reported config provenance, developer lane binding and any bound workspace config. The current CLI does not probe for its default transport. Use `--bus inmemory` for a one-run override. |
| `Kafka probe returned REACHABLE ...; the transport cannot be resolved repeatably` | This belongs to a no-config resolver caller, not the current config-resolved delegate default. Supply declared configuration or an explicit argument; see [probe-only callers](#probe-only-callers-and-historical-observations). |
| You set `ONEX_EVENT_BUS_TYPE` and want to know whether it applies here | It is ignored by the shared resolver and a nonempty value warns. Remove it; select via the explicit flag or the owning runtime config. |
| An infra CLI extension is missing from `onex --help` | Confirm the interpreter and installed package with `onex --verbose info`, then compare the pinned `onex.cli` entry points. `run` is a core command, not an infra alias. |
| A flipped run hangs against your self-hosted stack | Verify the stack on its own terms first — guide 2 step 5, gate before kernel. A flipped run cannot distinguish "broker unreachable" from "gate never went healthy". |
| External client connects, then fails on the next call | The broker's advertised address, per guide 2. Presents identically whether the client is a flipped local run or anything else. |
| An older scaffold lacks a terminal event or handler binding | Compare it with the pinned core template, which emits both. The historical scaffold mismatch is fixed; see Pattern C. |
| `Unknown node '<your-node>'` from `onex node` | `onex node` resolves nodes packaged into the installed distribution. A project-directory scaffold is not one. |
| `ONEX_API_TIMEOUT_SECONDS` appears to have no effect | A value that does not parse as an integer is skipped silently rather than raising. Check the value. |
| Exported `ONEX_API_KEY` but the client is unauthenticated | The env mapping is applied by an explicit `apply_environment_overrides()` call, not absorbed at construction. Call it. |
| A hosted route returns `401` and you cannot tell if it exists | Authentication is refused ahead of routing. Read `GET /openapi.json` — unauthenticated, and authoritative. |

---

## Verification posture for this page

**Current source audit, 2026-10-20:** public core `v0.47.49` and infra `v0.38.75`
were inspected for runtime construction, CLI entry points and flags, shared
transport/config authority, auth behavior, hash helpers and scaffold templates.
No model call, live broker probe, secret access, hosted authentication or deployment
was performed. Isolated checks of the pinned resolver source used a mocked probe
and synthetic environment values to confirm precedence, ignored env and all probe
states. The pinned catalog resolver was also exercised against public declarations
without loading operator env files or contacting containers. These narrow checks
do not constitute the full product test suite or deployment validation.

**Historical author reports, 2026-08-26:** the original chapter reported a clean
local harness run, then-current CLI inventory and refusals, no-config broker
probe observations, synthetic receipt-hash recomputation, and scaffold-generation
failures. The command inventory, transport default and scaffold mismatch have
since changed as documented above. Those reports do not validate the current
release, and their environmental observations are not current CLI defaults.

The same original report described unauthenticated health/OpenAPI checks and
matching `401` responses from real and invented routes. Hosted route availability
can change independently of these packages; guide 3's table is an attributed dated
report and its route-discovery procedure is the check to repeat. The auth round
trip, production receipt comparison and cross-platform execution remain
unverified in this source audit. Published test sources are not represented as
new passing product tests.

---

## Related pages

- [Building on the ONEX runtime](getting-started-local.md) — tier-0 in full.
- [Self-hosting the full stack](getting-started-self-hosted.md) — the stack a flipped run lands on.
- [Connecting to the cloud](connecting-to-the-cloud.md) — the hosted tier as a client.
- [Handler authoring guide](handler-authoring-guide.md) — writing the logic behind the contract.
