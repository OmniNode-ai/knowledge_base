---
type: architecture
status: accepted
date: "2026-05-31"
title: "Technical Design: OmniNode Platform Architecture"
topics: [architecture, contracts, nodes]
refs:
  - doctrine/contracts-define-reality.md
  - doctrine/authoritative-projections-own-truth.md
  - doctrine/state-is-materialized-projection.md
  - doctrine/ordering-must-be-explicit.md
  - doctrine/deterministic-under-replay.md
  - doctrine/evidence-is-first-class-output.md
  - doctrine/truth-must-be-proven.md
  - doctrine/fail-fast-and-loud.md
  - doctrine/degrade-safely.md
  - adrs/ADR-0003-registration-runtime-registry-boundary.md
  - adrs/ADR-0004-registry-owned-consumer-surface.md
  - adrs/ADR-0005-dispatch-lifecycle-canonical.md
  - adrs/ADR-0002-data-verification-invocation.md
---

# Technical Design: OmniNode Platform Architecture

> **State reviewed 2026-10-18.** This is the target architecture. For the beta workflow that users can run, read [Delegation](delegation.md) and [Beta status](../reference/beta-status.md). Historical implementation inventories have been withdrawn pending revision-scoped verification.

## Purpose

Define the OmniNode platform architecture as a single, end-to-end public Technical Design Document. This document subsumes the previously separate designs for the contract-native platform, orchestrator nodes and CI/full-TDD evidence gates, and folds in the supporting domains of state and projections, configuration and overlays, runtime registration and registry boundaries, and model/inference routing.

It establishes the primitives the platform is built from, the boundaries between them, how a unit of work flows from a contract through nodes and handlers onto the event bus and into reducers, projections, and durable evidence — and the evidence required to assess implementation against the canonical target. CI is treated as a proof pipeline, not just a test runner; truth is treated as something proven through contracts, events, projections, replay, and durable evidence, not asserted.

## Scope

This design covers:

- contracts, nodes, and handlers as the constructive runtime primitives;
- the four declarative node archetypes and the separate runtime-host kind;
- the dispatch seam (routing parse, glob match, single-protocol fan-out, terminal aggregation);
- orchestration and finite-state-machine workflows coordinated over the bus;
- the event bus as the inter-service transport, with publish/retry/dead-letter/ordering on the bus;
- state, reducers, projections, cursors, and the authoritative-truth boundary;
- configuration via contract requirements, overlays, manifests, subcontracts, and projection contracts;
- the runtime, registration, and registry-owned consumer-surface boundary, and dependency injection;
- validation requirements for generated capabilities, independent of retired prototypes;
- the model and inference routing boundary;
- CI gate families, the full-TDD validation layers, and evidence/receipt pairing;
- deterministic-truth requirements and proof bundles;
- current-versus-target labeling for the active dispatch/enforcement migrations.

## Non-Goals

This design does not publish private topology, internal work identifiers, internal class or symbol names, private repository URLs, hostnames, IP addresses, runtime-lane port numbers, operator names, secret-provider product names, authentication material, or branch-specific implementation claims. Internal layers are described by role (core layer, service-provider-interface layer, runtime/infra layer, compatibility layer, capability node packages, marketplace/routing layer, agent-plugin layer) rather than by private package name.

This document also **does not claim that reconciliation to the canonical target is complete.** Wide, deliberate divergence between the current running system and the canonical target exists and is held open behind a staged cutover. Where current and target differ, the difference is labeled `current`, `target`, or `divergent`. A target-state gate, seam, or validator is never described as current enforcement until it is wired and verified. Any claim that the dispatch architecture has converged must cite the selection-parity proof and the cutover evidence — neither of which this document asserts as produced.

## Architecture at a Glance

```mermaid
flowchart LR
    Contract["contract.yaml<br/>(source of truth)"] --> Node["node shell<br/>(thin, declarative)"]
    Node --> Dispatch["dispatch seam"]
    Dispatch --> Handler["handler<br/>(owns logic)"]
    Handler --> Output["structured output<br/>(by archetype)"]
    Output --> Bus["event bus<br/>(the transport)"]
    Bus --> Reducer["reducer<br/>(state fold)"]
    Bus --> Projection["projection<br/>(materialized read model)"]
    Projection --> API["projection-backed API"]
    Bus --> Replay["replay / replay-equivalent"]
    Replay --> Evidence["durable evidence receipt"]
    API --> Client["client renders truth"]
    API --> Evidence
```

