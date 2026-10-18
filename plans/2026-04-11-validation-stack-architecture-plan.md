---
type: plan
status: superseded
date: '2026-04-11'
title: Validation stack design
topics: [testing, architecture]
refs:
- architecture/onex-contract-system.md
---

# Validation stack design

This is a historical design record, not an execution plan or a product roadmap.

## Proposal at the time

The proposal combined architectural checks with end-to-end workflow evidence. In particular, a dispatch phase with no actual outcome was to be reported as missing or explicitly unevaluated rather than an unconditional success.

## Design reasoning

A green result is meaningful only when the check exercised the claimed behavior. Static conformance and a runtime terminal outcome answer different questions.

## Outcome of this record

The implementation checklist has been withdrawn. The current documentation is [the living reference](../architecture/onex-contract-system.md); this summary does not assert that every proposed change shipped.
