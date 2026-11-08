"""Pin the tutorials section of the public knowledge base.

The section lives in ``docs/tutorials``: self-contained HTML pages, one
``site.css`` and an ``index.html``. ``validate.py`` checks Markdown links only,
so a missing page or a dead link inside the HTML section, or an internal name
in a page, would pass every other check. These tests close that gap:

* the section holds only HTML pages and the stylesheet, with an index;
* every local link and stylesheet reference in every page resolves, and every
  page is reachable from the index or the gallery index;
* the repository front page links the tutorials index (the site root, which
  serves ``index.html``) and the section folder;
* no page carries a pattern the sanitization guard refuses, with a planted
  control showing the scan fails when one internal name is present;
* ``validate.py`` itself, the gate CI runs, scans the section's pages and
  stylesheet and fails on one planted internal name.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import sanitization_patterns  # noqa: E402  (path setup must precede import)
import validate  # noqa: E402

SECTION = _ROOT / "docs" / "tutorials"
INDEXES = ("index.html", "gallery-index.html")
_HREF = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
_PUBLIC_SITE = "https://omninode-ai.github.io/knowledge_base/"


def _pages() -> list[Path]:
    return sorted(SECTION.glob("*.html"))


def _local_targets(page: Path) -> list[str]:
    targets = []
    for ref in _HREF.findall(page.read_text(encoding="utf-8")):
        if ref.startswith(("http://", "https://", "mailto:", "#", "data:", "javascript:")):
            continue
        targets.append(ref.split("#", 1)[0].split("?", 1)[0])
    return [t for t in targets if t]


def _scan(name: str, text: str) -> list[str]:
    return sanitization_patterns.scan_text(text, label=name, honor_allowlist=False)


def test_section_holds_only_pages_and_the_stylesheet() -> None:
    assert SECTION.is_dir()
    stray = sorted(
        p.name for p in SECTION.iterdir() if not (p.is_file() and (p.suffix == ".html" or p.name == "site.css"))
    )
    assert stray == []
    assert (SECTION / "site.css").is_file()
    for index in INDEXES:
        assert (SECTION / index).is_file(), f"missing {index}"


@pytest.mark.parametrize("page", _pages(), ids=lambda p: p.name)
def test_every_local_reference_resolves(page: Path) -> None:
    missing = [t for t in _local_targets(page) if not (SECTION / t).is_file()]
    assert missing == [], f"{page.name} links to missing files: {missing}"


def test_every_page_is_reachable_from_an_index() -> None:
    linked: set[str] = set()
    for index in INDEXES:
        linked.update(_local_targets(SECTION / index))
    orphans = sorted(p.name for p in _pages() if p.name not in linked and p.name not in INDEXES)
    assert orphans == []


def test_index_links_pages_that_exist() -> None:
    page_links = [t for t in _local_targets(SECTION / "index.html") if t.endswith(".html")]
    assert len(page_links) > 1
    assert [t for t in page_links if not (SECTION / t).is_file()] == []


def test_front_page_links_the_tutorials_index() -> None:
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    assert _PUBLIC_SITE in readme
    assert "(docs/tutorials)" in readme


@pytest.mark.parametrize("page", _pages(), ids=lambda p: p.name)
def test_page_passes_the_sanitization_scan(page: Path) -> None:
    assert _scan(page.name, page.read_text(encoding="utf-8")) == []


def test_planted_internal_name_fails_the_scan() -> None:
    """Positive control: the scan the pages pass is able to fail on a page."""
    page = (SECTION / "index.html").read_text(encoding="utf-8")
    planted = page.replace("</body>", "<p>stored in infisical</p></body>", 1)
    assert planted != page
    findings = _scan("index.html", planted)
    assert len(findings) == 1
    assert "secrets manager" in findings[0]


def test_dead_link_control_is_detected(tmp_path: Path) -> None:
    """Positive control: the link resolver reports a reference to a missing file."""
    page = tmp_path / "page.html"
    page.write_text('<a href="gone.html">x</a><link href="site.css">', encoding="utf-8")
    missing = [t for t in _local_targets(page) if not (tmp_path / t).is_file()]
    assert missing == ["gone.html", "site.css"]


def test_gate_scans_every_page_and_the_stylesheet() -> None:
    """The gate script's own target list holds the whole section."""
    targets = {p.relative_to(_ROOT).as_posix() for p in validate._find_sanitization_targets(_ROOT)}
    expected = {p.relative_to(_ROOT).as_posix() for p in SECTION.iterdir() if p.is_file()}
    assert expected <= targets
    assert "docs/tutorials/site.css" in targets
    assert "docs/tutorials/index.html" in targets


def test_gate_passes_on_the_live_section() -> None:
    assert [e for e in validate.check_sanitization(_ROOT) if "docs/tutorials" in e] == []


@pytest.mark.parametrize("name", ["index.html", "site.css"])
def test_gate_fails_when_one_internal_name_is_planted(tmp_path: Path, name: str) -> None:
    """Positive control: validate.py exits non-zero on one planted name in the section."""
    section = tmp_path / "docs" / "tutorials"
    section.mkdir(parents=True)
    clean = (SECTION / name).read_text(encoding="utf-8")
    (section / name).write_text(clean, encoding="utf-8")
    assert validate.check_sanitization(tmp_path) == []
    (section / name).write_text(clean + "\nstored in infisical\n", encoding="utf-8")
    errors = validate.check_sanitization(tmp_path)
    assert len(errors) == 1
    assert f"docs/tutorials/{name}" in errors[0]
    assert "secrets manager" in errors[0]
