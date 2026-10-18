"""Plan frontmatter accepts ``historical``: a plan is a point-in-time record.

A plan describes work as it was intended on its date. Once that date has
passed, ``active`` reads as a live roadmap item to a reader or an agent, so a
plan that is kept only as history is marked ``historical``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import validate  # noqa: E402  (path setup must precede import)

PLAN = """---
type: plan
status: {status}
date: "2026-02-28"
title: "Test Plan"
---

Body.
"""


def _plan_errors(tmp_path: Path, status: str) -> list[str]:
    path = tmp_path / "plans" / "2026-02-28-test-plan.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(PLAN.format(status=status), encoding="utf-8")
    return validate.check_all_frontmatter(tmp_path)


def test_plan_accepts_historical(tmp_path: Path) -> None:
    assert _plan_errors(tmp_path, "historical") == []


def test_plan_still_rejects_unknown_status(tmp_path: Path) -> None:
    assert _plan_errors(tmp_path, "not-a-status"), "an unknown plan status must be rejected"