The platform is contract-native: a contract declares what a capability is and what it is allowed to do; a thin node shell binds it to the runtime; a handler implements the logic. Output is published only as the contract permits, and only onto the event bus. Downstream, reducers fold accepted events into state and projections materialize read models; clients render that truth but never create it. Every externally visible result is expected to leave durable, inspectable evidence. The primitives are intentionally small to prevent capabilities from sprouting their own engines, registries, daemons, routers, or direct transport paths outside the declared runtime.

## Core Primitives

The platform is constructed from exactly three primitives. The intent is that no bespoke classes, engines, adapters, routers, daemons, registries, managers, or runners survive outside these primitives and the runtime that hosts them. (This is the canonical target; see **Current Versus Target State**.)

| Primitive | Design responsibility |
| --- | --- |
| **Contract** | The source of runtime authority. Declares identity and version, typed input/output models, subscribe/publish topics, handler routing, config requirements and params, idempotency and retry/dead-letter semantics, failure handling, and evidence requirements. Topics, route policy, and model parameters are never hardcoded in handler source. |
| **Node** | A declarative runtime shell. Provides lifecycle, subscription binding, the dispatch entry, and contracted output publication. In the target, the node shell holds **no** custom logic — it routes to its handlers entirely from its contract. |
| **Handler** | Owns business logic. Implements the platform's single invocation seam and returns structured output. Holds no transport, no topics, and no authoritative state, and performs no undeclared ambient configuration lookup. |

**One handler invocation protocol.** There is exactly one async handler entry point — `handle(envelope) -> handler output` — resident in the core layer. The protocol carries handler identity, category, message types, and node kind. Its core residency is a **deliberate layering exception**: strict layering would place protocols in the service-provider-interface layer, but the protocol references core-resident I/O models, and relocating it would force a forbidden core-to-service-provider-interface import. This exception is a target decision, not a divergence; the platform does not claim a clean protocol-only boundary layer.

A capability is packaged as a contract-native node package:

```text
node_<capability>/
  contract.yaml      # source of runtime authority: handler routing, topics, params, terminal event
  metadata.yaml      # catalog discovery, node role
  node.py            # thin shell — no custom logic (target)
  handlers/          # the logic
  models/            # typed input/output and step models
  protocols/         # structural boundaries
  tests/             # parity, ordering, replay proofs
```

The contract is the runtime authority; the metadata file supports catalog discovery; the node shell is thin; handlers own implementation and are selected by contract routing. The contract declares `publish_topics` / `subscribe_topics` — topics are never hardcoded in Python and that prohibition is CI-enforced.

## Node Archetypes

The platform defines exactly **four** declarative node archetypes, plus a separate runtime-host kind for infrastructure that is not a handler archetype. The archetype enum deliberately excludes the runtime-host kind because a contract cannot declare itself as runtime infrastructure; the runtime-host kind is rejected as a handler node kind.

Each archetype is mechanically constrained to **one** allowed handler-output shape. This constraint is enforced **today** by a model-level validator at output construction: a violation raises a contract-violation error. This is live, not aspirational.

| Archetype | Responsibility | Allowed handler output |
| --- | --- | --- |
| **EFFECT** | External I/O at the boundary; publishes result events about external interactions. | `events[]` only |
| **COMPUTE** | Pure, stateless, deterministic transformation; never dispatches or routes. | `result` only (required unless explicitly allowed void; must be JSON-ledger-safe) |
| **REDUCER** | Pure finite-state fold `delta(state, event) -> (new_state, intents[])` with no I/O. | `projections[]` only |
| **ORCHESTRATOR** | Multi-step workflow coordination; selects and fans out to handlers; aggregates terminal results. | `events[]` and `intents[]` |
| _(runtime host)_ | Infrastructure runtime; not a handler archetype. Rejected as a handler node kind. | _n/a_ |

The output constraint keeps authoritative state and transport out of handler logic by construction: an orchestrator can never return a typed `result` or emit a projection; a reducer can only emit projections; an effect can only emit events; a compute can only return a result.

## Dispatch Seam

The dispatch seam turns one inbound envelope into invocations of every matching handler and then a single aggregated result. In the canonical target it is owned by exactly **two** archetypes — orchestrator and effect. The reducer stays a pure finite-state machine and is excluded from contract-table dispatch; the compute node loses routing entirely, because a compute node never legitimately dispatches.

Conceptually the seam does five things:

1. **Parse the routing table.** Read the contract's handler-routing declaration into a list of dispatch routes.
2. **Derive the selection keys.** From the inbound topic, derive a category; from the envelope, derive a message type (for example, from the payload class name).
3. **Match by glob.** Match routes by topic pattern, category, and message type. A single-segment wildcard (`*`) matches one path segment with no dots; a multi-segment wildcard (`**`) matches across segments. Matching is anchored and case-insensitive.
4. **Fan out the one invocation protocol.** For every matching handler, invoke the single platform protocol `handle(envelope) -> handler output`. There is exactly one handler entry point; the seam never calls bespoke per-handler signatures.
5. **Aggregate.** Collect the per-handler outputs into one dispatch result, isolating per-handler errors so one failing handler does not abort the fan-out.

The seam performs pure routing and fan-out only. It does not own workflow-ordering inference, retry, dead-letter routing, or output-publish ordering — those are runtime and bus responsibilities.

```mermaid
flowchart TD
    Envelope["inbound envelope (topic + payload)"] --> Parse["parse contract handler-routing → routes"]
    Parse --> Keys["derive category + message_type"]
    Keys --> Match["glob match: topic pattern + category + message_type"]
    Match --> Fanout["fan-out: handle(envelope) per matching handler"]
    Fanout --> H1["handler A → output"]
    Fanout --> H2["handler B → output"]
    Fanout --> Hn["handler N → output"]
    H1 --> Agg["aggregate → dispatch result"]
    H2 --> Agg
    Hn --> Agg
    Agg --> Emit["emit events[] / intents[]"]
```

Each handler is dispatched with a context appropriate to its node kind. **Context injection preserves purity:** effect and orchestrator handlers receive a context with an injected current time (clock); compute and reducer handlers receive a deterministic context with **no** clock injection. The runtime-host kind is rejected as a handler kind. The aggregation result model records, per dispatch, the status, route and handler identity, timing, outputs, error message and code, retry count, and correlation/trace/span identity. Per-handler errors are isolated: a failing handler is recorded and the fan-out continues.

## Orchestration & Workflows

An orchestrator node owns a multi-step, workflow-driven, or finite-state-machine-driven capability. Its defining responsibilities are:

- **Handler selection from the contract** — parse the contract's handler-routing declaration into routes and perform stateless, contract-table selection. No business logic in the shell decides which handler runs.
- **Coordination of sub-steps** — own the order in which steps execute and any gate semantics between them (for example, a findings threshold that must be met before a downstream stage proceeds).
- **Terminal aggregation** — aggregate per-handler structured outputs into one dispatch result or one contracted terminal output model.
- **Emission, not return** — emit `events[]` and `intents[]`; never return a typed `result` (compute's job) and never emit `projections[]` (reducer's job).
- **No direct external I/O** — delegate side effects to downstream effect nodes by emitting intents.

An orchestrator coordinates by emitting over the bus, not by calling other nodes' handlers in-process. The canonical coordination shape: the orchestrator emits a command or intent envelope onto a command topic; a downstream node consumes it, does its unit of work, and publishes a terminal event; the orchestrator (or its wiring) consumes the correlated terminal event and aggregates it into the workflow's terminal output.

```mermaid
sequenceDiagram
    participant Source as source event
    participant Orch as orchestrator
    participant Bus as event bus
    participant Sub as sub-node (effect / compute)
    participant Out as aggregated terminal output

    Source->>Orch: inbound envelope
    Orch->>Bus: publish command / intent (correlation id)
    Bus->>Sub: deliver command
    Sub->>Bus: publish terminal event (completed / failed)
    Bus->>Orch: deliver correlated terminal event
    Orch->>Out: aggregate terminal output + evidence
```

**Decision core.** The pure ordering and gate logic is kept side-effect-free — a common shape is an immutable finite-state-machine state model threaded step to step, each transition producing a new immutable state by copy rather than mutation. All external interactions are injected as protocol-typed boundaries so the decision core stays deterministic and testable.

**Sequential versus parallel sub-steps.** Steps run sequentially when a downstream stage depends on an upstream result or gate; a circuit breaker can halt the machine after a bounded number of consecutive failures. Where steps are independent, the seam's fan-out invokes all matching handlers, and ordering between independently emitted outputs is a bus concern, declared explicitly rather than assumed from arrival order.

**Terminal output shape.** Each orchestrator produces a single typed terminal result model (an external reference, a gate-result model carrying pass/fail and counts, or a verdict plus the ordered transition events and final state) — contracted, not a generic untyped blob.

