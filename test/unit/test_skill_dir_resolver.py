#!/usr/bin/env python3
"""Tests for the rename-resilient $SKILL_DIR fallback embedded in the prompts.

The fallback lets a git-clone install resolve even when its directory still
carries a pre-v0.1.0 name. It must key off the skill's declared frontmatter
identity so an unrelated skill sharing a skills home can never be selected.
"""

import re
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_NAME = "hve-video-director"
RESOLVER_DOCS = [
    ROOT / "SKILL.md",
    ROOT / "workflows" / "phase-3-design.md",
    ROOT / "workflows" / "phase-5-audio.md",
]
MARKER = (
    '[ -f "$c/SKILL.md" ] && grep -q '
    "'^name:[[:space:]]*" + SKILL_NAME + "[[:space:]]*$' \"$c/SKILL.md\""
)

# Mirrors the fallback loop as embedded in the prompts, reduced to one home.
PROBE = textwrap.dedent(
    """
    SKILL_DIR=
    for c in "$1"/*/; do
      MARKER && { SKILL_DIR="${c%/}"; break; }
    done
    printf '%s' "$SKILL_DIR"
    """
).replace("MARKER", MARKER)


def make_skill(home: Path, dirname: str, frontmatter_name: str) -> Path:
    d = home / dirname
    (d / "workflows").mkdir(parents=True)
    (d / "scripts").mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {frontmatter_name}\ndescription: test\n---\n", encoding="utf-8"
    )
    (d / "workflows" / "phase-5-audio.md").write_text("stub\n", encoding="utf-8")
    (d / "scripts" / "check_requirements.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    return d


def resolve(home: Path) -> str:
    return subprocess.run(
        ["sh", "-c", PROBE, "sh", str(home)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


class ResolverParity(unittest.TestCase):
    def test_marker_is_identical_across_every_resolver(self):
        """All three embedded resolvers must share one byte-identical marker."""
        for doc in RESOLVER_DOCS:
            self.assertIn(
                MARKER,
                doc.read_text(encoding="utf-8"),
                f"{doc.relative_to(ROOT)} does not carry the canonical marker",
            )

    def test_frontmatter_matches_the_marker(self):
        """A drifting frontmatter name would silently disable every fallback."""
        head = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertRegex(head, rf"(?m)^name:[ \t]*{re.escape(SKILL_NAME)}[ \t]*$")

    def test_no_resolver_matches_on_layout_alone(self):
        """Layout-only matching selects unrelated skills; it must not come back."""
        for doc in RESOLVER_DOCS:
            body = doc.read_text(encoding="utf-8")
            self.assertNotIn('[ -f "$c/workflows/phase-5-audio.md" ] && {', body)


class ResolverBehaviour(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_resolves_clone_left_under_legacy_directory_name(self):
        d = make_skill(self.home, "hve-spielberg", SKILL_NAME)
        self.assertEqual(resolve(self.home), str(d))

    def test_ignores_unrelated_skill_with_identical_layout(self):
        """The exact defect review flagged: same files, different skill."""
        make_skill(self.home, "some-other-skill", "some-other-skill")
        self.assertEqual(resolve(self.home), "")

    def test_ignores_stale_clone_still_declaring_the_old_name(self):
        make_skill(self.home, "hve-spielberg", "hve-spielberg")
        self.assertEqual(resolve(self.home), "")

    def test_empty_home_yields_empty_string_not_a_literal_glob(self):
        self.assertEqual(resolve(self.home), "")

    def test_resolves_when_the_path_contains_spaces(self):
        spaced = self.home / "skills home"
        spaced.mkdir()
        d = make_skill(spaced, "hve-spielberg", SKILL_NAME)
        self.assertEqual(resolve(spaced), str(d))

    def test_prefix_collision_does_not_match(self):
        make_skill(self.home, "fork", f"{SKILL_NAME}-fork")
        self.assertEqual(resolve(self.home), "")


if __name__ == "__main__":
    unittest.main()
