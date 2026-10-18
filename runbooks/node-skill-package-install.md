---
type: runbook
status: current
date: '2026-10-18'
title: Install a node package
topics: [nodes, packaging, runtime]
refs: []
---

# Install a node package

Install the package into the same Python environment as the runtime that discovers its node entry points. A package installed into a different environment is not visible to that runtime.

For the local delegation beta, follow the [Delegation quickstart](../guides/delegation-quickstart.md). It installs published packages and needs no source checkout or hosted account.

## Self-hosted runtime

1. Identify the runtime environment and the package versions compatible with it.
2. Stop new work before changing the environment, following your deployment procedure.
3. Install the released node package into that environment with its package manager and retain the resolved dependency versions.
4. Run the package's contract and entry-point discovery checks with the same interpreter the runtime uses.
5. Submit one representative request through the configured runtime and inspect its terminal outcome and receipt.

If discovery fails, check the active interpreter and installed distributions before changing routing. An installation completing is not evidence that a node can be invoked. Do not bypass a dependency or contract check to make a mismatched environment appear healthy.

For database schema changes supplied by a node package, read [Vendored node migrations](vendored-node-migrations.md).