Two boundaries are load-bearing. Orchestrators **delegate authoritative state**: they coordinate but do not persist; state progression and read-model truth belong to reducers and projections built from accepted events. And orchestrators are **not a place for I/O or transforms**: direct external I/O is the effect archetype's job, pure transformation is the compute archetype's job. The sharpest single line: orchestrators dispatch; computes never do. Lifecycle claims for a dispatched workflow must cite the canonical typed lifecycle-event chain observable on the bus rather than a self-attested local record (see `adrs/ADR-0005-dispatch-lifecycle-canonical.md`).

## Event Bus & Transport

The event bus is **the** inter-service transport. A synchronous HTTP edge is allowed only as a thin publisher or read edge during transition; direct browser reads, local fixtures, and skill output are explicitly not truth surfaces. Each node's contract is the single source of truth for subscribe/publish topics, handler routing, idempotency strategy, and retry policy — topics are never hardcoded in handlers.

**Topic naming convention.** Canonical topics follow `{env}.onex.{evt|cmd}.{producer}.{action}.v{N}`; all topics are currently at `v1`.

**Publish/retry/dead-letter/ordering live on the bus, not in handler code.** Handlers hold no direct bus access; only the coordinating layer publishes. The runtime publishes outputs in causality order: events, then projections, then intents (intents are runtime-internal by default).

**Consumer resilience.** Consumer failures retry with exponential backoff (bounded attempts) and then route to a dead-letter topic (`{original_topic}-dlq`) and commit the offset; the dead-letter payload carries the original event, the error, the failure timestamp, and the consumer group. A circuit breaker (closed / open / half-open, with fast-fail and resilient presets) guards downstream dependency edges, complementing retry and dead-lettering as a degrade-safely mechanism.

```mermaid
flowchart TD
    Deliver["deliver message"] --> Handle["consumer handles"]
    Handle -->|success| Commit["commit offset"]
    Handle -->|failure| Retry["retry with exponential backoff (bounded)"]
    Retry -->|attempts exhausted| DLQ["route to {topic}-dlq + commit offset"]
    Retry -->|succeeds| Commit
    Dep["downstream dependency call"] --> CB{circuit breaker}
    CB -->|closed| Call["call dependency"]
    CB -->|open| FastFail["fail fast"]
```

Transport acceptance evidence must exercise broker recovery, producer failure, dead-letter recovery and schema-version migration. This target design does not establish the current implementation status of those properties.

## State, Reducers & Projections

Authoritative truth is owned by the event log, contracted inputs, and materialized projections. **Clients render truth; they do not create it** — they subscribe or request, render, and invalidate-and-refetch; they must not infer state, merge event streams into truth, dedupe authoritative records, or read backend stores directly.

**Reducers fold events into state via a contract FSM.** State progression is defined by the projection's reducer contract: valid finite-state-machine transitions are declared in the contract, not in enum or application code, so transitions are enforced at the architecture layer. A reducer transition validates fail-fast before any write, then proceeds in a fixed order:

```mermaid
flowchart TD
    Event["accepted event"] --> Validate["validate (fail-fast):<br/>non-empty trigger, valid publish topic,<br/>promotion guards, evidence-tier gates"]
    Validate -->|invalid| Reject["reject (not silently applied)"]
    Validate -->|valid| Lock["optimistic-lock state update"]
    Lock --> Audit["append audit row"]
    Audit --> Idem["record idempotency key"]
    Idem --> Emit["emit event"]
    Emit -->|publish fails| DLQ["route to dead-letter (DB transition NOT rolled back)"]
    Emit -->|publish ok| Project["materialize / upsert projection row"]
    Project --> API["projection-backed read API"]
```

**Canonical reducers win, not arrival order.** Last-write-wins is valid only when a projection contract explicitly declares it; otherwise reducer semantics decide. Arrival order, UI sort order, or an accidental first/last write must never determine truth.

**State is a materialized projection.** State must be explicitly constructed from source events and contracted inputs; a projection owns sequencing, reduction, aggregation, shape, and cursor semantics. There is no hidden authoritative state. Projections derive from a base carrying a canonical key and a version that matches canonical state, designed for version-gated reads with fallback to canonical when projection lag exceeds a threshold.

**Ordering must be explicit and contracted.** Every projection must declare its ordering contract based on an ingest-assigned sequence, a projection version, or another contracted monotonic value. An event timestamp may be used only with an explicitly defined clock authority; no component may rely on incidental arrival order, and cross-source global ordering needs a shared ingest ledger.

