#!/usr/bin/env python3

import importlib.util
import json
import re
import shutil
import subprocess
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate_brief.py"
STORYBOARD_TEMPLATE = ROOT / "templates" / "storyboard.md"
PLAN_TEMPLATE = ROOT / "templates" / "project-plan.md"
WORK_ROOT = ROOT / "test" / ".work"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_brief", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VB = load_module()

# The director keys, read out of the template that tells authors to write them.
# Restating them here would fork a vocabulary `reasoning/scene-analysis.md` owns
# (ADR-008's posture) and would keep passing after a rename.
DIRECTOR_KEY_BULLET = re.compile(r"^-[ \t]+([a-z][a-z0-9_]*):")


def template_director_keys():
    section = STORYBOARD_TEMPLATE.read_text(encoding="utf-8").split(
        "\n## Director keys\n", 1
    )[1].split("\n## ", 1)[0]
    return [
        match.group(1)
        for match in (
            DIRECTOR_KEY_BULLET.match(line) for line in section.splitlines()
        )
        if match
    ]


def template_filled_example():
    """The template's one realistic frame, lifted out of its blockquote."""
    section = STORYBOARD_TEMPLATE.read_text(encoding="utf-8").split(
        "\n## Filled example\n", 1
    )[1]
    quoted = [
        line[2:] if line.startswith("> ") else line[1:]
        for line in section.splitlines()
        if line.startswith(">")
    ]
    return "\n".join(quoted)


# One frame carrying everything this skill writes: the official fields, the
# capture/clip bindings, the tutorial fields, and every director key.
OFFICIAL_FIELDS = {
    "status": "built",
    "src": "scenes/03-dashboard.html",
    "duration": "6s",
    "transition_in": "metallic-swoosh",
    "scene": "the dashboard assembles from its parts",
    "voiceover": "Everything lands in one place.",
    "poster": "3s",
}
EXTRA_FIELDS = {
    "transition_speed": "medium",
    "window": "24s → 30s",
    "screenshot": "public/screenshots/scene-03-dashboard.png",
    "capture": "screen-recording",
    "capture_duration": "6",
    "capture_region": "100,80,1280,720",
    "command": "bash -c 'npm run demo'",
    "record_timeout": "8",
    "clip": "public/clips/scene-03-dashboard.mp4",
    "clip_in": "2s",
    "clip_out": "8s",
    "speed": "1.0",
    "clip_audio": "none",
    "captions": "auto",
    "chapter": "Getting started",
    "step_label": "Step 2 of 5",
}
DIRECTOR_VALUES = {
    "goal": "the viewer understands where their data lands",
    "abstraction": "literal",
    "complexity": "compound",
    "tone": "relief",
    "energy": "resolve",
    "density": "composed",
    "camera": "push-in",
    "metaphor": "none — real product",
    "blueprint": "camera-journey",
    "motion": "`coordinate-target-zoom`, `depth-scatter-assemble`",
    "capabilities": "timeline-choreography, spatial-depth",
    "runtime": "gsap",
    "runtime_rejected": "three — no hero beat left in the budget",
    "user_directed": "true",
}


def official_storyboard(frontmatter=None, bullets=None, narrative="Why this beat earns its seconds."):
    globals_ = {
        "format": "1920x1080",
        "duration": "60s",
        "message": "Ship a launch video in an afternoon",
        "arc": "Hook → Problem → Solution → Proof → CTA",
        "audience": "indie devs",
        "content_mode": "promo",
        "product_surface": "ui",
        "emotional_journey": "curiosity → tension → relief",
        "web_capture_source": "navigate",
    }
    globals_.update(frontmatter or {})
    values = {**OFFICIAL_FIELDS, **EXTRA_FIELDS, **DIRECTOR_VALUES}
    values.update(bullets or {})
    return "\n".join(
        [
            "---",
            *(f"{key}: {value}" for key, value in globals_.items()),
            "---",
            "",
            "## Frame 1 — The dashboard",
            "",
            *(f"- {key}: {value}" for key, value in values.items()),
            "",
            narrative,
            "",
        ]
    )


LEGACY_STORYBOARD = """# Storyboard — legacy project

**Duration:** 30s | **Canvas:** 1920×1080 (16:9) | **Renderer:** HyperFrames
**Mode:** promo | **Theme:** dark
**Product surface:** ui
**Web capture source:** navigate
**Emotional journey:** curiosity → tension → relief

---

### Scene 0: Establishing

**Window:** 0s → 8s (8s)
**Scene file:** `scenes/00-establishing.html`  *(from `templates/scene-screenshot.html`)*
**Screenshot:** `public/screenshots/01-home.png`
**Capture:** screenshot

**Visual:**
- Text on screen: "the product"

**Voiceover (1.0s → ~6.8s):**
> "This is the product."

**Transition to next:** crossfade 0.4s quick

---

### Scene 1: Architecture

**Window:** 8s → 14s (6s)
**Scene file:** `scenes/01-architecture.html`
**Screenshot:** none — connective tissue
**Capture:** none
**Clip in/out:** 2s–8s
**Speed:** 1.5
**Camera:** slow motivated push-in on the wrapper, released before the crossfade

**Director keys:** *(Phase 1 Step 1.4b)*
- goal: the viewer understands the product is three cooperating layers
- abstraction: metaphor
- camera: exploded
- metaphor: Layered architecture
- motion: `depth-scatter-assemble`
- capabilities: timeline-choreography, spatial-depth
- user_directed: true

**Voiceover:**
> "Three layers, one system."

**Transition to next:** metallic-swoosh 0.7s medium

---
"""

# A pre-adoption storyboard whose *prose* is the hard part of a conversion.
#
#   - film-level content above the first scene: the document title and a free
#     paragraph, neither of which any frame owns;
#   - a scene whose narrative *begins* with lines in the `- key: value` shape;
#   - a scene whose narrative *contains* such a line further down, under a
#     `**Visual:**` prose block.
#
# Both prose shapes are ambiguous once written into the official format, where
# `- key: value` is how a frame states metadata. A conversion that writes them
# through untouched hands the next reader lines that mean one thing to their
# author and another to a parser.
LEGACY_WITH_PROSE = """# Storyboard — annotated project

An early note the director wrote above the first scene: this film opens quiet.

**Duration:** 12s | **Canvas:** 1920×1080 (16:9) | **Renderer:** HyperFrames
**Mode:** promo | **Theme:** dark

---

### Scene 0: Establishing

**Window:** 0s → 6s (6s)
**Scene file:** `scenes/00-establishing.html`

- overlay: the wordmark holds for a beat
- lower_third: the tagline fades in under it

**Visual:**
- caption: "one place for everything"

**Transition to next:** crossfade 0.4s quick

---

### Scene 1: Close

**Window:** 6s → 12s (6s)
**Scene file:** `scenes/01-close.html`

The logo settles and the film ends on it.

---
"""

