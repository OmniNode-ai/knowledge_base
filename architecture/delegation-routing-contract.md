---
type: architecture
status: accepted
date: "2026-08-25"
title: "Delegation Routing Contract"
topics: [delegation, contracts]
refs:
  - architecture/delegation-dispatch.md
---

# Delegation Routing Contract

> **Public interface review: 2026-10-18.** Customers supply their own model endpoints and provider keys (BYOK). Backend identities, credentials and availability are deployment configuration, not platform-wide facts.

The delegation routing contract is declared in two files under
`src/omnimarket/configs/`:

| File | Role |
| --- | --- |
| `bifrost_delegation.yaml` | Backend definitions: endpoint URLs, model names, tier, timeout, per-backend max_tokens, capabilities |
| `routing_tiers.yaml` | Tier escalation ladder: `local` → `cheap_cloud` → `cheap_frontier` → `claude` (ceiling) |

Site-local overrides are applied from `~/.omninode/delegation/bifrost_overrides.yaml`
at load time and are never committed to the repo.

## per-backend max_tokens

Every backend entry in `bifrost_delegation.yaml` carries a `max_tokens` field.
This is the per-backend output-token ceiling. The contract resolves the
effective output-token budget as follows:

1. If the caller supplies `max_tokens` in the delegation request, that value is
   used, capped at the selected backend's `max_tokens` ceiling.
2. If the caller omits `max_tokens`, the backend's ceiling is used as the
   effective value.

There is no contract-level default and no hardcoded 8192 cap system-wide —
that figure is the real output limit of one specific backend family (Gemini
Flash), not a universal default. The absolute schema bound in
`node_delegate_skill_orchestrator/contract.yaml` is `maximum: 200000`;
per-backend ceilings are lower and are the operative limit.

Example backend entries (see `bifrost_delegation.yaml` for the live values):

```yaml
- backend_id: local-coder
  tier: local
  max_tokens: 65536   # local Qwen code model, <onex-host> SGLang endpoint

- backend_id: cloud-gemini-pro
  tier: frontier_api   # serves as the routing_tiers.yaml `claude` ceiling slot
  max_tokens: 65536    # Gemini 2.5 Flash, 1M context window

- backend_id: cloud-gemini-flash
  tier: cheap_cloud
  max_tokens: 8192     # Gemini Flash family's real provider output limit
```

## Task-class tier escalation order

`routing_tiers.yaml` defines the escalation ladder. Tiers are tried in order,
cheapest first. When a quality gate fails or a backend is unavailable, the
next tier is selected:

1. `local` — on-premises vLLM/SGLang models (lowest cost, highest throughput)
2. `cheap_cloud` — metered Gemini backends via Google AI Studio and Vertex (moderate cost)
3. `cheap_frontier` — a configured frontier backend via OpenRouter, available when `OPENROUTER_API_KEY` is configured
4. `claude` — a historical ceiling-slot identifier, not a fixed provider. The configured backend determines the provider and uses the customer's credential. Read the routing contract for the selected backend, not deployment-specific account history.

Task classes that require capabilities only available on higher tiers skip
lower tiers that lack those capabilities. For example, a `code_generation`
task may match `local-coder` (tier: local) first; if that fails quality
gates it escalates through `cheap_cloud` and, if still failing, on to the
ceiling tier.

The escalation gate ordering was hardened so tiers are always evaluated in
the declared order, not insertion order. Contributors adding task-class routing
rules must declare them in the tier order they want the escalation to follow.

## Codegen fallback to headless Codex

When all LLM backends fail quality gates for a `code_generation` task, the
orchestrator can fall back to headless Codex execution. This path is opt-in;
it is activated by the `codex_sandbox_mode` field in the delegation request.
The fallback is not a backend tier — it is a separate dispatch path that
bypasses the LLM inference call and routes directly to a Codex subprocess.

## endpoint_url verbatim rule

See [Delegation Dispatch](delegation-dispatch.md) for the full endpoint_url
verbatim rule. In summary: every `endpoint_url` in `bifrost_delegation.yaml`
must be the complete, final URL including the chat path. Local backends use
`endpoint_url: null` and resolve the URL from the env var named by
`endpoint_url_env`. A bare base URL without a chat path is a misconfiguration.

## Writing a delegation node or overlay

When writing a node that participates in delegation dispatch:

1. Read the backend's `max_tokens` from the routing contract at runtime — never
   hardcode a token limit.
2. Use `task_type` from the allowed list in
   `node_delegate_skill_orchestrator/contract.yaml` (`allowed_task_types`).
3. Do not add a new backend without adding the corresponding `max_tokens` field.
4. For local overlay files, always provide the complete `endpoint_url`
   (including the chat path); do not use the bare base form.
