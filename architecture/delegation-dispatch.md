---
type: architecture
status: accepted
date: "2026-08-25"
title: "Delegation Dispatch Architecture"
topics: [omnimarket, delegation, llm-routing]
refs:
  - architecture/delegation-routing-contract.md
  - guides/onex-plugin-quickstart.md
  - reference/public-proof-index.md
---

# Delegation Dispatch Architecture

Public source checked on 2026-10-20 against `omnimarket` release `v0.4.317`.
Start with the [quickstart](../guides/onex-plugin-quickstart.md) for the shipped local product.
The [routing contract](delegation-routing-contract.md) owns configuration and credential
registration; exporting `OPENROUTER_API_KEY` does not register a local customer key.

## Local product and distributed runtime

`onex delegate` and the installed plugin's `/onex:delegate` invoke
`node_delegate_skill_orchestrator`. The public
[local dispatch port](https://github.com/OmniNode-ai/omnimarket/blob/v0.4.317/src/omnimarket/nodes/node_delegate_skill_orchestrator/ports/port_local_delegation_dispatch.py)
implements the local execution path without requiring a broker or hosted gateway. Your
machine calls your declared model endpoint or provider directly, using your registered key.

The distributed runtime composes delegation through command and event boundaries:

```text
caller → node_delegate_skill_orchestrator
       → node_delegation_orchestrator
       → routing and inference effects
       → quality gate → terminal result or escalation
       → projections / caller
```

The entry contract is [published here](https://github.com/OmniNode-ai/omnimarket/blob/v0.4.317/src/omnimarket/nodes/node_delegate_skill_orchestrator/contract.yaml).
These are two execution configurations of shared ONEX components. The distributed flow
is not a requirement to run the local quickstart, nor evidence that the hosted service
exposes a full event journal. The [cloud guide](../guides/connecting-to-the-cloud.md#what-a-receipt-says)
documents a terminal receipt with `event_count=1` and no workflow journal; its availability
reports must not be read as an independently validated production deployment.

## Inference effect boundary

The [delegation call handler](https://github.com/OmniNode-ai/omnimarket/blob/v0.4.317/src/omnimarket/nodes/node_llm_delegation_call_effect/handlers/handler_llm_delegation_call.py)
posts the resolved complete endpoint URL verbatim. Transport selection is profile-dependent
(curl or httpx); the older description of every call as `DirectCurl` was too broad.
Do not append `/v1/chat/completions` in another layer. The route must already carry its
provider's complete path. Local endpoint overrides and registered provider credentials
are separate inputs; the former does not authenticate the latter.

## Routing, escalation and result quality

Routing uses task capabilities, declared tiers, registered provider models and configured
gates. See [the routing contract](delegation-routing-contract.md) for the tier names and
budget rule. Tier names do not establish price or quality. A failed attempt may escalate;
a refusal or exhausted route is a terminal outcome rather than permission to use an
undeclared provider credential.

A receipt records the system's reported outcome and backend attribution. Provider
authentication establishes access to an inference service, and hash checks can establish
consistency with particular recorded fields. Neither establishes answer correctness.
Configured quality gates have their own criteria and coverage; generated code still needs
task-specific tests and review. See [public evidence and limits](../reference/public-proof-index.md#credentials-and-receipt-limits).

## Replay scope

Reducer determinism and replay are platform contracts tested with captured event inputs.
They do not imply that a fresh model request will generate the same answer. The public
[workflow receipt verifier](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/src/omnibase_infra/verification/workflow_receipt/verifier.py)
can recompute the terminal-event hash from a suitable Kafka replay; it explicitly cannot
reconstruct the full projection-row hash from terminal events alone. That capability also
does not establish customer access to a hosted journal. For test entry points, see
[replay tests](../guides/omnibase-infra-replay-tests.md).
