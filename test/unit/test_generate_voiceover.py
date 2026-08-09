import importlib.util
import io
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "generate_voiceover.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_voiceover_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seal_sections(project, bodies):
    """Write the manifest `verify_vo_sections.py seal` produces after a verified run."""
    (project / ".hve").mkdir(exist_ok=True)
    (project / ".hve" / "vo-sections.json").write_text(
        json.dumps({
            "schema_version": 1,
            "attest": "engine",
            "sections": {
                sid: {"audio_sha256": hashlib.sha256(body).hexdigest()}
                for sid, body in bodies.items()
            },
        }),
        encoding="utf-8",
    )


class GenerateVoiceoverTest(unittest.TestCase):
    def test_the_retired_acquisition_surface_is_gone(self):
        """M6 removed acquisition; only assembly survives.

        Named symbols rather than a source grep for the API host alone: a
        reintroduced ElevenLabs call is what makes this script need a key, a
        network, and a pip-installed `requests` again — the three properties
        the assembler no longer has, and the reason both audio paths can rely
        on it unconditionally.
        """
        module = load_module()

        for gone in ("API_KEY", "VOICE_ID", "generate_section",
                     "verify_transcript", "check_overlaps"):
            self.assertFalse(hasattr(module, gone), f"{gone} came back")

        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("api.elevenlabs.io", source)
        self.assertNotIn("import requests", source)

    def test_assemble_only_requires_every_external_section(self):
        module = load_module()
        module.sections = [(0.0, "First"), (2.0, "Second")]

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "vo_section_00.mp3").write_bytes(b"audio")
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                with mock.patch.object(module, "get_audio_duration", return_value=1.0):
                    self.assertEqual(module.main(["--assemble-only"]), 2)
            finally:
                os.chdir(old_cwd)

    def assert_main_assembles(self, argv):
        """`argv` loads every section and hands them to the assembler in order."""
        module = load_module()
        module.sections = [(0.0, "First"), (2.0, "Second")]

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "vo_section_00.mp3").write_bytes(b"first")
            Path(tmp, "vo_section_01.mp3").write_bytes(b"second")
            # Since #40 the assembler refuses sections nobody vouched for: an
            # existing file is not evidence it is the right take, because the TTS
            # engine leaves a failed line's previous audio in place. Sealing is what
            # `verify_vo_sections.py seal` writes after a verified synthesis run.
            seal_sections(Path(tmp), {"00": b"first", "01": b"second"})
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                with (
                    mock.patch.object(module, "get_audio_duration", return_value=2.0),
                    mock.patch.object(module, "assemble_voiceover") as assemble,
                ):
                    self.assertEqual(module.main(argv), 0)
                    assemble.assert_called_once_with(
                        [(0.0, "vo_section_00.mp3"), (2.0, "vo_section_01.mp3")]
                    )
            finally:
                os.chdir(old_cwd)

    def test_assemble_only_uses_the_external_sections(self):
        self.assert_main_assembles(["--assemble-only"])

    def test_bare_invocation_assembles_like_the_explicit_flag(self):
        """Assembly is the only mode, so the flag is optional, not removed.

        Both spellings must stay live: workflows pass `--assemble-only`, and a
        bare run used to be the acquisition path — it now assembles instead of
        erroring on a missing key.
        """
        self.assert_main_assembles([])

    def test_unknown_argument_is_rejected(self):
        module = load_module()
        self.assertEqual(module.main(["--generate"]), 2)