# What every reader of this format calls a frame's metadata: a list item whose
# first token is a bare key followed by a colon. Written out here rather than
# imported from the module under test — the point of the assertion is that the
# emitter agrees with the format, not with itself.
METADATA_SHAPED = re.compile(r"^\s*[-*]\s+[A-Za-z_][A-Za-z0-9_-]*\s*:")
FRAME_HEADING_LINE = re.compile(r"^#{2,3}\s+(?:Frame|Beat|Scene)\b", re.IGNORECASE)
ANY_HEADING_LINE = re.compile(r"^#{1,6}\s")

STORY = {
    "mode": "promo",
    "product_surface": "ui",
    "duration": "60s",
    "theme": "light",
    "aspect_ratio": "16:9 1920x1080",
    "identity_strategy": "design-system",
    "identity_choice": "github",
    "visual_ceiling": "derived",
    "voice": "elevenlabs:Matilda:XrExE9yKIg1WjnnlVkGX",
    "transition_style": "metallic-swoosh",
    "transition_speed": "medium",
    "music_strategy": "freesound",
}
TRACK_A = {
    "title": "Spark of Inspiration",
    "path": "background-music.mp3",
    "source": "https://freesound.org/s/746454/",
    "license": "CC-BY-4.0",
}
TRACK_B = {
    "title": "Quiet Momentum",
    "path": "audio/quiet-momentum.mp3",
    "source": "user-provided",
    "license": "user-owned",
}
TRACK_FREESOUND_B = {
    "title": "Forward Motion",
    "path": "background-music.mp3",
    "source": "https://freesound.org/s/123456/",
    "license": "CC0-1.0",
}


def ambiguous_prose_lines(text):
    """Prose lines a reader of this format could take for metadata.

    Walks the file the way the format is read: a frame opens at its heading and
    its metadata is the block of `- key: value` bullets directly under it, so
    the first line that is not such a bullet starts the prose. Any later line
    still in the bullet shape is ambiguous — the same bytes say "metadata" to
    one reader and "prose" to another, and which one wins is not the author's
    choice. A frame heading is where the ambiguity starts; a heading that opens
    no frame does not end it, because a reader that scans a whole section for
    bullets keeps scanning past one.
    """
    ambiguous, started, in_metadata = [], False, False
    for line in text.splitlines():
        if ANY_HEADING_LINE.match(line):
            if FRAME_HEADING_LINE.match(line):
                started, in_metadata = True, True
            else:
                in_metadata = False
            continue
        if not started:
            continue
        if in_metadata:
            if not line.strip() or METADATA_SHAPED.match(line):
                continue
            in_metadata = False
        if METADATA_SHAPED.match(line):
            ambiguous.append(line)
    return ambiguous


def project_plan(story=None, track=None, extra_rows=()):
    values = dict(STORY)
    if story:
        values.update(story)
    track_value = json.dumps(
        TRACK_A if track is None else track,
        sort_keys=True,
        separators=(",", ":"),
    ) if track != "none" else "none"
    rows = [
        *(f"| {key} | {value} |" for key, value in values.items()),
        f"| final_music_track | {track_value} |",
        *extra_rows,
    ]
    return "\n".join([
        "# Project Plan - test",
        "",
        "## Creative Brief",
        "",
        "| Field | Value |",
        "|---|---|",
        *rows,
        "",
        "## Phase Tracker",
        "",
    ])


class ProjectCase(unittest.TestCase):
    """Fixtures only — a generated project with a complete Creative Brief."""

    def setUp(self):
        self.project = WORK_ROOT / uuid.uuid4().hex
        self.project.mkdir(parents=True)
        self.write_plan()

    def tearDown(self):
        shutil.rmtree(self.project, ignore_errors=True)

    def write_plan(self, story=None, track=None, extra_rows=()):
        (self.project / "project-plan.md").write_text(
            project_plan(story=story, track=track, extra_rows=extra_rows),
            encoding="utf-8",
        )

    def write_storyboard(self, text, name="storyboard.md"):
        path = self.project / name
        path.write_text(text, encoding="utf-8")
        return path

    def run_cli(self, command, *args):
        return subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "--project-dir",
                str(self.project),
                command,
                *args,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def json_cli(self, command, *args):
        result = self.run_cli(command, *args, "--json")
        payload = json.loads(result.stdout)
        return result, payload

    def confirm_and_stamp_all(self):
        self.assertEqual(self.run_cli("confirm-story").returncode, 0)
        for phase in ("phase-1", "phase-2", "phase-3", "phase-4"):
            self.assertEqual(self.run_cli("stamp", phase).returncode, 0)
        self.assertEqual(self.run_cli("confirm-audio").returncode, 0)
        self.assertEqual(self.run_cli("stamp", "phase-5").returncode, 0)


