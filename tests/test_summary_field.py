"""The optional ``summary:`` frontmatter field and its use in the type index.

A long page states its point in two or three sentences in frontmatter, so a
reader or an agent working from an index sees it without opening the page.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import generate_indexes  # noqa: E402  (path setup must precede import)
import validate  # noqa: E402

GUIDE = """---
type: guide
status: current
date: "2026-10-17"
title: "Test Guide"
{extra}---

Body.
"""


def _guide_errors(tmp_path: Path, extra: str) -> list[str]:
    path = tmp_path / "guides" / "test-guide.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(GUIDE.format(extra=extra), encoding="utf-8")
    return validate.check_all_frontmatter(tmp_path)


def test_summary_is_optional(tmp_path: Path) -> None:
    assert _guide_errors(tmp_path, "") == []


def test_summary_string_is_accepted(tmp_path: Path) -> None:
    assert _guide_errors(tmp_path, 'summary: "Two sentences. That say the point."\n') == []


def test_summary_must_be_a_string(tmp_path: Path) -> None:
    assert _guide_errors(tmp_path, "summary: [not, a, string]\n")


def test_type_index_shows_summary_when_present() -> None:
    artifacts = [
        {
            "type": "guide",
            "title": "With",
            "_path": "guides/a.md",
            "status": "current",
            "date": "2026-10-17",
            "summary": "The point.",
        },
        {"type": "guide", "title": "Without", "_path": "guides/b.md", "status": "current", "date": "2026-10-17"},
    ]
    out = generate_indexes.generate_by_type(artifacts)
    assert "- **[With](../guides/a.md)** — current. The point." in out
    assert "- **[Without](../guides/b.md)** — current\n" in out
