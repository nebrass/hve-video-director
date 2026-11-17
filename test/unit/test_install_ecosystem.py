"""`test/install_ecosystem.py` decides what code CI executes.

The provisioned job clones the ecosystem and the suite then *runs* it: the
`STORYBOARD_EXTRA_KEYS` round-trip probe imports an upstream ESM module and drives it
under node. Whatever the installer fetches, CI executes.

Everything it fetches comes from `skills-lock.json` — a file in the repo, so a PR can
change it. Point `source` at another repo and that repo's JavaScript runs in CI.

What this file can and cannot buy is worth being exact about, because the difference is
easy to overstate:

- It **cannot** stop a determined malicious fork PR. A `pull_request` run uses the PR's
  own workflow and scripts, so a hostile PR can edit this guard out. GitHub's controls
  are the defence there: fork runs get no secrets and a read-only token, and first-time
  contributors need approval. Those properties are what keep the blast radius at zero,
  and the workflow comment now says so, because the way this becomes a real breach is
  someone adding secrets or `pull_request_target` to that job without knowing.
- It **does** stop the accident, which is the likely event: a lock edit, a rename, a
  copy-paste from another project silently redirecting CI at an unrelated repo. Before
  this, any string in that field was cloned and executed without comment.

It also makes a run auditable — the installer records which commit it actually ran —
and refuses a `skillPath` that escapes the clone.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INSTALLER = REPO / "test" / "install_ecosystem.py"


def fake_repo(tmp, lock, skills=("alpha",)):
    """A throwaway repo root: a lock file plus a source tree to copy from."""
    root = tmp / "repo"
    (root / "test").mkdir(parents=True, exist_ok=True)
    (root / "skills-lock.json").write_text(json.dumps(lock), encoding="utf-8")
    source = tmp / "source"
    for name in skills:
        skill = source / ".claude" / "skills" / name
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    return root, source


def lock_for(source, skills=("alpha",), source_type="github", path_template=None):
    template = path_template or ".claude/skills/{name}/SKILL.md"
    return {
        "skills": {
            name: {
                "sourceType": source_type,
                "source": source,
                "skillPath": template.format(name=name),
            }
            for name in skills
        }
    }


class SourceAllowlistTests(unittest.TestCase):
    """Only the ecosystem's own repo may be installed — and therefore executed."""

    def setUp(self):
        self.tmp = Path(__import__("tempfile").mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))

    def _install(self, lock, skills=("alpha",)):
        root, source = fake_repo(self.tmp, lock, skills)
        installer = root / "test" / "install_ecosystem.py"
        installer.write_bytes(INSTALLER.read_bytes())
        return subprocess.run(
            [sys.executable, str(installer),
             "--dest", str(root / ".agents" / "skills"),
             "--source-dir", str(source)],
            capture_output=True, text=True,
        )

    def test_the_real_lock_only_names_allowed_sources(self):
        """The allowlist has to actually admit the ecosystem, or CI is broken."""
        lock = json.loads((REPO / "skills-lock.json").read_text(encoding="utf-8"))
        sources = {meta.get("source") for meta in lock["skills"].values()}
        self.assertTrue(sources, "the lock names no sources")
        # Every source, not just the first: checking `sorted(sources)[0]` meant a second
        # source added to the lock was never admitted by this test, and its name said
        # otherwise.
        for source in sorted(sources):
            with self.subTest(source=source):
                proc = self._install(lock_for(source))
                self.assertEqual(0, proc.returncode, proc.stderr)

    def test_an_unknown_source_is_refused_before_anything_is_fetched(self):
        proc = self._install(lock_for("attacker/evil"))
        self.assertNotEqual(0, proc.returncode, "an unlisted source was accepted")
        self.assertIn("attacker/evil", proc.stderr + proc.stdout)

    def test_the_refusal_says_why_it_matters(self):
        """A bare 'not allowed' invites deleting the check. The message has to
        carry the reason: CI executes what this installs."""
        proc = self._install(lock_for("attacker/evil"))
        message = (proc.stderr + proc.stdout).lower()
        self.assertTrue(
            "execut" in message,
            f"refusal does not explain the consequence:\n{proc.stderr}",
        )

    def test_a_skillpath_escaping_the_checkout_is_refused(self):
        """The decoy has to actually exist outside the checkout.

        A traversing path that points at nothing is already refused as 'missing',
        which would make this pass without any containment check at all. So plant
        a real SKILL.md outside the source tree: an unguarded installer copies it
        and exits 0.
        """
        decoy = self.tmp / "outside" / "alpha"
        decoy.mkdir(parents=True, exist_ok=True)
        (decoy / "SKILL.md").write_text("# planted\n", encoding="utf-8")
        lock = lock_for(
            "heygen-com/hyperframes",
            path_template="../outside/{name}/SKILL.md",
        )
        proc = self._install(lock)
        self.assertNotEqual(
            0, proc.returncode,
            "a skillPath escaping the checkout was accepted and its contents copied in",
        )

    def test_it_records_the_commit_it_installed(self):
        """The docstring claims a run is auditable afterwards. Without this, deleting the
        line that prints the resolved commit left every test green."""
        proc = self._install(lock_for("heygen-com/hyperframes"))
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertIn("heygen-com/hyperframes @", proc.stdout, proc.stdout)

    def test_a_successful_install_reports_what_it_installed(self):
        proc = self._install(lock_for("heygen-com/hyperframes", ("alpha", "beta")),
                             skills=("alpha", "beta"))
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertIn("2", proc.stdout)