class ValidateBriefTestCase(ProjectCase):
    def test_status_accepts_complete_brief_and_rejects_incomplete_placeholder_duplicate(self):
        complete, payload = self.json_cli("status")
        self.assertEqual(complete.returncode, 0, complete.stderr)
        self.assertTrue(payload["complete"])
        self.assertEqual(payload["earliest_stale_phase"], "phase-1")

        self.write_plan(story={"voice": ""})
        incomplete, payload = self.json_cli("status")
        self.assertEqual(incomplete.returncode, 1)
        self.assertIn("voice: value is missing", payload["errors"])

        plan = project_plan().replace(
            "| transition_speed | medium |\n",
            "",
        )
        (self.project / "project-plan.md").write_text(plan, encoding="utf-8")
        missing, payload = self.json_cli("status")
        self.assertEqual(missing.returncode, 1)
        self.assertIn("transition_speed: value is missing", payload["errors"])

        self.write_plan(story={"voice": "{voice}"})
        placeholder, payload = self.json_cli("status")
        self.assertEqual(placeholder.returncode, 1)
        self.assertIn("voice: placeholder values are not allowed", payload["errors"])

        self.write_plan(extra_rows=("| mode | tutorial |",))
        duplicate, payload = self.json_cli("status")
        self.assertEqual(duplicate.returncode, 2)
        self.assertIn("duplicate Creative Brief field: mode", payload["errors"])

    def test_duplicate_brief_sections_are_rejected(self):
        plan_path = self.project / "project-plan.md"
        plan_path.write_text(
            project_plan()
            + "\n"
            + project_plan(story={"mode": "tutorial"}),
            encoding="utf-8",
        )

        result, payload = self.json_cli("status")

        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate heading: ## Creative Brief", payload["errors"])

    def test_legacy_plan_requires_consent_driven_placeholder_migration(self):
        legacy = "\n".join([
            "# Project Plan - legacy",
            "",
            "**Mode:** showcase",
            "**Theme:** dark",
            "",
            "## Phase Tracker",
            "",
            "Legacy tracker content remains here.",
            "",
        ])
        plan_path = self.project / "project-plan.md"
        plan_path.write_text(legacy, encoding="utf-8")

        status, payload = self.json_cli("status")
        self.assertEqual(status.returncode, 1)
        self.assertTrue(payload["migration_required"])
        self.assertEqual(payload["earliest_stale_phase"], "phase-1")
        self.assertIn("no ## Creative Brief table", payload["errors"][0])

        migrated, payload = self.json_cli("migrate")
        self.assertEqual(migrated.returncode, 0, migrated.stderr)
        self.assertFalse(payload["migration_required"])
        migrated_text = plan_path.read_text(encoding="utf-8")
        self.assertEqual(migrated_text.count("## Creative Brief"), 1)
        self.assertIn("**Mode:** showcase", migrated_text)
        self.assertIn("Legacy tracker content remains here.", migrated_text)
        self.assertIn(
            "| mode | {promo, showcase, or tutorial} |",
            migrated_text,
        )
        self.assertEqual(list(self.project.glob(".project-plan.md.*.tmp")), [])

        incomplete, payload = self.json_cli("status")
        self.assertEqual(incomplete.returncode, 1)
        self.assertFalse(payload["story"]["complete"])
        self.assertIn("mode: placeholder values are not allowed", payload["errors"])

        duplicate_migration = self.run_cli("migrate")
        self.assertEqual(duplicate_migration.returncode, 2)
        self.assertIn("already contains", duplicate_migration.stderr)

    def test_placeholder_track_metadata_cannot_be_confirmed(self):
        placeholder_track = {
            "title": "none",
            "path": "TBD later",
            "source": "placeholder source",
            "license": "unknown value",
        }
        self.write_plan(track=placeholder_track)
        self.assertEqual(self.run_cli("confirm-story").returncode, 0)

        result, payload = self.json_cli("confirm-audio")

        self.assertEqual(result.returncode, 1)
        for field in ("title", "path", "source", "license"):
            self.assertIn(
                f"final_music_track.{field}: placeholder values are not allowed",
                payload["errors"],
            )

        generic_track = {
            "title": "track title",
            "path": "path/to/file.mp3",
            "source": "source URL",
            "license": "license",
        }
        self.write_plan(track=generic_track)
        result, payload = self.json_cli("confirm-audio")
        self.assertEqual(result.returncode, 1)
        for field in ("title", "path", "source", "license"):
            self.assertIn(
                f"final_music_track.{field}: placeholder values are not allowed",
                payload["errors"],
            )

    def test_track_source_must_match_the_confirmed_music_strategy(self):
        self.assertEqual(self.run_cli("confirm-story").returncode, 0)

        wrong_freesound_source = dict(TRACK_A, source="https://example.org/track")
        self.write_plan(track=wrong_freesound_source)
        result, payload = self.json_cli("confirm-audio")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "final_music_track.source: freesound strategy requires an exact "
            "freesound.org track URL containing its numeric sound ID",
            payload["errors"],
        )

        generic_freesound_source = dict(TRACK_A, source="https://freesound.org/")
        self.write_plan(track=generic_freesound_source)
        result, payload = self.json_cli("confirm-audio")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "final_music_track.source: freesound strategy requires an exact "
            "freesound.org track URL containing its numeric sound ID",
            payload["errors"],
        )

        malformed_freesound_source = dict(TRACK_A, source="https://[")
        self.write_plan(track=malformed_freesound_source)
        result, payload = self.json_cli("status")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn(
            "final_music_track.source: freesound strategy requires an exact "
            "freesound.org track URL containing its numeric sound ID",
            payload["errors"],
        )

        self.write_plan(
            story={"music_strategy": "user-provided"},
            track=dict(TRACK_B, source="https://example.org/upload"),
        )
        self.assertEqual(self.run_cli("confirm-story").returncode, 0)
        result, payload = self.json_cli("confirm-audio")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "final_music_track.source: user-provided strategy requires "
            "the exact value user-provided",
            payload["errors"],
        )

        self.write_plan(
            story={"music_strategy": "user-provided"},
            track=dict(TRACK_B, source="USER-PROVIDED"),
        )
        result, payload = self.json_cli("confirm-audio")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "final_music_track.source: user-provided strategy requires "
            "the exact value user-provided",
            payload["errors"],
        )

    def test_story_confirmation_is_stable_and_final_track_is_not_part_of_story_fingerprint(self):
        first, first_payload = self.json_cli("confirm-story")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first_payload["story_revision"], 1)

        second, second_payload = self.json_cli("confirm-story")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(second_payload["story_revision"], 1)
        self.assertEqual(
            first_payload["story_fingerprint"],
            second_payload["story_fingerprint"],
        )

        self.write_plan(track=TRACK_FREESOUND_B)
        status, status_payload = self.json_cli("status")
        self.assertEqual(status.returncode, 0)
        self.assertEqual(
            first_payload["story_fingerprint"],
            status_payload["story"]["fingerprint"],
        )

    def test_story_can_be_confirmed_while_final_track_is_still_a_placeholder(self):
        plan = re.sub(
            r"^\| final_music_track \|.*$",
            "| final_music_track | {none or compact JSON with title, path, source, and license} |",
            project_plan(),
            flags=re.MULTILINE,
        )
        (self.project / "project-plan.md").write_text(plan, encoding="utf-8")

        confirmed = self.run_cli("confirm-story")
        self.assertEqual(confirmed.returncode, 0, confirmed.stderr)
        status, payload = self.json_cli("status")
        self.assertEqual(status.returncode, 1)
        self.assertTrue(payload["story"]["confirmed"])
        self.assertFalse(payload["audio"]["complete"])

    def test_story_rejects_incompatible_theme_and_unqualified_voice(self):
        self.write_plan(
            story={
                "theme": "light",
                "identity_choice": "linear-app",
                "voice": "Matilda (XrExE9yKIg1WjnnlVkGX)",
            }
        )

        result, payload = self.json_cli("confirm-story")

        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "identity_choice: linear-app supports dark theme only; "
            "change theme or identity before confirmation",
            payload["errors"],
        )
        self.assertIn(
            "voice: expected elevenlabs:<name>:<voice-id> or kokoro:<voice-id>",
            payload["errors"],
        )

        self.write_plan(
            story={
                "voice": "kokoro:af_nova",
            }
        )
        self.assertEqual(self.run_cli("confirm-story").returncode, 0)

    def test_changed_story_lever_invalidates_phases_one_through_five(self):
        self.confirm_and_stamp_all()
        fresh, fresh_payload = self.json_cli("status")
        self.assertEqual(fresh.returncode, 0)
        self.assertEqual(fresh_payload["stale_phases"], [])

        self.write_plan(story={"theme": "dark"})
        changed, payload = self.json_cli("status")
        self.assertEqual(changed.returncode, 0)
        self.assertEqual(
            payload["stale_phases"],
            ["phase-1", "phase-2", "phase-3", "phase-4", "phase-5"],
        )
        self.assertEqual(payload["earliest_stale_phase"], "phase-1")

        reconfirmed, reconfirmed_payload = self.json_cli("confirm-story")
        self.assertEqual(reconfirmed.returncode, 0)
        self.assertEqual(reconfirmed_payload["story_revision"], 2)
        required = self.run_cli("require", "phase-1")
        self.assertEqual(required.returncode, 1)
        self.assertIn("phase-1 is stale", required.stderr)

    def test_changed_final_track_invalidates_only_phase_five(self):
        self.confirm_and_stamp_all()
        self.write_plan(track=TRACK_FREESOUND_B)

        changed, payload = self.json_cli("status")
        self.assertEqual(changed.returncode, 0)
        self.assertEqual(payload["stale_phases"], ["phase-5"])
        self.assertEqual(payload["earliest_stale_phase"], "phase-5")

        reconfirmed, audio_payload = self.json_cli("confirm-audio")
        self.assertEqual(reconfirmed.returncode, 0)
        self.assertEqual(audio_payload["audio_revision"], 2)
        for phase in ("phase-1", "phase-2", "phase-3", "phase-4"):
            self.assertEqual(self.run_cli("require", phase).returncode, 0)
        self.assertEqual(self.run_cli("require", "phase-5").returncode, 1)

    def test_old_stamps_and_audio_do_not_resurrect_after_a_b_a_story_change(self):
        self.confirm_and_stamp_all()
        state_path = self.project / ".hve" / "brief-state.json"
        original = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(original["story"]["revision"], 1)
        self.assertEqual(original["audio"]["revision"], 1)

        self.write_plan(story={"theme": "dark"})
        changed, payload = self.json_cli("confirm-story")
        self.assertEqual(changed.returncode, 0)
        self.assertEqual(payload["story_revision"], 2)

        self.write_plan(story={"theme": "light"})
        restored, payload = self.json_cli("confirm-story")
        self.assertEqual(restored.returncode, 0)
        self.assertEqual(payload["story_revision"], 3)

        status, payload = self.json_cli("status")
        self.assertEqual(status.returncode, 0)
        self.assertFalse(payload["audio"]["confirmed"])
        self.assertEqual(payload["stale_phases"], [
            "phase-1",
            "phase-2",
            "phase-3",
            "phase-4",
            "phase-5",
        ])
        self.assertEqual(payload["phases"]["phase-1"]["stamped_revision"], 1)
        self.assertEqual(payload["phases"]["phase-1"]["expected_revision"], 3)

        audio, payload = self.json_cli("confirm-audio")
        self.assertEqual(audio.returncode, 0)
        self.assertEqual(payload["audio_revision"], 2)
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["audio"]["story_revision"], 3)
        self.assertEqual(self.run_cli("require", "phase-5").returncode, 1)

    def test_phase_stamp_and_require_enforce_current_prerequisites(self):
        before = self.run_cli("stamp", "phase-1")
        self.assertEqual(before.returncode, 1)
        self.assertIn("story brief is not confirmed", before.stderr)

        self.assertEqual(self.run_cli("confirm-story").returncode, 0)
        missing = self.run_cli("require", "phase-1")
        self.assertEqual(missing.returncode, 1)
        self.assertIn("phase-1 is stale", missing.stderr)

        self.assertEqual(self.run_cli("stamp", "phase-1").returncode, 0)
        self.assertEqual(self.run_cli("require", "phase-1").returncode, 0)
        self.assertEqual(self.run_cli("stamp", "phase-2").returncode, 0)

        premature = self.run_cli("stamp", "phase-5")
        self.assertEqual(premature.returncode, 1)
        self.assertIn("phase-4 must be fresh", premature.stderr)

    def test_malformed_state_is_an_actionable_error(self):
        state = self.project / ".hve" / "brief-state.json"
        state.parent.mkdir()
        state.write_text("{not json", encoding="utf-8")

        result, payload = self.json_cli("status")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(payload["complete"])
        self.assertIn("brief-state.json is malformed JSON", payload["errors"][0])
        self.assertIn("repair or move", payload["errors"][0])

        state.write_text(
            json.dumps({
                "schema_version": 1,
                "story": {"fingerprint": "bad", "revision": 0, "confirmed_at": ""},
                "audio": None,
                "phases": {},
            }),
            encoding="utf-8",
        )
        structural, payload = self.json_cli("status")
        self.assertEqual(structural.returncode, 2)
        self.assertIn("story.revision is invalid", payload["errors"][0])

    def test_state_records_reject_every_malformed_field_shape(self):
        """The per-field invariants of a confirmation record, pinned.

        A record is valid only when the key is present, of the declared type,
        not a bool wearing an int's clothes, and — for a revision — a counter
        that has actually counted. Every rejection below is current behavior;
        the test exists so that making the missing-key case explicit in the
        validator cannot quietly change which of them still raise.
        """
        state = self.project / ".hve" / "brief-state.json"
        state.parent.mkdir()
        story = {
            "fingerprint": "sha256:" + "0" * 64,
            "revision": 1,
            "confirmed_at": "2026-01-01T00:00:00Z",
        }
        base = {"schema_version": 1, "story": story, "audio": None, "phases": {}}
        state.write_text(json.dumps(base), encoding="utf-8")
        self.assertEqual(VB.load_state(state)["story"]["revision"], 1)

        rejected = {
            "missing revision": {k: v for k, v in story.items() if k != "revision"},
            "null revision": {**story, "revision": None},
            "zero revision": {**story, "revision": 0},
            "negative revision": {**story, "revision": -1},
            "boolean revision": {**story, "revision": True},
            "revision as a string": {**story, "revision": "1"},
            "missing confirmed_at": {
                k: v for k, v in story.items() if k != "confirmed_at"
            },
            "empty confirmed_at": {**story, "confirmed_at": ""},
            "null fingerprint": {**story, "fingerprint": None},
            "fingerprint as a number": {**story, "fingerprint": 1},
        }
        for label, record in rejected.items():
            with self.subTest(label):
                state.write_text(
                    json.dumps({**base, "story": record}), encoding="utf-8"
                )
                with self.assertRaises(VB.StateFormatError):
                    VB.load_state(state)

    def test_atomic_state_writes_leave_no_temporary_files(self):
        self.assertEqual(self.run_cli("confirm-story").returncode, 0)
        self.assertEqual(self.run_cli("confirm-story").returncode, 0)
        state = self.project / ".hve" / "brief-state.json"
        payload = json.loads(state.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(list(state.parent.glob(".brief-state.json.*.tmp")), [])


class DelegatedMusicTestCase(ProjectCase):
    """`music_strategy: delegated` — a bed another skill retrieved or generated.

    It has no public page to cite and no durable download URL, so the source
    records who produced it, by which route, from which request, and which bytes
    came out. The gate stays exactly as strong as the freesound one: the user
    still confirms the exact track, and a source that does not pin all four
    facts cannot be confirmed.
    """

    DELEGATED = {
        "title": "Calm Cinematic Underscore",
        "path": "background-music.mp3",
        "source": (
            "media-use:bgm?mode=retrieve&query=calm%20cinematic%20underscore"
            "#sha256=" + "6f" * 32
        ),
        "license": "HeyGen catalog terms",
    }
    MESSAGE = (
        "final_music_track.source: delegated strategy requires a provenance URI "
        "<skill>:<capability>?mode=retrieve|generate&query=<request>"
        "#sha256=<64 hex digest of the file at path>"
    )

    def confirm_delegated(self, source):
        self.write_plan(
            story={"music_strategy": "delegated"},
            track=dict(self.DELEGATED, source=source),
        )
        self.assertEqual(self.run_cli("confirm-story").returncode, 0)
        return self.json_cli("confirm-audio")

    def test_a_retrieved_or_generated_track_can_be_confirmed(self):
        result, payload = self.confirm_delegated(self.DELEGATED["source"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["audio_revision"], 1)

        generated = (
            "media-use:bgm?mode=generate&prompt=uplifting%20corporate%20tech"
            "&bpm=108#sha256=" + "ab" * 32
        )
        result, payload = self.confirm_delegated(generated)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["audio_revision"], 2)

    def test_a_source_missing_any_of_the_four_facts_is_rejected(self):
        digest = "#sha256=" + "6f" * 32
        for source in (
            # no digest — the bytes that were mixed are unidentifiable
            "media-use:bgm?mode=retrieve&query=calm",
            "media-use:bgm?mode=retrieve&query=calm#sha256=6f",
            "media-use:bgm?mode=retrieve&query=calm#md5=" + "6f" * 16,
            # no route — retrieval and generation carry different licensing
            "media-use:bgm?query=calm" + digest,
            # `auto` is a request, not what happened
            "media-use:bgm?mode=auto&query=calm" + digest,
            "media-use:bgm?mode=retrieve&mode=generate&query=calm" + digest,
            # no request text — nothing explains or reproduces the result
            "media-use:bgm?mode=generate" + digest,
            "media-use:bgm?mode=generate&query=" + digest,
            "media-use:bgm?mode=generate&query=a&prompt=b" + digest,
            # a query string that does not parse was mangled by hand
            "media-use:bgm?mode=generate&query=a&normalized" + digest,
            # no producer or no capability
            "bgm?mode=retrieve&query=calm" + digest,
            "media-use:?mode=retrieve&query=calm" + digest,
            # a plain URL is not a delegated provenance record
            "https://freesound.org/s/746454/",
            "user-provided",
        ):
            with self.subTest(source=source):
                result, payload = self.confirm_delegated(source)
                self.assertEqual(result.returncode, 1)
                self.assertIn(self.MESSAGE, payload["errors"])

    def test_the_older_strategies_did_not_widen(self):
        """The rejection that proves the new branch is additive.

        A delegated URI must stay invalid for the two strategies that already
        had a provenance rule — otherwise widening the vocabulary would have
        quietly weakened them.
        """
        self.write_plan(track=dict(TRACK_A, source=self.DELEGATED["source"]))
        self.assertEqual(self.run_cli("confirm-story").returncode, 0)
        result, payload = self.json_cli("confirm-audio")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "final_music_track.source: freesound strategy requires an exact "
            "freesound.org track URL containing its numeric sound ID",
            payload["errors"],
        )

        self.write_plan(
            story={"music_strategy": "user-provided"},
            track=dict(TRACK_B, source=self.DELEGATED["source"]),
        )
        self.assertEqual(self.run_cli("confirm-story").returncode, 0)
        result, payload = self.json_cli("confirm-audio")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "final_music_track.source: user-provided strategy requires "
            "the exact value user-provided",
            payload["errors"],
        )

    def test_an_unknown_strategy_is_still_rejected(self):
        self.write_plan(story={"music_strategy": "vibes"})
        result, payload = self.json_cli("status")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "music_strategy: expected freesound, delegated, user-provided, or none",
            payload["errors"],
        )

    def test_the_template_documents_the_same_vocabulary(self):
        plan = PLAN_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            f"| music_strategy | {VB.BRIEF_PLACEHOLDERS['music_strategy']} |",
            plan,
        )
        for row in VB.placeholder_brief_table().splitlines():
            if row.startswith("| ") and " | {" in row:
                self.assertIn(
                    row,
                    plan,
                    "templates/project-plan.md and the migration table disagree; "
                    "a legacy project would be migrated to a brief the template "
                    "does not document",
                )


