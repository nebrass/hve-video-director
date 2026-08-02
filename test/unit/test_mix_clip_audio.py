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
(d) the double-mix guard — every pass rewrites the canonical soundtrack, so a
    second pass over a window a clip already occupies must be refused, and only
    the user (an explicit `--force`, or deleting the record) may lift that.
    The guard must never lift itself, and a failed run must record nothing.
(e) the mix candidate's container must match `-c:a libmp3lame`, whatever the
    soundtrack is named.

No real encoding runs: `run_command` and the probe helpers are patched, so the
suite is hermetic and passes on a machine without ffmpeg.
"""

import hashlib
import importlib.util
import json
import os
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
STATE_NAME = SOUNDTRACK_NAME + ".clip-mix.json"
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
        self.state = self.work / STATE_NAME

    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)

    # -- helpers ---------------------------------------------------------

    def argv(self, flags=None, clip=None, force=False):
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
        if force:
            argv.append("--force")
        return argv

    def invoke(self, argv=None, *, flags=None, clip=None, force=False, durations=None,
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
                code = self.mix_clip_audio.main(argv or self.argv(flags, clip, force))
            commands = [call.args[0] for call in runner_mock.call_args_list]
        return Result(code, out.getvalue(), err.getvalue(), commands)

    def assertSoundtrackUntouched(self, result, expect=ORIGINAL, state=None):
        """Refusals publish nothing: not the audio, and not a record of it.

        `state` is the sidecar bytes that must survive verbatim; the default
        None means no record may exist — a failed run never counts as done.
        """
        self.assertEqual(result.code, 1)
        self.assertEqual(self.soundtrack.read_bytes(), expect)
        self.assertIn("left unchanged", result.stderr)
        self.assertEqual(sorted(p.name for p in self.work.glob(".*")), [])
        if state is None:
            self.assertFalse(self.state.exists(), "a failed run published a mix record")
        else:
            self.assertEqual(self.state.read_bytes(), state)

    def recorded(self):
        """The sidecar's `mixes`, parsed."""
        return json.loads(self.state.read_text(encoding="utf-8"))["mixes"]

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
        # The mix record is the one file a successful run adds: the scratch
        # candidate, its clip audio and the rollback copy are all gone.
        self.assertEqual(sorted(p.name for p in self.work.iterdir()),
                         sorted([CLIP_NAME, SOUNDTRACK_NAME, STATE_NAME]))
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

        # The record is published by the same `os.replace`, so it and its own
        # scratch file must be siblings of the soundtrack too. No ffmpeg command
        # writes them, so `seen` cannot cover this.
        self.assertEqual(self.state.parent, self.soundtrack.parent)
        scratch = self.mix_clip_audio._scratch_path(self.soundtrack, "clip-mix", ".json")
        self.assertEqual(scratch.parent, self.soundtrack.parent)

    # -- (e) the candidate's container must match the encoder --------------

    def test_mix_command_pins_the_container_to_the_encoder(self):
        command = self.mix_clip_audio.build_mix_command(
            self.soundtrack, "clip.wav", 60.0, "mixed.mp3")
        self.assertEqual(command[command.index("-c:a") + 1], "libmp3lame")
        self.assertEqual(command[command.index("-f") + 1], self.mix_clip_audio.MIX_FORMAT)
        self.assertEqual(self.mix_clip_audio.MIX_FORMAT, "mp3")
        self.assertEqual(self.mix_clip_audio.MIX_SUFFIX, ".mp3")
        # The output path stays last — the tests' runner writes to command[-1].
        self.assertEqual(command[-1], "mixed.mp3")

    def test_candidate_container_ignores_a_non_mp3_soundtrack_name(self):
        """Defect (e): the candidate used to inherit `.m4a`, which libmp3lame
        cannot be muxed into — ffmpeg either fails or mislabels the file."""
        self.soundtrack = self.work / "voiceover-with-music.m4a"
        self.soundtrack.write_bytes(ORIGINAL)
        self.state = self.work / "voiceover-with-music.m4a.clip-mix.json"

        result = self.invoke(durations={"voiceover-with-music.m4a": 60.0})
        self.assertEqual(result.code, 0, result.stderr)

        mixdown = result.encodes[1]
        candidate = mixdown[-1]
        self.assertTrue(candidate.endswith(".mp3"), candidate)
        self.assertNotIn(".m4a", Path(candidate).name)
        self.assertEqual(mixdown[mixdown.index("-f") + 1], "mp3")
        # …and the soundtrack it publishes over keeps its own name.
        self.assertEqual(self.soundtrack.read_bytes(), MIXED)

    # -- (d) the double-mix guard ------------------------------------------

    def test_the_record_lands_beside_the_soundtrack_and_fingerprints_it(self):
        result = self.invoke()
        self.assertEqual(result.code, 0, result.stderr)
        self.assertEqual(self.state, self.mix_clip_audio.state_path_for(self.soundtrack))
        self.assertIn(str(self.state), result.stdout)

        document = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(document["schema_version"],
                         self.mix_clip_audio.STATE_SCHEMA_VERSION)
        self.assertEqual(document["soundtrack"], SOUNDTRACK_NAME)
        # The fingerprint is of the bytes actually published, so a later run can
        # tell whether the record still describes the soundtrack on disk.
        self.assertEqual(document["fingerprint"],
                         {"algorithm": "sha256",
                          "value": hashlib.sha256(MIXED).hexdigest()})
        self.assertEqual(document["fingerprint"]["value"],
                         hashlib.sha256(self.soundtrack.read_bytes()).hexdigest())

        self.assertEqual(len(document["mixes"]), 1)
        entry = document["mixes"][0]
        self.assertEqual(entry["clip"], str(self.clip.resolve()))
        self.assertEqual(entry["at"], 18.5)
        self.assertEqual(entry["at_ms"], 18500)
        self.assertEqual(entry["clip_in"], 2.0)
        self.assertEqual(entry["clip_out"], 8.0)
        self.assertEqual(entry["speed"], 1.0)
        self.assertEqual(entry["volume"], 0.6)
        self.assertEqual(entry["play_duration"], 6.0)

    def test_re_running_the_same_mix_is_refused(self):
        """The Step 5.3a loop run twice, or a retry after a transient failure."""
        self.assertEqual(self.invoke().code, 0)
        recorded = self.state.read_bytes()

        again = self.invoke()
        self.assertSoundtrackUntouched(again, expect=MIXED, state=recorded)
        # Refused before a single encode, not after re-mixing and discarding.
        self.assertEqual(again.encodes, [])
        self.assertIn("already mixed into", again.stderr)

    def test_the_refusal_names_both_ways_forward(self):
        self.assertEqual(self.invoke().code, 0)
        message = self.invoke().stderr
        self.assertIn(str(self.state), message)          # what recorded it
        self.assertIn("18.5", message)                   # where it is placed
        self.assertIn("rebuild the soundtrack", message)  # fix the level/window
        self.assertIn("--force", message)                # layer deliberately
        self.assertIn("Nothing was published", message)

    def test_a_louder_retake_of_the_same_clip_is_refused(self):
        """The hazard a volume-sensitive key would miss: 0.6 then 0.4 leaves
        BOTH passes in the soundtrack, and nothing downstream can hear which."""
        self.assertEqual(self.invoke().code, 0)
        result = self.invoke(flags={"--volume": "0.4"})
        self.assertSoundtrackUntouched(
            result, expect=MIXED, state=self.state.read_bytes())
        self.assertIn("already mixed into", result.stderr)

    def test_a_mistyped_retake_that_overlaps_the_recorded_window_is_refused(self):
        """18.5 mistyped as 18.05 is the same double-mix, not a new placement."""
        self.assertEqual(self.invoke().code, 0)
        result = self.invoke(flags={"--at": "18.05"})
        self.assertSoundtrackUntouched(
            result, expect=MIXED, state=self.state.read_bytes())
        self.assertIn("overlaps", result.stderr)

    def test_the_same_clip_at_a_separate_placement_is_allowed(self):
        """One clip may legitimately appear in two scenes — the windows differ."""
        self.assertEqual(self.invoke().code, 0)          # 18.5s–24.5s
        result = self.invoke(flags={"--at": "30.0"})     # 30.0s–36.0s
        self.assertEqual(result.code, 0, result.stderr)
        self.assertEqual([entry["at"] for entry in self.recorded()], [18.5, 30.0])

    def test_a_different_clip_over_the_same_window_is_allowed(self):
        other = self.work / "scene-04-other.mp4"
        other.write_bytes(b"other clip bytes")
        self.assertEqual(self.invoke().code, 0)
        result = self.invoke(clip=str(other))
        self.assertEqual(result.code, 0, result.stderr)
        self.assertEqual([Path(entry["clip"]).name for entry in self.recorded()],
                         [CLIP_NAME, other.name])

    def test_the_same_clip_reached_by_another_spelling_is_the_same_clip(self):
        self.assertEqual(self.invoke().code, 0)
        # `..`, not `.`: pathlib collapses a `.` component at construction, so a
        # `.`-spelled path would be byte-identical to the first run's and the
        # test would pass without `mix_record` resolving anything.
        (self.work / "sub").mkdir()
        spelled = str(self.work / "sub" / ".." / CLIP_NAME)
        self.assertNotEqual(spelled, str(self.clip))
        result = self.invoke(clip=spelled)
        self.assertSoundtrackUntouched(
            result, expect=MIXED, state=self.state.read_bytes())
        self.assertIn("already mixed into", result.stderr)

    def test_force_layers_a_second_pass_and_records_both(self):
        self.assertEqual(self.invoke().code, 0)
        result = self.invoke(force=True)
        self.assertEqual(result.code, 0, result.stderr)
        self.assertIn("--force", result.stderr)          # the override is announced
        self.assertEqual([entry["at"] for entry in self.recorded()], [18.5, 18.5])

    def test_force_does_not_bypass_any_other_guard(self):
        """An escape hatch for one refusal, not a global override."""
        cases = (
            ({"--at": "58.0", "--clip-in": "0", "--clip-out": "6.0"}, "truncated"),
            ({"--speed": "9.0"}, "--speed"),
            ({"--volume": "1.4"}, "--volume"),
        )
        for flags, expected in cases:
            with self.subTest(flags=flags):
                result = self.invoke(flags=flags, force=True)
                self.assertSoundtrackUntouched(result)
                self.assertIn(expected, result.stderr)

        with self.subTest(case="no-op mix"):
            result = self.invoke(force=True, volumes=(-20.0, -20.02))
            self.assertSoundtrackUntouched(result)
            self.assertIn("no-op", result.stderr)

    def test_a_record_that_no_longer_matches_the_soundtrack_is_refused(self):
        """The guard never resets itself: when the soundtrack's bytes moved, the
        script cannot tell whether the recorded clip audio is still in there, so
        it refuses and names both remedies instead of guessing one."""
        self.assertEqual(self.invoke().code, 0)
        recorded = self.state.read_bytes()
        self.soundtrack.write_bytes(b"a soundtrack rebuilt in step 5.2")

        result = self.invoke()
        self.assertSoundtrackUntouched(
            result, expect=b"a soundtrack rebuilt in step 5.2", state=recorded)
        self.assertEqual(result.encodes, [])
        self.assertIn("sha256", result.stderr)
        self.assertIn(f"delete {self.state}", result.stderr)
        self.assertIn("--force", result.stderr)

    def test_force_accepts_a_record_that_no_longer_matches_and_keeps_history(self):
        self.assertEqual(self.invoke().code, 0)
        self.soundtrack.write_bytes(b"an sfx pass rewrote this")

        result = self.invoke(force=True)
        self.assertEqual(result.code, 0, result.stderr)
        self.assertIn("--force", result.stderr)
        self.assertEqual(len(self.recorded()), 2)

    def test_deleting_the_record_is_safe_and_clears_the_guard(self):
        """The user's own reset. Nothing but this guard reads the sidecar, so
        removing it costs a memory, never the soundtrack."""
        self.assertEqual(self.invoke().code, 0)
        self.state.unlink()

        result = self.invoke()
        self.assertEqual(result.code, 0, result.stderr)
        self.assertEqual(self.soundtrack.read_bytes(), MIXED)
        self.assertEqual(len(self.recorded()), 1)

    def test_an_unreadable_record_is_refused_and_force_rewrites_it(self):
        self.state.write_text("{ this is not json", encoding="utf-8")
        result = self.invoke()
        self.assertSoundtrackUntouched(result, state=b"{ this is not json")
        self.assertEqual(result.encodes, [])
        self.assertIn("cannot be trusted", result.stderr)
        self.assertIn("--force", result.stderr)

        forced = self.invoke(force=True)
        self.assertEqual(forced.code, 0, forced.stderr)
        self.assertEqual(len(self.recorded()), 1)

    def test_a_record_from_another_schema_version_is_refused(self):
        self.state.write_text(json.dumps({
            "schema_version": self.mix_clip_audio.STATE_SCHEMA_VERSION + 1,
            "soundtrack": SOUNDTRACK_NAME,
            "fingerprint": {"algorithm": "sha256",
                            "value": hashlib.sha256(ORIGINAL).hexdigest()},
            "mixes": [],
        }), encoding="utf-8")
        result = self.invoke()
        self.assertEqual(result.code, 1)
        self.assertIn("schema_version", result.stderr)

    def test_a_record_whose_entries_cannot_disarm_the_guard_is_refused(self):
        """A NaN `at` would make every overlap comparison false — that is the
        guard quietly disarming itself, which is what it must never do."""
        for broken in ({"clip": "x.mp4", "at": float("nan"), "play_duration": 6.0},
                       {"clip": "x.mp4", "at": 18.5, "play_duration": float("inf")},
                       {"clip": "x.mp4", "at": 18.5},
                       "not an entry"):
            with self.subTest(entry=broken):
                self.state.write_text(json.dumps({
                    "schema_version": self.mix_clip_audio.STATE_SCHEMA_VERSION,
                    "soundtrack": SOUNDTRACK_NAME,
                    "fingerprint": {"algorithm": "sha256",
                                    "value": hashlib.sha256(ORIGINAL).hexdigest()},
                    "mixes": [broken],
                }), encoding="utf-8")
                result = self.invoke()
                self.assertEqual(result.code, 1)
                self.assertIn("cannot be trusted", result.stderr)
                self.assertEqual(result.encodes, [])
                self.assertEqual(self.soundtrack.read_bytes(), ORIGINAL)

    def test_a_failed_mix_leaves_an_earlier_record_byte_identical(self):
        """A failed retake never counts as complete — and never edits history."""
        self.assertEqual(self.invoke().code, 0)
        recorded = self.state.read_bytes()

        other = self.work / "scene-04-other.mp4"
        other.write_bytes(b"other clip bytes")

        def failing(command):
            if "-filter_complex" in command:
                return subprocess.CompletedProcess(command, 1, "", "filter graph aborted")
            Path(command[-1]).write_bytes(b"clip audio bytes")
            return subprocess.CompletedProcess(command, 0, "", "")

        result = self.invoke(clip=str(other), runner=failing)
        self.assertSoundtrackUntouched(result, expect=MIXED, state=recorded)
        self.assertEqual(json.loads(recorded.decode())["mixes"][0]["clip"],
                         str(self.clip.resolve()))

    def test_a_disk_failure_before_publishing_reports_the_soundtrack_unchanged(self):
        """Not a traceback: the rollback copy and the record write are new I/O,
        and both happen before anything is published, so the standing promise
        (`Soundtrack left unchanged`) has to survive them failing."""
        for target, name in ((self.mix_clip_audio.shutil, "copy2"),
                             (self.mix_clip_audio, "_write_json")):
            with self.subTest(failing=name):
                with mock.patch.object(
                        target, name,
                        side_effect=OSError(28, "No space left on device")):
                    result = self.invoke()
                self.assertSoundtrackUntouched(result)
                self.assertIn("No space left on device", result.stderr)

    def test_a_record_that_cannot_be_written_rolls_the_soundtrack_back(self):
        """The mix and its record publish together or not at all: a soundtrack
        nothing remembers is exactly the state the guard exists to prevent."""
        real_replace = os.replace

        def replace(source, destination, *args, **kwargs):
            if Path(destination) == self.state:
                raise OSError(28, "No space left on device")
            return real_replace(source, destination, *args, **kwargs)

        with mock.patch.object(self.mix_clip_audio.os, "replace", side_effect=replace):
            result = self.invoke()

        self.assertSoundtrackUntouched(result)
        self.assertIn("publishing the mix failed", result.stderr)
        self.assertEqual(sorted(p.name for p in self.work.iterdir()),
                         sorted([CLIP_NAME, SOUNDTRACK_NAME]))


if __name__ == "__main__":
    unittest.main()
