---
type: adr
status: accepted
date: "2026-10-17"
title: "ADR-0053: Beta Scope — Local Install, Your Own Model Keys, No Hosted Service"
adr_id: ADR-0053
topics: [cloud-api, delegation, overview]
refs: [guides/onex-plugin-quickstart.md, guides/connecting-to-the-cloud.md]
supersedes: [ADR-0021]
superseded_by: []
summary: "The beta is the local install: users delegate from their own computer to a model they run or a provider on their own key, and OmniNode does not sell inference. The hosted service is not part of the beta. Supersedes ADR-0021."
---

# ADR-0053: Beta Scope — Local Install, Your Own Model Keys, No Hosted Service

## Context

[ADR-0021](ADR-0021-beta-ships-first-priority-lock.md) recorded a July 2026 internal
priority call for a beta that was then expected within days. That beta did not ship in that
form, and the record was never moved past `proposed`. Since then the public guides have
disagreed about what a beta user can reach: the quickstart said the hosted service had no
public address, while the cloud guide described a live production API. A reader, or an AI
agent reading on someone's behalf, could not tell from this knowledge base what the beta is.

This record states the beta's scope as of its date. It does not rewrite ADR-0021, which
stays as the historical record of the July plan.

## Decision

The beta is the **local install**, run on the user's own machine:

1. **Install and run locally.** The user installs the `onex` tool and delegates from their
   own computer, following the [quickstart](../guides/onex-plugin-quickstart.md). No
   OmniNode account, sign-up or OmniNode service is needed.
2. **Bring your own key.** Every model call goes to a model the user runs themselves, or to
   a provider on the user's own API key. The call goes from the user's machine to that model
   directly. The user pays the provider, not OmniNode.
3. **OmniNode does not sell inference.** OmniNode does not resell model access and does not
   put a model key of its own behind a user's work. That rule covers the hosted service as
   well.
4. **Every run is visible.** Each delegation writes the answer and a receipt naming the model
   that answered, and the user can read back the runs, the tokens sent and received, and the
   cost. A savings figure always names the baseline model and prices it was worked out from,
   and a run whose tokens were not measured counts as unknown, never as zero.
5. **The hosted service is not part of the beta.** Its sign-up is a waitlist, and accounts
   are granted by the OmniNode team. Nothing in the beta depends on it.
   [Connecting to the OmniNode Cloud](../guides/connecting-to-the-cloud.md) says which of its
   steps work today.

## Alternatives Considered

1. Keep ADR-0021 as the beta record. Rejected: its deadline passed in July, it names
   internal workstreams a reader cannot look up, and it describes a hosted-platform beta that
   is not the one shipping.
2. Rewrite ADR-0021 in place. Rejected: the decision ledger keeps what was decided when it
   was decided. A newer record supersedes an older one; it does not edit it.
3. Include the hosted service in the beta. Rejected for now: a beta user should not depend on
   a service whose account path is waitlist-gated.

## Consequences

Positive: one answer to "what is the beta", which the quickstart and the cloud guide now both
repeat. A beta user needs only their own computer and a model they choose.

Negative: users who want their work run on OmniNode's machines wait for the hosted service to
open. The cloud guide stays published, so the hosted service has to stay clearly labelled as
outside the beta until it opens.

## Related Pivots

## Related Doctrine

## Derived From

The public [quickstart](../guides/onex-plugin-quickstart.md) and
[cloud guide](../guides/connecting-to-the-cloud.md) as revised on the same date.

## Evidence

The beta's local path is the quickstart's steps 1 to 7. Each step says what the user should
see when it worked.

## Supersedes

[ADR-0021](ADR-0021-beta-ships-first-priority-lock.md) — the July 2026 beta priority lock.
