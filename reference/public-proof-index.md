---
type: reference
status: current
date: "2026-10-20"
title: "Public proof index: delegation and the ONEX platform"
topics: [overview, delegation, evidence, getting-started]
refs:
  - guides/what-is-omninode.md
  - guides/onex-plugin-quickstart.md
  - guides/connecting-to-the-cloud.md
  - architecture/omniclaude-repo-charter.md
summary: "Public releases, reproducible entry points and test sources for delegation, with explicit limits on what publication, author reports and receipt hashes establish."
---

# Public proof index: delegation and the ONEX platform

Delegation is the first shipped product path: hand coding-agent work to your own model or
provider, keep a receipt, and compare recorded spend with a baseline. **ONEX is the broader
platform** of shared nodes, contracts, events and projections. Begin with the
[one-page overview](../guides/what-is-omninode.md), then the
[quickstart](../guides/onex-plugin-quickstart.md). This index helps a newcomer or evaluator
inspect public evidence without treating architecture as a shipping promise.

## How to read the evidence

- **Published artifact:** a release, package, source file, test or example is publicly
  inspectable. Publication establishes availability of that artifact, not that its claims
  hold on your machine or in a hosted deployment.
- **Author report:** maintainers describe a run or outcome. It is attributed evidence,
  with the scope and date they report; it is not independent replication.
- **Independent validation:** a separate party reproduces a specified version and method
  and publishes the result. The sources indexed here do not establish that level of
  validation for product outcomes. This documentation check inspected source and package
  metadata; it did not execute paid inference or an authenticated hosted workflow.

## Published install and plugin

Checked against public GitHub releases and PyPI metadata on 2026-10-20:

