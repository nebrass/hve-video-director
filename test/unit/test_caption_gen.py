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

    def create_draft(self, language="en"):
        with mock.patch.object(
            self.module, "_probe_audio_duration", return_value=6.0
        ):
            return self.module.create_review_draft(
                input_path=self.transcript,
                audio_path=self.audio,
                manifest_path=self.manifest,
                srt_path=self.draft_srt,
                vtt_path=self.draft_vtt,
                language=language,
            )

    def approve_manifest(self, *, sound=True, expected_language=None):
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
                expected_language=expected_language,
            )

    def finalize(self, expected_language=None):
        with mock.patch.object(
            self.module, "_probe_audio_duration", return_value=6.0
        ):
            return self.module.finalize_reviewed_captions(
                audio_path=self.audio,
                manifest_path=self.manifest,
                srt_path=self.final_srt,
                vtt_path=self.final_vtt,
                state_path=self.state,
                expected_language=expected_language,
            )

    def validate(self, expected_language=None):
        with mock.patch.object(
            self.module, "_probe_audio_duration", return_value=6.0
        ):
            return self.module.validate_final_captions(
                audio_path=self.audio,
                manifest_path=self.manifest,
                srt_path=self.final_srt,
                vtt_path=self.final_vtt,
                state_path=self.state,
                expected_language=expected_language,
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

    def assert_draft_validates(self, segments, duration=6.0):
        """Draft from `segments`, then run the exact validation approve runs."""
        self.transcript.write_text(json.dumps(segments), encoding="utf-8")
        with mock.patch.object(
            self.module, "_probe_audio_duration", return_value=duration
        ):
            draft = self.module.create_review_draft(
                input_path=self.transcript,
                audio_path=self.audio,
                manifest_path=self.manifest,
                srt_path=self.draft_srt,
                vtt_path=self.draft_vtt,
                force=True,
            )
        draft["reviewed"] = True
        draft["speech_review"] = "verified"
        draft["speaker_review"] = "single-obvious"
        draft["sound_review"] = "none-meaningful"
        with mock.patch.object(
            self.module, "_sha256", return_value=draft["audio"]["sha256"]
        ):
            self.module.validate_review_manifest(
                draft, self.audio, duration, require_approval=False
            )
        return draft

    def test_a_tight_short_sentence_still_yields_a_validatable_cue(self):
        """draft → approve must be green by construction.

        "Go." flushes on sentence end at 0.30s and the next word starts at
        0.31s — the gap cannot cover MIN_DURATION, so the draft must merge
        rather than ship a cue its own validator refuses and ask the human
        to hand-repair machine formatting.
        """
        draft = self.assert_draft_validates([
            {"text": "Go.", "start": 0.0, "end": 0.3},
            {"text": "Now", "start": 0.31, "end": 0.7},
            {"text": "watch", "start": 0.7, "end": 1.0},
            {"text": "this.", "start": 1.0, "end": 1.3},
        ])
        self.assertIn("Go.", draft["cues"][0]["text"])

    def test_a_short_final_cue_is_repaired_within_the_audio(self):
        """The last cue has no following gap — it must borrow from the
        preceding one (or merge) without extending past the final audio."""
        draft = self.assert_draft_validates([
            {"text": "Welcome", "start": 0.0, "end": 1.0},
            {"text": "aboard.", "start": 1.0, "end": 2.0},
            {"text": "Go.", "start": 5.8, "end": 5.95},
        ])
        self.assertLessEqual(draft["cues"][-1]["end"], 6.0 + 0.05)

    def test_an_overwide_token_is_wrapped_not_shipped(self):
        url = "https://example.com/some/extremely/long/path/segment"
        self.assertGreater(len(url), self.module.MAX_CHARS)
        draft = self.assert_draft_validates([
            {"text": "Visit", "start": 0.0, "end": 0.6},
            {"text": url, "start": 0.6, "end": 3.0},
        ])
        wrapped = [c for c in draft["cues"] if "\n" in c["text"]]
        self.assertTrue(wrapped, "the over-wide token must wrap onto a second line")

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

    def test_new_drafts_canonicalize_the_locale(self):
        draft = self.create_draft(language="FR-ca")
        self.assertEqual(draft["language"], "fr-CA")
        self.assertFalse(draft["reviewed"])

    def test_mismatched_approval_leaves_the_unapproved_manifest_untouched(self):
        draft = self.create_draft(language="fr")
        draft.update(speech_review="verified", speaker_review="single-obvious",
                     sound_review="none-meaningful")
        self.manifest.write_text(json.dumps(draft), encoding="utf-8")
        before = self.manifest.read_bytes()
        with mock.patch.object(self.module, "_probe_audio_duration", return_value=6.0):
            with self.assertRaisesRegex(ValueError, "does not match expected narration"):
                self.module.approve_reviewed_captions(
                    self.audio, self.manifest, expected_language="en"
                )
        self.assertEqual(before, self.manifest.read_bytes())
        self.assertFalse(self.state.exists())
        self.assertFalse(self.final_srt.exists())
        self.assertFalse(self.final_vtt.exists())

    def test_language_mismatch_never_changes_approval_or_delivered_outputs(self):
        self.create_draft(language="fr")
        self.approve_manifest(sound=False, expected_language="fr")
        self.finalize(expected_language="fr")
        paths = (self.manifest, self.final_srt, self.final_vtt, self.state)
        before = {path: path.read_bytes() for path in paths}
        for expected in ("en", "fr-CA"):
            for command in ("approve", "finalize", "validate"):
                with self.subTest(expected=expected, command=command):
                    args = [command, "--audio", str(self.audio),
                            "--manifest", str(self.manifest), "--expected-language", expected]
                    if command != "approve":
                        args += ["--srt", str(self.final_srt), "--vtt", str(self.final_vtt),
                                 "--state", str(self.state)]
                    with mock.patch.object(self.module, "_probe_audio_duration", return_value=6.0):
                        self.assertEqual(self.module.main(args), 1)
                    self.assertEqual(before, {path: path.read_bytes() for path in paths})

    def test_canonical_comparison_does_not_rewrite_reviewed_language_or_cues(self):
        draft = self.create_draft(language="en-US")
        draft["language"] = "EN-us"
        draft["cues"][0]["text"] = "Cafe\u0301  API."
        draft.update(speech_review="verified", speaker_review="single-obvious",
                     sound_review="none-meaningful")
        self.manifest.write_text(json.dumps(draft), encoding="utf-8")
        with mock.patch.object(self.module, "_probe_audio_duration", return_value=6.0):
            approved = self.module.approve_reviewed_captions(
                self.audio, self.manifest, expected_language="en-US"
            )
        self.assertEqual(approved["language"], "EN-us")
        self.assertEqual(approved["cues"], draft["cues"])
        before = self.manifest.read_bytes()
        self.finalize(expected_language="en-US")
        self.validate(expected_language="en-US")
        self.assertEqual(self.manifest.read_bytes(), before)
        self.assertIn("Cafe\u0301  API.", self.final_srt.read_text(encoding="utf-8"))
        approved["language"] = "en-US"
        self.manifest.write_text(json.dumps(approved), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed after user approval"):
            self.finalize(expected_language="en-US")

    def test_grapheme_ceilings_include_rtl_marks_and_emoji_without_rewriting(self):
        for language, cluster in (
            ("fr", "e\u0301"), ("ar", "\u0628\u0650"), ("ja", "\U0001f469\u200d\U0001f4bb"),
        ):
            with self.subTest(language=language):
                text = cluster * self.module.MAX_CHARS
                draft = self.module._draft_manifest(
                    [{"start": 0.0, "end": 3.0, "text": text}], self.audio, 6.0, language
                )
                draft.update(speech_review="verified", speaker_review="single-obvious",
                             sound_review="none-meaningful")
                cues = self.module.validate_review_manifest(
                    draft, self.audio, 6.0, require_approval=False, expected_language=language
                )
                self.assertEqual(cues[0]["text"], text)
                draft["cues"][0]["text"] += cluster
                with self.assertRaisesRegex(ValueError, "42 characters"):
                    self.module.validate_review_manifest(
                        draft, self.audio, 6.0, require_approval=False
                    )
                draft["cues"][0].update(text=cluster * 26, end=1.0)
                with self.assertRaisesRegex(ValueError, "26.0 characters/s"):
                    self.module.validate_review_manifest(
                        draft, self.audio, 6.0, require_approval=False
                    )

    def test_language_dependency_errors_do_not_publish_a_draft(self):
        errors = (
            FileNotFoundError("node missing"),
            subprocess.TimeoutExpired(["node"], 30),
        )
        for error in errors:
            with self.subTest(error=type(error).__name__):
                self.module._locale_info.cache_clear()
                with mock.patch.object(self.module.subprocess, "run", side_effect=error):
                    with self.assertRaisesRegex(ValueError, "Node/Intl"):
                        self.create_draft(language="fr")
                self.assertFalse(self.manifest.exists())
                self.assertFalse(self.draft_srt.exists())
                self.assertFalse(self.draft_vtt.exists())
        with self.assertRaisesRegex(ValueError, "language handling failed"):
            self.create_draft(language="not_a_locale")
        self.assertFalse(self.manifest.exists())

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
            ["python3", str(SCRIPT), "draft", "--language", "EN-us"],
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
            ["python3", str(SCRIPT), "approve", "--expected-language", "en-US"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(approved.returncode, 0, approved.stderr)

        finalized = subprocess.run(
            ["python3", str(SCRIPT), "finalize", "--expected-language", "en-US"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(finalized.returncode, 0, finalized.stderr)
        validated = subprocess.run(
            ["python3", str(SCRIPT), "validate", "--expected-language", "en-US"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertTrue((self.root / "out" / "final.srt").is_file())
        self.assertTrue((self.root / "out" / "final.vtt").is_file())


class UnicodeCaptionTextTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def timed_words(self, texts):
        return [{"text": text, "start": i, "end": i + 0.9} for i, text in enumerate(texts)]

    def test_unspaced_scripts_and_rtl_keep_their_actual_word_joining(self):
        for language, tokens, expected in (
            ("ja", ["東京", "大学", "です。"], "東京大学です。"),
            ("zh-Hans", ["你好", "世界。"], "你好世界。"),
            ("th", ["ภาษา", "ไทย", "สนุก"], "ภาษาไทยสนุก"),
            ("ar", ["مرحبا", "بالعالم"], "مرحبا بالعالم"),
            ("fr", ["Bonjour", "le", "monde."], "Bonjour le monde."),
        ):
            with self.subTest(language=language):
                cues = self.module.group_cues(self.timed_words(tokens), language=language)
                self.assertEqual([cue["text"] for cue in cues], [expected])

    def test_mixed_script_keeps_supplied_whitespace_and_latin_word_separation(self):
        words = self.module.load_words(
            self.timed_words(["東京", "  ", "API", "client", " を", "確認"]), language="ja"
        )
        cues = self.module.group_cues(words, language="ja", max_dur=10, max_gap=3)
        self.assertEqual([cue["text"] for cue in cues], ["東京  API client を確認"])
        self.assertEqual(
            self.module._wrap_caption("東京\u3000API  client", 42, language="ja"),
            "東京\u3000API  client",
        )

    def test_sentence_timing_fallback_uses_icu_words_for_cjk_and_thai(self):
        for language, text in (("ja", "東京の大学で日本語を学びます"),
                               ("th", "ภาษาไทยอ่านได้โดยไม่เว้นวรรค")):
            with self.subTest(language=language):
                words = self.module.load_words(
                    {"segments": [{"text": text, "start": 0.0, "end": 20.0}]},
                    language=language,
                )
                self.assertGreater(len(words), 1)
                self.assertEqual("".join(word["text"] for word in words), text)
                self.assertAlmostEqual(words[-1]["end"], 20.0)
                cues = self.module.group_cues(
                    words, language=language, max_words=2, max_chars=100, max_dur=30
                )
                self.assertGreater(len(cues), 1)
                self.assertEqual("".join(cue["text"] for cue in cues), text)
                tools = self.module.CaptionText(language)
                tools.prime([cue["text"] for cue in cues])
                self.assertTrue(all(sum(w["word"] for w in tools.segments(cue["text"])["words"]) <= 2
                                    for cue in cues))

    def test_wrap_never_splits_combining_marks_flags_or_zwj_clusters(self):
        for language, cluster in (
            ("fr", "e\u0301"), ("ar", "\u0628\u0650"),
            ("ja", "\U0001f469\u200d\U0001f469\u200d\U0001f467"),
            ("en", "\U0001f1eb\U0001f1f7"),
        ):
            with self.subTest(language=language):
                text = cluster * 12
                wrapped = self.module._wrap_caption(text, 5, language=language)
                self.assertEqual(wrapped.replace("\n", ""), text)
                self.assertEqual(wrapped.splitlines(), [cluster * 5, cluster * 5, cluster * 2])

    def test_asr_token_boundaries_cannot_break_a_grapheme(self):
        for tokens, expected in (
            (["e", "\u0301"], "e\u0301"),
            (["\U0001f469", "\u200d", "\U0001f4bb"], "\U0001f469\u200d\U0001f4bb"),
        ):
            with self.subTest(tokens=tokens):
                cues = self.module.group_cues(self.timed_words(tokens), max_chars=1, max_dur=1)
                self.assertEqual([cue["text"] for cue in cues], [expected])

    def test_short_cjk_cue_merge_does_not_invent_a_space(self):
        cues = self.module.group_cues([
            {"text": "行。", "start": 0, "end": 0.3},
            {"text": "再看。", "start": 0.31, "end": 1.0},
        ], language="zh")
        self.assertEqual([cue["text"] for cue in cues], ["行。再看。"])

    def test_segmentation_is_batched_not_a_node_process_per_word(self):
        words = self.timed_words(["word"] * 120)
        with mock.patch.object(self.module.subprocess, "run",
                               wraps=self.module.subprocess.run) as run:
            cues = self.module.group_cues(words)
        self.assertTrue(cues)
        self.assertLessEqual(run.call_count, 4)

    def test_bad_unicode_helper_output_fails_explicitly(self):
        tools = self.module.CaptionText("fr")
        for stdout, message in (
            ("not JSON", "invalid JSON"),
            (json.dumps({"locale": tools.locale, "texts": [
                {"graphemes": ["wrong"], "words": [{"text": "bonjour", "word": True}]}
            ]}), "did not preserve"),
        ):
            with self.subTest(stdout=stdout):
                with mock.patch.object(self.module.subprocess, "run",
                                       return_value=mock.Mock(returncode=0, stdout=stdout, stderr="")):
                    with self.assertRaisesRegex(ValueError, message):
                        tools.prime(["bonjour"])


if __name__ == "__main__":
    unittest.main()