class StoryboardFormatTestCase(ProjectCase):
    """The storyboard is read in the official shape, and never fingerprinted."""

    def test_every_key_a_frame_writes_survives_a_round_trip(self):
        """The load-bearing assumption, checked end to end.

        Director keys survive the official format only because unknown bullets
        are preserved verbatim under a frame's `extra`. Parse must keep every
        one, and rendering them back must produce a file that parses to the same
        document — otherwise a migration silently drops a frame's direction while
        every gate stays green.
        """
        text = official_storyboard()
        document = VB.parse_storyboard(text)
        self.assertEqual(document["format"], "official")
        self.assertEqual(document["warnings"], [])
        self.assertEqual(len(document["frames"]), 1)
        frame = document["frames"][0]

        self.assertEqual(frame["title"], "The dashboard")
        self.assertEqual(frame["number"], 1)
        self.assertEqual(frame["duration_seconds"], 6.0)
        self.assertEqual(frame["narrative"], "Why this beat earns its seconds.")
        for key, value in OFFICIAL_FIELDS.items():
            self.assertEqual(frame[key], value, f"official field {key} was lost")

        keys = template_director_keys()
        self.assertEqual(
            sorted(keys),
            sorted(DIRECTOR_VALUES),
            "templates/storyboard.md and this round-trip disagree about the "
            "director keys a frame writes",
        )
        for key, value in {**EXTRA_FIELDS, **DIRECTOR_VALUES}.items():
            self.assertEqual(
                frame["extra"].get(key),
                value,
                f"`{key}` did not survive under `extra` — the mechanism every "
                f"director key rides on",
            )

        rendered = VB.render_storyboard(document)
        reparsed = VB.parse_storyboard(rendered)
        self.assertEqual(reparsed["frames"], document["frames"])
        self.assertEqual(reparsed["globals"], document["globals"])
        self.assertEqual(VB.render_storyboard(reparsed), rendered)

        self.assertEqual(
            document["globals"]["extra"]["content_mode"],
            "promo",
            "the content mode must not collide with the official `mode` key",
        )

    def test_the_template_example_keeps_its_direction(self):
        """A reflow that pushes bullets below the narrative loses them silently.

        The metadata block ends at the first line that is not a `- key: value`
        bullet. The template's filled example is the one place the shape is
        demonstrated, so it is parsed here rather than trusted.
        """
        document = VB.parse_storyboard(
            "---\nformat: 1920x1080\n---\n\n" + template_filled_example()
        )
        self.assertEqual(len(document["frames"]), 1)
        frame = document["frames"][0]
        written = dict(
            match.groups()
            for match in (
                VB.METADATA_BULLET.match(line.strip())
                for line in template_filled_example().splitlines()
            )
            if match
        )
        self.assertTrue(written, "the filled example carries no metadata bullets")
        for key, value in written.items():
            landed = (
                frame[key] if key in VB.FRAME_FIELDS else frame["extra"].get(key)
            )
            self.assertEqual(
                landed,
                value.strip(),
                f"the filled example writes `{key}` but the parser did not keep "
                f"it — the bullet block was reflowed below the narrative",
            )
        self.assertTrue(
            [key for key in written if key in template_director_keys()],
            "the filled example demonstrates no director key at all",
        )

    def test_a_legacy_storyboard_still_resumes_and_is_never_fingerprinted(self):
        self.confirm_and_stamp_all()
        before = json.loads(
            (self.project / ".hve" / "brief-state.json").read_text(encoding="utf-8")
        )
        fresh, baseline = self.json_cli("status")
        self.assertEqual(fresh.returncode, 0)
        self.assertEqual(baseline["stale_phases"], [])

        self.write_storyboard(LEGACY_STORYBOARD)
        resumed, payload = self.json_cli("status")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(payload["stale_phases"], [])
        self.assertEqual(
            payload["story"]["fingerprint"], baseline["story"]["fingerprint"]
        )
        self.assertEqual(
            payload["audio"]["fingerprint"], baseline["audio"]["fingerprint"]
        )
        self.assertEqual(
            json.loads(
                (self.project / ".hve" / "brief-state.json").read_text(
                    encoding="utf-8"
                )
            ),
            before,
        )
        for phase in ("phase-1", "phase-3", "phase-5"):
            self.assertEqual(self.run_cli("require", phase).returncode, 0)

        result, board = self.json_cli("storyboard")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(board["format"], "legacy")
        self.assertTrue(board["migration_available"])
        self.assertEqual(board["frame_count"], 2)
        self.assertEqual(board["globals"]["extra"]["content_mode"], "promo")
        self.assertEqual(board["globals"]["format"], "1920x1080")

        first, second = board["frames"]
        self.assertEqual(first["src"], "scenes/00-establishing.html")
        self.assertEqual(first["duration"], "8s")
        self.assertEqual(first["voiceover"], "This is the product.")
        self.assertIsNone(
            first["transition_in"],
            "a legacy file never said how the film opens; nothing may invent it",
        )
        self.assertEqual(second["transition_in"], "crossfade")
        self.assertEqual(second["extra"]["transition_speed"], "quick")
        self.assertEqual(second["extra"]["clip_in"], "2s")
        self.assertEqual(second["extra"]["clip_out"], "8s")
        self.assertEqual(second["extra"]["goal"].split()[0], "the")
        self.assertEqual(second["extra"]["camera"], "exploded")
        self.assertEqual(
            second["extra"]["motion"],
            "`depth-scatter-assemble`",
            "a lifted bullet is copied verbatim, decoration included",
        )
        self.assertIn(
            "push-in",
            second["extra"]["legacy_camera"],
            "the legacy prose Camera field must not be folded into the "
            "closed-vocabulary director key",
        )
        self.assertEqual(
            second["extra"]["legacy_transition_out"],
            "metallic-swoosh 0.7s medium",
        )

    def test_migration_is_additive_and_preserves_the_original(self):
        original = self.write_storyboard(LEGACY_STORYBOARD).read_text(
            encoding="utf-8"
        )
        self.confirm_and_stamp_all()
        state_path = self.project / ".hve" / "brief-state.json"
        before = state_path.read_text(encoding="utf-8")

        result, payload = self.json_cli("migrate-storyboard")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["frame_count"], 2)
        self.assertEqual(payload["format"], "official")
        for key in ("goal", "camera", "metaphor", "window", "legacy_scene"):
            self.assertIn(key, payload["carried_keys"])

        backup = self.project / "storyboard.legacy.md"
        self.assertEqual(backup.read_text(encoding="utf-8"), original)
        converted = (self.project / "storyboard.md").read_text(encoding="utf-8")
        self.assertTrue(converted.startswith("---\n"))
        self.assertIn("## Frame 1 — Establishing", converted)
        self.assertIn("- goal: the viewer understands", converted)
        self.assertEqual(list(self.project.glob(".storyboard*.tmp")), [])

        reparsed = VB.parse_storyboard(converted)
        self.assertEqual(reparsed["format"], "official")
        self.assertEqual(
            [frame["extra"] for frame in reparsed["frames"]],
            [
                frame["extra"]
                for frame in VB.parse_storyboard(original)["frames"]
            ],
            "conversion must not change what a frame carries",
        )

        self.assertEqual(state_path.read_text(encoding="utf-8"), before)
        self.assertEqual(self.json_cli("status")[1]["stale_phases"], [])

        again = self.run_cli("migrate-storyboard")
        self.assertEqual(again.returncode, 2)
        self.assertIn("not in the pre-adoption shape", again.stderr)

    def test_migrated_prose_is_never_read_back_as_metadata(self):
        """A conversion may not hand the next reader an ambiguous line.

        `- key: value` is how a frame states metadata in this format. Legacy
        prose written in that shape — a bullet list of on-screen beats — means
        prose to its author and metadata to a parser, and the file cannot say
        which. The emitter has to resolve it, at the top of a frame's prose and
        anywhere below it: a reader that scans the whole section rather than the
        contiguous block under the heading reclassifies a line in the middle
        just as silently.
        """
        original = self.write_storyboard(LEGACY_WITH_PROSE).read_text(
            encoding="utf-8"
        )
        before = VB.parse_storyboard(original)

        result, _ = self.json_cli("migrate-storyboard")
        self.assertEqual(result.returncode, 0, result.stderr)
        converted = (self.project / "storyboard.md").read_text(encoding="utf-8")

        self.assertEqual(
            ambiguous_prose_lines(converted),
            [],
            "the converted file writes prose that reads as a metadata bullet; "
            "the next read decides what it means, not the author",
        )

        after = VB.parse_storyboard(converted)
        self.assertEqual(
            [frame["extra"] for frame in after["frames"]],
            [frame["extra"] for frame in before["frames"]],
            "prose was promoted into frame metadata by the conversion",
        )
        self.assertEqual(
            [frame["narrative"] for frame in after["frames"]],
            [frame["narrative"] for frame in before["frames"]],
            "the frame's prose did not come back the way it went in",
        )
        narrative = after["frames"][0]["narrative"]
        self.assertIn("- overlay: the wordmark holds for a beat", narrative)
        self.assertIn('- caption: "one place for everything"', narrative)
        self.assertNotIn(
            "mixed shapes",
            " ".join(warning["message"] for warning in after["warnings"]),
            "the converted file must read as one shape, not two",
        )

    def test_a_section_below_the_last_scene_survives_the_conversion(self):
        """A heading that opens no scene still holds the user's writing.

        It ends the last frame here, but not for a reader that scans a whole
        section — so the text has to be carried *and* kept unambiguous, and the
        report has to say where it went.
        """
        self.write_storyboard(
            "# Storyboard — annotated project\n\n"
            "**Duration:** 6s\n\n"
            "### Scene 0: Establishing\n\n"
            "**Window:** 0s → 6s (6s)\n\n"
            "The wordmark holds.\n\n"
            "### Open questions\n\n"
            "- todo: confirm the voice before Phase 5\n"
        )

        result, payload = self.json_cli("migrate-storyboard")
        self.assertEqual(result.returncode, 0, result.stderr)
        converted = (self.project / "storyboard.md").read_text(encoding="utf-8")

        self.assertIn("### Open questions", converted)
        self.assertIn("confirm the voice before Phase 5", converted)
        self.assertEqual(ambiguous_prose_lines(converted), [])

        reparsed = VB.parse_storyboard(converted)
        self.assertEqual(
            reparsed["trailing"],
            "### Open questions\n\n- todo: confirm the voice before Phase 5",
        )
        self.assertEqual(len(reparsed["frames"]), 1)
        self.assertNotIn(
            "todo",
            reparsed["frames"][0]["extra"],
            "a note below the last scene became frame metadata",
        )
        self.assertEqual(VB.render_storyboard(reparsed), converted)
        self.assertTrue(
            [note for note in payload["adjusted"] if "opens no scene" in note],
            "the report does not say where the trailing section landed",
        )

    def test_a_field_stated_twice_is_reported_not_quietly_halved(self):
        """The official shape states a key once; a legacy file could state it
        twice. Keeping the last value is a defensible choice — keeping it
        without saying the first one went is not."""
        self.write_storyboard(
            "### Scene 0: Open\n\n"
            "**Window:** 0s → 6s (6s)\n"
            "**Screenshot:** `public/screenshots/first.png`\n"
            "**Screenshot:** `public/screenshots/second.png`\n"
        )

        result, payload = self.json_cli("migrate-storyboard")
        self.assertEqual(result.returncode, 0, result.stderr)

        messages = " ".join(warning["message"] for warning in payload["warnings"])
        self.assertIn("more than once", messages)
        self.assertIn("first.png", messages)
        self.assertIn("more than once", payload["message"])

        frame = VB.parse_storyboard(
            (self.project / "storyboard.md").read_text(encoding="utf-8")
        )["frames"][0]
        self.assertEqual(
            frame["extra"]["screenshot"], "public/screenshots/second.png"
        )

    def test_conversion_is_stable_when_it_runs_again(self):
        """Convert → read → convert must land on the same bytes.

        The property that makes a conversion trustworthy: whatever the emitter
        did to make the prose unambiguous has to survive being read back, or the
        file drifts every time something rewrites it.
        """
        document = VB.parse_storyboard(LEGACY_WITH_PROSE)
        once = VB.render_storyboard(document)
        reparsed = VB.parse_storyboard(once)
        twice = VB.render_storyboard(reparsed)

        self.assertEqual(twice, once, "a second conversion changed the file")
        self.assertEqual(reparsed["frames"], document["frames"])
        self.assertEqual(reparsed["globals"], document["globals"])
        self.assertEqual(reparsed["preamble"], document["preamble"])

    def test_film_level_prose_is_carried_and_the_report_says_where(self):
        """Content no frame owns still belongs to the document.

        The title and any free prose above the first scene are the user's
        writing. Dropping them while reporting a clean conversion is the worst
        of both: the content is gone and nothing said so.
        """
        self.write_storyboard(LEGACY_WITH_PROSE)

        result, payload = self.json_cli("migrate-storyboard")
        self.assertEqual(result.returncode, 0, result.stderr)
        converted = (self.project / "storyboard.md").read_text(encoding="utf-8")

        self.assertIn("# Storyboard — annotated project", converted)
        self.assertIn("this film opens quiet", converted)
        self.assertTrue(
            converted.startswith("---\n"),
            "the format allows nothing above the frontmatter, not even a title",
        )
        self.assertLess(
            converted.index("\n---\n"),
            converted.index("# Storyboard — annotated project"),
            "the carried title must sit below the frontmatter, never above it",
        )
        self.assertLess(
            converted.index("# Storyboard — annotated project"),
            converted.index("## Frame 1"),
            "film-level prose belongs to the document, not to a frame",
        )

        reparsed = VB.parse_storyboard(converted)
        self.assertIn("this film opens quiet", reparsed["preamble"])
        self.assertEqual(len(reparsed["frames"]), 2)

        message = payload["message"]
        self.assertNotIn(
            "no key was dropped",
            message,
            "a conversion that adjusts and leaves content behind may not report "
            "a blanket all-clear",
        )
        self.assertIn("frontmatter", message)
        self.assertIn("Not carried", message)
        self.assertIn("horizontal rule", message)
        self.assertTrue(
            [note for note in payload["adjusted"] if "escap" in note.lower()],
            "the report does not say the prose bullets were escaped",
        )
        self.assertTrue(payload["not_carried"])

    def test_migration_refuses_to_overwrite_an_existing_backup(self):
        self.write_storyboard(LEGACY_STORYBOARD)
        self.write_storyboard("earlier backup\n", name="storyboard.legacy.md")

        result = self.run_cli("migrate-storyboard")

        self.assertEqual(result.returncode, 2)
        self.assertIn("already exists", result.stderr)
        self.assertEqual(
            (self.project / "storyboard.legacy.md").read_text(encoding="utf-8"),
            "earlier backup\n",
        )
        self.assertEqual(
            (self.project / "storyboard.md").read_text(encoding="utf-8"),
            LEGACY_STORYBOARD,
        )

    def test_a_missing_or_unreadable_storyboard_is_reported_not_invented(self):
        missing, payload = self.json_cli("storyboard")
        self.assertEqual(missing.returncode, 1)
        self.assertIn("no storyboard.md", payload["errors"][0])
        self.assertEqual(self.run_cli("migrate-storyboard").returncode, 2)

        self.write_storyboard("Just some notes about the film.\n")
        unknown, payload = self.json_cli("storyboard")
        self.assertEqual(unknown.returncode, 1)
        self.assertEqual(payload["format"], "unknown")
        self.assertEqual(payload["frame_count"], 0)
        self.assertEqual(self.run_cli("migrate-storyboard").returncode, 2)

    def test_the_parser_warns_instead_of_throwing(self):
        """Leniency mirrors the official parser: surprises are warnings."""
        document = VB.parse_storyboard(
            official_storyboard(
                frontmatter={"mode": "autonomous"},
                bullets={"status": "polished"},
            )
        )
        messages = " ".join(warning["message"] for warning in document["warnings"])
        self.assertIn("interaction mode", messages)
        self.assertIn("content_mode", messages)
        self.assertIn("unknown status", messages)
        self.assertEqual(document["frames"][0]["status"], "polished")

        bare = VB.parse_storyboard("## Frame 1 — No metadata\n\nJust prose.\n")
        self.assertEqual(bare["frames"][0]["status"], "outline")
        self.assertIn(
            "no metadata bullets",
            " ".join(warning["message"] for warning in bare["warnings"]),
        )

    def test_bullets_below_the_narrative_are_prose_not_metadata(self):
        document = VB.parse_storyboard(
            "---\nformat: 1920x1080\n---\n\n"
            "## Frame 1 — Hook\n\n"
            "- goal: the viewer leans in\n\n"
            "Narrative starts here.\n\n"
            "- tone: curiosity\n"
        )
        frame = document["frames"][0]
        self.assertEqual(frame["extra"], {"goal": "the viewer leans in"})
        self.assertIn("- tone: curiosity", frame["narrative"])


