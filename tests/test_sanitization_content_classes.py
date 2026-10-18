"""Tests for the content classes the public-repo sanitization gate refuses.

Each class here reached the public tree before the gate knew about it: a
person's name in the manifest ``owner:`` field and an ADR author cell, a quoted
expletive in an ADR, plan banners addressed to a coding agent, citations of
private agent-memory files, private repository names spelled as bare slugs or
paths, self-hosted CI runner container names, and a ticket id written in
lowercase inside a branch name.

Every ``blocks`` case is a positive control (it passed the gate before this
change); every ``passes`` case is a negative control proving the new pattern
does not swallow the ordinary prose this repository already carries.

Fixtures are synthetic. Where a test must hit the exact shape of a real
private slug, the slug is assembled at runtime so the literal never appears in
this public file; expletives are assembled the same way.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import pytest  # noqa: E402  (path setup must precede import)
from sanitization_patterns import scan_text  # noqa: E402


def _findings(text: str) -> list[str]:
    return scan_text(text, label="probe")


def _assert_blocked_as(text: str, rule: str) -> None:
    errors = _findings(text)
    assert errors, f"{text!r} must be refused by the gate"
    assert any(rule in e for e in errors), f"expected the {rule!r} rule to fire, got: {errors}"


# Synthetic stand-ins: shaped like the real thing, naming nobody.
_PERSON = "Alex Example"
_EXPLETIVE = "f" + "uck"
_EXPLETIVE_2 = "sh" + "it"


class TestPersonNames:
    @pytest.mark.parametrize(
        "text",
        [
            f"        owner: {_PERSON}",
            f"owner: {_PERSON.split()[0]}",
            f"| **Author** | {_PERSON.split()[0]} |",
            f"Author: {_PERSON}",
            f"- **Owner**: {_PERSON}",
        ],
    )
    def test_person_in_owner_or_author_field_blocks(self, text: str) -> None:
        _assert_blocked_as(text, "Person name")

    @pytest.mark.parametrize(
        "text",
        [
            "        owner: docs-maintainers",
            "| **Author** | OmniNode Team |",
            "owner: platform-team",
            "The owner: the person answerable for whether it is true.",
            "Each node owns its handler; the author of a contract decides.",
            "| Owner | Role | Responsibility |",
            "| Date | Version | Author | Changes |",
            "**Owner**: Shared infrastructure (deployed separately)",
            "- **owner**: Who is responsible for the exception",
            "**Trigger owner:** Runtime startup",
            "| **Author** | Platform Team |",
        ],
    )
    def test_role_or_team_owner_passes(self, text: str) -> None:
        assert _findings(text) == []


class TestProfanity:
    @pytest.mark.parametrize(
        "text",
        [
            f'Rejected by the operator: "that is {_EXPLETIVE}ing boring"',
            f"{_EXPLETIVE.upper()} this",
            f"no {_EXPLETIVE}jing {_EXPLETIVE_2}",
            f"this is {_EXPLETIVE_2}ty",
        ],
    )
    def test_expletive_blocks(self, text: str) -> None:
        _assert_blocked_as(text, "Profanity")

    @pytest.mark.parametrize(
        "text",
        ["shiitake", "Shift the window", "the shitsuke step of 5S", "a buckled rail"],
    )
    def test_ordinary_words_pass(self, text: str) -> None:
        assert _findings(text) == []


class TestAgentDirectives:
    @pytest.mark.parametrize(
        "text",
        [
            "> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan.",
            "For Claude: implement task 1",
            "REQUIRED SUB-SKILL: executing-plans",
            "> For execution: pass this file to `/executing-plans` or `/plan-to-tickets`",
        ],
    )
    def test_agent_addressed_directive_blocks(self, text: str) -> None:
        _assert_blocked_as(text, "Agent-addressed directive")

    @pytest.mark.parametrize(
        "text",
        [
            "Claude Code loads CLAUDE.md first.",
            "Intents will be routed to Effect nodes for execution:",
            "Primary command-line interface for Claude Code enhancements",
        ],
    )
    def test_prose_about_agents_passes(self, text: str) -> None:
        assert _findings(text) == []


class TestAgentMemoryCitations:
    @pytest.mark.parametrize(
        "text",
        [
            "aligns with project memory `feedback_example_rule.md`",
            "Per memory `feedback_example.md`, queue repos drop entries",
            "see `project_example_by_design.md`",
            "this aligns with project memory",
        ],
    )
    def test_memory_file_citation_blocks(self, text: str) -> None:
        _assert_blocked_as(text, "Agent-memory citation")

    @pytest.mark.parametrize(
        "text",
        [
            "the feedback loop closes on the bus",
            "see `guides/project-setup.md`",
            "memory services start with the compose profile",
            "      - source_path: .serena/memories/project_overview.md",
        ],
    )
    def test_ordinary_memory_and_feedback_prose_passes(self, text: str) -> None:
        assert _findings(text) == []


class TestPrivateRepositoryNames:
    @pytest.mark.parametrize(
        "slug",
        [
            "omni" + "base" + "_internal",
            "omni" + "claude" + "-internal",
            "knowledge" + "_base" + "_internal",
        ],
    )
    def test_internal_slug_blocks(self, slug: str) -> None:
        _assert_blocked_as(f"the tool lives in {slug} for now", "Private repo name")

    def test_hosted_cloud_repository_path_blocks(self) -> None:
        _assert_blocked_as("bindings under `omninode_infra/k8s/` are generated", "Private repo path")

    @pytest.mark.parametrize(
        "text",
        [
            "the hosted-cloud deployment repository (private)",
            "omnibase_infra/src/omnibase_infra/nodes",
            "an internal tool",
            "private-internal-kb",
            "creates the proof tables in `omninode_internal`",
        ],
    )
    def test_public_repository_and_generic_prose_pass(self, text: str) -> None:
        assert _findings(text) == []


class TestRunnerContainerNames:
    def test_runner_container_name_blocks(self) -> None:
        _assert_blocked_as("docker logs omninode-runner-7", "CI runner container name")

    def test_generic_runner_prose_passes(self) -> None:
        assert _findings("a self-hosted runner picks up the job") == []


class TestLowercaseTicketIds:
    @pytest.mark.parametrize(
        "text",
        ["branch `example/omn-1234-add-thing`", "**Correlation ID**: `omn-12-import-rules-doc`"],
    )
    def test_lowercase_ticket_id_blocks(self, text: str) -> None:
        _assert_blocked_as(text, "Internal ticket reference")

    def test_omnibase_and_omni_prefixed_words_pass(self) -> None:
        assert _findings("omnibase-core and omnimarket and omn-XXXX") == []


class TestRedactionPlaceholderInTitles:
    @pytest.mark.parametrize(
        "text",
        [
            "# <ticket>: Fix the thing",
            "## Why <ticket> exists",
            'title: "<ticket> follow-on"',
        ],
    )
    def test_placeholder_in_title_or_heading_blocks(self, text: str) -> None:
        _assert_blocked_as(text, "Redaction placeholder")

    @pytest.mark.parametrize(
        "text",
        [
            "A ticket reference is replaced by `<ticket>` when a page is published.",
            "# Runbook titles name the capability",
            'title: "Application database cutover receipts"',
        ],
    )
    def test_placeholder_defined_in_prose_passes(self, text: str) -> None:
        assert _findings(text) == []


class TestListedPersonNames:
    def test_listed_name_blocks_when_a_names_file_is_configured(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        names = tmp_path / "names.txt"
        names.write_text("# synthetic list\nZanzibar Quill\nQuillen\n", encoding="utf-8")
        monkeypatch.setenv("ONEX_SANITIZATION_NAMES_FILE", str(names))
        _assert_blocked_as("Reviewed with Zanzibar Quill last week.", "Listed person name")
        _assert_blocked_as("branch quillen/fix-docs", "Listed person name")

    def test_listed_name_inside_a_longer_word_passes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        names = tmp_path / "names.txt"
        names.write_text("Quillen\n", encoding="utf-8")
        monkeypatch.setenv("ONEX_SANITIZATION_NAMES_FILE", str(names))
        assert _findings("The quillenoid widget renders a Quillenesque badge.") == []

    def test_no_names_file_means_no_listed_name_rule(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ONEX_SANITIZATION_NAMES_FILE", raising=False)
        assert _findings("Reviewed with Zanzibar Quill last week.") == []

    def test_missing_names_file_is_ignored(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ONEX_SANITIZATION_NAMES_FILE", str(tmp_path / "absent.txt"))
        assert _findings("Reviewed with Zanzibar Quill last week.") == []


class TestGateSourceTreeHygiene:
    """The gate's own tests and scripts must not publish what the gate refuses.

    The artifact walk does not cover ``tests/`` or ``scripts/``: their fixtures
    legitimately spell forbidden shapes with synthetic values. Real private
    repository names are the exception, and nothing in these trees may spell one.
    """

    def test_tests_and_scripts_spell_no_private_repository_name(self) -> None:
        from sanitization_patterns import SANITIZATION_PATTERNS

        rules = [p for p, desc in SANITIZATION_PATTERNS if desc == "Private repo name"]
        assert rules, "the private-repo-name rules must exist"
        root = Path(__file__).resolve().parent.parent
        offenders: list[str] = []
        for tree in ("tests", "scripts"):
            for path in sorted((root / tree).rglob("*.py")):
                for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if any(rule.search(line) for rule in rules):
                        offenders.append(f"{path.relative_to(root)}:{lineno}")
        assert offenders == [], f"private repository names spelled in the gate's own tree: {offenders}"
        probe = "see " + "knowledge_base" + "-internal for details"
        assert any(rule.search(probe) for rule in rules), "positive control: the rules must catch a private slug"
