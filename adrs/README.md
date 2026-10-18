# Architecture Decision Records

Architecture Decision Records (ADRs) are the formal decision ledger for OmniNode. Each ADR captures a specific architectural decision, the context that forced it, alternatives considered, and consequences.

## ADR Lifecycle

```
Proposed → Accepted → Superseded
              ↓           ↓
         Deprecated    (by newer ADR)
              ↓
          Rejected
```

### States

| State | Meaning |
|-------|---------|
| **Proposed** | Decision identified, under review — not yet in effect |
| **Accepted** | Decision ratified and actively governing the codebase |
| **Superseded** | Replaced by a newer ADR; links to its successor |
| **Deprecated** | No longer relevant but not replaced by a newer decision |
| **Rejected** | Considered and explicitly not adopted |

A decision moves from `Proposed` to `Accepted` via PR review. When a later ADR renders an earlier one obsolete, the earlier ADR is updated to `Superseded` with a `superseded_by` frontmatter link and the new ADR lists the older one in `supersedes`.

## How ADRs Relate to Other Artifacts

OmniNode uses four artifact types that work together:

- **Doctrine** — the principles and invariants that constrain all decisions. ADRs must not contradict doctrine; when they appear to, the doctrine must be updated first with explicit rationale.
- **Pivots** — explain why understanding changed, often triggering the need for a new ADR. A pivot identifies the insight; an ADR records the decision that follows from it.
- **Evidence** validates a decision through a PR, a CI run or a receipt in the owning product repository. An ADR cites that outcome instead of hosting it; see [the evidence pivot](../pivots/PIVOT-0006-evidence-lives-with-code.md).

The typical flow: an incident or operational pressure surfaces a gap → a pivot records the insight shift → an ADR formalizes the decision → a cited outcome proves the decision had the intended effect.

## How to Propose a New ADR

1. Copy `_template.md` to a new numbered file: `ADR-NNNN-descriptive-name.md`
2. Fill in all frontmatter fields (especially `topics`, `refs`, `supersedes`)
3. Set `status: proposed`
4. Complete the body sections: Context, Decision, Alternatives Considered, Consequences
5. Open a PR for review using public-safe metadata; keep private work tracking outside this repository
6. On approval, change `status` to `accepted` and update any superseded ADRs

Keep ADRs narrow — one decision per ADR. If the decision requires background explanation that would exceed ~400 words, trim it to what the decision needs — this repository does not carry a narrative-journal section to defer background into.

## Cross-References

Some ADRs build directly on others:

- **ADR-0004** follows from **ADR-0003**: once the registration/runtime/registry boundary was defined (ADR-0003), the consumer surface question required its own decision (ADR-0004).
- **ADR-0007** follows from **ADR-0005**: the same ambiguity that forced ADR-0005 (duplicate canonical source for dispatch lifecycle) recurred for skills migration plans, motivating the same pattern resolution.
- **ADR-0006** is architecturally adjacent to **ADR-0007**: both define where shared validator/migration logic lives in the repo layer hierarchy.

## Platform architecture

