---
type: reference
status: current
date: '2026-10-18'
title: Repository Registry
topics: [overview]
refs: []
---

# Repository Registry

*Public documentation reviewed as of 2026-10-18. Source links use the public platform registry and its current visibility vocabulary; hosted deployment repositories are excluded.*

| Repository | Responsibility |
|---|---|
| [`omnibase_core`](https://github.com/OmniNode-ai/omnibase_core) | Core models, contracts, validators and CLI. |
| [`omnibase_spi`](https://github.com/OmniNode-ai/omnibase_spi) | Protocol interfaces. |
| [`omnibase_infra`](https://github.com/OmniNode-ai/omnibase_infra) | Runtime, event bus and persistence. |
| [`omnibase_compat`](https://github.com/OmniNode-ai/omnibase_compat) | Shared wire types. |
| [`omnimarket`](https://github.com/OmniNode-ai/omnimarket) | Delegation, routing and product nodes. |
| [`omniclaude`](https://github.com/OmniNode-ai/omniclaude) | Coding-agent integration contracts and plugin surfaces. |
| [`omnidash`](https://github.com/OmniNode-ai/omnidash) | Dashboard widgets and projections. |
| [`omniintelligence`](https://github.com/OmniNode-ai/omniintelligence) | Intelligence nodes. |
| [`omnimemory`](https://github.com/OmniNode-ai/omnimemory) | Ingestion and semantic retrieval. |
| [`omnibase`](https://github.com/OmniNode-ai/omnibase) | Platform installer. |
| `knowledge_base` | Canonical public documentation. |

The hosted service's deployment infrastructure is private; the platform is open source. This table describes package responsibilities, not an installer clone list or a promise that every package is needed for the beta. Start with [the quickstart](../guides/delegation-quickstart.md) for the supported install, and [the repository map](../architecture/repository-map-and-runtime-concepts.md) for dependency boundaries.