**Cursors represent projection progress.** A cursor is not pagination — it is the maximum known truth boundary for a projection: monotonic, projection-scoped, comparable within scope, and derived from a canonical sequence or progress value. The core layer ships projection base, cursor, and watermark models.

**Idempotency.** Effect nodes declare idempotency (a request-identity strategy with a key field); a duplicate request returns the cached result with no write, preventing duplicate transitions on retry. The idempotency key is recorded best-effort after commit.

**Degrade safely.** Correctness is preferred over availability: delay, quarantine, dead-letter, or mark a projection explicitly degraded — never silently drop, guess missing state, reorder without authority, or present degraded data as complete. A projection-backed dashboard realizes this by disabling real-time updates and serving last-successful read-model data after backoff exhaustion.

The doctrine target and the current as-built path differ on ordering, cursors, replay, and the state/bus consistency seam; implementation claims require revision-scoped evidence as described in **Current Versus Target State**.

## Configuration: Contracts, Overlays, Manifests, Subcontracts, Projection Contracts

Configuration discipline is the spine that makes contracts the source of runtime authority. The flow is **declare → supply → resolve → inject**.

```mermaid
flowchart TB
    Req["contract config requirements<br/>(required keys + required transports, typed)"] --> Resolver["overlay resolver<br/>(filter, not passthrough; fail-fast on missing required)"]
    Overlay["scoped overlays<br/>BASE → ORG → PROJECT → ENV → USER → SESSION"] --> Resolver
    Resolver --> Manifest["resolution manifest<br/>(durable evidence, hash-stable identity)"]
    Manifest --> Materializer["runtime dependency materialization<br/>(contract deps → live providers)"]
    Materializer --> Container["typed dependency container"]
    Container --> Handler["handler receives typed deps<br/>(no ambient env reads)"]
```

- **Contract config requirements.** A contract declares required config keys and required transport types, aggregated into a typed, frozen requirements model. Contracts — not code — define what config must exist.
- **Overlay files.** A frozen, extra-forbidding, validated schema with environment, scope, and sectioned config. Overlays flatten to key/value pairs with conflicting-duplicate detection, expose a deterministic content hash, and redact secret-named values. They stack in canonical precedence (`BASE → ORG → PROJECT → ENV → USER → SESSION`, higher overriding lower).
- **Resolver.** Filters the loaded overlay against contract requirements — it takes only declared keys, never passes through arbitrary overlay keys, collects missing-optional keys, and **raises** when a required key is absent. Same overlay plus same requirements yields the same resolved set and hashes.
- **Resolution manifest.** A frozen evidence artifact recording overlay file hash, overlay version, scope stack, requirements hash, resolved-config hash, resolved-versus-required transports, runtime version, timestamp, and config source. A stable-identity hash deliberately excludes timestamp and runtime version so identical inputs yield the same identity across boots — an auditable, replayable config artifact.
- **Runtime dependency materialization.** A materializer reads a contract's dependency declarations and creates shared live providers (database pools, broker producers, HTTP clients) from resolved config, with no domain-specific boot code. Resolved protocol dependencies are held in a frozen typed container keyed by protocol and injected into node constructors. Handlers consume resolved deps rather than constructing I/O or reading env for transport lanes, secrets, or topics.

**Subcontracts** are declarative behavior modules referenced from the main contract by relative path plus an integration field, and exist as typed core models: effect, event-bus, compute, introspection, security, lifecycle, health-check, and validation subcontracts, plus retry-policy and circuit-breaker models. The effect subcontract carries discriminated-union I/O configs, idempotency-aware retry, a process-local circuit breaker, transaction config, and observability, and enforces invariants (for example, retry only on idempotent operations; no read retry inside repeatable-read/serializable isolation; no raw operations inside transactions). Retry and dead-letter behavior are contract-declared, not hand-rolled.

**Manifests** are durable identity artifacts. The runtime manifest binds runtime profile, contracts, owned command topics, subscribed event topics, handlers, skipped/failed contracts, ownership violations, image digest, and start time, with computed contract and topology hashes for deterministic identity. Topic ownership is first-class (owned command topics), supporting the one-owner-per-command-topic invariant; ownership violations are tracked as first-class data.

**Projection contracts** are first-class frozen models declaring: the projection name (ownership), source topics consumed, the fully-qualified schema model for rows, a freshness SLA (seconds plus a freshness field and source table), an ordering-contract reference, a cursor contract, and an explicit degraded-behavior choice with **no default** — serve-stale-with-warning, return-empty, or fail-closed.

