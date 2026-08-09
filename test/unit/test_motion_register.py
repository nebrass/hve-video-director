"""`motion_register.py` — does a scene's motion express more than one emotion?

The measurement behind it: across a real 60-second film, 56 tweens, every one a
decelerate-only curve. One scene set `var EASE = "expo.out"` and used it for nine
entrances at near-identical durations. `patterns/anti-slop.md` names that tell -- "same
ease + same duration = same emotion every time, which is no emotion" -- and `lint`,
`check`, the seam gate and `ANIMATION_MAP` all passed it green, because none of them is
looking for character.

Two properties matter more than the parsing, and both are tested here:

- **It is a report, not a gate.** A scene built from one repeated element -- a list
  revealing in stagger -- looks monotonous by this measure and is right. Exit 1 marks a
  finding for a human.
- **It is not a second `ANIMATION_MAP`.** ADR-003 forbids a parallel validator, so it
  reports no pacing verdict: no fast, no slow, no collision, no dead zone.

The end-to-end case is the committed reference build, where the tool has to reach the same
conclusion a motion designer did by eye: `06-capabilities.html` monotonous, `07-cta.html`
-- the scene they called the best-timed in the film -- varied.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "scripts" / "motion_register.py"
EXAMPLE_SCENES = REPO / "example" / "scenes"


def run(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True, text=True, cwd=str(cwd) if cwd else None,
    )


def scene(*tweens, prelude=""):
    body = "\n".join(tweens)
    return f"""<template><div data-composition-id="s"></div>
