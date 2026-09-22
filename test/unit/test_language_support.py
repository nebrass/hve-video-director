"""Provider-derived language contracts; all catalogs here are synthetic fixtures."""

import json
import os
import subprocess
import sys
import unittest
from unittest import mock

from test_validate_brief import (
    ProjectCase, ROOT, STORY, VB, language_catalog_fixture,
)


class ProviderCatalogTests(unittest.TestCase):
    def test_kokoro_native_codes_follow_cli_case_normalization(self):
        entry = VB.normalize_language_catalog(
            "kokoro", "fixture-kokoro",
            [{"id": "ff_siwis", "defaultLang": "fr-FR"}],
            languages=["fr-FR"],
        )
        self.assertEqual(entry["languages"][0]["code"], "fr-fr")
        self.assertEqual(entry["languages"][0]["tag"], "fr-FR")
        self.assertEqual(entry["voices"]["ff_siwis"]["default_code"], "fr-fr")

    def test_full_kokoro_voice_metadata_supplements_the_curated_list(self):
        catalog = VB.normalize_language_catalog(
            "kokoro", "fixture-kokoro",
            [{"id": "af_nova", "label": "Nova", "defaultLang": "en-us"}],
            voices=[{"id": "hf_alpha", "defaultLang": "hi"},
                    {"id": "af_nova", "defaultLang": "en-us"}],
            languages=["en-us", "hi"],
        )
        self.assertEqual(set(catalog["voices"]), {"af_nova", "hf_alpha"})
        self.assertEqual(catalog["voices"]["af_nova"]["name"], "Nova")

    def test_every_reported_model_language_is_retained(self):
        codes = ["en", "fr", "ar", "ja", "th", "sw"]
        entry = VB.normalize_language_catalog(
            "elevenlabs", "fixture-model",
            [{"model_id": "fixture-model", "can_do_text_to_speech": True,
              "languages": [{"language_id": code, "name": code} for code in codes]}],
            [{"voice_id": "test_voice"}],
        )
        self.assertEqual({row["code"] for row in entry["languages"]}, set(codes))
        self.assertIn("ar", {row["tag"] for row in entry["languages"]})

    def test_model_is_exact_and_must_declare_tts_support(self):
        for model in (
            {"model_id": "different", "can_do_text_to_speech": True, "languages": []},
            {"model_id": "chosen", "can_do_text_to_speech": False, "languages": []},
        ):
            with self.subTest(model=model):
                with self.assertRaisesRegex(VB.BriefFormatError, "TTS-capable"):
                    VB.normalize_language_catalog("elevenlabs", "chosen", [model])

    def test_curated_kokoro_voices_are_not_the_language_limit(self):
        voices = [{"id": "af_nova", "defaultLang": "en-us"}]
        with self.assertRaisesRegex(VB.BriefFormatError, "full supported"):
            VB.normalize_language_catalog("kokoro", "fixture-kokoro", voices)
        catalog = VB.normalize_language_catalog(
            "kokoro", "fixture-kokoro", voices,
            languages=["en-us", "fr-fr", "hi", "it", "pt-br"],
        )
        self.assertEqual(
            {row["tag"] for row in catalog["languages"]},
            {"en-US", "fr-FR", "hi", "it", "pt-BR"},
        )
        profile = VB.build_language_profile(
            {**STORY, "voice": "kokoro:af_nova", "narration_language": "hi"},
            {"providers": {"kokoro": catalog}},
        )
        self.assertEqual(profile["speech"]["tts_language"], "hi")

    def test_kokoro_and_asr_tokens_are_separate(self):
        for language, voice, expected_tts, expected_asr in (
            ("fr", "ff_siwis", "fr-fr", "fr"),
            ("pt-BR", "pf_dora", "pt-br", "pt"),
            ("en", "bm_george", "en-gb", "en"),
        ):
            with self.subTest(language=language):
                profile = VB.build_language_profile(
                    {**STORY, "voice": f"kokoro:{voice}", "narration_language": language},
                    language_catalog_fixture(),
                )
                self.assertEqual(profile["speech"]["tts_language"], expected_tts)
                self.assertEqual(profile["speech"]["asr_language"], expected_asr)

    def test_text_and_narration_directions_are_independent(self):
        profile = VB.build_language_profile(
            {**STORY, "text_language": "ar", "narration_language": "ja"},
            language_catalog_fixture(),
        )
        self.assertEqual(profile["text"]["direction"], "rtl")
        self.assertEqual(profile["narration"]["direction"], "ltr")
        self.assertEqual(profile["narration"]["word_separator"], "")

    def test_unsupported_language_and_unverified_voice_fail(self):
        for change in (
            {"voice": "kokoro:af_nova", "narration_language": "ar"},
            {"voice": "kokoro:af_nova", "narration_language": "fr-CA"},
            {"voice": "elevenlabs:Unknown:not_in_catalog"},
        ):
            with self.subTest(change=change):
                with self.assertRaises(VB.BriefFormatError):
                    VB.build_language_profile({**STORY, **change}, language_catalog_fixture())

    def test_ambiguous_generic_locale_is_not_first_row_wins(self):
        with self.assertRaisesRegex(VB.BriefFormatError, "ambiguous"):
            VB.build_language_profile(
                {**STORY, "voice": "kokoro:jf_alpha", "narration_language": "en"},
                language_catalog_fixture(),
            )

    def test_canonical_and_asr_aliases_preserve_native_tts_code(self):
        profile = VB.build_language_profile(
            {**STORY, "narration_language": "tl"}, language_catalog_fixture(),
        )
        self.assertEqual(profile["narration"]["tag"], "fil")
        self.assertEqual(profile["speech"]["tts_language"], "fil")
        self.assertEqual(profile["speech"]["asr_language"], "tl")

    def test_catalog_mapping_cannot_silently_select_another_language(self):
        catalog = language_catalog_fixture()
        catalog["providers"]["elevenlabs"]["languages"][0]["tag"] = "ar"
        with self.assertRaisesRegex(VB.BriefFormatError, "inconsistent"):
            VB.build_language_profile(STORY, catalog)

    def test_unicode_segmentation_preserves_combining_marks_and_nonspace_words(self):
        for language, value in (
            ("fr", "cafe\u0301"), ("ar", "\u0645\u064e\u0631\u0652\u062d\u064e\u0628\u064b\u0627"),
            ("ja", "\u3053\u3093\u306b\u3061\u306f\u4e16\u754c"),
            ("th", "\u0e2a\u0e27\u0e31\u0e2a\u0e14\u0e35\u0e0a\u0e32\u0e27\u0e42\u0e25\u0e01"),
        ):
            with self.subTest(language=language):
                result = VB.language_tool("segment", {"language": language, "texts": [value]})
                item = result["texts"][0]
                self.assertEqual("".join(item["graphemes"]), value)
                self.assertEqual("".join(word["text"] for word in item["words"]), value)
                if language == "fr":
                    self.assertIn("e\u0301", item["graphemes"])
                if language in {"ja", "th"}:
                    self.assertGreater(len(item["words"]), 1)


