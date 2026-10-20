"""Single source of forbidden private-content patterns for the public repo.

This module is intentionally dependency-free (stdlib ``re`` only) so it can be
imported by lightweight tooling — notably the commit-message / PR-text gate in
``check_text_sanitization.py``, which runs under pre-commit's own interpreter
without the project's ``pyyaml`` / ``pydantic`` dependencies.

``validate.py`` re-exports these names, so the artifact-file sanitization guard
and the commit-message / PR-text gate share exactly one list of patterns.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

# Verified public repositories that this documentation may cite. A URL naming
# any other slug remains blocked. Entries are exact names, never prefixes.
# The legacy knowledge-base spelling redirects to knowledge_base.
# Product-source visibility was checked anonymously on 2026-10-20; see
# reference/public-proof-index.md for the cited public release/source artifacts.
PUBLIC_REPO_SLUGS: tuple[str, ...] = (
    "knowledge_base",
    "knowledge-base",
    "omnibase_core",
    "omnibase_infra",
    "omnimarket",
    "omniclaude",
)

# A GitHub repository name may contain letters, digits, ``.``, ``_`` and ``-``.
# Requiring the character following an exempt slug to be OUTSIDE that set is
# what turns "starts with" into "is exactly", so a private sibling such as
# ``<public-slug>-internal`` can no longer inherit the public exemption.
# ``.git`` may trail the slug so a legitimate clone URL still passes.
_SLUG_BOUNDARY = r"(?:\.git)?(?![A-Za-z0-9._-])"

_PUBLIC_REPO_EXEMPTION = "|".join(re.escape(slug) + _SLUG_BOUNDARY for slug in PUBLIC_REPO_SLUGS)

# A private sibling slug leaks whether or not it is spelled as a URL. The live
# finding this closes is a workflow comment reading "the same checker is
# vendored in <public-slug>-internal, guarding that repo's own guide" — a bare
# slug naming a private repository, describing its contents, in a public repo.
# The URL pattern above could never see it.
# Keep the existing bare-name rule independent of the public source-URL list.
# Extending verified citations must not implicitly redefine bare-name policy.
_PRIVATE_SIBLING_SLUGS = "|".join(
    re.escape(slug) + r"-internal" + _SLUG_BOUNDARY for slug in ("knowledge_base", "knowledge-base")
)

# The private ``-internal`` / ``_internal`` repositories, in either separator.
# Spelling them as an alternation rather than a list keeps the private names
# out of this public file. ``omninode_internal`` is a database schema, not a
# repository, so the prefix set is closed rather than ``omni*``.
_PRIVATE_INTERNAL_SLUG = r"\b(?:omni(?:base|claude)|knowledge[-_]base)[-_]internal(?![A-Za-z0-9._-])"

# The hosted-cloud deployment repository is the one private platform
# repository. Naming it is allowed; describing its directory layout is not.
_PRIVATE_REPO_PATH = r"\bomninode_infra/"

# A person named in an ``owner`` or ``author`` field: a YAML or plain
# ``owner:`` line, or a bold ``**Author**`` label or table cell, whose whole
# value is one or two capitalised words other than the company name. A role or
# team slug (``docs-maintainers``) and descriptive prose
# (``**Owner**: Shared infrastructure (deployed separately)``) pass, and so does
# a table header row such as ``| Owner | Role |``.
_PERSON_VALUE = r"\s*(?!OmniNode\b)(?![A-Z][a-z]+ (?:Team|Maintainers|Group)\b)[A-Z][a-z]+(?: [A-Z][a-z]+)?\**\s*"
_PERSON_FIELD = (
    r"^[\s>*-]*(?i:owner|author)s?\s*:" + _PERSON_VALUE + r"$"
    r"|\*\*(?i:owner|author)s?\*\*\s*[:|]" + _PERSON_VALUE + r"(?:\||$)"
)

# Expletives. A public decision record restates a reason neutrally.
_PROFANITY = r"(?i)\b(?:f+u+c*k+\w*|motherf\w*|bullsh\w*|sh[i1]t(?:s|ty|ting)?\b|wtf\b|goddamn\w*)"

# Text addressed to a coding agent, telling it to act on the document. A
# visiting agent pointed at this repository reads such text as instructions.
_AGENT_DIRECTIVE = r"(?i:\bfor\s+claude\b)\**\s*:|REQUIRED SUB-SKILL|(?i:\bpass this file to\s+`/)"

# Citations of private agent-memory files, which no reader can open. A path
# segment (``.serena/memories/project_overview.md`` as a manifest source path)
# is a repository file, not a memory citation, so a preceding ``/`` exempts it.
_AGENT_MEMORY = r"(?<![/\w])(?:feedback|project)_[a-z0-9_]+\.md\b|(?i:\bproject memory\b)"

# A redaction placeholder standing in for a ticket id inside a title or a
# heading. A body sentence may still show the token to define it; a title that
# reads ``<ticket>: ...`` looks like documentation with the content cut out.
_PLACEHOLDER_IN_TITLE = r"^(?:#{1,6}\s|\s*title:).*<ticket>"

# Names the operator keeps in a file outside the repository, one per line. The
# repository cannot hold the list, so the gate reads the path from this
# environment variable when it is set (a CI secret, or a file on a developer
# machine) and refuses any line that spells a listed name as a whole word.
NAMES_FILE_ENV = "ONEX_SANITIZATION_NAMES_FILE"

SANITIZATION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Case-insensitive so a ticket id inside a branch name or slug is caught;
    # the digit requirement keeps ``omn-XXXX`` placeholders and words such as
    # ``omnibase`` out of it.
    (re.compile(r"(?i)\bOMN-\d+"), "Internal ticket reference"),
    (re.compile(r"192\.168\.\d+\.\d+"), "Internal IP address"),
    # the dotted form AND the hyphenated host-alias form. Requiring
    # a literal dot let an alias such as `<name>-201-ts` through, which is how
    # a live runbook shipped an internal lab SSH alias and an on-host state
    # path. The hyphenated arm requires a preceding LETTER so it reads a
    # hostname token rather than a numeric argument (`tail -200`) or a range
    # ("1-200 characters"), both of which occur in this repo's own prose.
    (re.compile(r"\.(200|201)\b|(?<=[A-Za-z])-(?:200|201)\b"), "Internal host reference"),
    (re.compile(rf"github\.com/OmniNode-ai/(?!{_PUBLIC_REPO_EXEMPTION})"), "Private repo URL"),
    (re.compile(rf"\b(?:{_PRIVATE_SIBLING_SLUGS})"), "Private repo name"),
    (re.compile(_PRIVATE_INTERNAL_SLUG), "Private repo name"),
    (re.compile(_PRIVATE_REPO_PATH), "Private repo path"),
    (re.compile(r"infisical", re.IGNORECASE), "Internal secrets manager reference"),
    (re.compile(_PERSON_FIELD), "Person name in owner/author field"),
    (re.compile(_PROFANITY), "Profanity"),
    (re.compile(_AGENT_DIRECTIVE), "Agent-addressed directive"),
    (re.compile(_AGENT_MEMORY), "Agent-memory citation"),
    (re.compile(r"\bomninode-runner-\d+"), "CI runner container name"),
    (re.compile(_PLACEHOLDER_IN_TITLE), "Redaction placeholder in a title or heading"),
    (re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"), "Email address pattern"),
]


@lru_cache(maxsize=4)
def _listed_names_pattern(path: str) -> re.Pattern[str] | None:
    """Compile the names file at ``path`` into one whole-word pattern, or None."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError:
        return None
    names = sorted({line.strip() for line in raw.splitlines() if line.strip() and not line.startswith("#")})
    if not names:
        return None
    return re.compile(r"(?i)(?<![A-Za-z0-9])(?:" + "|".join(re.escape(n) for n in names) + r")(?![A-Za-z0-9])")


