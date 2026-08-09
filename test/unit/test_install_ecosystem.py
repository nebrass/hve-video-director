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
        proc = self._install(lock_for(sorted(sources)[0]))
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


if __name__ == "__main__":
    unittest.main()
