<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/brand/omninode-inline-white.png">
    <source media="(prefers-color-scheme: light)" srcset="docs/assets/brand/omninode-inline-full-color.svg">
    <img alt="omninode" src="docs/assets/brand/omninode-inline-full-color.svg" width="420">
  </picture>
</p>

# OmniNode Knowledge Base

OmniNode's public documentation: what the platform is, how to use it, and why it is shaped the way it is.

[![CI](https://github.com/OmniNode-ai/knowledge_base/actions/workflows/ci.yml/badge.svg)](https://github.com/OmniNode-ai/knowledge_base/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What OmniNode is, and where it stands (as of 2026-10-17)

OmniNode lets you hand coding-agent work to a model you choose: a model you run on your own machine or network, or a provider you pay for on your own API key. The model call goes from your machine to that model directly and never passes through OmniNode. Every run leaves a receipt naming the model that answered, and `onex metering` prices each run against a baseline model so you can see what the work cost and what it would have cost on the baseline. **OmniNode does not sell inference.** You pay your provider, or nobody if you run the model yourself.

It is for developers and teams who use coding agents such as Claude Code and want to move work onto cheaper or self-hosted models without losing track of which model did what, and for developers building on the ONEX runtime the delegation path is built on.

**Shipped today**, from public MIT-licensed packages on PyPI, on your own machine, with no OmniNode account:

- a one-line local install of the `onex` command (Apple Silicon Mac and Linux from wheels, Intel Mac from source);
- `onex delegate`, to your own model server or your own OpenRouter or GLM key;
- a receipt for every run, naming the provider or server and the model;
- `onex metering`, with spend measured against a baseline model;
- `onex dashboard`, a local page showing each run and its receipt;
- the Claude Code plugin `onex@omninode-tools`, which adds `/onex:delegate`.

**In beta:** the beta for invited outside users exercises that same delegation path, from the same public quickstart.

**Not yet open:** the hosted service. It is not open to outside users: accounts are granted from a waitlist rather than self-served, and nothing on the shipped path needs it.

**Start with the [Delegation quickstart](guides/onex-plugin-quickstart.md)** (about 15 minutes). The one-page version of this section, with links for each part, is [What OmniNode is, and where it stands](guides/what-is-omninode.md). An AI agent reading this repository can start from [`llms.txt`](llms.txt).

## What this repository is

This repository is the canonical home for OmniNode's external documentation. Product repositories keep only what must physically ship beside their code, and point here for everything else; [the charter](#the-charter) below says exactly what that scope includes and excludes.

Two kinds of documentation live here, and telling them apart is what makes the collection navigable.

**Consumer documentation** answers *how do I use this*: guides, cross-repository reference, and operational runbooks. It is written for someone building against OmniNode, and it is deliberately independent of any single repository's release tag — so that finding out how something works never requires first knowing which repository implements it.

**Architectural provenance** answers *why is it like this*: plans, technical designs, decision records, pivots, doctrine, and experiments. Rather than architecture existing only in the heads of contributors or scattered across pull request descriptions, this repository makes the full evolutionary arc visible — what was decided, what changed, and what the evidence was.

## The charter

This is the **self-hoster's book**: everything needed to run the ONEX platform independently — its principles, its decisions, its architecture, and how to operate it — is documented here, generically and reproducibly. Two things are deliberately excluded: **OmniNode's own cloud deployment topology** (AWS account/cluster internals, deploy pipelines for our specific hybrid infrastructure) and **the public web properties**. Neither is platform architecture; both are our own product operations. Operational journals (narrative work logs) and evidence/receipt artifacts also stay out — a journal's durable insight is promoted into a doctrine or ADR page instead of the journal migrating, and OCC (`onex_change_control`) is the sole evidence authority, so this repository cites outcomes rather than hosting receipts. See [docs-taxonomy.md](docs-taxonomy.md) for the full decision rule.

The knowledge base is canonical for all external product, platform, architecture, and how-to documentation within that scope.

A product repository keeps a closed set of documents that cannot meaningfully live anywhere else: its landing README, its contribution guide, its executable installers, its versioned API reference tied to a release tag, its agent operating context, and the platform-convention files expected at fixed paths. Each of those is trimmed to the minimum that serves its purpose and carries a pointer here. Everything else is canonical, lives here, and exists in exactly one place.

That last clause is the whole point. The same claim — a node count, a version badge, a workflow name, a base-branch instruction — was previously copy-pasted into many repositories, where each copy then drifted independently. Fixing each copy in place guarantees they re-drift. One canonical copy is the only arrangement where a correction stays correct.

The rule for deciding where any individual document belongs is written down, not left to judgment: see **[docs-taxonomy.md](docs-taxonomy.md)**.

## Sections

| Directory | What it contains |
|-----------|-----------------|
| [`doctrine/`](doctrine/README.md) | Stable platform principles that govern OmniNode's architecture |
| [`adrs/`](adrs/README.md) | Architecture Decision Records — the formal decision ledger |
| [`architecture/`](architecture/README.md) | Technical Design Documents describing platform architecture — primitives, boundaries, runtime flow, and proof requirements |
| [`pivots/`](pivots/README.md) | Architectural pivots capturing fundamental changes in understanding |
| [`plans/`](plans/README.md) | Selected implementation plans showing intended work and proposed paths |
| [`experiments/`](experiments/README.md) | Hypothesis-driven experiments with structured outcomes |
| [`indexes/`](indexes/README.md) | Auto-generated indexes for browsing artifacts by date, topic, or type |
| [`guides/`](guides/README.md) | Task-oriented how-to documentation |
| [`reference/`](reference/README.md) | Cross-repository factual reference |
| [`runbooks/`](runbooks/README.md) | Parameterized operational procedures |

Migration status (2026-10-17): platform documentation from `omnibase_core`, `omnibase_infra`, `omniclaude`, `omnimarket`, `omnimemory`, `omniintelligence`, `omnidash`, `omnibase_compat` and `onex_change_control` has migrated here, and more than 400 documents are published across the sections above. Per-document state is in [`migration-manifest.yaml`](migration-manifest.yaml).

## Core Philosophy

**Truth must be proven.** Architectural claims require durable evidence — pull requests, CI runs, replay validation, or benchmarks. Assertions without proof are hypotheses.

**Completion requires durable evidence.** A decision is not accepted, a pivot is not confirmed, and an experiment is not concluded until the evidence artifact exists and is referenced.

**Decisions must be inspectable.** Every decision record captures not just what was decided but what was considered and rejected, and why. The reasoning is part of the record.

**Evolution must be replayable.** Pivots capture the before and after state, including which assumptions were wrong and what operational pressure forced the change. Future contributors should be able to reconstruct the reasoning arc from first principles.

## Getting Started

**To try OmniNode, start with the [Delegation quickstart](guides/onex-plugin-quickstart.md).** It installs the `onex` tool, runs a first delegation to a model you choose, and shows the receipt, `onex metering`, the local dashboard and the Claude Code plugin, with what you should see at each step.

**To build your own nodes on the ONEX runtime,** read [Building on the ONEX runtime](guides/getting-started-local.md). It is the shortest complete path to a working ONEX system: one package, one command, and a real event chain you can read back out of a local database file, with no broker, no database server, no container runtime and no account. It needs no model and does not delegate. From there:

- [Self-hosting the full stack](guides/getting-started-self-hosted.md) is the scale-up chapter: a real broker, PostgreSQL, a cache, an identity provider, and the runtime services on top, on your own infrastructure.
- [Combining deployment tiers](guides/combining-deployment-tiers.md) covers the seams between running locally, self-hosting, and talking to a hosted deployment.
- [Connecting to the cloud](guides/connecting-to-the-cloud.md) describes the hosted service, which is not yet open to outside users.

All of these, plus the rest of the task-oriented documentation, are indexed in [`guides/`](guides/README.md).

**To understand how the repositories fit together,** read [Repository map and runtime concepts](architecture/repository-map-and-runtime-concepts.md). It is the orientation layer above the per-repository designs: what each repository owns, why the build-time import staircase and the runtime message graph look nothing alike, and the five runtime concepts (the three primitives, the four node archetypes, the canonical handler shape, the bus as transport, and projected truth) that explain how code in separate repositories becomes one running system.

**To understand why the platform is shaped the way it is,** start with [`doctrine/`](doctrine/README.md), the stable principles that govern it. From there, decision records show specific choices that instantiate those principles, and pivots show where the principles themselves evolved.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to propose new artifacts, the PR process, and sanitization requirements. See [docs-taxonomy.md](docs-taxonomy.md) for deciding whether a document belongs here at all.

## Validation

```bash
uv run python scripts/validate.py
```

`scripts/validate.py` runs eight checks: a registered-location sweep (every `.md`/`.yaml`/`.yml` file must live in a declared section, a generated-content directory, or the root-file allowlist, or the build fails closed), frontmatter schema, the filename naming convention, ADR `adr_id` uniqueness (any two ADRs sharing an id fail the build, with no exemption), `refs:` cross-reference integrity, sanitization, index freshness, and broken relative links (across every artifact, the generated `indexes/`, the repository-root documents and the repository links in `llms.txt`). [CONTRIBUTING.md](CONTRIBUTING.md) covers the pull request process and the separate gate over commit messages and PR text, `scripts/check_text_sanitization.py`.

<!-- verified against scripts/validate.py and scripts/generate_indexes.py on 2026-10-17 -->