**Secrets** are referenced through governed provider paths, never inlined: contracts and overlays declare secret references and required keys, the runtime retrieves actual values via an infra-owned governed secret provider, and overlay dumps redact secret-named values.

## Runtime, Registration & Registry Boundary

The runtime, registration, and registry surfaces are separated by two accepted decisions (see `adrs/ADR-0003-registration-runtime-registry-boundary.md` and `adrs/ADR-0004-registry-owned-consumer-surface.md`).

```mermaid
flowchart LR
    Runtime["RUNTIME host<br/>discovery + handler/consumer wiring<br/>emits lifecycle facts"] --> Facts["normalized lifecycle facts:<br/>contract_discovered, consumer_started,<br/>node_announced, node_accepted,<br/>heartbeat_seen, node_expired,<br/>recovery_requested"]
    Facts --> Registration["REGISTRATION orchestration<br/>accept / liveness / expiry / recovery"]
    Registration --> Registry["REGISTRY projection<br/>(canonical durable read truth)"]
    Registry --> RegAPI["projection-backed registry API<br/>(only supported sync consumer surface)"]
    RegAPI --> Downstream["downstream consumers<br/>(read projections only)"]
```

- **Runtime owns discovery and wiring.** The runtime host process is the authority for discovering contracts (package and catalog surfaces), wiring handlers, dispatchers, and subscriptions, starting consumers, and emitting normalized lifecycle facts. It does **not** own durable registry truth or API read semantics. It is the wiring authority.
- **Registration owns orchestration.** Registration is a separate authority that consumes the normalized lifecycle facts plus explicit registry events and orchestrates acceptance, liveness, expiry, and recovery. It does **not** decide what contracts exist and does **not** bootstrap runtime discovery; lifecycle facts are the boundary objects, not raw startup internals.
- **Registry projections own durable read truth.** Registry projections are the sole durable read truth for registration state; runtime memory, startup logs, and compatibility paths are not read truth. Exactly one projection is declared canonical; any storage/effect table is non-canonical, and a compatibility read model must not become a second authority.
- **Consumer surface ownership.** The only supported synchronous consumer surface is the registry-owned API backed by a projection reader (node list/detail, discovery summaries derived from projection results). Direct downstream reads from the projection table are not the default integration contract, and snapshot publication is deferred. Downstream consumers read projections only — never tables, never runtime memory.

**Dependency injection is explicitly three-role.** The **container** is the service provider that owns protocol instances; the **runtime resolver** is the wiring authority that resolves and validates (fail-fast: it raises immediately if a required protocol cannot be resolved); the **node** is the consumer that receives resolved protocol dependencies via its constructor. Nodes never self-wire or hand-build buses; there is no manual handler wiring and no null event bus.

## Generated-capability experiments (historical)

A retired prototype explored generating a contract, node and handler from a request. It is not a core subsystem or beta deliverable. The durable design requirement is that generated code must pass contract, type, effect-boundary and behavior checks before it becomes callable; no current implementation or gate coverage is claimed here for the retired prototype.

## Model & Inference Routing Boundary

The binding invariant is that **model selection, escalation, fallback, pricing policy, and route evidence live in the platform routing layer, not in the agent that needs inference.** An agent emits an inference intent and consumes a terminal response; routing nodes own model selection and execution.

```mermaid
sequenceDiagram
    participant A as agent (needs inference)
    participant B as event bus
    participant R as platform routing layer
    participant L as inference effect
    participant E as evidence surface

    A->>B: inference intent
    B->>R: route request
    R->>B: route decision (model tier, escalation policy)
    B->>L: inference command
    L->>B: inference response
    B->>A: terminal response
    B->>E: route + terminal evidence
```

Delegation already has a bus-routed dispatch design, described in [Delegation dispatch](delegation-dispatch.md). Local execution can use an in-process transport. A separate retired agent prototype is not evidence of a gap in the delegation product. Model selection and provider calls remain owned by the routing and effect boundaries.

## CI & Full-TDD Evidence Gates

CI is a **proof pipeline**, not just a test runner.

**Full TDD ordering.** For implementation work, the expected sequence is: (1) derive behavior from a contract, design document, decision record, or acceptance criterion; (2) write the failing test before implementation; (3) capture the failing output; (4) implement the smallest contract-native change; (5) run targeted tests; (6) run repo-native lint and type checks; (7) run integration or golden-chain proof when behavior crosses a runtime, event, projection, registration, or evidence boundary; (8) bind required evidence before completion.

