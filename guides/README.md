# Guides

Task-oriented how-to documentation: getting started, onboarding, integration walkthroughs, and per-component usage guides. The distinguishing test is that the reader is trying to **do** something — if they are trying to look a fact up, it belongs in [`reference/`](../reference/README.md); if they are trying to operate or recover a running system, it belongs in [`runbooks/`](../runbooks/README.md).

## Start here

New to OmniNode? Read [What OmniNode is, and where it stands](what-is-omninode.md) first: one page on what ships today, what is in beta, and what is not yet open. Then try it.

| | Guide | What it is for |
|---|---|---|
| **1** | **[Delegation quickstart](onex-plugin-quickstart.md)** | **Hand a task to a model you choose, on your own machine or your own provider key, and get back the answer plus a receipt naming the model.** Install, first delegation, receipts, `onex metering`, the local dashboard and the Claude Code plugin, in about 15 minutes. **Start here** to evaluate OmniNode. |
| **2** | [Building on the ONEX runtime](getting-started-local.md) | For developers writing their own nodes. One package, one command, and a real event chain you can read back out of a local database file, with no broker, no database server, no container runtime and no account. It needs no model and does not delegate. |
| **3** | [Self-hosting the full stack](getting-started-self-hosted.md) | On your own infrastructure, in containers. The scale-up chapter: a real broker, PostgreSQL, a cache, an identity provider, and the runtime services on top. Read it when you have actually outgrown the local runtime; the page opens with the list of reasons that qualify. |
| **4** | [Connecting to the cloud](connecting-to-the-cloud.md) | The hosted service, which is not yet open to outside users. Nothing on the delegation path needs it. |
| **5** | [Combining deployment tiers](combining-deployment-tiers.md) | More than one of the runtime tiers at once. The seams between them: which knob moves you across one, what changes when you cross it, and what stays identical. |

[Supported platforms](supported-platforms.md) says where the `onex` tool installs, and how, on each kind of computer.

## Everything else

### Agent integrations

How each coding agent invokes OmniMarket nodes through a thin adapter: the skill or command
file the agent reads, and the runtime path it calls. The Claude Code plugin in the
[Delegation quickstart](onex-plugin-quickstart.md) is the one an outside user installs today.

- [`omnimarket-claude-code-adapter.md`](omnimarket-claude-code-adapter.md) — Claude Code adapter
- [`omnimarket-codex-adapter.md`](omnimarket-codex-adapter.md) — Codex adapter
- [`omnimarket-cursor-adapter.md`](omnimarket-cursor-adapter.md) — Cursor adapter
- [`omnimarket-gemini-adapter.md`](omnimarket-gemini-adapter.md) — Gemini CLI adapter

### Building on the ONEX kernel

The node-building and mixin-development tutorial series, the four node templates, and the
task-oriented guides for contracts, effects, protocols, threading, tracing and testing.
Migrated out of the `omnibase_core` repository.

