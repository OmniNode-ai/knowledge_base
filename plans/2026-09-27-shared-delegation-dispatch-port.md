---
type: plan
status: superseded
date: '2026-09-27'
title: Shared delegation dispatch protocol
topics: [delegation, handlers, agent-integrations]
refs:
- architecture/delegation-dispatch.md
---

# Shared delegation dispatch protocol

This is a historical design record, not an execution plan or a product roadmap.

## Proposal at the time

The proposal used one generic request/result protocol with static conformance checks in each owning repository. It rejected runtime protocol attribute presence as proof of a compatible parameter signature and avoided checks that depended on a sibling checkout.

## Design reasoning

An interface contract needs to cover the callable signature, not just the existence of a method. Repository-local checks remain usable in isolated CI environments.

## Outcome of this record

The implementation checklist has been withdrawn. The current documentation is [the living reference](../architecture/delegation-dispatch.md); this summary does not assert that every proposed change shipped.
