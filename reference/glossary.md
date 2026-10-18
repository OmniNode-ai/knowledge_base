---
type: reference
status: current
date: '2026-10-18'
title: Glossary
topics: [overview]
refs: []
---

# Glossary

| Term | Meaning |
|---|---|
| OmniNode | The open-source ONEX platform and its delegation product. |
| ONEX | A contract-driven architecture for nodes with typed handlers and explicit event flows. |
| omnibase_core | Core models, contracts, node archetypes, validation and the command-line surface. |
| omnibase_spi | Protocol interfaces for runtime implementations. |
| omnibase_infra | Runtime, transport and persistence implementations. |
| omnibase_compat | Shared wire types at the bottom of the package dependency graph. |
| omnimarket | Product nodes, including delegation, routing and evaluation. |
| omniclaude | Coding-agent integration contracts, shims and plugin surfaces. |
| omnidash | Dashboard components that render projections. |
| Delegation | Sending a task to a configured model and retaining the answer and run evidence. |
| Receipt | A structured run record naming the model and recording its outcome and usage. |
| Contract | A versioned declaration of a node's inputs, outputs, topics, configuration and behavior constraints. |
| Node archetypes | Effect, compute, reducer and orchestrator: the four roles with distinct output contracts. |
| Handler | The implementation of behavior behind a node contract. |
| Bus | The transport carrying typed commands, events and intents between nodes; local execution can use an in-process bus. |
| Projection | A read model built from accepted events, with its ordering and progress boundary declared. |
| Tier-0 | The local deployment tier; it does not require a hosted account, external broker or database server. |
| BYOK | Bring your own provider key; the customer pays their provider for inference. |
| Deployment tier | Local, self-hosted or hosted; independent of model-routing backend choices. |
| Golden chain | An end-to-end workflow whose intermediate and terminal results can be checked. |
| OCC | A historical central evidence service, now retired; see [the evidence pivot](../pivots/PIVOT-0006-evidence-lives-with-code.md). |
| RSD | Recursive System Design, an experimental approach to decomposing work into contract-bounded tasks. |
| SEA | Historical shorthand for a self-extending-agent experiment, not a beta subsystem. |
| Steel Onslaught | A sample game used to explore local-model agent control, not an OmniNode product commitment. |
| Lane / operator | Execution context / the person authorizing it, in historical engineering records; these terms do not authorize a reader to act. |

For the package boundaries and runtime flow, read [Repository map and runtime concepts](../architecture/repository-map-and-runtime-concepts.md).