**Side-effect assertions are mandatory.** Return-value-only tests are insufficient for handlers that publish events, materialize projections, write proof artifacts, or call approved effect edges — the test must assert the externally observable effect.

| Layer | Design purpose | Example proof | Status |
| --- | --- | --- | --- |
| Unit | Isolated logic correctness. | Focused test result. | current (Required) |
| Contract-to-test | Behavior came from a declared contract or acceptance criteria. | Failing-test evidence + traceable requirement. | target (process; fail-first ordering not machine-verified) |
| Integration | Declared side effects occur. | Event, projection, API, file, or effect assertion. | current (Required where wired) |
| Golden chain | End-to-end event-to-projection flow works. | Source event, terminal event, projection read, replay result. | target (replay tooling not yet evidenced as wired) |
| Cross-domain sweep | Shared contracts still compose. | Multi-repo contract or schema validation. | current |
| Standing sweep | Platform stays clean over time. | Scheduled or repeated validation result. | current |
| DoD verification | Completion evidence satisfies required proof. | Receipt or durable evidence artifact. | target (fail-closed completion automation) |

```mermaid
flowchart TB
    PR["pull request"] --> Static["static validators"]
    PR --> Tests["unit + integration tests"]
    PR --> Type["lint + type checks"]
    Static --> Evidence["evidence / receipt gate"]
    Tests --> Evidence
    Type --> Evidence
    Evidence --> Queue["merge queue"]
    Queue --> Merge["merge"]
```

**CI gate families** (honestly scoped per repository) include: repo-local tests; lint and format checks; configured type checks; contract compliance; handler-routing and invocation conformance; skip-token or bypass rejection where configured; evidence-receipt pairing for receipt-gated work; and deploy or runtime gates when deployment behavior changes. The gate set is narrower in some repositories than others — a single repository's gate set must not be cited as platform-wide full-TDD enforcement.

**Merge queue and runner health.** A merge queue is the integration proof boundary: it proves a candidate against the branch state it will enter, and queue failures must be classified before changing merge policy. Runner health is part of CI correctness — a process that appears alive is not sufficient; the proof surface must establish that jobs can be accepted, dependencies fetched, required checks published, and ambiguous check states fail loudly.

**Current versus target enforcement.** Current binding rules: run repo-local tests, lint, and configured type checks; reject bypass behavior where configured; require durable evidence pairing for receipt-gated work; treat contract/handler/architecture validators as binding where wired; require integration or replay-style proof for runtime and projection claims. Target-state rules: machine-verifiable fail-first TDD ordering across all repositories; universal adversarial-review gates for architecture-affecting changes; fail-closed completion automation for all evidence levels; and automatic merge freezes on affected paths after golden-chain failures. A target-state gate must not be described as current enforcement until it is wired and verified.

## Evidence & Deterministic Truth

Truth is proven through contracts, event logs, materialized projections, deterministic replay (or equivalent proof), and durable evidence in approved control-plane surfaces. Status, logs, and completion signals are not truth; clients render truth, they do not create it. A task is not done without durable evidence.

- **Evidence is a first-class output.** Every externally visible operation, state transition, deployment, and completion must emit durable, inspectable evidence — projection snapshots, event receipts, reducer outcomes, validation artifacts, replay outputs, checksums — reachable through approved surfaces (change contracts and receipts, CI, pull requests, committed manifests).
- **Truth must be proven, not claimed.** Truth requires authoritative downstream state reflecting the result, observability through approved boundaries, survival of replay/restart/reprocessing, and durable evidence outside the originating workstation.
- **Deterministic under replay.** The same canonical input sequence plus the same contract/reducer version yields the same projected state. Replay must not depend on wall-clock, consumer arrival order, restarts, or transient state. If replay produces a different authoritative state, the system is incorrect.

A proof bundle should include:

- contract identity and version;
- source-event and terminal-event identity;
- per-step terminal events for each sub-node invoked (for orchestrated workflows), observable on the bus;
- projection cursor or read-model proof for any state advanced;
- replay or replay-equivalent validation;
- a durable evidence receipt or equivalent artifact.

**Evidence/receipt pairing.** A code change cites acceptance evidence in its owning repository: a PR, a CI run or a receipt. Tests must exercise the changed behavior and fail without the change. See [the evidence pivot](../pivots/PIVOT-0006-evidence-lives-with-code.md).

