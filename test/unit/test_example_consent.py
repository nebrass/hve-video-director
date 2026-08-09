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

This is the only test that runs the real script against the real committed artifact.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXAMPLE = REPO / "example"
VALIDATOR = REPO / "scripts" / "validate_brief.py"


class ExampleConsentRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Not a skip. If `example/` or its consent record is gone, the doctrine in
        # CLAUDE.md and README that calls it a verifiable record is what needs the
        # edit -- and this failing here is what forces that into the same commit.
        assert EXAMPLE.is_dir(), "example/ is missing; the reference-build doctrine now overclaims"
        assert (EXAMPLE / ".hve" / "brief-state.json").is_file(), (
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
