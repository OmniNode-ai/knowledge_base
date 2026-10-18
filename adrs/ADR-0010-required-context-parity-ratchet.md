---
type: adr
status: deprecated
date: '2026-07-10'
title: 'ADR-0010: Historical required-check parity proposal'
adr_id: ADR-0010
topics: [governance, configuration, testing]
refs:
- reference/ci-validation-setup.md
supersedes: []
superseded_by: []
---

# ADR-0010: Historical required-check parity proposal

This unaccepted proposal tried to keep required-check declarations aligned with the checks CI actually produces. Its operational inventory and merge-policy assumptions are withdrawn rather than presented as current platform policy.

The durable principle is that a required check must have a defined producer and a terminal result for the revision being reviewed. Each product repository owns its current CI contract. See [CI validation setup](../reference/ci-validation-setup.md) for the reusable documentation-validation interface.
