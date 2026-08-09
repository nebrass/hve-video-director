"""`example/` claims to be the record of a real human-in-the-loop run.

That claim is the whole reason the directory is committed, and it is worth exactly as
much as its checkability. `.hve/brief-state.json` is the consent record: it binds each
phase stamp to the revision and fingerprint of the Creative Brief the user actually
approved. CLAUDE.md states the invariant in one line -- `validate_brief.py --project-dir
example status` must report complete, confirmed and unstale -- and until now nothing ran it.

Two failure modes this closes, neither visible in a diff:

- Someone edits a Creative Brief *field* in `example/project-plan.md`. The fingerprint
  moves, every phase stamp goes stale, and the directory silently stops being a record of
  anything. Note the limit, since an adversarial pass found it overstated here: the
  fingerprint covers the parsed brief table, so a comment or a prose edit elsewhere in
  that file is correctly not a change of consent — and this suite says nothing about
  whether the artifacts the record describes still exist.
- `validate_brief.py` changes shape -- a new required field, a renamed stage -- and the
  committed state file no longer parses. The validator's own unit tests all use synthetic
  fixtures, so they would stay green.

Two suites now run a real script against this real artifact: this one owns whether the
record is what it claims to be, and `test_keys_audit.py` owns what the audit says about it.
"""

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXAMPLE = REPO / "example"
VALIDATOR = REPO / "scripts" / "validate_brief.py"


# Commentary *about* the record, written by a human after the run — not output of it.
# Excluded from the digests on purpose: nobody greens a check by editing a README, and the
# record's own README is where its known defects are described.
COMMENTARY = {"README.md", ".gitignore"}

# Every artifact the run emitted, as committed. Media is gitignored.
#
# The consent record covers the parsed brief table in `project-plan.md` and nothing else —
# the storyboard is deliberately outside every fingerprint, because it describes the film
# while the brief records consent. Correct, and it leaves the record's other bytes on
# doctrine alone: swapping `capabilities: —` for a real tag in storyboard.md makes
# keys-audit report two fewer findings while `status` stays complete, confirmed and
# unstale. Verified. That edit is the cheapest way to green any check aimed at example/,
# and until this test existed nothing in the repo could see it.
#
# Regenerating these digests is NEVER the response to a red. A red means an artifact
# changed, and the only legal way one changes is a full human-in-the-loop re-run
# (CLAUDE.md; ADR-001) — in which case every digest moves at once and the replacement
# arrives with its own consent record:
#   git ls-files -z -- example | xargs -0 shasum -a 256
RECORD_DIGESTS = {
    ".hve/brief-state.json": "7809e1ec260e45e49f4ab4534ea4c4b3c0c4788bf6c068dba78ab40bfb168609",
    "CREDITS.md": "6a58a0df160309de011e5bd3fc28a7b1a48cede16ab1da25b5d7a56be07d6f09",
    "DESIGN.md": "b491bb2cfe4021e129648fc76555618ace5378d4540d897370df066826ddfdf0",
    "context.md": "32c702196587dac88530cc5b3e939257e2e1285c55569869df4d4aae5134f06f",
    "index.html": "cb1fc5ff959c7ec9c029fb63af76bb62338e7fd76e41b3766c4196e2183458c8",
    "ledger.json": "8e7bde0f9c980b457d11cd7c0289ea8c65d0d32b6c0238ede52bc4c871b9e484",
    "project-plan.md": "47611d2a9330affe53e10a05b86742faed1385c1d238e9213fe0a29a9099de69",
    "scenes/00-hook.html": "89f10a20ced463f3eaf9b04fd81e2f2fffd3a5ca348b26403bda63d1989d5b9a",
    "scenes/01-pain.html": "56033fc30549e54682f9d69c6922eacb983d8524147d5059447f167613f1bb75",
    "scenes/02-turn.html": "4a4a25c67413088ee97bcbde6a6debe7ce80207a0c0f8631352eae32c1208ab3",
    "scenes/03-reasoning.html": "7297dc1d4d515f6582005187d4e2970c8e3df4c0f6731a858049ed5934bc45d6",
    "scenes/04-stack.html": "8f16431a6a7b0cbd29c20fc9720cc50acb0b84dea7404a26c6c436d0a0ecdd4b",
    "scenes/05-hero.html": "a478a2ba2b2715e61268af3a7688bbf886631ad50a94b9ea30560150fcaf4623",
    "scenes/06-capabilities.html": "99d22933c9cfb1f0e919079d904adedd66d3130e2c5abde8b826660a9e82dd34",
    "scenes/07-cta.html": "f623cf4c2806d718ea289bc8dca9294cffca75d2bdf6e80b18f46023ccd3c463",
    "storyboard.md": "baeb82cadb8e59e0d8ed9cb260418dc0928ddac987f093101f2c8a4ce646f694",
    "voiceover.py": "17e0a55433cc90eb7ac659120743e5d67cfd5e3346ae88a99a34391167c40709",
}

