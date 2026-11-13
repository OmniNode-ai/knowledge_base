"""Guard against retired repositories re-entering migration-manifest.yaml.

The repositories in RETIRED_REPOSITORIES have been retired: they were
deleted from the manifest and are no longer migration targets, so the live
manifest must never name one as a sync target again. The main test walks
the real manifest at the repository root and fails if any retired
repository appears as an entry under a repository-collection key. The
remaining tests pin the helper's behaviour with synthetic positive and
negative controls: a prose mention (a note that merely says a repository
is retired) is deliberately not a target — only a value under a key named
``repos``, ``repositories``, or ending in ``_repos`` counts as an entry.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml

RETIRED_REPOSITORIES = ("omnibase_compat", "onex_change_control", "ycbench_onex")


def _is_repository_collection_key(key: str) -> bool:
    return key in {"repos", "repositories"} or key.endswith("_repos")


def _repository_entry_lists(node: object) -> Iterator[list]:
    """Yield every list that sits under a repository-collection key,
    walking the whole document recursively (through nested mappings and
    lists), so a retired repository cannot hide at any depth."""
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(key, str) and _is_repository_collection_key(key) and isinstance(value, list):
                yield value
            yield from _repository_entry_lists(value)
    elif isinstance(node, list):
        for item in node:
            yield from _repository_entry_lists(item)


def _entry_strings(entry: object) -> Iterator[str]:
    """Yield the candidate names an entry contributes: plain string items
    contribute themselves, dict items contribute their string values."""
    if isinstance(entry, str):
        yield entry
    elif isinstance(entry, dict):
        for value in entry.values():
            if isinstance(value, str):
                yield value


def retired_repository_entries(manifest: dict) -> list[str]:
    """Return the sorted retired repository names found as entries under
    any repository-collection key anywhere in the manifest. Names are
    compared by their last "/"-segment with a trailing ".git" removed, so
    a fully-qualified or clone-suffixed spelling is still caught."""
    found: set[str] = set()
    for entries in _repository_entry_lists(manifest):
        for entry in entries:
            for candidate in _entry_strings(entry):
                name = candidate.rsplit("/", 1)[-1]
                if name.endswith(".git"):
                    name = name[: -len(".git")]
                if name in RETIRED_REPOSITORIES:
                    found.add(name)
    return sorted(found)


def test_real_manifest_has_no_retired_repository_entries() -> None:
    manifest_path = Path(__file__).resolve().parent.parent / "migration-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    found = retired_repository_entries(manifest)
    assert found == [], (
        "the host reconcile unit refuses retired repositories in sync inputs; "
        f"remove the retired target(s) {found} from migration-manifest.yaml before syncing"
    )


def test_positive_control_catches_a_retired_entry_in_repos() -> None:
    manifest = {"repos": [{"repo": "omnibase_core"}, {"repo": "onex_change_control"}]}
    assert retired_repository_entries(manifest) == ["onex_change_control"]


@pytest.mark.parametrize("name", RETIRED_REPOSITORIES)
def test_each_retired_repository_is_matched_by_name(name: str) -> None:
    manifest = {"repos": [{"repo": name}]}
    assert retired_repository_entries(manifest) == [name]


def test_prose_mention_is_not_a_target() -> None:
    manifest = {"notes": "onex_change_control is retired"}
    assert retired_repository_entries(manifest) == []


def test_path_prefixed_and_git_suffixed_spellings_are_caught() -> None:
    manifest = {
        "repositories": [
            "https://example.com/omnigroup/omnibase_compat.git",
            {"repo": "gitlab.com/omnigroup/onex_change_control"},
        ]
    }
    assert retired_repository_entries(manifest) == ["omnibase_compat", "onex_change_control"]


def test_nested_repository_collection_keys_are_walked() -> None:
    manifest = {"waves": [{"notes": "second wave", "wave_repos": [{"repo": "ycbench_onex"}]}]}
    assert retired_repository_entries(manifest) == ["ycbench_onex"]
