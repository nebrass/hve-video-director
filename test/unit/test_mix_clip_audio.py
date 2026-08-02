#!/usr/bin/env python3
"""Unit suite for `scripts/mix_clip_audio.py` (Phase 5, Step 5.3a).

The three defects this script replaced are each pinned by a named test:

(a) `--at` is SECONDS — `--at 18.5` must emit `adelay=18500|18500`, the bug the
    prose block shipped when it asked for milliseconds while `index.html`
    states `data-start` in seconds.
(b) the post-mix verification must be able to fail — a clip placed past the end
    of the soundtrack is rejected before any encode, and a mix that leaves the
    placed window unchanged is refused instead of published.
(c) every input rejection.

No real encoding runs: `run_command` and the probe helpers are patched, so the
suite is hermetic and passes on a machine without ffmpeg.
"""

import importlib.util
import re
import shutil
import subprocess
import unittest
import uuid
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "mix_clip_audio.py"
WORK_ROOT = ROOT / "test" / ".work"

CLIP_NAME = "scene-03-demo.mp4"
SOUNDTRACK_NAME = "voiceover-with-music.mp3"
ORIGINAL = b"original soundtrack bytes"
MIXED = b"mixed soundtrack bytes"


def load_module():
    spec = importlib.util.spec_from_file_location("mix_clip_audio", SCRIPT)
    if spec is None or spec.loader is None:
        # Only reachable if the script is missing or unreadable; fail with the
        # path rather than an AttributeError on None three frames deeper.
        raise unittest.SkipTest(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Result:
    """Outcome of one patched `main()` run."""

    def __init__(self, code, stdout, stderr, commands):
        self.code = code
        self.stdout = stdout
        self.stderr = stderr
        self.commands = commands

    @property
    def encodes(self):
        return [c for c in self.commands if c[0] == "ffmpeg"]


class MixClipAudioTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mix_clip_audio = load_module()

    def setUp(self):
        self.work = WORK_ROOT / uuid.uuid4().hex
        self.work.mkdir(parents=True)
        self.clip = self.work / CLIP_NAME
        self.clip.write_bytes(b"clip bytes")
        self.soundtrack = self.work / SOUNDTRACK_NAME
        self.soundtrack.write_bytes(ORIGINAL)

    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)

    # -- helpers ---------------------------------------------------------

    def argv(self, flags=None, clip=None):
        options = {
            "--soundtrack": str(self.soundtrack),
            "--clip-in": "2.0",
            "--clip-out": "8.0",
            "--speed": "1.0",
            "--at": "18.5",
            "--volume": "0.6",
        }
        options.update(flags or {})
        argv = [clip if clip is not None else str(self.clip)]
        for flag, value in options.items():
            if value is not None:
                argv += [flag, str(value)]
        return argv

    def invoke(self, argv=None, *, flags=None, clip=None, durations=None,
               has_audio=True, volumes=(-20.0, -14.0), runner=None, which=True):
        """Run `main()` with ffmpeg/ffprobe fully patched out."""
        table = {CLIP_NAME: 30.0, SOUNDTRACK_NAME: 60.0, "candidate": 60.0}
        table.update(durations or {})
        measurements = list(volumes)

        def fake_duration(path):
            return table.get(Path(path).name, table["candidate"])

        def fake_volume(path, start, duration):
            return measurements.pop(0) if len(measurements) > 1 else measurements[0]

        def default_runner(command):
            destination = Path(command[-1])
            destination.write_bytes(
                MIXED if "-filter_complex" in command else b"clip audio bytes")
            return subprocess.CompletedProcess(command, 0, "", "")

        out, err = StringIO(), StringIO()
        with mock.patch.object(self.mix_clip_audio, "run_command",
                               side_effect=runner or default_runner) as runner_mock, \
                mock.patch.object(self.mix_clip_audio, "probe_duration",
                                  side_effect=fake_duration), \
                mock.patch.object(self.mix_clip_audio, "probe_has_audio",
                                  return_value=has_audio), \
                mock.patch.object(self.mix_clip_audio, "probe_window_mean_volume",
                                  side_effect=fake_volume), \
                mock.patch.object(self.mix_clip_audio.shutil, "which",
                                  side_effect=lambda name: f"/usr/bin/{name}" if which
                                  else None):
            with redirect_stdout(out), redirect_stderr(err):
                code = self.mix_clip_audio.main(argv or self.argv(flags, clip))
            commands = [call.args[0] for call in runner_mock.call_args_list]
        return Result(code, out.getvalue(), err.getvalue(), commands)

    def assertSoundtrackUntouched(self, result):
        self.assertEqual(result.code, 1)
        self.assertEqual(self.soundtrack.read_bytes(), ORIGINAL)
        self.assertIn("left unchanged", result.stderr)
        self.assertEqual(sorted(p.name for p in self.work.glob(".*")), [])

    @staticmethod
    def filter_of(command, flag="-af"):
        return command[command.index(flag) + 1]

    # -- (a) the seconds/milliseconds regression -------------------------

    def test_at_is_seconds_and_converts_to_adelay_milliseconds(self):
        """Defect (a): `data-start="18.5"` means 18.5 SECONDS, not 18 ms."""
        command = self.mix_clip_audio.build_clip_command(
            self.clip, 2.0, 8.0, 1.0, 0.6, 18.5, "clip.wav")
        self.assertIn("adelay=18500|18500", self.filter_of(command))

        for seconds, expected in ((0.0, 0), (0.25, 250), (9.0, 9000), (18.5, 18500)):
            with self.subTest(at=seconds):
                self.assertEqual(self.mix_clip_audio.delay_ms(seconds), expected)

    def test_at_flag_help_names_the_seconds_unit(self):
        # Read the raw help strings: argparse hyphen-wraps `data-start` in the
        # rendered block, which would make a substring assert flaky.
        helps = {action.dest: action.help or ""
                 for action in self.mix_clip_audio._parser()._actions}
        self.assertIn("SECONDS", helps["at"])
        self.assertIn("data-start", helps["at"])
        self.assertIn("milliseconds", helps["at"])
        self.assertIn("SECONDS", helps["clip_in"])
        self.assertIn("SECONDS", helps["clip_out"])

    # -- atempo chaining -------------------------------------------------

    def test_atempo_stages_multiply_to_the_requested_speed(self):
        for speed in (0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0):
            with self.subTest(speed=speed):
                command = self.mix_clip_audio.build_clip_command(
                    self.clip, 0.0, 4.0, speed, 0.5, 1.0, "clip.wav")
                emitted = [float(v) for v in
                           re.findall(r"atempo=([0-9.]+)", self.filter_of(command))]
                self.assertTrue(emitted, "no atempo stage emitted")
                product = 1.0
                for factor in emitted:
                    self.assertGreaterEqual(factor, self.mix_clip_audio.ATEMPO_MIN)
                    self.assertLessEqual(factor, self.mix_clip_audio.ATEMPO_MAX)
                    product *= factor
                # The formatted strings that reach ffmpeg must multiply out, not
                # just the floats they were rounded from.
                self.assertAlmostEqual(product, speed, places=4)

    def test_atempo_uses_fewest_stages(self):
        self.assertEqual(len(self.mix_clip_audio.atempo_chain(1.0)), 1)
        self.assertEqual(len(self.mix_clip_audio.atempo_chain(2.0)), 1)
        self.assertEqual(len(self.mix_clip_audio.atempo_chain(0.5)), 1)
        self.assertEqual(len(self.mix_clip_audio.atempo_chain(3.0)), 2)
        self.assertEqual(len(self.mix_clip_audio.atempo_chain(0.1)), 4)

    # -- argv construction ------------------------------------------------

    def test_clip_command_preserves_the_reviewed_filter_order(self):
        command = self.mix_clip_audio.build_clip_command(
            self.clip, 2.0, 8.0, 2.0, 0.6, 18.5, "clip.wav")
        self.assertEqual(command[0], "ffmpeg")
        self.assertEqual(command[command.index("-ss") + 1], "2.0")
        self.assertEqual(command[command.index("-to") + 1], "8.0")
        self.assertLess(command.index("-to"), command.index("-i"))
        self.assertEqual(command[command.index("-ac") + 1], "2")

        stages = [stage.split("=")[0] for stage in self.filter_of(command).split(",")]
        self.assertEqual(stages, ["atempo", "loudnorm", "volume", "adelay"])
        self.assertIn(self.mix_clip_audio.CLIP_LOUDNORM, self.filter_of(command))
        self.assertIn("volume=0.6", self.filter_of(command))

    def test_mix_command_keeps_the_verified_constants(self):
        command = self.mix_clip_audio.build_mix_command(
            self.soundtrack, "clip.wav", 60.0, "mixed.mp3")
        graph = self.filter_of(command, "-filter_complex")
        self.assertIn("sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300", graph)
        self.assertIn("alimiter=limit=0.89", graph)
        self.assertIn("amix=inputs=2:duration=first:dropout_transition=0:normalize=0", graph)
        self.assertIn("apad=whole_dur=60.0,atrim=duration=60.0", graph)
        # Both sidechain legs pinned to one sample format/rate/layout: a mono
        # voiceover against a stereo key aborts the graph (Step 5.2's lesson).
        self.assertEqual(graph.count(self.mix_clip_audio.STEREO), 2)
        # Never a dynamic loudnorm master here — it undoes the duck.
        self.assertNotIn("loudnorm", graph)
        self.assertEqual(command[command.index("-map") + 1], "[out]")
        self.assertEqual(command[command.index("-c:a") + 1], "libmp3lame")

    def test_probe_window_mean_volume_parses_values_and_silence(self):
        def stub(command):
            self.assertEqual(command[command.index("-ss") + 1], "18.5")
            self.assertEqual(command[command.index("-t") + 1], "6.0")
            self.assertIn("volumedetect", command)
            return subprocess.CompletedProcess(command, 0, "", stderr)

        stderr = "[Parsed_volumedetect_0] mean_volume: -23.4 dB\n"
        with mock.patch.object(self.mix_clip_audio, "run_command", side_effect=stub):
            self.assertAlmostEqual(
                self.mix_clip_audio.probe_window_mean_volume(self.soundtrack, 18.5, 6.0),
                -23.4)

        stderr = "[Parsed_volumedetect_0] mean_volume: -inf dB\n"
        with mock.patch.object(self.mix_clip_audio, "run_command", side_effect=stub):
            self.assertEqual(
                self.mix_clip_audio.probe_window_mean_volume(self.soundtrack, 18.5, 6.0),
                self.mix_clip_audio.SILENCE_FLOOR_DB)

    # -- (c) input validation --------------------------------------------

    def test_rejects_clip_out_not_after_clip_in(self):
        for clip_out in ("2.0", "1.5"):
            with self.subTest(clip_out=clip_out):
                result = self.invoke(flags={"--clip-out": clip_out})
                self.assertSoundtrackUntouched(result)
                self.assertIn("--clip-out", result.stderr)
                self.assertEqual(result.encodes, [])

    def test_rejects_speed_outside_the_supported_range(self):
        for speed in ("0.05", "0", "5.1", "-1"):
            with self.subTest(speed=speed):
                result = self.invoke(flags={"--speed": speed})
                self.assertSoundtrackUntouched(result)
                self.assertIn("--speed", result.stderr)
                self.assertIn(speed.lstrip("+"), result.stderr)

    def test_rejects_volume_outside_zero_to_one(self):
        for volume in ("0", "-0.2", "1.1"):
            with self.subTest(volume=volume):
                result = self.invoke(flags={"--volume": volume})
                self.assertSoundtrackUntouched(result)
                self.assertIn("--volume", result.stderr)

    def test_rejects_negative_at(self):
        result = self.invoke(flags={"--at": "-0.5"})
        self.assertSoundtrackUntouched(result)
        self.assertIn("--at", result.stderr)

    def test_rejects_negative_clip_in(self):
        result = self.invoke(flags={"--clip-in": "-1"})
        self.assertSoundtrackUntouched(result)
        self.assertIn("--clip-in", result.stderr)

    def test_rejects_missing_or_empty_clip(self):
        missing = self.work / "absent.mp4"
        result = self.invoke(clip=str(missing))
        self.assertSoundtrackUntouched(result)
        self.assertIn(str(missing), result.stderr)

        self.clip.write_bytes(b"")
        result = self.invoke()
        self.assertSoundtrackUntouched(result)
        self.assertIn("empty", result.stderr)

    def test_rejects_missing_or_empty_soundtrack(self):
        missing = self.work / "absent.mp3"
        result = self.invoke(flags={"--soundtrack": str(missing)})
        self.assertEqual(result.code, 1)
        self.assertIn(str(missing), result.stderr)
        self.assertEqual(self.soundtrack.read_bytes(), ORIGINAL)

        self.soundtrack.write_bytes(b"")
        result = self.invoke()
        self.assertEqual(result.code, 1)
        self.assertIn("empty", result.stderr)

    def test_rejects_a_clip_with_no_audio_stream(self):
        result = self.invoke(has_audio=False)
        self.assertSoundtrackUntouched(result)
        self.assertIn("no audio stream", result.stderr)
        self.assertEqual(result.encodes, [])

    def test_rejects_a_clip_window_past_the_end_of_the_clip(self):
        result = self.invoke(durations={CLIP_NAME: 5.0}, flags={"--clip-out": "8.0"})
        self.assertSoundtrackUntouched(result)
        self.assertIn("past the end", result.stderr)

    def test_missing_ffmpeg_fails_before_touching_the_soundtrack(self):
        result = self.invoke(which=False)
        self.assertSoundtrackUntouched(result)
        self.assertIn("ffmpeg", result.stderr)

    # -- (b) verifications that can actually fail -------------------------

    def test_rejects_a_clip_that_would_be_truncated_at_the_end_of_the_film(self):
        """Defect (b): the real failure the tautological duration compare missed."""
        result = self.invoke(flags={"--at": "58.0", "--clip-in": "0", "--clip-out": "6.0"})
        self.assertSoundtrackUntouched(result)
        self.assertIn("truncated", result.stderr)
        self.assertIn("4.0", result.stderr)          # seconds that would be lost
        self.assertEqual(result.encodes, [])

    def test_rejects_a_scene_start_at_or_past_the_end_of_the_soundtrack(self):
        result = self.invoke(flags={"--at": "60.0"})
        self.assertSoundtrackUntouched(result)
        self.assertIn("end of the", result.stderr)

    def test_rejects_a_mix_that_leaves_the_placed_window_unchanged(self):
        result = self.invoke(volumes=(-20.0, -20.02))
        self.assertSoundtrackUntouched(result)
        self.assertIn("no-op", result.stderr)
        self.assertEqual(len(result.encodes), 2)     # extract + mix ran, publish refused

    def test_rejects_a_mix_that_changed_the_soundtrack_length(self):
        result = self.invoke(durations={"candidate": 42.0})
        self.assertSoundtrackUntouched(result)
        self.assertIn("length", result.stderr)

    def test_failed_extract_leaves_the_soundtrack_byte_identical(self):
        def failing(command):
            if "-filter_complex" in command:
                self.fail("mix must not run after a failed extract")
            return subprocess.CompletedProcess(command, 1, "", "ffmpeg: no such filter")

        result = self.invoke(runner=failing)
        self.assertSoundtrackUntouched(result)
        self.assertIn("clip audio", result.stderr)

    def test_failed_mix_leaves_the_soundtrack_byte_identical(self):
        def failing(command):
            destination = Path(command[-1])
            if "-filter_complex" in command:
                return subprocess.CompletedProcess(command, 1, "", "filter graph aborted")
            destination.write_bytes(b"clip audio bytes")
            return subprocess.CompletedProcess(command, 0, "", "")

        result = self.invoke(runner=failing)
        self.assertSoundtrackUntouched(result)
        self.assertIn("mix failed", result.stderr)

    # -- success ----------------------------------------------------------

    def test_success_replaces_the_soundtrack_and_removes_every_scratch_file(self):
        result = self.invoke()
        self.assertEqual(result.code, 0, result.stderr)
        self.assertEqual(self.soundtrack.read_bytes(), MIXED)
        self.assertEqual(sorted(p.name for p in self.work.glob(".*")), [])
        self.assertEqual(sorted(p.name for p in self.work.iterdir()),
                         sorted([CLIP_NAME, SOUNDTRACK_NAME]))
        self.assertIn("18.5", result.stdout)

        extract, mixdown = result.encodes[0], result.encodes[1]
        self.assertIn("adelay=18500|18500", self.filter_of(extract))
        self.assertEqual(mixdown[mixdown.index("-i") + 1], str(self.soundtrack))

    def test_scratch_files_are_written_beside_the_soundtrack(self):
        """`os.replace` is only atomic within one filesystem."""
        seen = []

        def watcher(command):
            destination = Path(command[-1])
            seen.append(destination)
            destination.write_bytes(
                MIXED if "-filter_complex" in command else b"clip audio bytes")
            return subprocess.CompletedProcess(command, 0, "", "")

        result = self.invoke(runner=watcher)
        self.assertEqual(result.code, 0, result.stderr)
        self.assertTrue(seen)
        for destination in seen:
            self.assertEqual(destination.parent, self.soundtrack.parent)


if __name__ == "__main__":
    unittest.main()