```mermaid
flowchart LR
    PR["code change"] --> Pointer["evidence pointer"]
    EvidenceRepo["owning product repository"] --> Contract["change contract"]
    EvidenceRepo --> Receipt["PASS receipt (verifier ≠ runner)"]
    Pointer --> Gate["receipt gate"]
    Contract --> Gate
    Receipt --> Gate
    Gate --> Merge["merge allowed"]
```

**Data-verification blocking semantics** (see `adrs/ADR-0002-data-verification-invocation.md`): a data-verification failure blocks Done (via a completion guard) but does **not** block PR merge, because verification targets often exist only post-merge or post-deploy. Merge-time correctness is covered by CI and golden-chain proof; data verification is post-deploy confirmation. A partial or timed-out verification is treated as a failure requiring retry. The canonical invocation path for data verification is a command topic on the bus, with a local CLI as a debug/CI fallback that must not satisfy a real Done receipt (the runtime wiring for the bus publisher path on that flow is itself deferred follow-on work).

## Current Versus Target State

*State as of 2026-10-18: this document is a target architecture, not a current deployment inventory.*

The public beta workflow is local delegation: submit a task to a customer-configured model, evaluate the answer, and retain a receipt for metering and inspection. The [quickstart](../guides/delegation-quickstart.md) describes that path. The [delegation architecture guide](delegation.md) maps its dispatch, routing and ownership boundaries. Self-hosted delegation uses the configured bus transport; local execution can use an in-process bus. The hosted service is not open to outside users.

The earlier May divergence list has been withdrawn because it was not reverified against current default branches. It must not be read as a live defect list. In particular, its inference-routing statement described a separate agent experiment and did not describe the delegation workflow. No remaining May item is asserted resolved without current implementation evidence.

The self-extending-agent prototype is retired and is not a core platform subsystem or a beta deliverable. Generated-node admission remains an architectural validation requirement, independent of that prototype.

For any implementation-convergence claim, cite the owning repository's PR, test or receipt and its revision, following [Evidence lives with the code it proves](../pivots/PIVOT-0006-evidence-lives-with-code.md).

## Acceptance Criteria / Platform Invariants

- New platform capabilities map to the three primitives and are packaged as contract-native node packages with a thin node shell and contract-declared handler routing.
- A node's allowed handler output matches its archetype — effect emits `events[]`, compute returns `result`, reducer emits `projections[]`, orchestrator emits `events[]` and `intents[]` — and this is enforced at output construction.
- Dispatch selection is driven by the contract routing table through the single handler invocation protocol; the seam parses routing, glob-matches, fans out the one protocol, and aggregates, isolating per-handler errors.
- Coordination flows over the event bus; handlers hold no direct bus access and no in-process cross-node handler imports; publish, retry, dead-letter, and ordering live on the bus.
- Authoritative state is delegated to reducers and projections built from accepted events; clients render truth and do not create it; ordering is explicit and contracted; cursors mark the maximum known truth boundary.
- Runtime configuration is contract-visible and typed: contracts declare requirements, scoped overlays supply values, a resolver filters and fails fast on missing required keys, and a hash-stable manifest is the durable evidence; handlers receive typed dependencies and never read ambient process state for transport lanes, secrets, or topics.
- Runtime owns discovery and wiring; registration owns orchestration over normalized lifecycle facts; registry projections own durable read truth; the only supported synchronous consumer surface is the projection-backed registry API; nodes never self-wire.
- Generated capabilities are rejected before registration when they fail validation; generated effect handlers emit effect events rather than performing direct I/O; model-routing authority remains outside the generating agent; a generated artifact is invokable through the runtime and its identity and result are proven by evidence.
- Inference flows as agent-emitted intent into a platform routing layer that owns model selection, escalation, fallback, pricing, and route evidence (target).
- CI status is read from the hosting platform and workflow outputs, not from agent summaries; ambiguous CI state fails loudly; handler and effect changes include side-effect assertions; receipt-gated changes have durable evidence pairing; runtime and projection claims include integration or golden-chain proof.
- Completion is proven, not asserted: a proof bundle binds contract identity, source and terminal events, projection/replay proof, and a durable receipt; truth survives replay/restart/reprocessing and lives durably outside the originating workstation.
- Current-versus-target claims are labeled honestly; any claim that the dispatch architecture has converged cites the selection-parity proof and the cutover evidence — neither of which this document asserts as produced.
