---
type: reference
status: current
date: '2026-10-18'
title: Verification Doctrine
topics: [evidence, governance, agent-integrations]
refs: []
---

# Verification Doctrine

A claim about a file, a runtime or a workflow is only as current as the evidence behind it. Record the revision, observation time, command and result, and distinguish source inspection from runtime observation.

| Claim | Evidence to cite |
|---|---|
| A node or handler exists | The file at an identified revision of the owning repository. |
| A behavior works | A test or workflow receipt that exercises the behavior and records a terminal outcome. |
| A regression is prevented | A test that fails without the change and passes with it. |
| A projection is current | The read model's cursor or watermark and the source-event boundary being compared. |
| A check passed | The check run for the exact revision under review, including its terminal conclusion. |
| A hosted feature is available | The dated public availability statement and an authorized end-to-end observation; a route definition alone is insufficient. |

Do not use a stale checkout, a ticket description or an agent's summary as proof of current behavior. A missing result is unverified, not a pass. A health response establishes reachability, not completion of a workflow. A receipt records one run, not a general claim about cost or answer quality.

Evidence belongs beside the code it proves. Public documentation cites a PR, a CI run or a receipt in the owning repository. See [the evidence pivot](../pivots/PIVOT-0006-evidence-lives-with-code.md), [Truth must be proven](../doctrine/truth-must-be-proven.md), and [Evidence is a first-class output](../doctrine/evidence-is-first-class-output.md).
