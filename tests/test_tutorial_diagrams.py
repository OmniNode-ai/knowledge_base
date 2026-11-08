"""Tests that the tutorial diagram page covers every tutorial and tour, and stays clean.

``guides/tutorial-diagrams.md`` draws one Mermaid diagram per interactive tutorial
and repository tour, because GitHub shows the tutorial HTML pages as source. These
tests pin the three properties a reader depends on: every tutorial the two tutorial
indexes list has a diagram and a link on the page, each link resolves, and the
diagram text passes the sanitization guard.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import sanitization_patterns  # noqa: E402  (path setup must precede import)
import validate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "guides" / "tutorial-diagrams.md"
TUTORIALS = ROOT / "docs" / "tutorials"
INDEX_PAGES = ("index.html", "gallery-index.html")

_HTML_HREF = re.compile(r'href="([A-Za-z0-9_.-]+\.html)"')
_FILE_LINK = re.compile(r"^(?:Tutorial|Tour) file: \[`([^`]+)`\]\(([^)]+)\)", re.MULTILINE)
_FENCE = re.compile(r"^```mermaid\n(.*?)^```$", re.MULTILINE | re.DOTALL)
_DIAGRAM_KEYWORDS = ("flowchart", "graph", "sequenceDiagram", "stateDiagram", "journey")


def _listed_tutorials() -> set[str]:
    listed: set[str] = set()
    for name in INDEX_PAGES:
        text = (TUTORIALS / name).read_text(encoding="utf-8")
        listed.update(_HTML_HREF.findall(text))
    return listed - set(INDEX_PAGES)


def _sections(text: str) -> list[str]:
    """Split the page at its third-level headings, dropping the preamble."""
    return re.split(r"^### ", text, flags=re.MULTILINE)[1:]


class TestEveryTutorialHasADiagram:
    def test_every_listed_tutorial_is_linked_from_the_page(self) -> None:
        listed = _listed_tutorials()
        # Positive control: the indexes list tutorials and tours, not nothing.
        assert len(listed) >= 30
        linked = {Path(href).name for _label, href in _FILE_LINK.findall(PAGE.read_text(encoding="utf-8"))}
        assert sorted(listed - linked) == []
        assert sorted(linked - listed) == []

    def test_every_section_has_exactly_one_diagram_and_one_resolving_link(self) -> None:
        sections = _sections(PAGE.read_text(encoding="utf-8"))
        assert len(sections) == len(_listed_tutorials())
        for section in sections:
            title = section.splitlines()[0]
            links = _FILE_LINK.findall(section)
            assert len(links) == 1, f"{title}: expected one tutorial link, found {len(links)}"
            assert (PAGE.parent / links[0][1]).resolve().is_file(), f"{title}: {links[0][1]} does not resolve"
            assert len(_FENCE.findall(section)) == 1, f"{title}: expected exactly one mermaid diagram"

    def test_every_diagram_opens_with_a_diagram_keyword(self) -> None:
        bodies = _FENCE.findall(PAGE.read_text(encoding="utf-8"))
        assert len(bodies) == len(_listed_tutorials())
        for body in bodies:
            assert body.lstrip().startswith(_DIAGRAM_KEYWORDS), body.splitlines()[0]

    def test_unclosed_fence_is_not_miscounted(self) -> None:
        # Negative control: a fence that never closes yields no diagram.
        assert _FENCE.findall("```mermaid\nflowchart LR\n  a --> b\n") == []


class TestPageLinksAreChecked:
    def test_live_page_passes_the_broken_link_check(self) -> None:
        errors = [e for e in validate.check_broken_links(ROOT) if "tutorial-diagrams.md" in e]
        assert errors == []

    def test_renamed_tutorial_file_is_reported_as_a_broken_link(self, tmp_path: Path) -> None:
        (tmp_path / "guides").mkdir()
        (tmp_path / "docs" / "tutorials").mkdir(parents=True)
        shutil.copy(PAGE, tmp_path / "guides" / PAGE.name)
        for tutorial in TUTORIALS.glob("*.html"):
            shutil.copy(tutorial, tmp_path / "docs" / "tutorials" / tutorial.name)
        # Control: the copied tree has no broken tutorial link in the page. The
        # page's links to sibling guides are outside the copy and are not counted.
        assert [e for e in validate.check_broken_links(tmp_path) if ".html" in e] == []
        (tmp_path / "docs" / "tutorials" / "node-effect.exhibit.html").rename(
            tmp_path / "docs" / "tutorials" / "node-effect-renamed.exhibit.html"
        )
        errors = [e for e in validate.check_broken_links(tmp_path) if ".html" in e]
        assert errors
        assert all("node-effect.exhibit.html" in e for e in errors)


class TestPageIsSanitized:
    def test_live_page_has_no_sanitization_findings(self) -> None:
        assert sanitization_patterns.scan_text(PAGE.read_text(encoding="utf-8"), label=PAGE.name) == []

    def test_ticket_id_in_a_diagram_label_is_flagged(self) -> None:
        text = PAGE.read_text(encoding="utf-8")
        marker = '"Kafka Bus"'
        assert marker in text
        tainted = text.replace(marker, '"Kafka Bus OMN-1234"', 1)
        assert sanitization_patterns.scan_text(tainted, label=PAGE.name)