- [`onex-handler-contracts.md`](onex-handler-contracts.md) — Handler Contract Guide
- [`onex-introspection-subcontract.md`](onex-introspection-subcontract.md) — Introspection Subcontract Guide
- [`onex-error-handling-best-practices.md`](onex-error-handling-best-practices.md) — ONEX Error Handling Best Practices
- [`onex-pydantic-best-practices.md`](onex-pydantic-best-practices.md) — Pydantic Best Practices for ONEX
- [`omnibase-core-first-node.md`](omnibase-core-first-node.md) — Build Your First Node
- [`omnibase-core-quick-start.md`](omnibase-core-quick-start.md) — Quick Start Guide
- [`omnibase-core-installation.md`](omnibase-core-installation.md) — Installation Guide - omnibase_core
- [`onex-contract-patching.md`](onex-contract-patching.md) — Contract Patching Guide
- [`onex-contract-profiles.md`](onex-contract-profiles.md) — Contract Profile Guide
- [`onex-declarative-node-import-rules.md`](onex-declarative-node-import-rules.md) — Declarative Node Import Rules
- [`onex-effect-boundary.md`](onex-effect-boundary.md) — Effect Boundary Guide
- [`onex-effect-subcontracts.md`](onex-effect-subcontracts.md) — Effect Subcontract Guide
- [`onex-execution-corpus.md`](onex-execution-corpus.md) — Execution Corpus Guide
- [`onex-golden-chain-harness.md`](onex-golden-chain-harness.md) — Golden-Chain Harness — Authoring Guide
- [`onex-mixin-subcontract-mapping.md`](onex-mixin-subcontract-mapping.md) — Mixin-Subcontract Mapping Guide
- [`omnibase-core-performance-benchmarks.md`](omnibase-core-performance-benchmarks.md) — ONEX Performance Testing Suite
- [`onex-pipeline-hook-registry.md`](onex-pipeline-hook-registry.md) — Pipeline Runner and Hook Registry Guide
- [`onex-production-cache-tuning.md`](onex-production-cache-tuning.md) — Cache Tuning for Production Deployment
- [`onex-protocol-discovery.md`](onex-protocol-discovery.md) — Protocol Discovery Guide
- [`onex-request-tracing.md`](onex-request-tracing.md) — Request Tracing in ONEX
- [`omnibase-core-testing.md`](omnibase-core-testing.md) — Testing Guide - omnibase_core
- [`onex-threading.md`](onex-threading.md) — Thread Safety in Omnibase Core
- [`onex-mixin-development-01-creating-mixins.md`](onex-mixin-development-01-creating-mixins.md) — Creating Mixins - Step-by-Step Guide
- [`onex-mixin-development-02-mixin-yaml-schema.md`](onex-mixin-development-02-mixin-yaml-schema.md) — Mixin YAML Schema Reference
- [`onex-mixin-development-03-pydantic-models.md`](onex-mixin-development-03-pydantic-models.md) — Pydantic Models for Mixins
- [`onex-mixin-development-04-mixin-integration.md`](onex-mixin-development-04-mixin-integration.md) — Mixin Integration Guide
- [`onex-mixin-development-05-best-practices.md`](onex-mixin-development-05-best-practices.md) — Mixin Development Best Practices
- [`onex-mixin-development-overview.md`](onex-mixin-development-overview.md) — Mixin Development Guide
- [`onex-node-building-01-what-is-a-node.md`](onex-node-building-01-what-is-a-node.md) — What is a Node?
- [`onex-node-building-02-node-types.md`](onex-node-building-02-node-types.md) — Node Types
- [`onex-node-building-03-compute-node-tutorial.md`](onex-node-building-03-compute-node-tutorial.md) — COMPUTE Node Tutorial
- [`onex-node-building-04-effect-node-tutorial.md`](onex-node-building-04-effect-node-tutorial.md) — EFFECT Node Tutorial: Build a File Backup System
- [`onex-node-building-05-reducer-node-tutorial.md`](onex-node-building-05-reducer-node-tutorial.md) — REDUCER Node Tutorial: Build a Pure FSM Metrics Aggregator
- [`onex-node-building-06-orchestrator-node-tutorial.md`](onex-node-building-06-orchestrator-node-tutorial.md) — ORCHESTRATOR Node Tutorial: Build a Data Processing Pipeline
- [`onex-node-building-07-patterns-catalog.md`](onex-node-building-07-patterns-catalog.md) — Patterns Catalog -- Common ONEX Node Patterns
- [`onex-node-building-08-common-pitfalls.md`](onex-node-building-08-common-pitfalls.md) — Common Pitfalls - What to Avoid When Building Nodes
- [`onex-node-building-10-agent-templates.md`](onex-node-building-10-agent-templates.md) — Agent Templates for ONEX Node Development
- [`onex-node-building-overview.md`](onex-node-building-overview.md) — Node Building Guide
- [`onex-replay-safety-integration.md`](onex-replay-safety-integration.md) — Replay Safety Integration Guide
- [`onex-compute-node-template.md`](onex-compute-node-template.md) — COMPUTE Node Template
- [`onex-effect-node-template.md`](onex-effect-node-template.md) — EFFECT Node Template
- [`onex-orchestrator-node-template.md`](onex-orchestrator-node-template.md) — ORCHESTRATOR Node Template
- [`onex-reducer-node-template.md`](onex-reducer-node-template.md) — REDUCER Node Template
- [`omnibase-core-test-coverage.md`](omnibase-core-test-coverage.md) — Code Coverage Testing
- [`omnibase-core-integration-testing.md`](omnibase-core-integration-testing.md) — Integration Testing Guide - omnibase_core
- [`omnibase-core-parallel-testing.md`](omnibase-core-parallel-testing.md) — Parallel Testing Architecture and Resource Management
- [`omnibase-core-performance-testing.md`](omnibase-core-performance-testing.md) — Performance Testing Guide
- [`omnibase-core-testmon-usage.md`](omnibase-core-testmon-usage.md) — pytest-testmon Usage Guide
- [`onex-example-contract-security.md`](onex-example-contract-security.md) — Security Considerations for Example Contracts
- [`onex-effect-contract-security.md`](onex-effect-contract-security.md) — Security Considerations for Effect Contracts
- [`omnibase-core-model-validation-demo.md`](omnibase-core-model-validation-demo.md) — Model Validation Demo: Support Ticket Classification

## This section is open

Frontmatter `type: guide`, with `status: draft | current | stale | deprecated`. The validator discovers files recursively, so a nested path (e.g. `guides/getting-started/install.md`) is validated the same as a top-level one.

See [docs-taxonomy.md](../docs-taxonomy.md) for what belongs here, and [migration-manifest.yaml](../migration-manifest.yaml) for the planned mapping.