<script>
{prelude}
const tl = gsap.timeline({{paused:true}});
{body}
window.__timelines["s"] = tl;
</script></template>
"""


def tween(ease, duration, target=".x"):
    return f'tl.to("{target}", {{ y: 0, duration: {duration}, ease: "{ease}" }}, 0);'


class MotionRegisterTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.scenes = self.dir / "scenes"
        self.scenes.mkdir()
        self.addCleanup(lambda: __import__("shutil").rmtree(self.dir, ignore_errors=True))

    def write(self, name, text):
        (self.scenes / name).write_text(text, encoding="utf-8")

    def audit(self):
        proc = run("--json", cwd=self.dir)
        return proc, json.loads(proc.stdout) if proc.stdout.strip() else {}

    def test_a_varied_scene_reports_nothing(self):
        self.write("00-a.html", scene(
            tween("expo.out", 0.8), tween("power2.inOut", 1.4),
            tween("power1.in", 0.35), tween("power2.out", 2.1),
            tween("none", 0.5),
        ))
        proc, payload = self.audit()
        self.assertEqual(0, proc.returncode, proc.stdout)
        self.assertEqual(0, payload["finding_count"], payload["scenes"])

    def test_one_ease_across_near_identical_durations_is_reported(self):
        self.write("00-a.html", scene(*[tween("expo.out", 0.8 + i * 0.02) for i in range(9)]))
        proc, payload = self.audit()
        self.assertEqual(1, proc.returncode)
        self.assertIn("expo.out", json.dumps(payload["scenes"]))

    def test_an_ease_held_in_a_constant_is_resolved(self):
        """The measured failure form: `var EASE = "expo.out"` reused everywhere. Reading
        the literal only would miss precisely the case this tool was built for."""
        self.write("00-a.html", scene(
            *[f'tl.to(".x", {{ y: 0, duration: {0.8 + i * 0.01}, ease: EASE }}, 0);' for i in range(8)],
            prelude='var EASE = "expo.out";',
        ))
        _, payload = self.audit()
        self.assertEqual(1, payload["finding_count"], payload["scenes"])
        self.assertIn("expo.out", json.dumps(payload["scenes"]))

    def test_the_same_ease_across_a_wide_duration_spread_is_not_a_finding(self):
        """One family used deliberately across events of different weight is a register,
        not monotony. Flagging it would make the report noise."""
        self.write("00-a.html", scene(
            tween("power2.out", 0.3), tween("power2.out", 0.9),
            tween("power2.out", 1.8), tween("power2.out", 3.2),
            tween("power2.out", 2.4),
        ))
        _, payload = self.audit()
        self.assertEqual(0, payload["finding_count"], payload["scenes"])

    def test_a_small_scene_is_not_judged(self):
        self.write("00-a.html", scene(tween("expo.out", 0.8), tween("expo.out", 0.8)))
        _, payload = self.audit()
        self.assertEqual(0, payload["finding_count"])
        self.assertIn("too few", json.dumps(payload["scenes"]))

    def test_a_set_call_is_not_a_tween(self):
        """`gsap.set` has no duration and no character; counting it would skew the share."""
        self.write("00-a.html", scene(
            'gsap.set(".x", { opacity: 0 });',
            tween("expo.out", 0.8), tween("power2.inOut", 1.6),
            tween("power1.out", 0.4), tween("none", 2.0),
        ))
        _, payload = self.audit()
        self.assertEqual(5, payload["scenes"][0]["tween_count"] + 1, payload["scenes"])

    # ---- the two properties that keep it legal ----

    def test_it_reports_rather_than_gates(self):
        self.write("00-a.html", scene(*[tween("expo.out", 0.8) for _ in range(6)]))
        proc = run(cwd=self.dir)
        self.assertEqual(1, proc.returncode)
        self.assertRegex(proc.stdout, r"report|blocks? a phase")

    def test_it_reports_no_pacing_verdict(self):
        """ADR-003: ANIMATION_MAP owns pacing. A second opinion on it would be the
        parallel validator that record forbids."""
        self.write("00-a.html", scene(*[tween("expo.out", 0.8) for _ in range(6)]))
        _, payload = self.audit()
        blob = json.dumps(payload).lower()
        for owned in ("paced-fast", "paced-slow", "collision", "dead zone", "dead-zone"):
            self.assertNotIn(owned, blob, f"reports {owned}, which ANIMATION_MAP owns")

    def test_it_writes_nothing(self):
        self.write("00-a.html", scene(*[tween("expo.out", 0.8) for _ in range(6)]))
        before = {p.name: p.read_bytes() for p in self.dir.rglob("*") if p.is_file()}
        run("--json", cwd=self.dir)
        after = {p.name: p.read_bytes() for p in self.dir.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_a_missing_scene_is_a_usage_error_not_a_finding(self):
        proc = run("scenes/nope.html", "--json", cwd=self.dir)
        self.assertEqual(2, proc.returncode)


class AgainstTheReferenceBuildTests(unittest.TestCase):
    """The end-to-end case: agree with a human who looked at the same eight scenes."""

    def setUp(self):
        if not EXAMPLE_SCENES.is_dir():
            self.skipTest("example/scenes is absent")
        proc = run("--json", cwd=REPO / "example")
        self.payload = json.loads(proc.stdout)
        self.by_scene = {s["scene"]: s for s in self.payload["scenes"]}

    def test_it_finds_the_monotonous_scene(self):
        """06-capabilities.html sets one EASE constant and fires nine entrances off it."""
        found = self.by_scene.get("06-capabilities.html")
        assert found is not None, sorted(self.by_scene)
        self.assertTrue(found["findings"], "the nine-identical-entrance scene reported clean")

    def test_it_clears_the_best_timed_scene(self):
        """07-cta.html has an arrival, a morph, an approach, a press and a settle -- five
        classes of event, five registers. A measure that flagged this one would be wrong."""
        found = self.by_scene.get("07-cta.html")
        assert found is not None, sorted(self.by_scene)
        self.assertEqual([], found["findings"], found)

    def test_it_does_not_flag_most_of_the_film(self):
        """A report that fires everywhere is noise. One finding in eight scenes is the
        signal-to-noise this is worth having at."""
        flagged = [s["scene"] for s in self.payload["scenes"] if s["findings"]]
        self.assertLessEqual(len(flagged), 2, f"flagged {flagged} of 8 scenes")


if __name__ == "__main__":
    unittest.main()
