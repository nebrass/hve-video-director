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
        """`—` means "adds nothing beyond the baseline" in a grammar ROW. On a frame it is
        not a value — and the reason is architectural, not documentary: a frame bullet is
        read by a builder whose packet carries no grammar file (ADR-004), so the notation
        arrives with no decoder. `timeline-choreography` is self-describing; `—` is not."""
        self.write(storyboard(frame(1, caps="—")))
        _, payload = self.audit()
        blob = json.dumps(payload["frames"])
        self.assertIn("timeline-choreography", blob)
        self.assertNotIn("missing required key", blob,
                         "the dash finding already says what to write; do not also "
                         "report the key as absent")

    def test_an_em_dash_is_caught_on_every_key_not_just_capabilities(self):
        """The same notation fails in the OTHER direction, which a capabilities-only
        check missed: `motion: —` is *truthy*, so a frame carrying it and no `blueprint:`
        slid past the presence rule entirely. Found in the committed reference build,
        frame 6 — the dash made the check miss a real non-conformance."""
        self.write(storyboard(frame(1)).replace("- motion: fade-in, rise", "- motion: —"))
        _, payload = self.audit()
        # Read the findings, not json.dumps of them: the dash is escaped to \u2014 there,
        # so an assertion on the literal passes or fails for the wrong reason.
        findings = payload["frames"][0]["findings"]
        self.assertTrue(
            any("`motion: —`" in f for f in findings), findings,
        )
        self.assertTrue(
            any("neither `blueprint:` nor `motion:` is present" in f for f in findings),
            findings,
        )

    def test_a_legitimate_baseline_only_frame_reports_nothing(self):
        """The check must not fire on the correct spelling of the same derivation.

        Frames that genuinely add nothing beyond the baseline are legitimate — the
        reference build has two, and their scenes really do only choreograph. What is
        wrong is writing `—` instead of the baseline's name.
        """
        self.write(storyboard(frame(1, caps="timeline-choreography")))
        proc, payload = self.audit()
        self.assertEqual(0, proc.returncode, proc.stdout)
        self.assertEqual(0, payload["finding_count"], payload["frames"])

    def test_an_undeclared_frame_bullet_is_reported(self):
        """The real sideways-growth surface: a generated project, not a grammar file.

        Upstream's parser preserves an unknown bullet under `extra`, a packet carries
        it, and a builder may act on it — while every doc-to-doc check stays green,
        because the name was never in a contract table. A misspelled `surface_readng:`
        was invisible here until ADR-010's supersession review found it.
        """
        self.write(storyboard(frame(1, extra="surface_readng: shiny|parallax_bed: shallow")))
        proc, payload = self.audit()
        self.assertEqual(1, proc.returncode)
        blob = json.dumps(payload["frames"])
        self.assertIn("surface_readng", blob)
        self.assertIn("parallax_bed", blob)

    def test_an_official_field_and_a_capture_binding_are_not_undeclared(self):
        """The vocabulary is derived from the template's own tables, so a legitimate
        binding must not read as growth. A check that fires on `screenshot:` would be
        deleted within a day."""
        self.write(storyboard(frame(
            1, extra="screenshot: public/screenshots/x.png|transition_in: crossfade",
        )))
        _, payload = self.audit()
        blob = json.dumps(payload["frames"])
        for legitimate in ("screenshot", "transition_in"):
            self.assertNotIn(f"`{legitimate}:` is not", blob, blob)

    def test_the_fifteenth_key_is_audited_like_any_other(self):
        """surface_reading: was promoted out of a second vocabulary precisely so this
        works: a bad value is now a vocabulary finding, not an invisible bullet."""
        self.write(storyboard(frame(1, extra="surface_reading: shiny")))
        _, payload = self.audit()
        self.assertIn("surface_reading: shiny", json.dumps(payload["frames"]))

    def test_a_frame_with_neither_blueprint_nor_motion_is_reported(self):
        self.write(storyboard(frame(1)).replace("- motion: fade-in, rise\n", ""))
        _, payload = self.audit()
        self.assertIn("blueprint", json.dumps(payload["frames"]))

    # ---- the constraints, each a rejected proposal ----

    def test_the_hero_limit_comes_from_the_budget_table_not_the_code(self):
        """ADR-008/C6. If the table moves, the audit moves with it.

        Asserting only that the reported number appears in the table was not a test of
        this: a hard-coded 3 satisfies it too, which an adversarial pass demonstrated by
        replacing the parse with a literal and staying green. So rewrite the table in a
        copy of the skill and require the loader to follow it.
        """
        import shutil
        skill = self.dir / "skill"
        (skill / "reasoning").mkdir(parents=True, exist_ok=True)
        shutil.copytree(REPO / "scripts", skill / "scripts")
        shutil.copytree(REPO / "templates", skill / "templates")
        for name in ("scene-analysis.md", "capability-catalog.md"):
            shutil.copy(REPO / "reasoning" / name, skill / "reasoning" / name)

        table = skill / "reasoning" / "scene-analysis.md"
        original = table.read_text(encoding="utf-8")
        self.assertIn("≤ 3 frames in the film", original, "budget table anchor moved")
        table.write_text(
            original.replace("≤ 3 frames in the film", "≤ 7 frames in the film", 1),
            encoding="utf-8",
        )

        self.write(storyboard(frame(1)))
        proc = subprocess.run(
            [sys.executable, str(skill / "scripts" / "validate_brief.py"),
             "--project-dir", str(self.dir), "keys-audit", "--json"],
            capture_output=True, text=True,
        )
        self.assertEqual(
            7, json.loads(proc.stdout)["hero_budget"]["limit"],
            "the limit did not follow the budget table — it is hard-coded",
        )

    def test_a_value_near_the_vocabulary_is_still_outside_it(self):
        """`runtime:`'s row ends in prose, so a whole-cell vocabulary parser left it with
        none — and `runtime: Three` was then neither counted toward the hero budget nor
        reported. The audit's one budget was defeated by a capital letter."""
        self.write(storyboard(frame(1, extra="runtime: Three|user_directed: yes")))
        _, payload = self.audit()
        blob = json.dumps(payload["frames"])
        self.assertIn("runtime: Three", blob)
        self.assertIn("user_directed: yes", blob)
        self.assertEqual(0, payload["hero_budget"]["counted"], payload["hero_budget"])

    def test_a_legacy_storyboard_is_told_it_is_legacy(self):
        """CLAUDE.md: no generated project is ever stranded. A pre-adoption file carries
        no director keys by construction, so reporting each one missing would tell the
        author to add keys their shape has no home for.

        The fixture needs enough legacy signal for the shape detector to classify it --
        a lone `**Duration:**` line reads as official and gets ten spurious findings.
        """
        (self.dir / "storyboard.md").write_text(
            "# Storyboard\n\n### Scene 1: Opening\n\n"
            "**Duration:** 5s\n**Voiceover:** hello\n**Visual:** a card\n",
            encoding="utf-8",
        )
        proc = run(self.dir)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("pre-adoption", proc.stdout)
        self.assertIn("migrate-storyboard", proc.stdout)

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

    # The record reports findings, and that is the correct state, not a defect to route
    # around. It is also not a goalpost this audit moved: `reasoning/scene-analysis.md`
    # required `capabilities:` non-empty and from the catalog in the SAME commit that
    # added example/storyboard.md carrying `—`. Contract and violation shipped together,
    # and nothing could see it until this audit existed. So the findings are evidence
    # about the pipeline — a real run, human-approved at every gate, emitted keys no gate
    # of the day could check. A synthetic fixture cannot show that.
    #
    # Pinned by (frame, rule signature) rather than by count, so a *different* pair still
    # fails, and by substring rather than exact text, so rewording a message is not a
    # doctrine review.
    #
    # WHEN THIS GOES RED: a new rule fired on the record, or an accepted finding vanished.
    # Adjudicate it HERE — add a row with the date and why it stands, or retire the rule.
    # Never edit example/. That temptation is real and measured: two words in
    # storyboard.md silences the capabilities findings while `status` stays complete,
    # confirmed and unstale. This pin is only safe because
    # test_example_consent.py digests the record's bytes. Do not keep one without the other.
    ACCEPTED_FINDINGS = {
        (2, "capabilities: —"): "2026-08-09 — non-conforming as emitted; a record is not repaired",
        (6, "motion: —"): "2026-08-09 — same notation, opposite failure: `—` is truthy, so the "
                          "presence rule missed it until the dash was normalized",
        (6, "neither `blueprint:` nor `motion:` is present"): "2026-08-09 — the contract "
                          "violation the dash was hiding",
        (7, "capabilities: —"): "2026-08-09 — non-conforming as emitted; a record is not repaired",
    }

    def test_the_committed_reference_build_audits_end_to_end(self):
        """The audit's only run against real pipeline output. Every other test here builds
        frames from a helper written to the same mental model as the parser, so a shared
        blind spot passes all of them."""
        proc = run(REPO / "example", "--json")
        self.assertIn(proc.returncode, (0, 1), proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(8, payload["frame_count"])
        self.assertTrue(payload["denials"], "the reference build records no denials")

    def test_the_record_reports_exactly_the_findings_already_adjudicated(self):
        payload = json.loads(run(REPO / "example", "--json").stdout)
        self.assertEqual(
            len(self.ACCEPTED_FINDINGS), payload["finding_count"],
            "the findings against example/ changed. Adjudicate them in ACCEPTED_FINDINGS "
            "above — example/ is a record and is never edited to satisfy a check "
            "(CLAUDE.md; ADR-001).",
        )
        for (index, signature), why in sorted(self.ACCEPTED_FINDINGS.items()):
            frame_report = next(f for f in payload["frames"] if f["index"] == index)
            with self.subTest(frame=index, rule=signature):
                self.assertTrue(
                    any(signature in f for f in frame_report["findings"]),
                    f"frame {index} no longer reports {signature!r} ({why})",
                )


if __name__ == "__main__":
    unittest.main()
