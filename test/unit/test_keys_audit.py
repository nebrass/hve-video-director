"""`keys-audit` — a structural audit of the director keys a storyboard carries.

The one item all three review panelists endorsed, and the constraints are as much the
feature as the check. It reports and never gates (`vo-budget`'s precedent, and ADR-001's
reason for it: the storyboard is the user's). It invents no score. It reports DENIALS --
what `runtime_rejected:` recorded -- and never headroom, because "you used 1 of 3 hero
beats" reads as pressure to spend two more, and the contrast between flat and hero beats
IS the storytelling. And it hard-codes no budget number: ADR-008/C6 makes the budget table
the only place those live, so the audit parses them out of it.

The tests below check the constraints, not just the happy path, because each one is a
rejected proposal that would be easy to reintroduce as a helpful improvement.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VALIDATOR = REPO / "scripts" / "validate_brief.py"

FRONTMATTER = """---
title: probe
canvas: 1920x1080
---

"""

FRAME = """## Frame {n} — {title}

- src: scenes/{i:02d}-x.html
- duration: 5s
- goal: {goal}
- abstraction: literal
- complexity: atomic
- tone: calm
- energy: calm
- density: focal
- camera: static
- metaphor: none — real product
- motion: fade-in, rise
- capabilities: {caps}
{extra}
Prose.