class VisualCeilingTestCase(ProjectCase):
    """The `visual_ceiling` lever: a ceiling the user owns, never a request.

    The architectural rule it has to keep is asymmetric, so the tests are too.
    `flat` must *bar* WebGL and canvas heroes everywhere; `derived` must grant
    nothing — it is the absence of a ceiling, not permission for a runtime,
    because capability derivation alone decides what a frame earns (ADR-005).
    A third value meaning "prefer 3D" would invert that, which is why the enum
    is closed to exactly two and this file says so out loud.
    """

    LEVER = "visual_ceiling"

    def test_only_the_two_ceiling_values_are_accepted(self):
        for value in ("derived", "flat"):
            self.write_plan(story={self.LEVER: value})
            result, payload = self.json_cli("status")
            self.assertEqual(result.returncode, 0, payload)

        # Anything that reads as *requesting* a runtime is not a ceiling.
        for value in ("prefer-3d", "three", "always-3d", "no-3d", ""):
            self.write_plan(story={self.LEVER: value})
            result, payload = self.json_cli("status")
            self.assertEqual(result.returncode, 1, f"{value!r} was accepted")
            self.assertTrue(
                any(self.LEVER in error for error in payload["errors"]),
                f"{value!r} was rejected without naming {self.LEVER}: {payload['errors']}",
            )

    def test_changing_the_ceiling_stales_every_phase(self):
        """It changes the film, so it is a story field — not an audio-only one.

        Going flat can retire a scene's whole runtime, so a storyboard and every
        build downstream of it are no longer answers to the confirmed brief.
        """
        self.confirm_and_stamp_all()
        fresh, fresh_payload = self.json_cli("status")
        self.assertEqual(fresh.returncode, 0)
        self.assertEqual(fresh_payload["stale_phases"], [])

        self.write_plan(story={self.LEVER: "flat"})
        changed, payload = self.json_cli("status")
        self.assertEqual(
            payload["stale_phases"],
            ["phase-1", "phase-2", "phase-3", "phase-4", "phase-5"],
        )
        self.assertEqual(payload["earliest_stale_phase"], "phase-1")

    def test_the_ceiling_vocabulary_agrees_across_every_file_that_states_it(self):
        """Validator, brief template and Phase-1 prompt must offer one vocabulary.

        Three files spell this enum. A value added to the picker but not the
        validator is a question the user can answer and the brief then rejects;
        the reverse is a value no one can reach. Neither shows up in a diff of
        any single file, which is the same drift `test_instruction_parity`
        exists to catch.
        """
        import re

        validator = (ROOT / "scripts" / "validate_brief.py").read_text(encoding="utf-8")
        declared = re.search(r"VISUAL_CEILINGS = \{([^}]*)\}", validator)
        self.assertIsNotNone(declared, "VISUAL_CEILINGS is no longer declared as a set literal")
        from_validator = set(re.findall(r'"([a-z0-9-]+)"', declared.group(1)))

        template = (ROOT / "templates" / "project-plan.md").read_text(encoding="utf-8")
        placeholder = re.search(rf"\| {self.LEVER} \| \{{([^}}]*)\}} \|", template)
        self.assertIsNotNone(placeholder, f"{self.LEVER} has no row in the brief template")
        from_template = set(re.findall(r"[a-z0-9-]+", placeholder.group(1))) - {"or"}

        workflow = (ROOT / "workflows" / "phase-1-storytelling.md").read_text(encoding="utf-8")
        recorded = re.search(rf"`{self.LEVER}: ([a-z0-9|\- ]+)`", workflow)
        self.assertIsNotNone(recorded, f"Phase 1 never records {self.LEVER}")
        from_workflow = {v.strip() for v in recorded.group(1).split("|")}

        self.assertEqual(from_validator, from_template, "template vocabulary drifted")
        self.assertEqual(from_validator, from_workflow, "Phase-1 vocabulary drifted")

    def test_the_confirmation_summary_shows_every_story_field(self):
        """The summary the user confirms must contain what confirm-story signs.

        Phase 1 promises this table holds "every story-owned field", and
        `confirm-story` fingerprints exactly STORY_FIELDS. A field that is
        fingerprinted but absent from the summary is consent the user never
        actually gave — ADR-001's central failure, not a formatting slip.

        This is a regression test with a real defect behind it: `visual_ceiling`
        shipped fingerprinted and missing from this table, because an edit
        matched a substring in the wrong table and nothing checked the two
        against each other.
        """
        import re

        workflow = (ROOT / "workflows" / "phase-1-storytelling.md").read_text(encoding="utf-8")
        start = workflow.index("### Confirm the complete story brief before storyboarding")
        end = workflow.index("Then require an explicit native confirmation", start)
        shown = set(re.findall(r"`([a-z_]+)`", workflow[start:end]))

        validator = (ROOT / "scripts" / "validate_brief.py").read_text(encoding="utf-8")
        declared = re.search(r"STORY_FIELDS = \(([^)]*)\)", validator)
        self.assertIsNotNone(declared, "STORY_FIELDS is no longer a tuple literal")
        story_fields = set(re.findall(r'"([a-z_]+)"', declared.group(1)))

        self.assertTrue(story_fields, "parsed no story fields — the regex has rotted")
        self.assertEqual(
            story_fields - shown,
            set(),
            "story fields are fingerprinted by confirm-story but never shown in the "
            "summary the user confirms",
        )

    def test_every_multi_value_brief_vocabulary_agrees_with_the_validator(self):
        """Generalizes the ceiling check to every `field: a | b | c` record line.

        Scoped to that one shape on purpose — `transition_style` records one
        value per line and needs a different reader, so sweeping it here would
        mean a regex that matches everything and asserts nothing.

        It earns its keep immediately: `music_strategy` had dropped `delegated`
        from its record line while the picker offered it and the validator
        accepted it, and the single-field version could not see that.
        """
        import re

        validator = (ROOT / "scripts" / "validate_brief.py").read_text(encoding="utf-8")
        workflow = (ROOT / "workflows" / "phase-1-storytelling.md").read_text(encoding="utf-8")

        for field, constant in (("visual_ceiling", "VISUAL_CEILINGS"), ("music_strategy", "MUSIC_STRATEGIES")):
            with self.subTest(field=field):
                declared = re.search(rf"{constant} = \{{([^}}]*)\}}", validator)
                self.assertIsNotNone(declared, f"{constant} is no longer a set literal")
                accepted = set(re.findall(r'"([a-z0-9-]+)"', declared.group(1)))

                recorded = re.search(rf"`{field}: ([a-z0-9|\- ]+)`", workflow)
                self.assertIsNotNone(recorded, f"Phase 1 never records {field}")
                written = {v.strip() for v in recorded.group(1).split("|")}

                self.assertEqual(
                    accepted, written,
                    f"{field}: the validator accepts {sorted(accepted)} but Phase 1 records "
                    f"{sorted(written)} — a value in one and not the other is either a question "
                    f"the brief will reject or a value no one can reach",
                )


if __name__ == "__main__":
    unittest.main()