class AssemblerBehaviourTest(unittest.TestCase):
    """Characterization of `--assemble-only`, the role BOTH audio paths use.

    Written against the pre-M6 implementation and kept byte-for-byte across the
    prune of the ElevenLabs acquisition path, so "behavior unchanged" is a
    passing assertion rather than a claim: exact start times, silence spacers,
    absolute concat paths, the pad to VIDEO_DURATION, and the overrun warning.
    """

    def run_assembler(self, module, durations):
        """Assemble in a temp cwd with ffmpeg mocked; return (calls, concat)."""
        calls = []
        captured = {}

        def fake_run(argv, *args, **kwargs):
            calls.append(list(argv))
            if "concat" in argv:
                # The concat list is unlinked in `finally`; read it while it lives.
                captured["list"] = Path(argv[argv.index("-i") + 1]).read_text(
                    encoding="utf-8"
                )
            return mock.Mock(returncode=0, stdout="", stderr="")

        def fake_duration(path):
            return durations[Path(path).name]

        with tempfile.TemporaryDirectory() as tmp:
            for name in durations:
                if name.startswith("vo_section_"):
                    Path(tmp, name).write_bytes(b"audio")
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                with (
                    mock.patch.object(module, "subprocess") as sub,
                    mock.patch.object(
                        module, "get_audio_duration", side_effect=fake_duration
                    ),
                ):
                    sub.run.side_effect = fake_run
                    module.assemble_voiceover(
                        [(start, f"vo_section_{i:02d}.mp3")
                         for i, (start, _) in enumerate(module.sections)]
                    )
            finally:
                os.chdir(old_cwd)
        return calls, captured.get("list", "")

    def test_sections_land_at_their_exact_start_times(self):
        module = load_module()
        module.sections = [(1.0, "A"), (6.0, "B"), (9.0, "C")]
        module.VIDEO_DURATION = 20

        calls, concat = self.run_assembler(module, {
            "vo_section_00.mp3": 2.0,
            "vo_section_01.mp3": 5.0,
            "vo_section_02.mp3": 1.0,
            "voiceover.mp3": 20.0,
        })

        entries = [line[len("file '"):-1] for line in concat.splitlines()]
        self.assertTrue(
            all(os.path.isabs(p) for p in entries),
            f"ffmpeg concat resolves relative to the list file, not cwd: {entries}",
        )
        # 1s lead-in, section 0, a 3s gap (6.0 - 1.0 - 2.0), section 1, then
        # section 2 with NO spacer: section 1 overruns its 3s slot by 2s.
        silences = [c[c.index("-t") + 1] for c in calls if "anullsrc=r=44100:cl=mono" in c]
        self.assertEqual(silences, ["1.0", "3.0"])
        # Spacer filenames are temp names, so the shape is asserted by position.
        names = [Path(p).name for p in entries]
        self.assertEqual(names[1], "vo_section_00.mp3")
        self.assertEqual(names[3], "vo_section_01.mp3")
        self.assertEqual(names[4], "vo_section_02.mp3")
        self.assertEqual(len(names), 5)

    def test_output_is_padded_to_the_configured_video_duration(self):
        module = load_module()
        module.sections = [(0.0, "only")]
        module.VIDEO_DURATION = 42

        calls, _ = self.run_assembler(module, {
            "vo_section_00.mp3": 3.0,
            "voiceover.mp3": 42.0,
        })

        pad = next(c for c in calls if "-af" in c)
        self.assertEqual(pad[pad.index("-af") + 1], "apad=whole_dur=42")

    def test_overrunning_section_warns_on_stderr(self):
        module = load_module()
        module.sections = [(0.0, "long"), (2.0, "next")]
        module.VIDEO_DURATION = 10

        with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            self.run_assembler(module, {
                "vo_section_00.mp3": 5.0,
                "vo_section_01.mp3": 1.0,
                "voiceover.mp3": 10.0,
            })

        self.assertIn("overruns", err.getvalue())
        self.assertIn("3.0s", err.getvalue())

    def test_final_overrun_past_video_duration_warns_on_stderr(self):
        module = load_module()
        module.sections = [(0.0, "only")]
        module.VIDEO_DURATION = 5

        with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            self.run_assembler(module, {
                "vo_section_00.mp3": 9.0,
                "voiceover.mp3": 9.0,
            })

        self.assertIn("apad only extends", err.getvalue())


class ManifestAnchorWriteIsAtomic(unittest.TestCase):
    """Recording script_sha256 must not be able to truncate the sealed manifest.

    verify_script_unchanged writes the anchor into the manifest on the first
    verified assembly after a seal — an ordinary run, not an exceptional one.
    An in-place write opens a corruption window on every assembly: a crash or
    full disk mid-write destroys the freshness proof and forces re-synthesis.
    """

    def test_a_failed_anchor_write_preserves_the_manifest(self):
        module = load_module()
        module.sections = [(0.0, "hello")]
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                seal_sections(Path(tmp), {"00": b"audio"})
                manifest = Path(tmp) / ".hve" / "vo-sections.json"
                before = manifest.read_bytes()
                with mock.patch.object(
                    module.os, "replace", side_effect=OSError("disk full")
                ):
                    with self.assertRaises(OSError):
                        module.verify_script_unchanged()
                self.assertEqual(
                    manifest.read_bytes(), before,
                    "a failed anchor write must leave the seal byte-identical",
                )
                self.assertEqual(
                    list(manifest.parent.glob(".vo-sections.json.*.tmp")), []
                )
            finally:
                os.chdir(old_cwd)


