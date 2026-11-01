---
type: reference
status: current
date: "2026-11-01"
title: "OmniUI ONEX models schema mirror and its provenance record"
topics:
  - omniui
  - schema
  - generated-artifacts
refs: []
---

# OmniUI ONEX models schema mirror and its provenance record

OmniUI renders against the ONEX contract models. It does not define them. The models are defined in `omnibase_core`, and OmniUI keeps a checked-in mirror of their combined JSON Schema so that its TypeScript types can be generated without a Python toolchain.

## The files

| File in the OmniUI repository | What it is | Written by |
|---|---|---|
| `schema/onex-models.json` | Combined JSON Schema of the contract models OmniUI renders against | `scripts/emit_ts_types.py` in `omnibase_core`, copied in at refresh time |
| `schema/onex-models.provenance.json` | Where the schema came from and what it contained when it was mirrored | `npm run generate:onex-models` |
| `src/generated/onex-models.ts` | TypeScript types compiled from the schema | `npm run generate:onex-models` |

The schema is generated and is never hand-edited. The provenance record is generated too and carries the same banner as every other generated artifact in the repository.

## Provenance record fields

| Field | Meaning |
|---|---|
| `source_repo` | The repository the schema was emitted from (`OmniNode-ai/omnibase_core`) |
| `source_commit` | The 40-character commit of that repository the emitter ran at |
| `emitter` | The emitting script, `scripts/emit_ts_types.py`, which reads the `MODELS` registry in that script |
| `schema_sha256` | SHA-256 of `schema/onex-models.json` as checked in |
| `defs_count` | Number of entries under `$defs` in the schema |

`schema_sha256` and `defs_count` are computed from the schema on disk each time the generate script runs. `source_repo`, `source_commit` and `emitter` describe the upstream run, which no file in OmniUI can derive, so the script carries them forward from the previous record and replaces the commit only when `ONEX_MODELS_SOURCE_COMMIT` names the upstream commit that was mirrored.

## Refresh procedure

```bash
# in an omnibase_core checkout at the commit you intend to mirror
uv run python scripts/emit_ts_types.py /path/to/omniui/schema/onex-models.json

# in omniui, naming the upstream commit that was mirrored
ONEX_MODELS_SOURCE_COMMIT=<40-character commit> npm run generate:onex-models
npm run lint && npm run typecheck && npm test
```

## What the checks enforce

The upstream emitter needs a Python toolchain and an `omnibase_core` checkout, so OmniUI's CI cannot regenerate the schema. It enforces the half that goes stale instead:

- `npm run check:generated` fails when the digest or the definitions count recorded in the provenance file disagrees with the schema on disk, or when the file does not record a 40-character source commit. A schema refreshed without running the generate script therefore fails the build instead of drifting.
- `src/generated/mirror-freshness.test.ts` asserts the same digest and count, and asserts that the theme schema and the widget envelope symbols are present both in the schema and in the generated TypeScript.

The upstream registry already carries the theme instance, theme catalog and widget envelope models, so the mirror contains them. What the repository was missing was a consumer: a checked-in mirror, a regeneration path and a test that fails when the two disagree. A gate satisfied upstream by a script nobody runs downstream does not protect the consumer.

## Why the provenance is data and not a document

Tooling reads the digest, the count and the commit, so they are kept as a generated data file that a check can compare with the schema. Prose that restates them goes stale in one place or the other. The explanation lives on this page and the repository keeps only its README.
