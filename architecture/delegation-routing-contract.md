---
type: architecture
status: accepted
date: "2026-08-25"
title: "Delegation Routing Contract"
topics: [omnimarket, delegation, llm-routing]
refs:
  - architecture/delegation-dispatch.md
  - guides/onex-plugin-quickstart.md
  - reference/public-proof-index.md
---

# Delegation Routing Contract

Public source checked on 2026-10-20 against `omnimarket` release `v0.4.317`.
For installation and supported provider registration, follow the
[quickstart](../guides/onex-plugin-quickstart.md). This page describes routing
configuration, not a promise that every declared backend is available to every user.

## Configuration authority

The routing declarations live under `src/omnimarket/configs/`:

| File | Role |
| --- | --- |
| [bifrost_delegation.yaml](https://github.com/OmniNode-ai/omnimarket/blob/v0.4.317/src/omnimarket/configs/bifrost_delegation.yaml) | Backend definitions, endpoint references, model names, capabilities and output-token ceilings |
| [routing_tiers.yaml](https://github.com/OmniNode-ai/omnimarket/blob/v0.4.317/src/omnimarket/configs/routing_tiers.yaml) | Tier declarations and task-class escalation order |

Site-local endpoint and model overrides come from
`~/.omninode/delegation/bifrost_overrides.yaml`. The quickstart shows its minimal shape.
Provider route substitution also uses the customer's registered credential and model;
the repository defaults alone do not establish the route a customer will execute.

## Credentials: registration is required

For the shipped local path, register a provider key with `onex secret set`, for example:

```bash
onex secret set llm.openrouter.api_key
```

Choose the model as the quickstart describes. Exporting `OPENROUTER_API_KEY` or
`LLM_OPENROUTER_API_KEY` does not register the key or enable a customer provider route.
The public [local credential adapter](https://github.com/OmniNode-ai/omnimarket/blob/v0.4.317/src/omnimarket/inference/local_byok_credential_adapter.py)
and [resolver](https://github.com/OmniNode-ai/omnimarket/blob/v0.4.317/src/omnimarket/inference/secret_store_resolver.py)
resolve local provider references from the local store, including refusal when only an
environment key exists. This replaces the older environment-key advice on this page.
Endpoint environment references in the backend configuration are a separate matter:
an endpoint address is not a registered provider credential.

## Task-class tier escalation

The checked contract declares `local` → `cheap_cloud` → `cheap_frontier` → `claude`.
Task classes declare their own order and required capabilities. These names are routing
slots, not promises about a provider, model, price or measured answer quality. In particular,
`claude` is the ceiling slot's identifier; it does not imply an Anthropic call.

A customer's effective route depends on declared endpoints, registered provider models,
capability requirements and the configured gates. Failure can cause escalation or a terminal
refusal. Do not infer that a tier named `cheap_frontier` is always free, that a local server
has no operating cost, or that every default backend will run on a fresh installation.
Read the receipt for the actual route and model, and the provider's terms for charges.

## Output-token budget

The public [backend resolver](https://github.com/OmniNode-ai/omnimarket/blob/v0.4.317/src/omnimarket/routing/delegation_backend_resolution.py)
requires each backend to declare a positive integer `max_tokens`:

1. An omitted request budget uses the backend's ceiling.
2. An explicit request is capped at that ceiling with `min(requested, backend_max_tokens)`.

The [entry contract](https://github.com/OmniNode-ai/omnimarket/blob/v0.4.317/src/omnimarket/nodes/node_delegate_skill_orchestrator/contract.yaml)
has an absolute schema maximum of `200000`. That is not a guarantee that any selected model
can emit that many tokens. Per-backend values are versioned configuration; consult the
linked declaration instead of copying model-specific limits into a second table here.

## Endpoint rule

The resolved endpoint is the complete URL, including the provider's chat-completions path.
It is posted verbatim, without appending a path. A local override must supply the complete
`endpoint_url`, not just a host. See [dispatch](delegation-dispatch.md) for the effect boundary.

## When extending routing

Read budgets and task types from the contracts at runtime. Declare every new backend's
capabilities and token ceiling, retain complete endpoints in overlays, and test refusal as
well as successful routing. A gate pass means the configured criteria passed; it does not
guarantee that generated code is correct or that the chosen model is globally optimal.
Historical design decisions remain in the ADRs; the [public proof index](../reference/public-proof-index.md)
separates those designs from releases, test sources and reported outcomes.