REPAIR = (
    "example/ is a record. The only legal way an artifact in it changes is a full "
    "human-in-the-loop re-run with its own consent record — never an edit that makes a "
    "check pass, and never a digest regenerated to match one (CLAUDE.md; ADR-001). If the "
    "run really was replaced, every digest moves together."
)


class RecordArtifactsAreUnchangedTests(unittest.TestCase):
    """The bytes, not just the consent record.

    Without this, a finding against `example/` creates an incentive rather than a
    decision: the cheapest green is a two-word edit to the record, and the fingerprints
    cannot see it because they cover the brief and the storyboard is deliberately
    outside them.
    """

    def tracked_artifacts(self):
        try:
            done = subprocess.run(
                ["git", "-C", str(REPO), "ls-files", "-z", "--", "example"],
                capture_output=True, text=True, check=True,
            )
        except (subprocess.CalledProcessError, OSError) as error:
            raise unittest.SkipTest(f"not a git worktree: {error}")
        return {
            Path(entry).relative_to("example").as_posix()
            for entry in done.stdout.split("\0")
            if entry and Path(entry).relative_to("example").as_posix() not in COMMENTARY
        }

    def test_the_artifact_set_is_exactly_what_the_run_emitted(self):
        """A file added to example/ is a claim about what the pipeline produced."""
        self.assertEqual(set(RECORD_DIGESTS), self.tracked_artifacts(), REPAIR)

    def test_every_artifact_is_byte_for_byte_the_committed_run(self):
        for relative, want in sorted(RECORD_DIGESTS.items()):
            with self.subTest(artifact=relative):
                got = hashlib.sha256((EXAMPLE / relative).read_bytes()).hexdigest()
                self.assertEqual(want, got, f"example/{relative} was edited. {REPAIR}")


class ExampleConsentRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Not a skip. If `example/` or its consent record is gone, the doctrine in
        # CLAUDE.md and README that calls it a verifiable record is what needs the
        # edit -- and this failing here is what forces that into the same commit.
        # Plain `assert` would vanish under `python -O`, taking the guard with it.
        if not EXAMPLE.is_dir():
            raise AssertionError("example/ is missing; the reference-build doctrine now overclaims")
        if not (EXAMPLE / ".hve" / "brief-state.json").is_file():
            raise AssertionError(
                "example/.hve/brief-state.json is missing -- it is the consent record that "
                "makes the human-in-the-loop claim checkable"
            )
        cls.proc = subprocess.run(
            [sys.executable, str(VALIDATOR), "--project-dir", str(EXAMPLE), "status", "--json"],
            capture_output=True, text=True,
        )

    def test_the_validator_accepts_the_committed_record(self):
        self.assertEqual(
            0, self.proc.returncode,
            f"validate_brief.py rejected example/:\nstdout: {self.proc.stdout}\n"
            f"stderr: {self.proc.stderr}",
        )

    def _report(self):
        return json.loads(self.proc.stdout)

    def test_the_brief_is_complete_with_no_errors(self):
        report = self._report()
        self.assertTrue(report["complete"], "example/ brief is incomplete")
        self.assertEqual([], report["errors"], "example/ brief reports errors")

    def test_both_consent_fingerprints_are_confirmed(self):
        """Story and audio are separately confirmed because they stale different phases."""
        report = self._report()
        for stage in ("story", "audio"):
            with self.subTest(stage=stage):
                self.assertTrue(report[stage]["complete"], f"{stage} answers incomplete")
                self.assertTrue(
                    report[stage]["confirmed"],
                    f"{stage} fingerprint is unconfirmed -- example/ would be a record of "
                    "a run whose brief was never approved",
                )

    def test_no_phase_is_stale(self):
        report = self._report()
        self.assertIsNone(report["earliest_stale_phase"], "a phase stamp went stale")
        self.assertEqual([], report["stale_phases"])

    def test_every_phase_is_stamped_fresh_against_the_brief_it_ran_on(self):
        """A phase is fresh only when its stamped fingerprint still equals the brief's.

        This is the assertion that catches a hand-edit of example/project-plan.md.
        """
        phases = self._report()["phases"]
        self.assertEqual(
            ["phase-1", "phase-2", "phase-3", "phase-4", "phase-5"], sorted(phases),
            "example/ is not stamped through all five phases",
        )
        for name, phase in sorted(phases.items()):
            with self.subTest(phase=name):
                self.assertEqual("fresh", phase["status"])
                self.assertEqual(phase["expected_fingerprint"], phase["stamped_fingerprint"])
                self.assertEqual(phase["expected_revision"], phase["stamped_revision"])


if __name__ == "__main__":
    unittest.main()
