#!/usr/bin/env python3
"""Truth checks for the agent instruction files.

`CLAUDE.md`, `.github/copilot-instructions.md` and `AGENTS.md` tell three
different agent runtimes how this repo works. They are deliberately NOT copies
of each other — the Copilot file is a condensed, Copilot-facing rewrite, and
`AGENTS.md` is a short discovery note — so a byte-parity test would be wrong.

What they must share is *facts*. Both real drifts were false claims, not
formatting differences:

- **M0** — the Copilot file kept requiring the `lint|inspect|validate` chain
  after `check` replaced it, so a Copilot session would have run a deprecated
  gate as its release gate.
- **M6** — it still described `scripts/search_music.py` and a `gsap` companion
  skill after both were removed, pointing an agent at things that did not exist.

Neither is visible to a diff of the two files, because the *other* file was
right. So this suite checks each file against the repository itself, and
cross-checks only the handful of facts that must agree everywhere.

`SKILL.md` is in the set for the same reason: it is the orchestrator prompt —
resident in every phase — and the drift class it suffered was identical.
After M6's `search_music.py` retirement was reversed, SKILL.md went on
claiming the script did not exist while phase-5 invoked it as the default
music path; this suite never saw it because the one file every session reads
was the one file it did not cover.

Adding another instruction file? Put it in `INSTRUCTION_FILES` and the same
checks apply.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

INSTRUCTION_FILES = [
    ROOT / "CLAUDE.md",
    ROOT / ".github" / "copilot-instructions.md",
    ROOT / "AGENTS.md",
    ROOT / "SKILL.md",
]

# Directories an instruction file may reference by path. A reference into one of
# these must resolve, because the whole point of naming it is that an agent opens it.
# `example` earns its place here by having been absent once: it was omitted while
# the directory existed, so when the rebase removed it the Copilot file went on
# telling a session to run `example/voiceover.py` and nothing failed. A directory
# this repo may reference has to stay checkable across its own deletion and return —
# which is exactly when references to it go stale.
REPO_DIRS = (
    "scripts", "workflows", "patterns", "templates",
    "reasoning", "grammar", "sub-agents", "compat", "design-systems", "test",
    "example",
)

PATH_REF = re.compile(
    r"`((?:" + "|".join(REPO_DIRS) + r")/[A-Za-z0-9_./-]+)`"
)

# The ecosystem's stable skill names — the same contract `test_compat_pointers`
# pins. A companion skill named outside this set is either a typo or a skill that
# does not exist; `gsap` was the latter for two milestones.
KNOWN_SKILLS = frozenset({
    "hyperframes", "hyperframes-core", "hyperframes-animation", "hyperframes-creative",
    "hyperframes-cli", "hyperframes-registry", "hyperframes-keyframes", "media-use",
    "motion-doctrine", "seam-craft", "cut-the-curve", "oversized-cursor",
    "motion-graphics", "figma",
})

# `check` is the required final gate; these still run but are deprecated aliases.
DEPRECATED_GATES = ("inspect", "validate", "layout")


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def strip_code_fences(text):
    """Prose only. A fenced block may legitimately show a deprecated command
    while explaining that it is deprecated."""
    return re.sub(r"```.*?```", "", text, flags=re.S)


def rel(path):
    return str(path.relative_to(ROOT))


class ReferencedPathsExist(unittest.TestCase):
    """An instruction file may not send an agent to a file that is not there."""

    def test_every_referenced_repo_path_resolves(self):
        missing = []
        for path in INSTRUCTION_FILES:
            for ref in sorted(set(PATH_REF.findall(read(path)))):
                if "*" in ref or "<" in ref:
                    continue  # a glob or a placeholder, not a literal path
                if not (ROOT / ref).exists():
                    missing.append(f"{rel(path)}: `{ref}` does not exist")
        self.assertFalse(
            missing,
            "instruction files reference paths that are not in the repo — this is "
            "the M6 drift (search_music.py was described after deletion):\n  "
            + "\n  ".join(missing),
        )


class NamedSkillsExist(unittest.TestCase):
    """A companion skill named in prose must be a real ecosystem skill."""

    def test_no_unknown_companion_skill_is_named(self):
        # Matches "the `x` skill" / "`x` companion skill" — the shapes these files use.
        pattern = re.compile(r"`([a-z][a-z0-9-]{2,})`(?=\s+(?:companion\s+)?skill\b)")
        # A file may name a non-existent skill *to say it does not exist* — that
        # sentence is the fix for the M6 drift. But the exemption is evaluated
        # per LINE, never per file: judged file-wide, one correct denial anywhere
        # would exempt every wrong claim about the same skill elsewhere in it.
        # (Found by mutation-testing this suite: re-injecting the exact M6 line
        # into a file that already denied `gsap` produced a false pass.)
        # Denial vocabulary covers both "it does not exist" and "it was removed".
        # A line documenting the removal is describing history, not asserting the
        # skill is available — this rule's own entry in CLAUDE.md § Common edits is
        # exactly that shape, and tripped the check before `gone|removed` was added.
        denial = re.compile(
            r"\bno\b|not installed|does not exist|is not an? (?:ecosystem|real)"
            r"|\bgone\b|\bremoved\b|\bretired\b|\bdeleted\b",
            re.I,
        )
        unknown = []
        for path in INSTRUCTION_FILES:
            for number, line in enumerate(strip_code_fences(read(path)).splitlines(), 1):
                for name in sorted(set(pattern.findall(line))):
                    if name in KNOWN_SKILLS or name == "hve-video-director":
                        continue
                    if denial.search(line):
                        continue
                    unknown.append(f"{rel(path)}:{number}: names `{name}` as a skill")
        self.assertFalse(
            unknown,
            "instruction files name a companion skill outside the known set — this "
            "is the M6 drift (`gsap` was described as a companion skill for two "
            "milestones after it was established that none exists):\n  "
            + "\n  ".join(unknown),
        )


class GateNamesAreCurrent(unittest.TestCase):
    """`check` is the required gate; a deprecated alias may be mentioned, never required."""

    def test_no_file_requires_a_deprecated_gate(self):
        # The chain form is unambiguous: it names the gate an agent must pass.
        chain = re.compile(r"hyperframes\s+lint\s*\|\s*inspect\s*\|\s*validate")
        offenders = [
            f"{rel(p)}: requires the deprecated lint|inspect|validate chain"
            for p in INSTRUCTION_FILES
            if chain.search(read(p))
        ]
        self.assertFalse(
            offenders,
            "an instruction file still requires the chain `check` replaced — this is "
            "the M0 drift, and it points a session at a deprecated release gate:\n  "
            + "\n  ".join(offenders),
        )

    def test_a_deprecated_gate_is_only_mentioned_as_deprecated(self):
        problems = []
        for path in INSTRUCTION_FILES:
            for number, line in enumerate(strip_code_fences(read(path)).splitlines(), 1):
                for gate in DEPRECATED_GATES:
                    if f"hyperframes {gate}" not in line:
                        continue
                    if re.search(r"deprecat|alias|replaced|superseded", line, re.I):
                        continue
                    problems.append(f"{rel(path)}:{number}: `hyperframes {gate}` without saying it is deprecated")
        self.assertFalse(
            problems,
            "a deprecated gate is named as if it were current:\n  " + "\n  ".join(problems),
        )


class SharedFactsAgree(unittest.TestCase):
    """The few facts every runtime must be told identically.

    Deliberately small. These files are supposed to differ in wording, length and
    emphasis; only claims that would send one runtime down a different path belong
    here.
    """

    def _mirrors(self):
        return [p for p in (ROOT / "CLAUDE.md", ROOT / ".github" / "copilot-instructions.md") if p.exists()]

    def test_both_name_check_as_the_gate(self):
        for path in self._mirrors():
            self.assertRegex(
                read(path), r"hyperframes\s+check",
                f"{rel(path)} never names `hyperframes check`, the required final gate. "
                "Every runtime has to know which gate blocks a release.",
            )

    def test_scripts_described_are_the_scripts_that_exist(self):
        """A mirror may describe a subset, but never a script the repo lacks."""
        on_disk = {p.name for p in (ROOT / "scripts").iterdir() if p.is_file()}
        wrong = []
        for path in self._mirrors():
            named = set(re.findall(r"`scripts/([A-Za-z0-9_.-]+)`", read(path)))
            for name in sorted(named - on_disk):
                wrong.append(f"{rel(path)}: describes scripts/{name}, which does not exist")
        self.assertFalse(
            wrong,
            "a mirror describes a script the repo does not have:\n  " + "\n  ".join(wrong),
        )


def cli_bullet(path):
    """The one line each mirror uses to enumerate the `npx hyperframes` surface."""
    for line in read(path).splitlines():
        if "`npx hyperframes` CLI for" in line:
            return line
    return ""


def commands_named_in(path):
    """Commands a mirror presents as current, i.e. minus the deprecated aliases
    it names only to mark them deprecated."""
    tokens = set(re.findall(r"`([a-z][a-z-]*)`", cli_bullet(path)))
    return tokens - set(DEPRECATED_GATES)


def compat_cli_table():
    """(current, deprecated) command names from compat/ecosystem.md § CLI surface.

    That table is the owner of this vocabulary; the mirrors only restate it.
    Deprecated rows are struck through (`~~name~~`), which is how they stay
    documented without being offered.
    """
    text = read(ROOT / "compat" / "ecosystem.md")
    section = text.split("## CLI surface", 1)[-1].split("\n## ", 1)[0]
    current, deprecated = set(), set()
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        first = line.strip().strip("|").split("|")[0].strip()
        struck = re.findall(r"~~`([a-z][a-z-]*)`~~", first)
        if struck:
            deprecated.update(struck)
            continue
        plain = re.findall(r"^`([a-z][a-z-]*)`$", first)
        current.update(plain)
    return current, deprecated


class CliSurfaceIsMirroredFaithfully(unittest.TestCase):
    """The `npx hyperframes` command list is a fact, and it lives in one place.

    `compat/ecosystem.md` § CLI surface owns it. Each mirror restates a subset in
    prose, and a restatement is exactly where a rename or a retirement goes stale —
    the M0 drift was this shape. Three ways it can rot, one check each.
    """

    def _mirrors(self):
        return [
            p for p in (ROOT / "CLAUDE.md", ROOT / ".github" / "copilot-instructions.md")
            if p.exists()
        ]

    def test_the_bullet_is_findable_in_every_mirror(self):
        """Guard on the guard: if the bullet is reworded away, the two checks
        below start comparing empty sets and pass forever."""
        for path in self._mirrors():
            self.assertTrue(
                commands_named_in(path),
                f"{rel(path)}: no `npx hyperframes` CLI bullet found — the parity "
                "checks below would silently compare nothing",
            )

    def test_every_named_command_is_a_real_current_command(self):
        current, deprecated = compat_cli_table()
        self.assertTrue(current, "compat § CLI surface parsed to nothing")
        problems = []
        for path in self._mirrors():
            for name in sorted(commands_named_in(path)):
                if name in deprecated:
                    problems.append(f"{rel(path)}: offers `{name}`, a deprecated alias")
                elif name not in current:
                    problems.append(f"{rel(path)}: names `{name}`, absent from compat § CLI surface")
        self.assertFalse(
            problems,
            "a mirror names a command the CLI surface does not have:\n  " + "\n  ".join(problems),
        )

    def test_every_command_a_workflow_runs_is_listed(self):
        """The operational contract: what a session actually executes.

        A command a phase runs but the instructions never mention is a tool an
        agent has no reason to expect — and the omission is invisible in a diff
        of the two mirrors, because only one of them is wrong.
        """
        invoked = set()
        for workflow in sorted((ROOT / "workflows").glob("*.md")):
            invoked.update(re.findall(r"npx hyperframes ([a-z][a-z-]*)", read(workflow)))
        self.assertTrue(invoked, "no workflow invokes the CLI — parse broke")
        missing = []
        for path in self._mirrors():
            for name in sorted(invoked - commands_named_in(path)):
                missing.append(f"{rel(path)}: workflows run `{name}` but it is not listed")
        self.assertFalse(
            missing,
            "a mirror omits a command the phases actually run:\n  " + "\n  ".join(missing),
        )


if __name__ == "__main__":
    unittest.main()