class ConcatListRobustnessTest(unittest.TestCase):
    """The concat list must survive paths ffmpeg's demuxer parses specially.

    ffmpeg's concat demuxer reads `file '...'` with shell-like quoting: a
    literal apostrophe inside the quoted path must be written `'\\''`, or the
    path is truncated at the quote and assembly fails with "No such file" —
    for a project living under e.g. `~/Bob's Videos/promo`.
    """

    def assemble_in(self, dirname):
        """Run one-section assembly inside `dirname`; return (concat, abspath)."""
        module = load_module()
        module.sections = [(0.0, "only")]
        module.VIDEO_DURATION = 5
        captured = {}

        def fake_run(argv, *args, **kwargs):
            if "concat" in argv:
                captured["list"] = Path(argv[argv.index("-i") + 1]).read_text(
                    encoding="utf-8"
                )
            return mock.Mock(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp, dirname)
            workdir.mkdir()
            (workdir / "vo_section_00.mp3").write_bytes(b"audio")
            old_cwd = os.getcwd()
            os.chdir(workdir)
            try:
                expected = os.path.abspath("vo_section_00.mp3")
                with (
                    mock.patch.object(module.subprocess, "run", side_effect=fake_run),
                    mock.patch.object(module, "get_audio_duration", return_value=1.0),
                ):
                    module.assemble_voiceover([(0.0, "vo_section_00.mp3")])
            finally:
                os.chdir(old_cwd)
        return captured["list"], expected

    def test_apostrophe_in_project_path_is_concat_escaped(self):
        concat, expected = self.assemble_in("Bob's Videos")
        [line] = [ln for ln in concat.splitlines() if "vo_section_00" in ln]
        self.assertEqual(line, "file '" + expected.replace("'", "'\\''") + "'")

    def test_plain_path_stays_plainly_quoted(self):
        concat, expected = self.assemble_in("plain")
        [line] = [ln for ln in concat.splitlines() if "vo_section_00" in ln]
        self.assertEqual(line, f"file '{expected}'")

    def test_concat_failure_surfaces_ffmpeg_stderr(self):
        """A concat failure must show ffmpeg's own diagnostic, not swallow it.

        `capture_output=True, check=True` turns an assembly failure into a
        bare CalledProcessError whose str() omits stderr — the one line that
        names the unopenable file. The assembler must re-raise with it.
        """
        module = load_module()
        module.sections = [(0.0, "only")]
        module.VIDEO_DURATION = 5

        def fake_run(argv, *args, **kwargs):
            if "concat" in argv:
                raise subprocess.CalledProcessError(
                    1, argv, stderr=b"Impossible to open '/tmp/Bob'"
                )
            return mock.Mock(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "vo_section_00.mp3").write_bytes(b"audio")
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                with (
                    mock.patch.object(module.subprocess, "run", side_effect=fake_run),
                    mock.patch.object(module, "get_audio_duration", return_value=1.0),
                ):
                    with self.assertRaises(RuntimeError) as ctx:
                        module.assemble_voiceover([(0.0, "vo_section_00.mp3")])
            finally:
                os.chdir(old_cwd)
        self.assertIn("Impossible to open", str(ctx.exception))



class AnchorWriteIsDurable(unittest.TestCase):
    """The anchor is published, not just written.

    `verify_script_unchanged` writes the script fingerprint that later assemblies are
    checked against, so a torn write here is a freshness claim nobody can trust. It
    already used tmp + fsync + rename; a review noticed it never fsynced the parent
    directory, which is what makes the *rename* durable — while the sibling writer in
    `verify_vo_sections.write_text_atomic` did. Two atomic writers in one repo, and the
    weaker one guarded the claim.
    """

    def test_both_the_bytes_and_the_rename_are_fsynced(self):
        G = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            manifest = tmp / "anchor.json"
            manifest.write_text(json.dumps({"sections": {"00": "abc"}}), encoding="utf-8")

            seen = []
            real = os.fsync
            with mock.patch.object(G, "MANIFEST", manifest), \
                 mock.patch.object(G, "sections", [("00", "hello there")]), \
                 mock.patch.object(os, "fsync", lambda fd: (seen.append(fd), real(fd))[1]):
                self.assertEqual([], G.verify_script_unchanged())

            self.assertEqual(
                2, len(seen),
                "expected two fsyncs — the file's bytes and the parent directory that "
                f"carries the rename; saw {len(seen)}",
            )
            self.assertIn("script_sha256", json.loads(manifest.read_text(encoding="utf-8")))
            leftovers = [p.name for p in tmp.iterdir() if p.name.startswith(".anchor")]
            self.assertEqual([], leftovers, f"temp file left behind: {leftovers}")


if __name__ == "__main__":
    unittest.main()