class LanguageConsentTests(ProjectCase):
    def test_historical_inspection_does_not_require_node(self):
        self.historical_record()
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_brief.py"),
             "--project-dir", str(self.project), "status", "--json"],
            env={**os.environ, "PATH": ""}, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["language_upgrade_required"])

    def test_new_language_validation_does_not_fall_back_when_node_is_missing(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_brief.py"),
             "--project-dir", str(self.project), "status", "--json"],
            env={**os.environ, "PATH": ""}, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertFalse(report["story"]["complete"])
        self.assertIn("working Node/Intl support", " ".join(report["errors"]))

    def test_native_catalog_profile_commands_preserve_all_reported_languages(self):
        models = self.project / "models.json"
        voices = self.project / "voices.json"
        models.write_text(json.dumps([{
            "model_id": "fixture-new-model", "can_do_text_to_speech": True,
            "languages": [{"language_id": "sw", "name": "Swahili"}],
        }]), encoding="utf-8")
        voices.write_text(json.dumps({
            "voice_id": STORY["voice"].split(":")[-1], "name": "Fixture",
            "unneeded_samples": ["not copied into the catalog"],
        }), encoding="utf-8")
        self.write_plan(story={"text_language": "ar", "narration_language": "sw"})
        result, report = self.json_cli(
            "language-catalog", "--provider", "elevenlabs", "--model", "fixture-new-model",
            "--input", str(models), "--voices", str(voices),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["languages"][0]["tag"], "sw")
        self.assertNotIn("unneeded_samples", (self.project / VB.LANGUAGE_CATALOG_PATH).read_text())
        _, options = self.json_cli("language-options")
        self.assertTrue(any(row["tag"] == "sw" for row in options["languages"]))
        result, checked = self.json_cli("language-profile")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(checked["profile"]["text"]["direction"], "rtl")
        self.assertEqual(checked["profile"]["speech"]["model"], "fixture-new-model")
        self.assertEqual(self.run_cli("confirm-story").returncode, 0)

    def test_catalog_and_profile_schema_versions_require_integers(self):
        for relative in (VB.LANGUAGE_CATALOG_PATH, VB.LANGUAGE_PROFILE_PATH):
            path = self.project / relative
            original = path.read_bytes()
            for version in (True, 1.0, "1"):
                with self.subTest(path=relative, version=version):
                    data = json.loads(original)
                    data["schema_version"] = version
                    path.write_text(json.dumps(data), encoding="utf-8")
                    result, report = self.json_cli("status")
                    self.assertEqual(result.returncode, 1)
                    self.assertFalse(report["story"]["complete"])
            path.write_bytes(original)

    def test_language_options_reject_malformed_cached_capabilities(self):
        path = self.project / VB.LANGUAGE_CATALOG_PATH
        catalog = json.loads(path.read_text())
        catalog["providers"]["elevenlabs"]["languages"][0]["tag"] = "ar"
        path.write_text(json.dumps(catalog), encoding="utf-8")
        result, report = self.json_cli("language-options")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(report["complete"])
        self.assertIn("inconsistent", report["message"])

    def historical_record(self):
        plan = (ROOT / "example" / "project-plan.md").read_bytes()
        state = (ROOT / "example" / ".hve" / "brief-state.json").read_bytes()
        (self.project / "project-plan.md").write_bytes(plan)
        (self.project / VB.STATE_RELATIVE_PATH).write_bytes(state)
        return plan, state

    def test_historical_status_is_unchanged_but_generation_requires_language_consent(self):
        plan, state = self.historical_record()
        result, payload = self.json_cli("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(payload["complete"])
        self.assertTrue(payload["language_upgrade_required"])
        self.assertEqual(payload["brief_schema_version"], 1)
        self.assertTrue(payload["story"]["confirmed"])
        self.assertEqual(payload["stale_phases"], [])
        self.assertEqual(self.run_cli("require", "phase-4").returncode, 1)
        self.assertEqual(self.run_cli("stamp", "phase-5").returncode, 1)
        self.assertEqual((self.project / "project-plan.md").read_bytes(), plan)
        self.assertEqual((self.project / VB.STATE_RELATIVE_PATH).read_bytes(), state)

    def test_language_migration_is_additive_and_does_not_confirm_or_delete(self):
        _, state = self.historical_record()
        plan_path = self.project / "project-plan.md"
        old_values = VB.parse_brief(plan_path)
        output = self.project / "out" / "final.mp4"
        output.parent.mkdir()
        output.write_bytes(b"synthetic prior output")
        result, report = self.json_cli("migrate-languages")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(report["inserted"]), set(VB.LANGUAGE_FIELDS))
        values = VB.parse_brief(plan_path)
        self.assertEqual({key: values[key] for key in old_values}, old_values)
        self.assertTrue(all(VB.is_placeholder(values[key]) for key in VB.LANGUAGE_FIELDS))
        self.assertEqual((self.project / VB.STATE_RELATIVE_PATH).read_bytes(), state)
        self.assertEqual(output.read_bytes(), b"synthetic prior output")
        before = plan_path.read_bytes()
        _, repeated = self.json_cli("migrate-languages")
        self.assertFalse(repeated["changed"])
        self.assertEqual(plan_path.read_bytes(), before)
        self.assertEqual(self.run_cli("confirm-story").returncode, 1)

    def test_language_migration_preserves_crlf_and_existing_bytes(self):
        plan, _ = self.historical_record()
        original = plan.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        path = self.project / "project-plan.md"
        path.write_bytes(original)
        result = self.run_cli("migrate-languages")
        self.assertEqual(result.returncode, 0, result.stderr)
        preserved = b"".join(
            line for line in path.read_bytes().splitlines(keepends=True)
            if not any(line.startswith(f"| {field} |".encode()) for field in VB.LANGUAGE_FIELDS)
        )
        self.assertEqual(preserved, original)

    def test_failed_language_migration_preserves_the_prior_plan(self):
        plan, state = self.historical_record()
        with mock.patch.object(VB.os, "replace", side_effect=OSError("synthetic replace failure")), \
                mock.patch.object(VB, "emit"):
            self.assertEqual(VB.command_migrate_languages(self.project, True), 2)
        self.assertEqual((self.project / "project-plan.md").read_bytes(), plan)
        self.assertEqual((self.project / VB.STATE_RELATIVE_PATH).read_bytes(), state)
        self.assertEqual(list(self.project.glob(".project-plan.md.*.tmp")), [])

    def test_schema_two_cannot_downgrade_by_removing_language_rows(self):
        self.confirm_and_stamp_all()
        path = self.project / "project-plan.md"
        path.write_text(
            "".join(line for line in path.read_text().splitlines(keepends=True)
                    if not any(line.startswith(f"| {field} |") for field in VB.LANGUAGE_FIELDS)),
            encoding="utf-8",
        )
        result, report = self.json_cli("status")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(report["language_upgrade_required"])
        self.assertFalse(report["story"]["complete"])
        self.assertEqual(report["stale_phases"], list(VB.PHASES))

    def test_either_language_change_stales_story_and_audio(self):
        for field in VB.LANGUAGE_FIELDS:
            with self.subTest(field=field):
                self.write_plan()
                self.confirm_and_stamp_all()
                self.write_plan(story={field: "ar"})
                _, report = self.json_cli("status")
                self.assertFalse(report["story"]["confirmed"])
                self.assertFalse(report["audio"]["confirmed"])
                self.assertEqual(report["stale_phases"], list(VB.PHASES))

    def test_profile_must_match_current_language_and_voice(self):
        self.confirm_and_stamp_all()
        profile = self.project / VB.LANGUAGE_PROFILE_PATH
        data = json.loads(profile.read_text())
        data["speech"]["tts_language"] = "fr"
        profile.write_text(json.dumps(data), encoding="utf-8")
        result, report = self.json_cli("status")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(report["story"]["confirmed"])
        self.assertIn("profile is stale", " ".join(report["errors"]))

    def test_model_change_reopens_audio_even_when_story_choices_are_unchanged(self):
        self.confirm_and_stamp_all()
        path = self.project / VB.LANGUAGE_CATALOG_PATH
        catalog = json.loads(path.read_text())
        catalog["providers"]["elevenlabs"]["model"] = "fixture-next-model"
        path.write_text(json.dumps(catalog), encoding="utf-8")
        self.assertEqual(self.run_cli("language-profile").returncode, 0)
        _, report = self.json_cli("status")
        self.assertTrue(report["story"]["confirmed"])
        self.assertFalse(report["audio"]["confirmed"])
        self.assertEqual(report["stale_phases"], ["phase-5"])

    def test_locale_casing_is_canonical_but_not_rewritten(self):
        self.write_plan(story={"text_language": "fr-FR", "narration_language": "fr-FR"})
        self.assertEqual(self.run_cli("confirm-story").returncode, 0)
        self.write_plan(story={"text_language": "FR-fr", "narration_language": "FR-fr"})
        _, report = self.json_cli("status")
        self.assertTrue(report["story"]["confirmed"])
        self.assertEqual(VB.parse_brief(self.project / "project-plan.md")["text_language"], "FR-fr")


if __name__ == "__main__":
    unittest.main()