| ID | Decision | Status | Date |
|---|---|---|---|
| [ADR-0002](ADR-0002-data-verification-invocation.md) | Data Verification Node Invocation Policy | accepted | 2026-04-23 |
| [ADR-0003](ADR-0003-registration-runtime-registry-boundary.md) | Registration Runtime / Registry Boundary | accepted | 2026-04-23 |
| [ADR-0004](ADR-0004-registry-owned-consumer-surface.md) | Registry-Owned Consumer Surface | accepted | 2026-04-23 |
| [ADR-0005](ADR-0005-dispatch-lifecycle-canonical.md) | Dispatch Lifecycle Canonical Source | accepted | 2026-04-28 |
| [ADR-0026](ADR-0026-two-databases-tenant-vs-internal.md) | Two Databases — Tenant-Facing vs Internal/Ops | superseded | 2026-07-29 |
| [ADR-0027](ADR-0027-one-application-database-domain-separation.md) | One Application Database with Contract-Classified Domains | accepted | 2026-07-29 |
| [ADR-0028](ADR-0028-receipt-type-consolidation.md) | Receipt Type Consolidation onto ModelDodReceipt | accepted | 2026-04-27 |
| [ADR-0030](ADR-0030-protocol-based-di-architecture.md) | Protocol-Based Dependency Injection Architecture | accepted | 2025-10-30 |
| [ADR-0031](ADR-0031-centralized-field-limit-constants.md) | Centralized Field Limit Constants | accepted | 2025-12-27 |
| [ADR-0032](ADR-0032-reducer-output-exception-consistency.md) | Reducer Output Exception Consistency | accepted | 2025-12-16 |
| [ADR-0033](ADR-0033-registration-trigger-architecture.md) | Registration Trigger Architecture | accepted | 2025-12-19 |
| [ADR-0034](ADR-0034-core-infra-dependency-boundary.md) | Core-Infra Dependency Boundary | accepted | 2025-12-26 |
| [ADR-0035](ADR-0035-status-taxonomy-and-categorical-organization.md) | Status Taxonomy and Categorical Organization | accepted | 2026-01-12 |
| [ADR-0036](ADR-0036-context-mutability-design-decision.md) | Context Mutability Design Decision | accepted | 2025-12-15 |
| [ADR-0037](ADR-0037-validator-error-handling-modelonexerror.md) | Validator Error Handling with ModelOnexError | accepted | 2026-01-18 |
| [ADR-0039](ADR-0039-omnidash-typography-system.md) | Dashboard Typography System — Tokens Plus Typed Primitives | accepted | 2026-04-24 |
| [ADR-0040](ADR-0040-omnidash-storybook-widget-coverage.md) | Storybook Coverage for Every Dashboard Widget | accepted | 2026-04-24 |
| [ADR-0041](ADR-0041-omnidash-baselines-roi-card-stays-bespoke.md) | BaselinesROICard Stays Bespoke, Outside the Generic Widget Primitives | accepted | 2026-04-29 |
| [ADR-0042](ADR-0042-omnidash-cross-renderer-typed-empty-state-gate.md) | Cross-Renderer Typed Empty-State Gate | accepted | 2026-06-18 |
| [ADR-0043](ADR-0043-omnidash-rjsf-discriminated-union-handling.md) | Render Pydantic-Generated JSON Schema With Stock @rjsf, No Custom Field | accepted | 2026-06-20 |
| [ADR-0044](ADR-0044-event-fan-out-and-app-owned-catalogs.md) | Event Fan-Out Strategy and App-Owned Event Catalogs | accepted | 2026-02-09 |
| [ADR-0047](ADR-0047-dual-emission-privacy-split.md) | Dual-Topic Emission for Prompt Privacy | accepted | 2026-02-19 |
| [ADR-0051](ADR-0051-sibling-plugin-strategy.md) | Sibling Plugin Strategy (omnigemini, omnimemory, omniintelligence) | accepted | 2026-04-23 |

## Delegation and routing

| ID | Decision | Status | Date |
|---|---|---|---|
| [ADR-0008](ADR-0008-delegation-config-authority-and-budget-aware-tier-cost.md) | Delegation configuration authority (historical) | superseded | 2026-06-18 |
| [ADR-0009](ADR-0009-complexity-aware-delegation-routing.md) | Complexity-aware delegation routing (historical) | superseded | 2026-06-18 |
| [ADR-0018](ADR-0018-delegation-graded-benchmark-ladder.md) | Withdrawn planning proposal | deprecated | 2026-07-04 |
| [ADR-0045](ADR-0045-candidate-list-injection.md) | Remove YAML Loading from Synchronous Hook Path | accepted | 2026-02-19 |
| [ADR-0046](ADR-0046-no-fallback-routing.md) | Fail-Fast Routing — No Silent Fallback to general-purpose | accepted | 2026-02-19 |
| [ADR-0048](ADR-0048-delegation-orchestrator-quality-gate.md) | Local LLM Delegation with 2-Clean-Run Quality Gate | accepted | 2026-02-19 |
| [ADR-0049](ADR-0049-three-tier-agent-routing.md) | Three-Tier Agent Routing (LLM → Fuzzy → Explicit) | accepted | 2026-02-19 |
| [ADR-0053](ADR-0053-beta-scope-local-install-own-keys.md) | Beta Scope — Local Install, Your Own Model Keys, No Hosted Service | accepted | 2026-10-17 |