"""


def storyboard(*frames):
    return FRONTMATTER + "".join(frames)


def frame(n, *, goal="a viewer understands", caps="timeline-choreography", extra=""):
    body = "".join(f"- {line}\n" for line in extra.split("|") if line)
    return FRAME.format(n=n, i=n - 1, title=f"F{n}", goal=goal, caps=caps, extra=body)


def run(project, *args):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--project-dir", str(project), "keys-audit", *args],
        capture_output=True, text=True,
    )


class KeysAuditTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.dir, ignore_errors=True))

    def write(self, text):
        (self.dir / "storyboard.md").write_text(text, encoding="utf-8")

    def audit(self, *args):
        proc = run(self.dir, "--json", *args)
        return proc, json.loads(proc.stdout) if proc.stdout.strip() else {}

    def test_a_clean_storyboard_reports_nothing_and_exits_zero(self):
        self.write(storyboard(frame(1), frame(2)))
        proc, payload = self.audit()
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertEqual(0, payload["finding_count"], payload["frames"])

    def test_a_missing_required_key_is_reported(self):
        text = storyboard(frame(1)).replace("- tone: calm\n", "")
        self.write(text)
        proc, payload = self.audit()
        self.assertEqual(1, proc.returncode)
        self.assertIn("tone", json.dumps(payload["frames"]))

    def test_a_value_outside_its_closed_vocabulary_is_reported(self):
        self.write(storyboard(frame(1)).replace("- energy: calm", "- energy: frantic"))
        _, payload = self.audit()
        self.assertIn("frantic", json.dumps(payload["frames"]))

    def test_a_capability_outside_the_catalog_is_reported(self):
        self.write(storyboard(frame(1, caps="depth-staging")))
        _, payload = self.audit()
        self.assertIn("depth-staging", json.dumps(payload["frames"]))

    def test_an_em_dash_capability_is_reported_with_the_reason(self):
        """`—` means 'adds nothing' in a grammar table. On a frame it is not a value:
        every scene carries the baseline, so a derived set is never empty. Found on the
        first run against the committed reference build."""
        self.write(storyboard(frame(1, caps="—")))
        _, payload = self.audit()
        self.assertIn("timeline-choreography", json.dumps(payload["frames"]))

    def test_a_frame_with_neither_blueprint_nor_motion_is_reported(self):
        self.write(storyboard(frame(1)).replace("- motion: fade-in, rise\n", ""))
        _, payload = self.audit()
        self.assertIn("blueprint", json.dumps(payload["frames"]))

    # ---- the constraints, each a rejected proposal ----

    def test_the_hero_limit_comes_from_the_budget_table_not_the_code(self):
        """ADR-008/C6. If the table moves, the audit moves with it."""
        _, payload = self.audit_of(storyboard(frame(1)))
        table = (REPO / "reasoning" / "scene-analysis.md").read_text(encoding="utf-8")
        limit = payload["hero_budget"]["limit"]
        self.assertIsNotNone(limit, "hero limit was not parsed at all")
        self.assertIn(
            f"≤ {limit} frames", table,
            f"the audit reports a limit of {limit} that the budget table does not state",
        )

    def audit_of(self, text):
        self.write(text)
        return self.audit()

    def test_hero_frames_over_the_limit_are_reported_as_over(self):
        limit = self.audit_of(storyboard(frame(1)))[1]["hero_budget"]["limit"]
        frames = [
            frame(n, extra="runtime: three|runtime_rejected: typegpu — no compute need")
            for n in range(1, limit + 2)
        ]
        _, payload = self.audit_of(storyboard(*frames))
        self.assertTrue(payload["hero_budget"]["over"], payload["hero_budget"])

    def test_a_user_directed_hero_frame_is_counted_and_shown_but_not_a_violation(self):
        """ADR-001: exempt-but-visible. It appears in the report and does not push the
        film over budget, because the user directed it and the budget yields."""
        limit = self.audit_of(storyboard(frame(1)))[1]["hero_budget"]["limit"]
        frames = [
            frame(n, extra="runtime: three|runtime_rejected: typegpu — no compute need|user_directed: true")
            for n in range(1, limit + 2)
        ]
        _, payload = self.audit_of(storyboard(*frames))
        hero = payload["hero_budget"]
        self.assertFalse(hero["over"], "user-directed frames were counted as a violation")
        self.assertEqual(limit + 1, hero["user_directed"], hero)
        self.assertEqual(limit + 1, len(hero["frames"]), "directed frames vanished from the report")

    def test_denials_are_reported_and_headroom_is_not(self):
        """The rejected P2-1. A denial is evidence the derivation ran; headroom is an
        invitation to spend."""
        self.write(storyboard(
            frame(1, extra="runtime_rejected: three — GSAP serves the derived set"),
        ))
        _, payload = self.audit()
        self.assertEqual(1, len(payload["denials"]))
        self.assertIn("GSAP serves", payload["denials"][0]["runtime_rejected"])
        blob = json.dumps(payload).lower()
        for banned in ("headroom", "unspent", "under_spend", "underspend", "remaining_hero"):
            self.assertNotIn(banned, blob, f"the payload reports {banned}")

    def test_the_payload_carries_no_score(self):
        """ADR-005 and the anti-slop law both ban invented numerics."""
        _, payload = self.audit_of(storyboard(frame(1), frame(2)))
        blob = json.dumps(payload).lower()
        for banned in ("score", "rating", "grade", "quality", "premium"):
            self.assertNotIn(banned, blob, f"the payload invents a {banned}")

    def test_it_reports_rather_than_gates(self):
        """Exit 1 marks a finding. The message has to say so, because a nonzero exit is
        exactly what a workflow author would otherwise wire into a gate."""
        self.write(storyboard(frame(1, caps="not-a-tag")))
        proc = run(self.dir)
        self.assertEqual(1, proc.returncode)
        self.assertIn("report", proc.stdout.lower())
        self.assertRegex(proc.stdout, r"blocks? a phase|does not block")

    def test_it_writes_nothing(self):
        """Read-only, and outside every fingerprint: the storyboard describes the film,
        the brief records consent."""
        self.write(storyboard(frame(1)))
        before = {p.name: p.read_bytes() for p in self.dir.rglob("*") if p.is_file()}
        run(self.dir, "--json")
        after = {p.name: p.read_bytes() for p in self.dir.rglob("*") if p.is_file()}
        self.assertEqual(before, after, "keys-audit modified the project directory")

    def test_the_committed_reference_build_can_be_audited(self):
        """An end-to-end run against real data. It is allowed to report findings --
        example/ is a record, not a fixture, and is never edited to satisfy a check."""
        proc = run(REPO / "example", "--json")
        self.assertIn(proc.returncode, (0, 1), proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(8, payload["frame_count"])
        self.assertTrue(payload["denials"], "the reference build records no denials")


if __name__ == "__main__":
    unittest.main()
