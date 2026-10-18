---
type: pivot
status: accepted
date: '2026-10-18'
title: Evidence lives with the code it proves
observed_date: "2026-10-18"
confidence: high
topics: [evidence, testing]
refs: []
---

# Evidence lives with the code it proves

## Context

A separate central evidence service separates a code change from the checks that establish its behavior. An architecture page should cite evidence a reader can follow to the repository responsible for the implementation.

## Decision

Acceptance evidence belongs in the product repository that owns the code. Documentation cites a PR, a CI run or a receipt in that repository. A regression test must fail without the change and pass with it; a passing test that never exercises the changed behavior is insufficient.

## Consequences

Historical plans that require a central change-control companion are superseded. Documentation remains reference material rather than a receipt store. This decision describes the evidence boundary; it does not assert that every repository has completed its migration.
