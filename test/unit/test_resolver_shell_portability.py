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

from shell_helpers import native_path, shell_executable, shell_path

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


def the_guard():
    """The single guard spelling, read from every SKILL_HOMES block."""
    guards = set()
    for doc in {d for d, _, _ in RESOLVERS}:
        text = doc.read_text(encoding="utf-8")
        for block in re.findall(r"```bash\n(.*?)```", text, re.S):
            if "SKILL_HOMES=" in block:
                guards.update(
                    line.strip()
                    for line in re.findall(r"^.*ZSH_VERSION.*$", block, re.M)
                )
    if len(guards) != 1:
        raise AssertionError(f"guard spellings diverged: {sorted(guards)}")
    return guards.pop()


def available_shells():
    return [s for s in ("zsh", "bash", "dash", "sh") if shutil.which(s)]


class ResolverShellPortability(unittest.TestCase):
    """Each embedded resolver resolves in every shell an agent might hand it."""

    def _run(self, shell: str, doc: Path, var: str, skill: str, *,
             location="global", nested_source=False) -> tuple:
        block = extract_block(doc, var)
        with tempfile.TemporaryDirectory() as td:
            fake_home = Path(td) / "home dir with spaces"  # paths may contain spaces
            fake_home.mkdir()
            cwd = Path(td) / "video output"
            cwd.mkdir()
            source = None
            if location in {"source", "both"}:
                source = Path(td) / "source project"
                source.mkdir()
                expected = make_skill(source / ".github" / "skills", skill)
                if nested_source:
                    subprocess.run(
                        ["git", "init", "--quiet", str(source)],
                        capture_output=True, text=True, check=True,
                    )
                    source = source / "packages" / "feature"
                    source.mkdir(parents=True)
            if location in {"global", "both"}:
                expected = make_skill(fake_home / FIXTURE_HOME_SUFFIX, skill)

            # The blocks legitimately run other commands (`node --version`), so the
            # resolved value is fenced by a sentinel rather than read off raw stdout.
            script = Path(td) / "probe.sh"
            script.write_text(
                block + f'\nprintf "\\n__RESOLVED__%s__END__" "${var}"\n'
                + 'printf "\\n__CWD__%s__END__" "$(pwd -P)"\n',
                encoding="utf-8", newline="\n",
            )

            env = dict(os.environ, HOME=shell_path(fake_home, shell))
            env.pop("ZSH_VERSION", None)  # never inherit; each shell sets its own
            env.pop("SOURCE_DIR", None)
            if source is not None:
                env["SOURCE_DIR"] = shell_path(source, shell)
            proc = subprocess.run(
                [shell_executable(shell), script.as_posix()],
                capture_output=True,
                encoding="utf-8",
                cwd=cwd,
                env=env,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"{shell} aborted on {doc.name}:{var}\nstderr: {proc.stderr}",
            )
            m = re.search(r"__RESOLVED__(.*?)__END__", proc.stdout, re.S)
            if m is None:
                self.fail(f"{shell} produced no sentinel for {doc.name}:{var}")
            resolved = native_path(m.group(1), shell)
            self.assertTrue(resolved.is_absolute(), m.group(1))
            after = re.search(r"__CWD__(.*?)__END__", proc.stdout, re.S)
            self.assertIsNotNone(after, proc.stdout)
            self.assertEqual(native_path(after.group(1), shell).resolve(), cwd.resolve())
            return str(resolved.resolve()), str(expected.resolve())

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

    def test_source_local_install_resolves_from_sibling_output(self):
        for shell in available_shells():
            for doc, var, skill in RESOLVERS:
                with self.subTest(shell=shell, doc=doc.name, var=var):
                    got, expected = self._run(
                        shell, doc, var, skill, location="source",
                    )
                    self.assertEqual(got, expected)
                    self.assertTrue(Path(got).is_absolute())

    def test_source_git_root_install_resolves_from_package_directory(self):
        for doc, var, skill in RESOLVERS:
            with self.subTest(doc=doc.name, var=var):
                got, expected = self._run(
                    "bash", doc, var, skill, location="source", nested_source=True,
                )
                self.assertEqual(got, expected)

    def test_global_home_precedence_is_unchanged(self):
        for doc, var, skill in RESOLVERS:
            with self.subTest(doc=doc.name, var=var):
                got, expected = self._run("bash", doc, var, skill, location="both")
                self.assertEqual(got, expected)

    def test_explicit_missing_source_is_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as td:
            env = dict(
                os.environ, HOME=shell_path(td),
                SOURCE_DIR=shell_path(Path(td) / "missing-source"),
            )
            env.pop("ZSH_VERSION", None)
            for doc, var, _ in RESOLVERS:
                with self.subTest(doc=doc.name, var=var):
                    proc = subprocess.run(
                        [shell_executable()], input=extract_block(doc, var), cwd=td,
                        env=env, encoding="utf-8", capture_output=True,
                    )
                    self.assertEqual(proc.returncode, 2)
                    self.assertIn("missing-source", proc.stderr)

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
        """Every fenced block that defines SKILL_HOMES carries the same guard.

        Keyed off the SKILL_HOMES definition, not off a result variable. The
        canonical block in SKILL.md § Runtime Compatibility assigns nothing — it is
        the template resolvers are copied from — so a check that only visited blocks
        with a `VAR=` assignment would let its guard be removed while staying green,
        and the next resolver written from it would reintroduce the bug.
        """
        guards = set()
        blocks = 0
        for doc in {d for d, _, _ in RESOLVERS}:
            text = doc.read_text(encoding="utf-8")
            for block in re.findall(r"```bash\n(.*?)```", text, re.S):
                if "SKILL_HOMES=" not in block:
                    continue
                blocks += 1
                found = re.findall(r"^.*ZSH_VERSION.*$", block, re.M)
                self.assertTrue(
                    found,
                    f"a SKILL_HOMES block in {doc.name} has no zsh portability guard",
                )
                guards.update(line.strip() for line in found)
        self.assertEqual(
            blocks, 6, f"expected 6 markdown SKILL_HOMES blocks, found {blocks}"
        )
        self.assertEqual(
            len(guards), 1, f"guard spellings diverged: {sorted(guards)}"
        )

    def test_guard_enables_both_options(self):
        """`shwordsplit` alone still dies on the first missing home."""
        guard = the_guard()
        self.assertIn("shwordsplit", guard)
        self.assertIn("nullglob", guard)

    def test_guard_tolerates_set_u(self):
        """check_requirements.sh runs under `set -u`; a bare $ZSH_VERSION is fatal there."""
        self.assertIn("${ZSH_VERSION:-}", the_guard(), "guard must default the variable")

    def test_only_relative_homes_are_prefixed_with_the_source(self):
        for doc in {d for d, _, _ in RESOLVERS}:
            cases = re.findall(
                r'^[ \t]*(case "\$(h|home)" in .* esac)$',
                doc.read_text(encoding="utf-8"), re.M,
            )
            self.assertTrue(cases, doc)
            for clause, variable in cases:
                for shell in available_shells():
                    for value in ("/skills", "C:/skills", r"D:\skills", "relative skills"):
                        with self.subTest(doc=doc.name, shell=shell, value=value):
                            script = (
                                f'{variable}="$1"\nSKILL_SEARCH_DIR=/source\n'
                                + clause + f'\nprintf "%s" "${variable}"\n'
                            )
                            result = subprocess.run(
                                [shell_executable(shell), "-s", "--", value],
                                input=script.encode("utf-8"),
                                capture_output=True, check=True,
                            )
                            expected = "/source/" + value if value == "relative skills" else value
                            self.assertEqual(result.stdout.decode("utf-8"), expected)


if __name__ == "__main__":
    unittest.main()