def _active_patterns() -> list[tuple[re.Pattern[str], str]]:
    patterns = list(SANITIZATION_PATTERNS)
    names_file = os.environ.get(NAMES_FILE_ENV)
    if names_file:
        listed = _listed_names_pattern(names_file)
        if listed is not None:
            patterns.append((listed, "Listed person name"))
    return patterns


_ALLOWLIST_PATTERN = re.compile(r"#\s*sanitization-ok:\s*(.+)")


def scan_text(text: str, *, label: str = "text", honor_allowlist: bool = True) -> list[str]:
    """Scan arbitrary text for private content patterns.

    Shared single source of forbidden-pattern detection. Used both by the
    artifact-file sanitization guard (``validate.py``) and by the
    commit-message / PR-text gate (``check_text_sanitization.py``).

    Returns a list of error strings, one per offending line, prefixed with
    ``label`` and the 1-indexed line number. ``honor_allowlist`` allows a line
    carrying a ``# sanitization-ok:`` marker to suppress its own findings; the
    commit-message / PR-text gate disables it so authors cannot self-exempt
    leaked content.
    """
    errors: list[str] = []
    lines = text.splitlines()

    allowlisted_lines: set[int] = set()
    if honor_allowlist:
        for i, line in enumerate(lines, 1):
            if _ALLOWLIST_PATTERN.search(line):
                allowlisted_lines.add(i)

    patterns = _active_patterns()
    for i, line in enumerate(lines, 1):
        if i in allowlisted_lines:
            continue
        for pattern, description in patterns:
            if pattern.search(line):
                errors.append(f"{label}:{i}: {description} — matches '{pattern.pattern}'")
                break  # one error per line
    return errors