## Engineering process

These records concern contributor workflows. Superseded records are history and do not authorize an agent to execute them.

| ID | Decision | Status | Date |
|---|---|---|---|
| [ADR-0001](ADR-0001-dependabot-approval-manual.md) | Dependabot PR Approval Remains Manual | accepted | 2026-03-25 |
| [ADR-0006](ADR-0006-skill-liveness-validator-home.md) | Skill Liveness Validator Home | accepted | 2026-04-28 |
| [ADR-0007](ADR-0007-skills-canonical-plan.md) | Canonical Skills Migration Plan (historical) | deprecated | 2026-04-28 |
| [ADR-0010](ADR-0010-required-context-parity-ratchet.md) | Historical required-check parity proposal | deprecated | 2026-07-10 |
| [ADR-0019](ADR-0019-no-self-authored-evidence.md) | Historical evidence-process proposal | superseded | 2026-07-06 |
| [ADR-0020](ADR-0020-branch-preview-verification.md) | Withdrawn planning proposal | deprecated | 2026-07-06 |
| [ADR-0021](ADR-0021-beta-ships-first-priority-lock.md) | Withdrawn beta planning record | superseded | 2026-07-06 |
| [ADR-0022](ADR-0022-shift-left-and-occ-evidence-only-fast-lane.md) | Historical evidence-process proposal | superseded | 2026-07-07 |
| [ADR-0023](ADR-0023-remove-occ-merge-queue.md) | Historical evidence-process proposal | superseded | 2026-07-07 |
| [ADR-0024](ADR-0024-merge-stall-tooling-not-capacity.md) | Historical evidence-process proposal | superseded | 2026-07-06 |
| [ADR-0025](ADR-0025-occ-validator-redesign-option-a.md) | Historical evidence-process proposal | superseded | 2026-07-03 |
| [ADR-0029](ADR-0029-model-b-failing-rollup-validator-enforcement.md) | Model B — Failing-Rollup Validator Enforcement (pilot: omnibase_core) | accepted | 2026-06-24 |
| [ADR-0038](ADR-0038-ci-workflow-modification-risk.md) | CI Workflow Modification Risk (Transport Import Branch Protection) | accepted | 2025-12-10 |
| [ADR-0050](ADR-0050-ai-slop-checker-rule-set-v1.md) | AI-Slop Checker Rule Set v1.0 | accepted | 2026-03-02 |

## Sample applications

Withdrawn research proposals are kept as historical context. The game-specific decisions have been removed from the platform ledger; [the glossary](../reference/glossary.md) defines the historical testbed.

| ID | Decision | Status | Date |
|---|---|---|---|
| [ADR-0011](ADR-0011-rsd-recursive-system-design-naming.md) | Withdrawn planning proposal | deprecated | 2026-07-06 |
| [ADR-0012](ADR-0012-seams-first-class.md) | Withdrawn planning proposal | deprecated | 2026-07-06 |
| [ADR-0013](ADR-0013-deterministic-fsm-control-plane.md) | Withdrawn planning proposal | deprecated | 2026-07-06 |
| [ADR-0014](ADR-0014-factory-economics-frontier-fissions-locals-build.md) | Withdrawn planning proposal | deprecated | 2026-07-06 |
| [ADR-0052](ADR-0052-adaptive-recursive-contract-bisection.md) | Withdrawn planning proposal | deprecated | 2026-07-06 |
