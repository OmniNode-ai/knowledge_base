---
type: guide
status: draft
date: "2026-10-30"
title: "Validate the OmniMarket RightModeler integration"
topics: [omnimarket, onex-runtime, rightmodeler, testing]
refs:
  - runbooks/omnimarket-rightmodeler-model-swap-validation.md
summary: "Validate the client, durable state and runtime terminal wiring without treating synthetic responses as model-quality evidence."
---

# Validate the service integration

This contribution implements an HTTP client boundary, durable local command
state and runtime terminal wiring. It does not implement or deploy the remote
RightModeler service. No container runner, native-output capture or workflow
change is included.

## Reproducible local checks

Use Python 3.12 and the repository's `uv` environment. Shared Core models and the
SPI protocol must be available; before their releases, isolated source-built
sibling wheels can validate this dependent change without committing dependency
overrides or changing the lockfile. This guide covers a proposed contribution;
it does not establish that those APIs are present in the current upstream
development branch or installable from its dependency pins.

The commands below assume compatible shared-package releases are declared and
resolved by the repository. When validating with isolated source-built sibling
wheels, invoke that environment's Python directly, or select it explicitly
with `UV_PROJECT_ENVIRONMENT` before using `uv run --no-sync`: an automatic sync
can replace the proposed wheels with the locked baseline. Record any dependency
incompatibility rather than changing metadata or versions to conceal it. Source-built wheels establish local compatibility
only; they do not replace maintainer releases.

The contribution targets `dev`. Verify the actual PR base and fetch it before
deriving the changed-state comparison; use that branch in both commands if
the PR targets a different base.

```bash
git fetch origin dev
BASE_SHA="$(git merge-base HEAD origin/dev)"
uv run pytest tests/unit/nodes/node_model_swap_validation_effect -q --no-cov
uv run pytest tests/unit/contracts -k every_node_auto_wires_in_process -q --no-cov
uv run ruff check src/omnimarket/nodes/node_model_swap_validation_effect tests/unit/nodes/node_model_swap_validation_effect
uv run ruff format --check src/omnimarket/nodes/node_model_swap_validation_effect tests/unit/nodes/node_model_swap_validation_effect
uv run mypy src/omnimarket/nodes/node_model_swap_validation_effect --strict
uv run python scripts/ci/check_node_metadata_dependencies.py
uv run python src/omnimarket/nodes/node_runtime_sweep/__main__.py --import-check
uv run python scripts/validate_node_drift.py --check-all --check-orphan-nodes --strict
uv run python scripts/validate_state_coverage.py --check-changed "$BASE_SHA" --head-ref HEAD --strict --check-stale
uv build
```

The canonical file-shape and lifecycle gates use their own exact source pins.
Follow the repository's checked-in CI and pre-commit configuration for those
gates. An installed dependency version does not establish that the pinned
validators passed.

The node's focused suite covers all twelve synthetic terminal chains, configured
byte/deadline limits, explicit secret-store authentication, malformed and
contradictory evidence, identity encoding, secret-echo containment, cancellation,
concurrent delivery, corrupt state and immutable recovery. The finite ownership
model covers crash/duplicate interleavings. Actual bus tests verify correlated
completed and failed publication through the platform result applier.

For independent validation, additionally exercise real local HTTP sockets,
cross-process overlap, killed workers, file-backed secret configuration and
the public runtime wiring APIs described in
[the runbook](../runbooks/omnimarket-rightmodeler-model-swap-validation.md).
These are acceptance checks to perform, not a separate committed QA suite.
Fixture responses are deterministic protocol examples; they are not model
judgments.

## Deployment prerequisites

Maintainers own the shared package releases and dependency floors, governed
upstream re-landing and hosted workflow approval. Fork-policy refusal or an
approval timeout does not establish a test result.

The operator must supply a compatible complete service endpoint and credential,
approved replay bundles resolvable by digest, actual provenance and backend
configuration, plus the labelled public-data pilot inputs. The current public
CLI does not expose this HTTP protocol. Until those prerequisites exist, live
service compatibility, agreement with human labels and routing benefit remain
unverified. Every returned result remains evidence-only.
