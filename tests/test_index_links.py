"""Tests that every link a reader or an agent follows from an entry point resolves.

The generated indexes under ``indexes/`` used to write each link relative to the
repository root (``guides/x.md``) while sitting one directory down, so on GitHub
every link resolved to ``indexes/guides/x.md`` and returned 404. The broken-link
check never saw it because it scanned artifact sections only. These tests pin
both halves: the generator emits paths relative to the index file, and the
broken-link check covers the indexes, the repository-root documents and
``llms.txt``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import generate_indexes  # noqa: E402  (path setup must precede import)
import validate  # noqa: E402

GUIDE = """---
type: guide
status: current
date: "2026-10-17"
title: "Nested Guide"
topics: [delegation]
---

Body.
"""

LIVE_ROOT = Path(__file__).resolve().parent.parent


def _write(root: Path, rel: str, content: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for d in validate.ARTIFACT_DIRS:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    (tmp_path / "indexes").mkdir()
    _write(tmp_path, "guides/sub/nested-guide.md", GUIDE)
    return tmp_path


def _write_indexes(root: Path) -> None:
    artifacts = generate_indexes.collect_artifacts(root)
    _write(root, "indexes/chronological.md", generate_indexes.generate_chronological(artifacts))
    _write(root, "indexes/by-topic.md", generate_indexes.generate_by_topic(artifacts))
    _write(root, "indexes/by-type.md", generate_indexes.generate_by_type(artifacts))


class TestGeneratedIndexLinksResolve:
    def test_every_generated_link_resolves_from_the_index_file(self, repo: Path) -> None:
        _write_indexes(repo)
        hrefs = []
        for index in sorted((repo / "indexes").glob("*.md")):
            for _text, href in validate._LINK_PATTERN.findall(index.read_text(encoding="utf-8")):
                hrefs.append(href)
                assert (index.parent / href).resolve().is_file(), f"{index.name}: {href} does not resolve"
        # Positive control: the fixture guide is linked from all three indexes.
        assert hrefs.count("../guides/sub/nested-guide.md") == 3

    def test_generated_indexes_pass_the_broken_link_check(self, repo: Path) -> None:
        _write_indexes(repo)
        assert validate.check_broken_links(repo) == []


class TestBrokenLinkCheckCoversEntryPoints:
    def test_broken_link_in_an_index_fails(self, repo: Path) -> None:
        _write(repo, "indexes/by-topic.md", "# Topic Index\n\n- [Gone](guides/nested-guide.md)\n")
        errors = validate.check_broken_links(repo)
        assert any("indexes/by-topic.md" in e and "guides/nested-guide.md" in e for e in errors)

    def test_broken_link_in_root_readme_fails(self, repo: Path) -> None:
        _write(repo, "README.md", "# KB\n\n[Start](guides/missing.md)\n[Ok](guides/sub/nested-guide.md)\n")
        errors = validate.check_broken_links(repo)
        assert len(errors) == 1
        assert "README.md" in errors[0] and "guides/missing.md" in errors[0]

    def test_llms_txt_repository_url_must_resolve(self, repo: Path) -> None:
        base = validate.REPO_BLOB_URL
        _write(
            repo,
            "llms.txt",
            f"# OmniNode\n\n## Docs\n\n- [Guide]({base}guides/sub/nested-guide.md): fine\n"
            f"- [Gone]({base}guides/missing.md): broken\n- [Outside](https://example.com/x.md): ignored\n",
        )
        errors = validate.check_broken_links(repo)
        assert len(errors) == 1
        assert "llms.txt" in errors[0] and "guides/missing.md" in errors[0]


class TestLiveTree:
    def test_live_tree_has_no_broken_links(self) -> None:
        assert validate.check_broken_links(LIVE_ROOT) == []

    def test_live_llms_txt_exists_and_links_into_this_repository(self) -> None:
        text = (LIVE_ROOT / "llms.txt").read_text(encoding="utf-8")
        assert text.startswith("# ")
        assert text.count(validate.REPO_BLOB_URL) >= 5
