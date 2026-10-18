---
type: plan
status: superseded
date: '2026-03-18'
title: Required environment coverage
topics: [configuration, testing]
refs:
- guides/getting-started-self-hosted.md
---

# Required environment coverage

This is a historical design record, not an execution plan or a product roadmap.

## Proposal at the time

The design compared required deployment variables with the variables supplied by an integration-test fixture. A missing required value was intended to be rejected by the coverage check before an unrelated downstream integration test encountered it.

## Design reasoning

A declaration and the fixture used to validate it can drift independently. Checking their coverage together localizes that mismatch.

## Outcome of this record

The implementation checklist has been withdrawn. The current documentation is [the living reference](../guides/getting-started-self-hosted.md); this summary does not assert that every proposed change shipped.
