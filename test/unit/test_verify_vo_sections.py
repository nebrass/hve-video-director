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
                setattr(m1, "sections", [(0.0, "Original line.")])
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


if __name__ == "__main__":
    unittest.main()
