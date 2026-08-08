#!/usr/bin/env python3
"""The embedded $SKILL_HOMES resolvers must resolve under every shell an agent may use.

The resolver blocks are prompt text: an agent copies them into whatever shell its
Bash tool provides. That is zsh on macOS Claude Code, bash on most Linux runtimes,
and dash wherever /bin/sh is not bash. The same characters have to work in all of
them, which two zsh defaults quietly break:

  * `shwordsplit` is OFF, so unquoted `$SKILL_HOMES` under `IFS='|'` is ONE word.
    The loop runs once, matches nothing, and the resolver returns empty.
  * `nomatch` is ON, so an unmatched `"$home"/*/` is a FATAL error rather than an
    empty list. `$SKILL_HOMES` lists 21 candidate homes and most never exist, so a
    splitting-only fix still dies at the first missing home.

Both produce the same visible symptom — an empty resolver — which the workflows read
as "the companion skill is not installed" and quietly degrade on.

This test executes the blocks **as written in the markdown** rather than a retyped
reduction. `test_skill_dir_resolver.py` retypes a one-home probe and runs it under
`sh`, which is why it exercised a resolver every run and still never saw this.
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Every markdown block that defines SKILL_HOMES and iterates it, with the skill each
# one looks for and the variable it leaves the answer in.
RESOLVERS = [
    (ROOT / "SKILL.md", "SKILL_DIR", "hve-video-director"),
    (ROOT / "workflows" / "phase-3-design.md", "SKILL_DIR", "hve-video-director"),
    (ROOT / "workflows" / "phase-4-production.md", "DOCTRINE_SKILL_DIR", "motion-doctrine"),
    (ROOT / "workflows" / "phase-4-production.md", "ANIM_SKILL_DIR", "hyperframes-animation"),
    (ROOT / "workflows" / "phase-5-audio.md", "SKILL_DIR", "hve-video-director"),
    (ROOT / "workflows" / "phase-5-audio.md", "MEDIA_SKILL_DIR", "media-use"),
]

# The home the fixture installs into. Deliberately NOT the first entry of
# $SKILL_HOMES: the earlier entries must be absent so the block has to survive
# both a missing home (nomatch) and a real split (shwordsplit) to reach it.
FIXTURE_HOME_SUFFIX = Path(".agents") / "skills"


def extract_block(doc: Path, var: str) -> str:
    """Return the fenced bash block in `doc` that assigns `var` from SKILL_HOMES."""
    text = doc.read_text(encoding="utf-8")
    for block in re.findall(r"```bash\n(.*?)```", text, re.S):
        if "SKILL_HOMES=" in block and re.search(rf"^{var}=", block, re.M):
            return block
    raise AssertionError(f"no SKILL_HOMES block assigning {var} in {doc}")


def make_skill(home: Path, name: str) -> Path:
    """Install a minimal but identity-valid skill so every resolver shape matches."""
    d = home / name
    (d / "scripts").mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: fixture\n---\n", encoding="utf-8"
    )
    # SKILL.md's fast path keys off this file; the others key off the directory.
    (d / "scripts" / "check_requirements.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    return d


def available_shells():
    return [s for s in ("zsh", "bash", "dash", "sh") if shutil.which(s)]


class ResolverShellPortability(unittest.TestCase):
    """Each embedded resolver resolves in every shell an agent might hand it."""

    def _run(self, shell: str, doc: Path, var: str, skill: str) -> tuple:
        block = extract_block(doc, var)
        with tempfile.TemporaryDirectory() as td:
            fake_home = Path(td) / "home dir with spaces"  # paths may contain spaces
            skills_home = fake_home / FIXTURE_HOME_SUFFIX
            skills_home.mkdir(parents=True)
            expected = make_skill(skills_home, skill)

            # The blocks legitimately run other commands (`node --version`), so the
            # resolved value is fenced by a sentinel rather than read off raw stdout.
            script = Path(td) / "probe.sh"
            script.write_text(
                block + f'\nprintf "\\n__RESOLVED__%s__END__" "${var}"\n',
                encoding="utf-8",
            )

            env = dict(os.environ, HOME=str(fake_home))
            env.pop("ZSH_VERSION", None)  # never inherit; each shell sets its own
            proc = subprocess.run(
                [shell, str(script)],
                capture_output=True,
                text=True,
                cwd=td,  # not a git repo, so SKILL_ROOT falls back to pwd
                env=env,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"{shell} aborted on {doc.name}:{var}\nstderr: {proc.stderr}",
            )
            m = re.search(r"__RESOLVED__(.*)__END__", proc.stdout, re.S)
            if m is None:
                self.fail(f"{shell} produced no sentinel for {doc.name}:{var}")
            return m.group(1), str(expected)

    def test_every_resolver_resolves_in_every_shell(self):
        shells = available_shells()
        self.assertIn("bash", shells, "bash is required to run this suite meaningfully")
        for shell in shells:
            for doc, var, skill in RESOLVERS:
                with self.subTest(shell=shell, doc=doc.name, var=var):
                    got, expected = self._run(shell, doc, var, skill)
                    self.assertEqual(
                        got,
                        expected,
                        f"{var} in {doc.name} resolved to {got!r} under {shell}; "
                        f"expected {expected!r}. An empty value is the silent-degrade "
                        f"failure: the workflow reads it as 'skill not installed'.",
                    )

    def test_zsh_is_actually_exercised(self):
        """Guard against the coverage gap that let this ship.

        The suite must not report success on this class of bug merely because zsh
        was absent. Skip loudly rather than pass silently.
        """
        if not shutil.which("zsh"):
            self.skipTest("zsh not installed; the regression this pins is zsh-specific")
        self.assertIn("zsh", available_shells())


class ResolverGuardIsUniform(unittest.TestCase):
    """The portability guard must be identical everywhere, like SKILL_HOMES itself.

    Two spellings of the same guard is how these blocks drift apart, and a resolver
    that is fixed in four files and missed in two fails exactly where it is hardest
    to notice.
    """

    def test_guard_present_and_byte_identical(self):
        guards = set()
        for doc, var, _ in RESOLVERS:
            block = extract_block(doc, var)
            found = re.findall(r"^.*ZSH_VERSION.*$", block, re.M)
            self.assertTrue(
                found, f"{doc.name}:{var} has no zsh portability guard"
            )
            guards.update(line.strip() for line in found)
        self.assertEqual(
            len(guards), 1, f"guard spellings diverged: {sorted(guards)}"
        )

    def test_guard_enables_both_options(self):
        """`shwordsplit` alone still dies on the first missing home."""
        guard = next(iter({
            line.strip()
            for doc, var, _ in RESOLVERS
            for line in re.findall(r"^.*ZSH_VERSION.*$", extract_block(doc, var), re.M)
        }))
        self.assertIn("shwordsplit", guard)
        self.assertIn("nullglob", guard)

    def test_guard_tolerates_set_u(self):
        """check_requirements.sh runs under `set -u`; a bare $ZSH_VERSION is fatal there."""
        guard = next(iter({
            line.strip()
            for doc, var, _ in RESOLVERS
            for line in re.findall(r"^.*ZSH_VERSION.*$", extract_block(doc, var), re.M)
        }))
        self.assertIn("${ZSH_VERSION:-}", guard, "guard must default the variable")


if __name__ == "__main__":
    unittest.main()