| Artifact | Public version / inspection entry point | What it establishes |
| --- | --- | --- |
| CLI | [omnibase-core 0.47.49](https://pypi.org/project/omnibase-core/0.47.49/), [release](https://github.com/OmniNode-ai/omnibase_core/releases/tag/v0.47.49) | Published CLI package; metadata requires Python `>=3.12` |
| Delegation CLI integration | [omnibase-infra 0.38.75](https://pypi.org/project/omnibase-infra/0.38.75/), [entry points](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/pyproject.toml) | Registers the `delegate` subcommand |
| Delegation implementation and cloud client | [omnimarket 0.4.317](https://pypi.org/project/omnimarket/0.4.317/), [package declaration](https://github.com/OmniNode-ai/omnimarket/blob/v0.4.317/pyproject.toml) | Published nodes and CLI extensions, including `cloud`, `local` and `secret`; declares compatible core/infra dependency ranges |
| Customer Claude Code plugin | [marketplace manifest](https://github.com/OmniNode-ai/omniclaude/blob/be0561f096be14c5584c5a43cadf5401c450a7a9/.claude-plugin/marketplace.json), [selected plugin](https://github.com/OmniNode-ai/omniclaude/blob/be0561f096be14c5584c5a43cadf5401c450a7a9/plugins/onex-delegate/.claude-plugin/plugin.json) | Marketplace selects `plugins/onex-delegate`, version `0.3.2`, one skill and no hooks or agents |

The quickstart's three-package install specifies supported minimum versions, not exact
pins. The resolver chooses a compatible combination; the checked releases above are a
snapshot, not a guarantee that a later floating install is identical. Keep `--python 3.12`
and consult [supported platforms](../guides/supported-platforms.md) for wheel/build limits.

The broader omniclaude repository contains hooks, agent routing and other workflows.
Its [repository charter](../architecture/omniclaude-repo-charter.md#installed-plugin-versus-repository-scope)
explains ownership; those files are not installed by the customer marketplace entry.

## Reproducible entry points

| Check | Public method / source | Limit |
| --- | --- | --- |
| Local user path | [Quickstart steps 1–7](../guides/onex-plugin-quickstart.md): install, initialize identity, declare model or register key, delegate, inspect receipt, meter, open dashboard, optionally install plugin | Requires your own model endpoint or provider account; record resolved versions and your own outcome |
| Provider registration and refusal | [Local-store credential tests](https://github.com/OmniNode-ai/omnimarket/blob/v0.4.317/tests/unit/inference/test_omn18695_customer_key_from_local_store.py) and [local OpenRouter route tests](https://github.com/OmniNode-ai/omnimarket/blob/v0.4.317/tests/unit/delegation/test_omn18694_local_byok_openrouter.py) | Published tests include environment-present refusal cases and use fixtures; they do not establish a live provider's availability |
| Metering calculation | [CLI metering tests](https://github.com/OmniNode-ai/omnimarket/blob/v0.4.317/tests/test_cli_metering_omn18697.py) | Tests of calculations and rendering, not measured quality-adjusted savings |
| Reducer replay | [Replay test guide](../guides/omnibase-infra-replay-tests.md), [test source](https://github.com/OmniNode-ai/omnibase_infra/tree/v0.38.75/tests/replay) | Determinism and idempotency under test inputs; not full hosted workflow or fresh model-answer replay |
| Receipt hash comparison | [Replay-and-diff tests](https://github.com/OmniNode-ai/omnibase_infra/blob/v0.38.75/tests/unit/verification/workflow_receipt/test_verifier_replay_and_diff.py) | Terminal-event hash scope only; not independent model/provider attestation |

For source tests, use the linked release's contribution instructions and dependencies and
run the linked test path with pytest. A test's existence is not a passing result; inspect
the matching revision's CI result or reproduce it and report fixtures, skips and failures.

The cloud guide's [availability table](../guides/connecting-to-the-cloud.md#availability-of-each-step-stated-honestly)
preserves author reports of hosted checks. It also records missing browser click-through
and production route evidence. Those reports do not independently validate the hosted
service today. The shipped local path needs no hosted account.

## Credentials and receipt limits

Local provider keys are registered with `onex secret set`. The
[resolver](https://github.com/OmniNode-ai/omnimarket/blob/v0.4.317/src/omnimarket/inference/secret_store_resolver.py)
and refusal tests above support the quickstart's statement that exporting a provider key
does not register a local route. An endpoint environment variable configures an address,
not a provider credential.

A provider credential authenticates access to inference. An OmniNode API credential
authenticates access to the hosted API. A receipt's unkeyed hashes can check consistency
with the covered data; they are not digital signatures and can be recomputed by someone
who replaces the data. The [hosted receipt format and replay limits](../guides/connecting-to-the-cloud.md#what-a-receipt-says)
specify no signing key or signature-verification procedure. Neither hashes, authentication,
backend attribution nor a quality-gate pass guarantees that an answer is correct.

## Broader platform and missing evidence

The public [local runtime guide](../guides/getting-started-local.md) and
[self-hosting guide](../guides/getting-started-self-hosted.md) describe swapping bus and
store adapters while preserving the node contract. That is the design intent; full parity
across every local and Dockerized workflow needs versioned comparative evidence.
The MIT license makes the software free to use, not model calls, hardware or operations.
Inference remains entirely on your provider key or your own model; OmniNode does not
offer or resell inference.

Public [memory architecture](../architecture/omnimemory-four-node-architecture.md) describes
storage, querying and coordination nodes; [context enrichment](../architecture/context-enrichment-pipeline.md)
describes a hook workflow. These show how workflows can share platform components. Their
presence does not establish that ledger-backed memory, context packs, agent communication,
ingestion, automatic routing or ledger-backed compaction ship in the customer plugin.
This index does not establish a release/adoption path for those broader workflows or resolve
integration/mod naming. A roadmap statement needs its own public source and status.

Evidence still needed before stronger product or business claims:

- **Quality-adjusted net savings:** matched tasks, accepted-output criteria, baseline,
  retries/escalations, human review and operating costs. A token-price counterfactual alone
  cannot establish equal-quality output or net economic benefit.
- **Outside-user outcomes:** attributable, consented public results from users beyond the
  authors, with versions, methods and unsuccessful cases. An invitation to beta is not
  evidence of adoption, retention or successful outcomes.
- **Commercial model:** the public overview says OmniNode does not sell inference; the
  sources here do not establish a decided paid offer, pricing, demand or revenue. Those
  remain unestablished in this evidence set.
- **Hosted guarantees:** current authenticated end-to-end results, a verifiable signature
  contract if one is promised, and journal access before claiming full hosted replay.

Historical ADRs preserve decisions and proposals. Their current-navigation annotations
point to living docs; they do not retroactively turn a design into implementation evidence.