def load_installer():
    """The installer as a module, for the one function a subprocess cannot reach."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("install_ecosystem", INSTALLER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PinnedInstallTests(unittest.TestCase):
    """Upstream's tip can be unusable for weeks; the pin is what stays installable.

    On 2026-10-21 upstream retired twelve of the skills `skills-lock.json` names. The
    installer only knew how to fetch the tip, so there was no way left to install an
    ecosystem this repo's registry resolves against. `--pinned` and `--ref` are that way.
    Every refusal below has to happen BEFORE a fetch: these tests run offline, and the
    lock names a real GitHub source.
    """

    def setUp(self):
        self.tmp = Path(__import__("tempfile").mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))

    def _run(self, *extra, pin=None):
        root, source = fake_repo(self.tmp, lock_for("heygen-com/hyperframes"))
        installer = root / "test" / "install_ecosystem.py"
        installer.write_bytes(INSTALLER.read_bytes())
        if pin is not None:
            (root / "compat").mkdir(parents=True, exist_ok=True)
            (root / "compat" / "ecosystem-pin.json").write_text(
                pin if isinstance(pin, str) else json.dumps(pin), encoding="utf-8"
            )
        proc = subprocess.run(
            [sys.executable, str(installer),
             "--dest", str(root / ".agents" / "skills"), *extra],
            capture_output=True, text=True, timeout=60,
        )
        return proc, source

    def test_the_committed_pin_is_a_full_commit_of_an_allowed_source(self):
        """A branch or tag name in the pin would move, and then it is not a pin."""
        installer = load_installer()
        source, ref = installer.read_pin(REPO / "compat" / "ecosystem-pin.json")
        self.assertIn(source, installer.ALLOWED_SOURCES)
        self.assertRegex(ref, r"\A[0-9a-f]{40}\Z")

    def test_the_committed_pin_names_a_source_the_lock_actually_uses(self):
        """A pin for a source the lock never installs from would pin nothing."""
        installer = load_installer()
        source, _ = installer.read_pin(REPO / "compat" / "ecosystem-pin.json")
        lock = json.loads((REPO / "skills-lock.json").read_text(encoding="utf-8"))
        self.assertIn(source, {meta.get("source") for meta in lock["skills"].values()})

    def test_a_moving_name_in_the_pin_is_refused_before_anything_is_fetched(self):
        proc, _ = self._run(
            "--pinned", pin={"source": "heygen-com/hyperframes", "ref": "main"}
        )
        self.assertEqual(2, proc.returncode, proc.stderr)
        self.assertIn("40-character commit", proc.stderr)

    def test_a_pin_for_an_unlisted_source_is_refused(self):
        proc, _ = self._run(
            "--pinned", pin={"source": "attacker/evil", "ref": "a" * 40}
        )
        self.assertEqual(2, proc.returncode, proc.stderr)
        self.assertIn("attacker/evil", proc.stderr)

    def test_a_missing_or_malformed_pin_is_reported_not_raised(self):
        cases = (
            ("missing", None),
            ("malformed", "{not json"),
            ("not an object", "[]"),
            ("source is not a string", '{"source": ["x"], "ref": "' + "a" * 40 + '"}'),
        )
        for label, pin in cases:
            with self.subTest(pin=label):
                proc, _ = self._run("--pinned", pin=pin)
                self.assertEqual(2, proc.returncode, proc.stderr)
                self.assertIn("ecosystem-pin.json", proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)

    def test_a_ref_that_git_would_read_as_an_option_is_refused(self):
        """`--ref` reaches git's argv; a leading dash there is an option, not a name."""
        for ref in ("--upload-pack=touch pwned", "-x", "a..b", "a b", ""):
            with self.subTest(ref=ref):
                proc, _ = self._run(f"--ref={ref}")
                self.assertEqual(2, proc.returncode, proc.stderr)
                self.assertIn("refusing --ref", proc.stderr)

    def test_a_checkout_on_disk_cannot_also_be_given_a_ref(self):
        """`--source-dir` is copied as it is; pretending to pin it would be a lie."""
        for flag in (("--ref", "v1"), ("--pinned",)):
            with self.subTest(flag=flag[0]):
                root, source = fake_repo(self.tmp, lock_for("heygen-com/hyperframes"))
                installer = root / "test" / "install_ecosystem.py"
                installer.write_bytes(INSTALLER.read_bytes())
                proc = subprocess.run(
                    [sys.executable, str(installer),
                     "--dest", str(root / ".agents" / "skills"),
                     "--source-dir", str(source), *flag],
                    capture_output=True, text=True, timeout=60,
                )
                self.assertEqual(2, proc.returncode, proc.stderr)
                self.assertIn("--source-dir", proc.stderr)

    def test_ref_and_pinned_are_mutually_exclusive(self):
        proc, _ = self._run("--pinned", "--ref", "v1")
        self.assertEqual(2, proc.returncode)
        self.assertIn("not allowed with", proc.stderr)

    @unittest.skipUnless(
        __import__("shutil").which("git"), "git is not on PATH"
    )
    def test_a_ref_installs_that_commit_and_not_the_tip(self):
        """The whole point: the skill the tip deleted is still there at the ref."""
        upstream = self.tmp / "upstream"
        skill = upstream / "skills" / "alpha"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("# alpha\n", encoding="utf-8")

        def git(*args):
            return subprocess.run(
                ["git", "-C", str(upstream),
                 "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", *args],
                capture_output=True, text=True, check=True,
            ).stdout.strip()

        git("init", "--quiet")
        # GitHub serves any reachable commit by id; a bare local repo needs telling.
        git("config", "uploadpack.allowAnySHA1InWant", "true")
        git("add", "-A")
        git("commit", "--quiet", "--no-verify", "-m", "skill present")
        before = git("rev-parse", "HEAD")
        (skill / "SKILL.md").unlink()
        git("add", "-A")
        git("commit", "--quiet", "--no-verify", "-m", "skill retired")

        installer = load_installer()
        at_ref, at_tip = self.tmp / "at-ref", self.tmp / "at-tip"
        installer.checkout(upstream.as_uri(), at_ref, ref=before)
        installer.checkout(upstream.as_uri(), at_tip)

        self.assertTrue((at_ref / "skills" / "alpha" / "SKILL.md").is_file())
        self.assertFalse((at_tip / "skills" / "alpha" / "SKILL.md").exists())
        self.assertEqual(before, installer.resolved_commit(at_ref))


if __name__ == "__main__":
    unittest.main()
