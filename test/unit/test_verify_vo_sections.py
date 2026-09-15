#!/usr/bin/env python3
"""A section left over from an earlier run must not reach the film.

The delegated TTS engine reports a failed line as a non-fatal anomaly, exits 0, and
never deletes a destination file before writing — so the previous run's audio survives
at the exact expected path. In one production session 8 of 83 requested lines failed
that way across four batches, and on the rewrite pass three of them left PRE-REWRITE
takes on disk. Assembling there would have shipped narration the storyboard no longer
said, with every downstream check green.

Two engine properties rule out the obvious defences, and the tests below encode both:

  * Its success predicate is `exit == 0 and the file exists`, so a stale file can be
    reported as a success WITH a plausible duration and word timings. Counting
    `voices[]` cannot prove freshness.
  * `--only tts` replaces `voices[]` wholesale, so a 2-line retry leaves the metadata
    describing 2 sections out of 40. Counting entries is wrong on the recovery path.

Freshness is therefore established by ABSENCE — clear the targets first, so a line
that fails to regenerate is missing rather than stale — and made provable downstream
by a sealed manifest, because assembly runs in a different process and cannot observe
the deletion.
"""

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(
        f"_{name}", ROOT / "scripts" / f"{name}.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VV = load("verify_vo_sections")


def make_project(tmp, ids=("00", "01"), text="Some narration."):
    project = Path(tmp)
    (project / "assets" / "voice").mkdir(parents=True)
    (project / "audio_request.json").write_text(
        json.dumps({
            "provider": "elevenlabs", "voice": "v", "lang": "en", "speed": 1.0,
            "lines": [{"id": i, "text": f"{text} {i}"} for i in ids],
        }),
        encoding="utf-8",
    )
    return project


def write_section(project, section_id, body=b"fresh-audio"):
    (project / f"vo_section_{section_id}.mp3").write_bytes(body)
    (project / "assets" / "voice" / f"{section_id}.wav").write_bytes(body)


def write_language_profile(project, *, text_language="en"):
    """Synthetic repo-owned identity, not evidence of a real provider capability."""
    request = json.loads((project / "audio_request.json").read_text(encoding="utf-8"))
    speech = {
        "provider": request["provider"], "voice": request["voice"], "model": request["model"],
        "narration_language": request["narration_language"],
        "tts_language": request["lang"], "asr_language": request["narration_language"].split("-")[0],
    }
    profile = {
        "schema_version": 1,
        "text": {"tag": text_language},
        "narration": {"tag": request["narration_language"]},
        "speech": speech, "speech_fingerprint": f"sha256:{VV.sha256_json(speech)}",
    }
    (project / ".hve").mkdir(exist_ok=True)
    (project / ".hve" / "language-profile.json").write_text(json.dumps(profile), encoding="utf-8")
    return profile


def make_language_project(tmp):
    project = make_project(tmp)
    path = project / "audio_request.json"
    request = json.loads(path.read_text(encoding="utf-8"))
    request.update(model="synthetic-model-v1", narration_language="en")
    path.write_text(json.dumps(request), encoding="utf-8")
    write_language_profile(project)
    return project


class PrepareClearsBothLayers(unittest.TestCase):
    """Absence is the only unforgeable freshness signal, so clearing must be complete."""

    def test_prepare_removes_the_wav_and_the_transcoded_mp3(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(tmp)
            write_section(project, "00", b"stale")
            write_section(project, "01", b"stale")
            self.assertEqual(VV.main(["--project-dir", str(project), "prepare", "00"]), 0)
            # Clearing only the wav would let a stale mp3 survive; clearing only the
            # mp3 would let the next transcode launder a stale wav into a fresh one.
            self.assertFalse((project / "vo_section_00.mp3").exists())
            self.assertFalse((project / "assets" / "voice" / "00.wav").exists())
            self.assertTrue((project / "vo_section_01.mp3").exists(),
                            "an untargeted section must survive — re-billing a good "
                            "take rolls the ~10% failure dice again")

    def test_prepare_records_a_pending_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(tmp)
            VV.main(["--project-dir", str(project), "prepare"])
            pending = json.loads(
                (project / ".hve" / "vo-sections.pending.json").read_text()
            )
            self.assertEqual(pending["ids"], ["00", "01"])


class CheckFindsTheGap(unittest.TestCase):
    def test_a_line_that_never_came_back_is_named_and_a_retry_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(tmp)
            VV.main(["--project-dir", str(project), "prepare"])
            write_section(project, "00")          # 00 synthesized, 01 failed
            code = VV.main(["--project-dir", str(project), "check", "--json"])
            self.assertEqual(code, 1)
            retry = json.loads((project / "audio_request.retry.json").read_text())
            self.assertEqual([l["id"] for l in retry["lines"]], ["01"],
                             "retry must carry only the failed id")
            self.assertEqual(retry["provider"], "elevenlabs",
                             "retry must preserve the confirmed provider — never "
                             "substitute one on failure")

    def test_a_complete_set_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(tmp)
            VV.main(["--project-dir", str(project), "prepare"])
            write_section(project, "00")
            write_section(project, "01")
            self.assertEqual(VV.main(["--project-dir", str(project), "check"]), 0)


class RetryRoundKeepsAbsenceProof(unittest.TestCase):
    """A subset re-prepare must extend the round, not restart it.

    The documented retry flow is prepare → engine (partial) → check →
    prepare <failed ids> → engine → seal. Overwriting the pending marker on
    the second prepare erases the first round's absence-proof, and seal then
    refuses exactly the sections that synthesized correctly — with
    "prepare with no ids and synthesize again" (re-billing every line, the
    thing check's own advice forbids) as the only escape.
    """

    def test_seal_succeeds_after_a_subset_reprepare(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(tmp)
            self.assertEqual(VV.main(["--project-dir", str(project), "prepare"]), 0)
            write_section(project, "00")          # 00 came back, 01 failed
            self.assertEqual(VV.main(["--project-dir", str(project), "check"]), 1)
            self.assertEqual(
                VV.main(["--project-dir", str(project), "prepare", "01"]), 0
            )
            write_section(project, "01")          # retry succeeded
            self.assertEqual(VV.main(["--project-dir", str(project), "seal"]), 0)
            manifest = json.loads((project / ".hve" / "vo-sections.json").read_text())
            self.assertEqual(sorted(manifest["sections"]), ["00", "01"])

    def test_subset_reprepare_unions_the_pending_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(tmp)
            VV.main(["--project-dir", str(project), "prepare"])
            write_section(project, "00")
            VV.main(["--project-dir", str(project), "prepare", "01"])
            pending = json.loads(
                (project / ".hve" / "vo-sections.pending.json").read_text()
            )
            self.assertEqual(pending["ids"], ["00", "01"])
            self.assertEqual(sorted(pending["request_sha256"]), ["00", "01"])


class SealBindsBytes(unittest.TestCase):
    def test_seal_without_prepare_is_refused(self):
        """Sealing files that were never cleared would certify stale bytes as fresh."""
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(tmp)
            write_section(project, "00")
            write_section(project, "01")
            self.assertEqual(VV.main(["--project-dir", str(project), "seal"]), 2)
            self.assertFalse((project / ".hve" / "vo-sections.json").exists())

    def test_seal_refuses_an_incomplete_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(tmp)
            VV.main(["--project-dir", str(project), "prepare"])
            write_section(project, "00")
            self.assertEqual(VV.main(["--project-dir", str(project), "seal"]), 1)

    def test_seal_records_the_bytes_and_clears_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(tmp)
            VV.main(["--project-dir", str(project), "prepare"])
            write_section(project, "00", b"aaa")
            write_section(project, "01", b"bbb")
            self.assertEqual(VV.main(["--project-dir", str(project), "seal"]), 0)
            manifest = json.loads((project / ".hve" / "vo-sections.json").read_text())
            self.assertEqual(
                manifest["sections"]["00"]["audio_sha256"],
                hashlib.sha256(b"aaa").hexdigest(),
            )
            self.assertFalse((project / ".hve" / "vo-sections.pending.json").exists())

    def test_the_no_engine_paths_seal_by_attestation(self):
        """A confirmed local voice or a user recording has no request to bind against."""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "vo_section_00.mp3").write_bytes(b"kokoro")
            code = VV.main(["--project-dir", str(project), "seal",
                            "--attest", "local-tts"])
            self.assertEqual(code, 0, "the non-delegated paths must remain usable")
            manifest = json.loads((project / ".hve" / "vo-sections.json").read_text())
            self.assertEqual(manifest["attest"], "local-tts")


class StateWritesAreAtomic(unittest.TestCase):
    """A crash or full disk mid-write must not destroy the previous record.

    The manifest is the proof generate_voiceover.py consults before
    assembling; a truncated manifest destroys the seal and the only remedy
    is re-synthesis. Publication must be tmp-write + rename, so a failed
    publish leaves the sealed record byte-identical.
    """

    def test_a_failed_manifest_publish_preserves_the_previous_seal(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(tmp)
            VV.main(["--project-dir", str(project), "prepare"])
            write_section(project, "00")
            write_section(project, "01")
            self.assertEqual(VV.main(["--project-dir", str(project), "seal"]), 0)
            manifest = project / ".hve" / "vo-sections.json"
            before = manifest.read_bytes()

            VV.main(["--project-dir", str(project), "prepare", "01"])
            write_section(project, "01", b"retake")
            with mock.patch.object(VV.os, "replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    VV.main(["--project-dir", str(project), "seal"])
            self.assertEqual(
                manifest.read_bytes(), before,
                "a failed publish must leave the sealed record byte-identical",
            )
            self.assertEqual(list(manifest.parent.glob(".vo-sections.json.*.tmp")), [])


class UpstreamSchemaChurnDegradesSafely(unittest.TestCase):
    """audio_meta.json is an advisory diagnostic. It must never gate."""

    def test_a_missing_or_unreadable_audio_meta_does_not_fail_the_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(tmp)
            VV.main(["--project-dir", str(project), "prepare"])
            write_section(project, "00")
            write_section(project, "01")
            (project / "audio_meta.json").write_text("{ not json", encoding="utf-8")
            self.assertEqual(
                VV.main(["--project-dir", str(project), "check"]), 0,
                "an upstream schema change must degrade to 'no explanation printed', "
                "never to a false red or a false green",
            )


class AssemblerRefusesStaleSections(unittest.TestCase):
    """The gate that actually stops the film shipping.

    This is the production failure, reproduced: a line fails, its previous take is
    still on disk, and every existence check passes.
    """

    def _assembler(self):
        return load("generate_voiceover")

    def test_a_stale_section_is_refused_even_though_the_file_exists(self):
        module = self._assembler()
        setattr(module, 'sections', [(0.0, "First"), (2.0, "Second")])
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".hve").mkdir()
            Path(project, "vo_section_00.mp3").write_bytes(b"fresh-00")
            Path(project, "vo_section_01.mp3").write_bytes(b"STALE-from-a-previous-run")
            # The manifest records what the engine actually produced this run.
            (project / ".hve" / "vo-sections.json").write_text(json.dumps({
                "schema_version": 1, "attest": "engine",
                "sections": {
                    "00": {"audio_sha256": hashlib.sha256(b"fresh-00").hexdigest()},
                    "01": {"audio_sha256": hashlib.sha256(b"fresh-01").hexdigest()},
                },
            }), encoding="utf-8")
            old = os.getcwd()
            os.chdir(tmp)
            try:
                self.assertEqual(module.main(["--assemble-only"]), 2)
            finally:
                os.chdir(old)

    def test_an_unsealed_project_is_refused(self):
        module = self._assembler()
        setattr(module, 'sections', [(0.0, "First")])
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "vo_section_00.mp3").write_bytes(b"audio")
            old = os.getcwd()
            os.chdir(tmp)
            try:
                self.assertEqual(module.main(["--assemble-only"]), 2)
            finally:
                os.chdir(old)

    def test_editing_the_script_after_sealing_is_refused(self):
        """Matching bytes do not prove the bytes still say what the script says.

        Edit a `sections` line without re-synthesizing and the old take still matches
        the old manifest, so the audio-hash gate alone passes and assembly ships
        narration the script no longer asks for.
        """
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".hve").mkdir()
            Path(project, "vo_section_00.mp3").write_bytes(b"take-00")
            (project / ".hve" / "vo-sections.json").write_text(json.dumps({
                "schema_version": 1, "attest": "engine",
                "sections": {"00": {"audio_sha256":
                                    hashlib.sha256(b"take-00").hexdigest()}},
            }), encoding="utf-8")
            old = os.getcwd()
            os.chdir(tmp)
            try:
                first = load("generate_voiceover")
                setattr(first, "sections", [(0.0, "The line that was spoken.")])
                with mock.patch.object(first, "get_audio_duration", return_value=1.0), \
                     mock.patch.object(first, "assemble_voiceover"):
                    self.assertEqual(first.main(["--assemble-only"]), 0,
                                     "first verified assembly anchors the script hash")

                # Same audio, edited script, no re-synthesis.
                second = load("generate_voiceover")
                setattr(second, "sections", [(0.0, "A DIFFERENT line entirely.")])
                with mock.patch.object(second, "get_audio_duration", return_value=1.0), \
                     mock.patch.object(second, "assemble_voiceover"):
                    self.assertEqual(second.main(["--assemble-only"]), 2)
            finally:
                os.chdir(old)

    def test_a_reseal_reanchors_the_script_instead_of_tripping(self):
        """`seal` rewrites the manifest, so a genuine re-synthesis is not a false positive."""
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(tmp, ids=("00",))
            VV.main(["--project-dir", str(project), "prepare"])
            write_section(project, "00", b"first-take")
            VV.main(["--project-dir", str(project), "seal"])
            old = os.getcwd()
            os.chdir(tmp)
            try:
                m1 = load("generate_voiceover")
                requested_text = json.loads(
                    (project / "audio_request.json").read_text(encoding="utf-8")
                )["lines"][0]["text"]
                setattr(m1, "sections", [(0.0, requested_text)])
                with mock.patch.object(m1, "get_audio_duration", return_value=1.0), \
                     mock.patch.object(m1, "assemble_voiceover"):
                    self.assertEqual(m1.main(["--assemble-only"]), 0)
            finally:
                os.chdir(old)
            # Rewrite the line, re-prepare, re-synthesize, re-seal.
            (project / "audio_request.json").write_text(json.dumps({
                "provider": "elevenlabs", "voice": "v", "lang": "en", "speed": 1.0,
                "lines": [{"id": "00", "text": "Rewritten line."}],
            }), encoding="utf-8")
            VV.main(["--project-dir", str(project), "prepare"])
            write_section(project, "00", b"second-take")
            VV.main(["--project-dir", str(project), "seal"])
            os.chdir(tmp)
            try:
                m2 = load("generate_voiceover")
                setattr(m2, "sections", [(0.0, "Rewritten line.")])
                with mock.patch.object(m2, "get_audio_duration", return_value=1.0), \
                     mock.patch.object(m2, "assemble_voiceover"):
                    self.assertEqual(m2.main(["--assemble-only"]), 0,
                                     "a re-seal must re-anchor, not trip")
            finally:
                os.chdir(old)

    def test_the_escape_hatch_is_a_flag_you_add_not_one_you_remove(self):
        """The guarded path must be the one already written into every workflow."""
        source = (ROOT / "scripts" / "generate_voiceover.py").read_text(encoding="utf-8")
        self.assertIn("--allow-unverified", source)
        # The literal invocation in phase-5-audio.md must stay the checked one.
        audio = (ROOT / "workflows" / "phase-5-audio.md").read_text(encoding="utf-8")
        self.assertIn("python3 ./voiceover.py --assemble-only", audio)
        self.assertNotIn("--assemble-only --allow-unverified", audio)


class SynthesisIdentityTest(unittest.TestCase):
    def run_command(self, project, *args):
        return VV.main(["--project-dir", str(project), *args])

    def synthesize_and_seal(self, project, attest="engine"):
        self.assertEqual(self.run_command(project, "prepare"), 0)
        write_section(project, "00", b"same-00")
        write_section(project, "01", b"same-01")
        self.assertEqual(self.run_command(project, "seal", "--attest", attest), 0)
        return json.loads((project / ".hve" / "vo-sections.json").read_text(encoding="utf-8"))

    def test_all_synthesis_settings_invalidate_unchanged_text_subset_reuse(self):
        for label, changes in (
            ("provider", {"provider": "kokoro"}),
            ("voice", {"voice": "other-voice"}),
            ("model", {"model": "synthetic-model-v2"}),
            ("language", {"lang": "ja", "narration_language": "ja"}),
            ("native-code", {"lang": "en-us"}),
            ("locale", {"narration_language": "en-US"}),
            ("speed", {"speed": 1.25}),
            ("voice-settings", {"voice_settings": {"stability": 0.4}}),
            ("other-tts-data", {"seed": 79, "normalization": {"numbers": False}}),
        ):
            with self.subTest(setting=label), tempfile.TemporaryDirectory() as tmp:
                project = make_language_project(tmp)
                original = self.synthesize_and_seal(project)
                path = project / "audio_request.json"
                request = json.loads(path.read_text(encoding="utf-8"))
                request.update(changes)
                path.write_text(json.dumps(request), encoding="utf-8")
                write_language_profile(project)
                manifest = project / ".hve" / "vo-sections.json"
                before = manifest.read_bytes()
                self.assertEqual(self.run_command(project, "prepare", "01"), 2)
                self.assertEqual(before, manifest.read_bytes())
                self.assertEqual((project / "vo_section_01.mp3").read_bytes(), b"same-01")
                self.assertEqual((project / "assets" / "voice" / "01.wav").read_bytes(), b"same-01")
                self.assertFalse((project / ".hve" / "vo-sections.pending.json").exists())
                replacement = self.synthesize_and_seal(project)
                self.assertNotEqual(original["synthesis_sha256"], replacement["synthesis_sha256"])
                self.assertNotEqual(original["sections"]["00"]["request_sha256"],
                                    replacement["sections"]["00"]["request_sha256"])
                self.assertEqual(original["script_sha256"], replacement["script_sha256"])

    def test_bgm_sfx_and_text_only_locale_changes_do_not_force_narration_regeneration(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_language_project(tmp)
            original = self.synthesize_and_seal(project)
            path = project / "audio_request.json"
            request = json.loads(path.read_text(encoding="utf-8"))
            request.update(bgm={"query": "a different music bed"}, sfx=[{"at": 1, "query": "tap"}])
            path.write_text(json.dumps(request), encoding="utf-8")
            write_language_profile(project, text_language="ar")
            self.assertEqual(self.run_command(project, "prepare", "01"), 0)
            self.assertEqual((project / "vo_section_00.mp3").read_bytes(), b"same-00")
            write_section(project, "01", b"retake-01")
            self.assertEqual(self.run_command(project, "seal"), 0)
            replacement = json.loads((project / ".hve" / "vo-sections.json").read_text())
            self.assertEqual(original["synthesis_sha256"], replacement["synthesis_sha256"])
            self.assertEqual(original["speech_fingerprint"], replacement["speech_fingerprint"])
            self.assertEqual(original["sections"]["00"], replacement["sections"]["00"])

    def test_edited_after_prepare_fails_check_and_seal_without_publishing(self):
        for change in ("text", "line-setting", "speed", "model", "line-order", "line-removed"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                project = make_language_project(tmp)
                self.synthesize_and_seal(project)
                self.assertEqual(self.run_command(project, "prepare"), 0)
                write_section(project, "00")
                write_section(project, "01")
                path = project / "audio_request.json"
                request = json.loads(path.read_text(encoding="utf-8"))
                if change == "text":
                    request["lines"][0]["text"] += " "
                elif change == "line-setting":
                    request["lines"][0]["style"] = "quiet"
                elif change == "line-order":
                    request["lines"].reverse()
                elif change == "line-removed":
                    request["lines"].pop()
                else:
                    request[change] = 1.1 if change == "speed" else "synthetic-model-v2"
                path.write_text(json.dumps(request), encoding="utf-8")
                write_language_profile(project)
                proof = project / ".hve" / "vo-sections.json"
                pending = project / ".hve" / "vo-sections.pending.json"
                before = {p: p.read_bytes() for p in (proof, pending)}
                self.assertEqual(self.run_command(project, "check"), 2)
                self.assertEqual(self.run_command(project, "seal"), 2)
                self.assertEqual(before, {p: p.read_bytes() for p in before})
                self.assertFalse((project / "audio_request.retry.json").exists())

    def test_prepared_id_hashes_are_checked_even_when_global_request_hash_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_language_project(tmp)
            self.assertEqual(self.run_command(project, "prepare"), 0)
            write_section(project, "00")
            write_section(project, "01")
            path = project / ".hve" / "vo-sections.pending.json"
            pending = json.loads(path.read_text())
            pending["request_sha256"]["00"] = "0" * 64
            path.write_text(json.dumps(pending), encoding="utf-8")
            self.assertEqual(self.run_command(project, "seal"), 2)
            self.assertFalse((project / ".hve" / "vo-sections.json").exists())

    def test_retry_preserves_complete_line_metadata_and_current_round_proofs(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_language_project(tmp)
            path = project / "audio_request.json"
            request = json.loads(path.read_text())
            request["lines"][1]["pronunciation"] = {"API": "user-reviewed pronunciation"}
            request["voice_settings"] = {"stability": 0.5}
            path.write_text(json.dumps(request), encoding="utf-8")
            self.assertEqual(self.run_command(project, "prepare"), 0)
            write_section(project, "00")
            self.assertEqual(self.run_command(project, "check"), 1)
            retry = json.loads((project / "audio_request.retry.json").read_text())
            self.assertEqual(retry, {**request, "lines": [request["lines"][1]]})
            self.assertEqual(self.run_command(project, "prepare", "01"), 0)
            write_section(project, "01")
            self.assertEqual(self.run_command(project, "seal"), 0)

    def test_retry_after_a_full_settings_change_ignores_the_obsolete_prior_seal(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_language_project(tmp)
            self.synthesize_and_seal(project)
            path = project / "audio_request.json"
            request = json.loads(path.read_text())
            request["speed"] = 1.1
            path.write_text(json.dumps(request), encoding="utf-8")
            self.assertEqual(self.run_command(project, "prepare"), 0)
            write_section(project, "00")
            self.assertEqual(self.run_command(project, "check"), 1)
            self.assertEqual(self.run_command(project, "prepare", "01"), 0)
            write_section(project, "01")
            self.assertEqual(self.run_command(project, "seal"), 0)

    def test_changed_line_metadata_requires_preparing_that_line_not_just_other_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_language_project(tmp)
            self.synthesize_and_seal(project)
            path = project / "audio_request.json"
            request = json.loads(path.read_text())
            request["lines"][0]["style"] = "quiet"
            path.write_text(json.dumps(request), encoding="utf-8")
            self.assertEqual(self.run_command(project, "prepare", "01"), 0)
            write_section(project, "01")
            self.assertEqual(self.run_command(project, "seal"), 1)
            self.assertEqual(self.run_command(project, "prepare", "00"), 0)
            write_section(project, "00")
            self.assertEqual(self.run_command(project, "seal"), 0)

    def test_edited_pending_line_cannot_be_laundered_by_preparing_another_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_language_project(tmp)
            self.assertEqual(self.run_command(project, "prepare"), 0)
            write_section(project, "00")
            write_section(project, "01", b"do-not-delete")
            path = project / "audio_request.json"
            request = json.loads(path.read_text())
            request["lines"][0]["text"] = "Changed."
            path.write_text(json.dumps(request), encoding="utf-8")
            self.assertEqual(self.run_command(project, "prepare", "01"), 2)
            self.assertEqual((project / "vo_section_01.mp3").read_bytes(), b"do-not-delete")
            self.assertEqual(self.run_command(project, "prepare", "00"), 0)
            write_section(project, "00")
            self.assertEqual(self.run_command(project, "seal"), 0)

    def test_legacy_text_only_proofs_need_full_prepare_before_new_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_language_project(tmp)
            request = json.loads((project / "audio_request.json").read_text())
            for line in request["lines"]:
                write_section(project, line["id"])
            path = project / ".hve" / "vo-sections.json"
            path.write_text(json.dumps({
                "schema_version": 1, "attest": "engine", "sections": {
                    line["id"]: {"audio_sha256": VV.sha256_text("fresh-audio"),
                                 "request_sha256": VV.sha256_text(line["text"])}
                    for line in request["lines"]
                },
            }), encoding="utf-8")
            before = path.read_bytes()
            self.assertEqual(self.run_command(project, "prepare", "01"), 2)
            self.assertEqual(path.read_bytes(), before)
            replacement = self.synthesize_and_seal(project)
            self.assertEqual(replacement["schema_version"], 2)
            self.assertIsNotNone(replacement["speech_fingerprint"])

    def test_request_and_profile_errors_are_rejected_before_clearing_any_media(self):
        for kind in ("mismatch", "missing", "bad-fingerprint", "bad-schema"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                project = make_language_project(tmp)
                write_section(project, "00", b"keep")
                profile_path = project / ".hve" / "language-profile.json"
                profile = json.loads(profile_path.read_text())
                if kind == "missing":
                    profile_path.unlink()
                else:
                    if kind == "mismatch":
                        profile["speech"]["voice"] = "another-voice"
                        profile["speech_fingerprint"] = f"sha256:{VV.sha256_json(profile['speech'])}"
                    elif kind == "bad-fingerprint":
                        profile["speech_fingerprint"] = "sha256:" + "0" * 64
                    else:
                        profile["schema_version"] = True
                    profile_path.write_text(json.dumps(profile), encoding="utf-8")
                self.assertEqual(self.run_command(project, "prepare"), 2)
                self.assertEqual((project / "vo_section_00.mp3").read_bytes(), b"keep")
                self.assertEqual((project / "assets" / "voice" / "00.wav").read_bytes(), b"keep")

    def test_malformed_requests_do_not_delete_or_create_proofs(self):
        for value in (
            [], {"lines": []}, {"lines": [{"id": "../00", "text": "unsafe"}]},
            {"lines": [{"id": "00", "text": {"not": "text"}}]},
            {"lines": [{"id": "00", "text": "x"}, {"id": "00", "text": "y"}]},
            {"lines": [{"id": "00", "text": "x"}], "speed": float("nan")},
            {"lines": [{"id": "00", "text": "x"}], "speed": False},
            {"lines": [{"id": "00", "text": "x"}], "voice": []},
        ):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmp:
                project = make_project(tmp)
                write_section(project, "00", b"keep")
                (project / "audio_request.json").write_text(json.dumps(value), encoding="utf-8")
                self.assertEqual(self.run_command(project, "prepare"), 2)
                self.assertEqual((project / "vo_section_00.mp3").read_bytes(), b"keep")
                self.assertEqual((project / "assets" / "voice" / "00.wav").read_bytes(), b"keep")
                self.assertFalse((project / ".hve" / "vo-sections.pending.json").exists())

    def test_language_aware_attestations_require_the_same_preparation_proof(self):
        for attest in ("local-tts", "user-supplied"):
            with self.subTest(attest=attest), tempfile.TemporaryDirectory() as tmp:
                project = make_language_project(tmp)
                write_section(project, "00")
                write_section(project, "01")
                self.assertEqual(self.run_command(project, "seal", "--attest", attest), 2)
                manifest = self.synthesize_and_seal(project, attest)
                self.assertEqual(manifest["attest"], attest)
                self.assertIn("script_sha256", manifest)
                self.assertIsNotNone(manifest["speech_fingerprint"])
                (project / ".hve" / "language-profile.json").unlink()
                request_path = project / "audio_request.json"
                request = json.loads(request_path.read_text())
                del request["narration_language"]
                request_path.write_text(json.dumps(request), encoding="utf-8")
                self.assertEqual(self.run_command(project, "prepare"), 2)
                self.assertEqual(self.run_command(project, "seal", "--attest", attest), 2)

    def test_language_aware_attestations_reject_settings_edited_after_prepare(self):
        for attest in ("local-tts", "user-supplied"):
            with self.subTest(attest=attest), tempfile.TemporaryDirectory() as tmp:
                project = make_language_project(tmp)
                self.assertEqual(self.run_command(project, "prepare"), 0)
                write_section(project, "00")
                write_section(project, "01")
                path = project / "audio_request.json"
                request = json.loads(path.read_text())
                request["voice"] = "another-confirmed-voice"
                path.write_text(json.dumps(request), encoding="utf-8")
                write_language_profile(project)
                self.assertEqual(self.run_command(project, "seal", "--attest", attest), 2)
                self.assertFalse((project / ".hve" / "vo-sections.json").exists())

    def test_real_verifier_seal_is_consumed_by_schema_independent_assembler(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_language_project(tmp)
            request_path = project / "audio_request.json"
            request = json.loads(request_path.read_text())
            request["lines"][0]["text"] = "Cafe\u0301 API."
            request["lines"][1]["text"] = "مرحبا بالعالم"
            request_path.write_text(json.dumps(request), encoding="utf-8")
            self.synthesize_and_seal(project)
            assembler = load("generate_voiceover")
            assembler.sections = [(float(i * 2), line["text"])
                                  for i, line in enumerate(request["lines"])]
            old_cwd = os.getcwd()
            os.chdir(project)
            try:
                with (
                    mock.patch.object(assembler, "get_audio_duration", return_value=1.0),
                    mock.patch.object(assembler, "assemble_voiceover") as assemble,
                ):
                    self.assertEqual(assembler.main(["--assemble-only"]), 0)
                    request.update(lang="ar", narration_language="ar")
                    request_path.write_text(json.dumps(request), encoding="utf-8")
                    write_language_profile(project)
                    self.assertEqual(assembler.main(["--assemble-only"]), 2)
                    self.assertEqual(assemble.call_count, 1)
                    self.synthesize_and_seal(project)
                    self.assertEqual(assembler.main(["--assemble-only"]), 0)
                    self.assertEqual(assemble.call_count, 2)
            finally:
                os.chdir(old_cwd)

    def test_corrupt_pending_state_and_empty_outputs_are_explicit_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_language_project(tmp)
            self.assertEqual(self.run_command(project, "prepare"), 0)
            write_section(project, "00", b"")
            write_section(project, "01")
            self.assertEqual(self.run_command(project, "check"), 1)
            pending = project / ".hve" / "vo-sections.pending.json"
            pending.write_text("{ not json", encoding="utf-8")
            self.assertEqual(self.run_command(project, "prepare", "01"), 2)
            self.assertTrue((project / "vo_section_01.mp3").exists())


if __name__ == "__main__":
    unittest.main()
