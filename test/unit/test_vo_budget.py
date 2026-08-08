#!/usr/bin/env python3
"""The narration-fit estimate must catch a film whose approved VO cannot be spoken.

Phase 1 accepts each frame's `voiceover` line and its `duration` in the same pass,
but nothing compares how long the line takes to SPEAK against the slot it has. On a
real 40-frame / 540s run the accepted narration measured 619.4s — 147s of overrun
across 34 frames — and was only discovered in Phase 5, after TTS had been paid for.

Two properties are pinned here, and they are different in kind:

  * The FILM-WIDE TOTAL is the alarm. Per-line estimates carry real uncertainty, but
    per-line errors are independent and average out, so the total is the number worth
    trusting. One Phase-1 line reading "~600s of narration for a 540s film" would have
    caught the reported issue outright.
  * The PER-FRAME TIER is triage. It says where to cut, and it is graded so a
    borderline line costs a glance rather than a bad edit.

The estimator is validated against `example/`, which is a committed end-to-end run
narrated by the same voice as the calibration data. Its Phase-1 storyboard and its
Phase-5 `voiceover.py` disagree on exactly two frames — frames 2 and 7 were shortened
between approval and synthesis. That disagreement is a real, in-repo instance of this
bug, and it is the only labelled data available.
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_validate_brief import ProjectCase, load_module  # noqa: E402

VB = load_module()
ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "example"


def storyboard_with(frames):
    """Build an official-shape storyboard from (duration_s, voiceover) pairs."""
    out = ["---", "format: 1920x1080", f"duration: {sum(d for d, _ in frames)}s", "---", ""]
    for i, (dur, vo) in enumerate(frames, 1):
        out += [f"## Frame {i} — Frame {i}", ""]
        out.append(f"- duration: {dur}s")
        if vo is not None:
            out.append(f'- voiceover: "{vo}"')
        out += ["", f"Narrative for frame {i}.", ""]
    return "\n".join(out) + "\n"


class SyllableEstimator(unittest.TestCase):
    """The estimate keys off syllables, because words are not the unit of speech."""

    def test_syllable_count_is_exact_on_unambiguous_words(self):
        """Words a vowel-group heuristic can get right, and must."""
        for word, expected in [
            ("the", 1), ("agent", 2), ("video", 3), ("orchestrator", 4),
            ("approval", 3), ("make", 1), ("changelog", 3), ("a", 1),
        ]:
            with self.subTest(word=word):
                self.assertEqual(VB.count_syllables(word), expected)

    def test_syllable_count_is_accurate_in_aggregate(self):
        """The estimator needs corpus accuracy, not per-word perfection.

        A stdlib vowel-group counter cannot resolve every English word — a compound
        with an internal silent e ("pipeline") reads as three. That is tolerable
        because the estimate is consumed as a per-frame band and a film-wide total,
        both of which average such errors out. What is NOT tolerable is systematic
        drift, so the aggregate is pinned here.
        """
        truth = {
            "the": 1, "agent": 2, "pipeline": 2, "video": 3, "orchestrator": 4,
            "approval": 3, "make": 1, "changelog": 3, "narration": 3, "scene": 1,
            "storyboard": 3, "capture": 2, "design": 2, "production": 3, "audio": 3,
        }
        got = sum(VB.count_syllables(w) for w in truth)
        want = sum(truth.values())
        self.assertLess(
            abs(got - want) / want, 0.10,
            f"counted {got} syllables against a true {want} — aggregate drift "
            "would bias every estimate in the same direction",
        )

    def test_equal_word_counts_can_differ_in_estimate(self):
        """A word-rate model cannot tell these apart; speech plainly does."""
        short = "The cat sat on a mat and had a nap by the door"          # 13 monosyllables
        dense = "Extraordinary infrastructure orchestrates deployment"      # 4 dense words
        self.assertGreater(VB.estimate_speech_seconds(dense) * 3,
                           VB.estimate_speech_seconds(short),
                           "syllable density must move the estimate")

    def test_empty_and_missing_narration_cost_nothing(self):
        self.assertEqual(VB.estimate_speech_seconds(""), 0.0)
        self.assertEqual(VB.estimate_speech_seconds(None), 0.0)


class LabelledExampleRun(unittest.TestCase):
    """Validated against the only real labelled data in the repo.

    `example/storyboard.md` holds narration approved in Phase 1; `example/voiceover.py`
    holds what was actually synthesized. Frames 2 and 7 were shortened between the two.
    A useful estimator flags those and does not cry wolf across the whole film.
    """

    @classmethod
    def setUpClass(cls):
        if not (EXAMPLE / "storyboard.md").exists():
            raise unittest.SkipTest("example/ reference build is absent")
        sb = (EXAMPLE / "storyboard.md").read_text(encoding="utf-8")
        cls.vo = [m.strip().strip('"') for m in re.findall(r"^- voiceover:\s*(.+)$", sb, re.M)]
        cls.dur = [float(d) for d in re.findall(r"^- duration:\s*([\d.]+)s", sb, re.M)]

    def test_the_two_rewritten_frames_are_the_ones_flagged_over(self):
        over = {
            i for i, (vo, slot) in enumerate(zip(self.vo, self.dur), 1)
            if VB.estimate_speech_seconds(vo) > slot
        }
        self.assertEqual(
            over, {2, 7},
            "frames 2 and 7 are the two the real run shortened between Phase 1 and "
            f"Phase 5; the estimator flagged {sorted(over)}",
        )

    def test_the_film_wide_total_is_close_to_the_declared_duration(self):
        total = sum(VB.estimate_speech_seconds(v) for v in self.vo)
        film = sum(self.dur)
        self.assertLess(
            abs(total - film) / film, 0.20,
            f"estimated {total:.1f}s against a {film:.0f}s film — the total is the "
            "number the alarm rests on, so it must not drift",
        )


class VoBudgetCommand(ProjectCase):
    """The subcommand reports; it never blocks and never rewrites."""

    def test_a_film_that_cannot_be_spoken_is_reported_with_a_total(self):
        # 5s slots against lines that plainly cannot be said in 5s.
        long_line = ("Extraordinary infrastructure orchestrates deployment "
                     "continuously, reliably, and observably across every region.")
        self.write_storyboard(storyboard_with([(5, long_line)] * 4))
        result, payload = self.json_cli("vo-budget")
        self.assertEqual(result.returncode, 1, "an OVER frame exits 1")
        self.assertEqual(payload["over_count"], 4)
        self.assertGreater(payload["estimated_total_seconds"], payload["film_seconds"])
        self.assertIn("message", payload, "emit() falls back to brief status without it")
        for frame in payload["frames"]:
            self.assertEqual(frame["tier"], "OVER")
            self.assertIn("estimate_low_seconds", frame)
            self.assertIn("estimate_high_seconds", frame)

    def test_a_film_that_fits_is_clean_and_exits_zero(self):
        self.write_storyboard(storyboard_with([(12, "A short line."), (12, "Another one.")]))
        result, payload = self.json_cli("vo-budget")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["over_count"], 0)
        self.assertTrue(all(f["tier"] in ("OK", "TAIL", "TIGHT") for f in payload["frames"]))

    def test_a_silent_frame_is_skipped_not_failed(self):
        """`voiceover` is optional upstream; a connective beat legitimately has none."""
        self.write_storyboard(storyboard_with([(6, None), (10, "Spoken here.")]))
        result, payload = self.json_cli("vo-budget")
        self.assertEqual(result.returncode, 0)
        silent = payload["frames"][0]
        self.assertEqual(silent["tier"], "SILENT")
        self.assertEqual(silent["estimate_seconds"], 0.0)

    def test_a_frame_without_a_duration_is_unmeasurable_not_fitting(self):
        self.write_storyboard(
            "---\nformat: 1920x1080\n---\n\n"
            '## Frame 1 — No slot\n\n- voiceover: "Some narration here."\n\nProse.\n'
        )
        result, payload = self.json_cli("vo-budget")
        self.assertEqual(payload["frames"][0]["tier"], "UNMEASURABLE")
        self.assertEqual(result.returncode, 0, "unmeasurable is not an overrun")

    def test_a_missing_storyboard_is_reported_not_invented(self):
        result, payload = self.json_cli("vo-budget")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no storyboard.md", payload["errors"][0])

    def test_it_writes_nothing(self):
        """Report-only: no state, no storyboard edit. The brief records consent; this does not."""
        self.write_storyboard(storyboard_with([(3, "A line that will not fit in three.")]))
        state = self.project / ".hve" / "brief-state.json"
        before = state.read_bytes() if state.exists() else None
        sb_before = (self.project / "storyboard.md").read_bytes()
        self.json_cli("vo-budget")
        after = state.read_bytes() if state.exists() else None
        self.assertEqual(before, after, "vo-budget must not touch the consent record")
        self.assertEqual(sb_before, (self.project / "storyboard.md").read_bytes(),
                         "vo-budget must never rewrite narration the user approved")


class VoBudgetIsNotAGate(unittest.TestCase):
    """Exit 1 is a signal to present, never a blocker.

    ADR-001's override clause is categorical: never infer, never overrule. Making a
    narration verdict block Phase 1 would override narration the user explicitly
    approved, which is an ADR-001 amendment rather than a bugfix.
    """

    def test_vo_budget_is_not_a_require_target(self):
        source = (ROOT / "scripts" / "validate_brief.py").read_text(encoding="utf-8")
        require = re.search(r'"require".*?\)\n', source, re.S)
        if require is None:
            self.fail("could not locate the require subcommand registration")
        self.assertNotIn("vo-budget", require.group(0))

    def test_stamp_does_not_consult_the_narration_estimate(self):
        source = (ROOT / "scripts" / "validate_brief.py").read_text(encoding="utf-8")
        body = source[source.index("def command_stamp"):]
        body = body[: body.index("\ndef ")]
        for name in ("estimate_speech_seconds", "vo_budget_payload", "count_syllables"):
            self.assertNotIn(name, body, "phase freshness must not depend on narration")


if __name__ == "__main__":
    unittest.main()
