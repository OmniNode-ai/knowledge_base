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
            "> **For " + "Claude:** REQUIRED " + "SUB-SKILL: Use executing-plans to implement this plan.",
            "For " + "Claude: implement task 1",
            "REQUIRED " + "SUB-SKILL: executing-plans",
            "> For " + "execution: pass this file " + "to `/executing-plans` or `/plan-to-tickets`",
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
            "aligns with project" + " memory `feedback" + "_example_rule.md`",
            "Per memory `feedback" + "_example.md`, queue repos drop entries",
            "see `project" + "_example_by_design.md`",
            "this aligns with project" + " memory",
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
        _assert_blocked_as("bindings under `omninode" + "_infra/k8s/` are generated", "Private repo name")

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
        _assert_blocked_as("docker logs omninode-runner-" + "7", "CI runner container name")

    def test_generic_runner_prose_passes(self) -> None:
        assert _findings("a self-hosted runner picks up the job") == []


class TestLowercaseTicketIds:
    @pytest.mark.parametrize(
        "text",
        ["branch `example/omn-" + "1234-add-thing`", "**Correlation ID**: `omn-" + "12-import-rules-doc`"],
    )
    def test_lowercase_ticket_id_blocks(self, text: str) -> None:
        _assert_blocked_as(text, "Internal ticket reference")

    def test_omnibase_and_omni_prefixed_words_pass(self) -> None:
        assert _findings("omnibase-core and omnimarket and omn-XXXX") == []


class TestPublicationBoundaries:
    @pytest.mark.parametrize(
        "text, rule",
        [
            ('owner: "Alex Example"', "Person name"),
            ("| Author | Alex Example |", "Person name"),
            ("the deployment lives in " + "omninode" + "_infra", "Private repo name"),
            ("see " + "omni" + "_home/docs/audit.md", "Private workspace"),
            ("see /private/" + "feedback" + "_example.md", "Agent-memory"),
            ("For " + "execution: run the plan", "Agent-addressed"),
            ("DO NOT " + "re-implement this plan", "Agent-addressed"),
            ("git " + "add src/", "Agent-addressed"),
        ],
    )
    def test_unsafe_publication_is_refused(self, text: str, rule: str) -> None:
        _assert_blocked_as(text, rule)

    @pytest.mark.parametrize(
        "text",
        [
            'owner: "docs-maintainers"',
            "| Author | OmniNode Team |",
            "the hosted service's deployment infrastructure is private",
            "git status --short",
            "A git commit stores a revision.",
            "Your workspace contains the installed packages.",
        ],
    )
    def test_public_reference_prose_passes(self, text: str) -> None:
        assert _findings(text) == []

    def test_source_files_are_sanitized(self, tmp_path: Path) -> None:
        import validate

        source = tmp_path / "tests" / "test_example.py"
        source.parent.mkdir()
        source.write_text('PRIVATE = "' + "omni" + "base_internal" + '"\n')
        assert validate.check_sanitization(tmp_path)
        source.write_text('PUBLIC = "omnibase_core"\n')
        assert validate.check_sanitization(tmp_path) == []

    def test_publication_cannot_self_exempt_a_private_name(self, tmp_path: Path) -> None:
        import validate

        page = tmp_path / "README.md"
        page.write_text("omni" + "base_internal # sanitization-ok: author approved\n")
        assert validate.check_sanitization(tmp_path)

    def test_hook_command_refuses_source_fixture_then_accepts_safe_source(self, tmp_path: Path) -> None:
        import subprocess

        source = tmp_path / "tests" / "test_example.py"
        source.parent.mkdir()
        command = [sys.executable, str(_SCRIPTS_DIR / "validate.py"), "--sanitize-only", "--root", str(tmp_path)]
        source.write_text('PRIVATE = "' + "omni" + "base_internal" + '"\n')
        refused = subprocess.run(command, capture_output=True, text=True)
        assert refused.returncode == 1
        assert "Private repo name" in refused.stdout
        source.write_text('PUBLIC = "omnibase_core"\n')
        accepted = subprocess.run(command, capture_output=True, text=True)
        assert accepted.returncode == 0
        assert "Sanitization passed." in accepted.stdout

    def test_internal_fleet_runbook_is_rejected_even_with_generic_body(self, tmp_path: Path) -> None:
        import validate

        page = tmp_path / "runbooks" / ("runner-" + "fleet-listener.md")
        page.parent.mkdir()
        page.write_text("# Listener procedure\n")
        assert validate.check_sanitization(tmp_path)
        page.unlink()
        page = page.parent / "broker-recovery.md"
        page.write_text("# Broker recovery\n\nRecover your own broker.\n")
        assert validate.check_sanitization(tmp_path) == []

    @pytest.mark.parametrize("address", ["reader@example.invalid", "reader@nested.example.invalid"])
    def test_nondeliverable_example_address_passes(self, address: str) -> None:
        assert _findings(address) == []

    def test_deliverable_suffix_after_invalid_label_is_rejected(self) -> None:
        _assert_blocked_as("reader" + "@example.invalid.example.com", "Email address")
