#!/usr/bin/env python3

import json
import re
import shutil
import subprocess
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate_brief.py"
WORK_ROOT = ROOT / "test" / ".work"

STORY = {
    "mode": "promo",
    "product_surface": "ui",
    "duration": "60s",
    "theme": "light",
    "aspect_ratio": "16:9 1920x1080",
    "identity_strategy": "design-system",
    "identity_choice": "github",
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


class ValidateBriefTestCase(unittest.TestCase):
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

    def test_atomic_state_writes_leave_no_temporary_files(self):
        self.assertEqual(self.run_cli("confirm-story").returncode, 0)
        self.assertEqual(self.run_cli("confirm-story").returncode, 0)
        state = self.project / ".hve" / "brief-state.json"
        payload = json.loads(state.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(list(state.parent.glob(".brief-state.json.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
