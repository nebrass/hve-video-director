import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "caption_gen.py"


def load_module():
    spec = importlib.util.spec_from_file_location("caption_gen_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CaptionGeneratorTestCase(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.audio = self.root / "voiceover-with-music.mp3"
        self.audio.write_bytes(b"final mixed audio")
        self.transcript = self.root / "transcript.json"
        self.transcript.write_text(
            json.dumps(
                [
                    {"text": "Welcome", "start": 0.5, "end": 1.2},
                    {"text": "aboard.", "start": 1.2, "end": 2.5},
                    {"text": "Ready", "start": 3.0, "end": 3.7},
                    {"text": "now.", "start": 3.7, "end": 4.5},
                ]
            ),
            encoding="utf-8",
        )
        self.manifest = self.root / "captions-review.json"
        self.draft_srt = self.root / "voiceover.srt"
        self.draft_vtt = self.root / "voiceover.vtt"
        self.final_srt = self.root / "out" / "final.srt"
        self.final_vtt = self.root / "out" / "final.vtt"
        self.state = self.root / ".hve" / "captions-state.json"

    def tearDown(self):
        self.temporary.cleanup()

    def create_draft(self):
        with mock.patch.object(
            self.module, "_probe_audio_duration", return_value=6.0
        ):
            return self.module.create_review_draft(
                input_path=self.transcript,
                audio_path=self.audio,
                manifest_path=self.manifest,
                srt_path=self.draft_srt,
                vtt_path=self.draft_vtt,
            )

    def approve_manifest(self, *, sound=True):
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["speech_review"] = "verified"
        manifest["speaker_review"] = "single-obvious"
        manifest["sound_review"] = "included" if sound else "none-meaningful"
        if sound:
            manifest["cues"][0]["sound"] = "Soft music begins"
        self.manifest.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        with mock.patch.object(
            self.module, "_probe_audio_duration", return_value=6.0
        ):
            return self.module.approve_reviewed_captions(
                audio_path=self.audio,
                manifest_path=self.manifest,
            )

    def finalize(self):
        with mock.patch.object(
            self.module, "_probe_audio_duration", return_value=6.0
        ):
            return self.module.finalize_reviewed_captions(
                audio_path=self.audio,
                manifest_path=self.manifest,
                srt_path=self.final_srt,
                vtt_path=self.final_vtt,
                state_path=self.state,
            )

    def validate(self):
        with mock.patch.object(
            self.module, "_probe_audio_duration", return_value=6.0
        ):
            return self.module.validate_final_captions(
                audio_path=self.audio,
                manifest_path=self.manifest,
                srt_path=self.final_srt,
                vtt_path=self.final_vtt,
                state_path=self.state,
            )

    def test_draft_is_audio_bound_unreviewed_and_non_destructive(self):
        draft = self.create_draft()

        self.assertFalse(draft["reviewed"])
        self.assertEqual(draft["speech_review"], "pending")
        self.assertEqual(draft["speaker_review"], "pending")
        self.assertEqual(draft["sound_review"], "pending")
        self.assertIsNone(draft["approval"])
        self.assertTrue(draft["audio"]["sha256"].startswith("sha256:"))
        self.assertTrue(self.draft_srt.is_file())
        self.assertTrue(self.draft_vtt.is_file())

        with self.assertRaisesRegex(ValueError, "already exists"):
            self.create_draft()

    def test_finalize_requires_explicit_human_review(self):
        self.create_draft()

        with self.assertRaisesRegex(ValueError, "not human-reviewed"):
            self.finalize()

        self.assertFalse(self.state.exists())
        self.assertFalse(self.final_srt.exists())
        self.assertFalse(self.final_vtt.exists())

    def test_finalize_writes_reviewed_delivery_and_validate_accepts_it(self):
        self.create_draft()
        self.approve_manifest(sound=True)

        state = self.finalize()
        validated = self.validate()

        self.assertEqual(validated["audio"]["sha256"], state["audio"]["sha256"])
        self.assertIn(
            "[Soft music begins]",
            self.final_srt.read_text(encoding="utf-8"),
        )
        self.assertTrue(
            self.final_vtt.read_text(encoding="utf-8").startswith("WEBVTT\n")
        )
        self.assertTrue(self.state.is_file())

    def test_validate_rejects_changed_audio_manifest_or_outputs(self):
        self.create_draft()
        self.approve_manifest(sound=False)
        self.finalize()

        self.audio.write_bytes(b"changed final mixed audio")
        with self.assertRaisesRegex(ValueError, "audio changed"):
            self.validate()

        self.audio.write_bytes(b"final mixed audio")
        self.final_srt.write_text("modified\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "srt is stale|SRT does not match"):
            self.validate()

    def test_changed_cues_invalidate_exact_user_approval(self):
        self.create_draft()
        self.approve_manifest(sound=False)
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["cues"][0]["text"] = "Unapproved replacement."
        self.manifest.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "changed after user approval"):
            self.finalize()

    def test_validate_rejects_any_state_schema_change(self):
        self.create_draft()
        self.approve_manifest(sound=False)
        self.finalize()
        state = json.loads(self.state.read_text(encoding="utf-8"))
        state["unexpected"] = True
        self.state.write_text(
            json.dumps(state, indent=2) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "state is stale or was modified"):
            self.validate()

    def test_failed_bundle_publication_restores_prior_delivery(self):
        self.create_draft()
        self.approve_manifest(sound=False)
        self.finalize()
        before = {
            path: path.read_bytes()
            for path in (self.final_srt, self.final_vtt, self.state)
        }
        real_replace = self.module.os.replace

        def fail_vtt_publication(source, destination):
            source = Path(source)
            destination = Path(destination)
            if destination == self.final_vtt and source.suffix == ".tmp":
                raise OSError("simulated VTT publication failure")
            return real_replace(source, destination)

        with mock.patch.object(
            self.module.os,
            "replace",
            side_effect=fail_vtt_publication,
        ):
            with self.assertRaisesRegex(
                OSError,
                "simulated VTT publication failure",
            ):
                self.finalize()

        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content)
        self.validate()

    def test_manifest_validation_rejects_unreviewed_accessibility_claims(self):
        draft = self.create_draft()
        draft["reviewed"] = True
        draft["speech_review"] = "verified"
        draft["speaker_review"] = "included"
        draft["sound_review"] = "included"

        with mock.patch.object(self.module, "_sha256", return_value=draft["audio"]["sha256"]):
            with self.assertRaisesRegex(ValueError, "no cue has a speaker"):
                self.module.validate_review_manifest(draft, self.audio, 6.0)

        draft["speaker_review"] = "single-obvious"
        with mock.patch.object(self.module, "_sha256", return_value=draft["audio"]["sha256"]):
            with self.assertRaisesRegex(ValueError, "no cue has a meaningful sound"):
                self.module.validate_review_manifest(draft, self.audio, 6.0)

    def test_manifest_validation_rejects_overlap_and_unreadable_cues(self):
        draft = self.create_draft()
        draft["reviewed"] = True
        draft["speech_review"] = "verified"
        draft["speaker_review"] = "single-obvious"
        draft["sound_review"] = "none-meaningful"
        draft["cues"][1]["start"] = 2.0

        with mock.patch.object(self.module, "_sha256", return_value=draft["audio"]["sha256"]):
            with self.assertRaisesRegex(ValueError, "overlaps"):
                self.module.validate_review_manifest(draft, self.audio, 6.0)

        draft["cues"][1]["start"] = 3.0
        draft["cues"][0]["end"] = 0.9
        draft["cues"][0]["text"] = "This caption is much too dense to read"
        with mock.patch.object(self.module, "_sha256", return_value=draft["audio"]["sha256"]):
            with self.assertRaisesRegex(ValueError, "characters/s"):
                self.module.validate_review_manifest(draft, self.audio, 6.0)

    def test_legacy_invocation_still_writes_draft_sidecars(self):
        srt = self.root / "legacy.srt"
        vtt = self.root / "legacy.vtt"

        result = self.module.main(
            [
                "--input",
                str(self.transcript),
                "--srt",
                str(srt),
                "--vtt",
                str(vtt),
            ]
        )

        self.assertEqual(result, 0)
        self.assertTrue(srt.is_file())
        self.assertTrue(vtt.is_file())

    @unittest.skipUnless(
        shutil.which("ffmpeg") and shutil.which("ffprobe"),
        "ffmpeg/ffprobe are required for the caption CLI integration test",
    )
    def test_cli_round_trip_uses_real_final_audio_fingerprint(self):
        audio = self.root / "voiceover-with-music.mp3"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=44100:cl=mono",
                "-t",
                "6",
                "-c:a",
                "libmp3lame",
                str(audio),
            ],
            capture_output=True,
            check=True,
        )

        draft = subprocess.run(
            ["python3", str(SCRIPT), "draft"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(draft.returncode, 0, draft.stderr)
        manifest_path = self.root / "captions-review.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["speech_review"] = "verified"
        manifest["speaker_review"] = "single-obvious"
        manifest["sound_review"] = "none-meaningful"
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        approved = subprocess.run(
            ["python3", str(SCRIPT), "approve"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(approved.returncode, 0, approved.stderr)

        finalized = subprocess.run(
            ["python3", str(SCRIPT), "finalize"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(finalized.returncode, 0, finalized.stderr)
        validated = subprocess.run(
            ["python3", str(SCRIPT), "validate"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertTrue((self.root / "out" / "final.srt").is_file())
        self.assertTrue((self.root / "out" / "final.vtt").is_file())


if __name__ == "__main__":
    unittest.main()
