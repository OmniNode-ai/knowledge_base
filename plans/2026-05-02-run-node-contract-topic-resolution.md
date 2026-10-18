---
type: plan
status: superseded
date: '2026-05-02'
title: Contract-declared topic resolution
topics: [contracts, bus, runtime]
refs:
- architecture/onex-contract-system.md
---

# Contract-declared topic resolution

This is a historical design record, not an execution plan or a product roadmap.

## Proposal at the time

The design derived command and terminal topics from the target node's contract instead of publishing to generic topics without a matching consumer. Unresolvable contract topics were to be explicit errors.

## Design reasoning

A successful publish alone does not establish that any node consumes the message. The command route and correlated terminal route must agree with the node's contract.

## Outcome of this record

The implementation checklist has been withdrawn. The current documentation is [the living reference](../architecture/onex-contract-system.md); this summary does not assert that every proposed change shipped.
