#!/usr/bin/env python3

import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import unittest
import uuid
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "capture_screen.py"
STITCH = ROOT / "scripts" / "stitch_clip.py"
WORK_ROOT = ROOT / "test" / ".work"


def load_module():
    spec = importlib.util.spec_from_file_location("capture_screen", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CaptureScreenTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture_screen = load_module()

    def setUp(self):
        self.work = WORK_ROOT / uuid.uuid4().hex
        self.work.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)

    @staticmethod
    def probe(duration=1.0, frames=30):
        return {
            "streams": [{
                "codec_type": "video",
                "codec_name": "h264",
                "profile": "High",
                "pix_fmt": "yuv420p",
                "width": 1280,
                "height": 720,
                "avg_frame_rate": "30/1",
                "r_frame_rate": "30/1",
                "duration": str(duration),
                "nb_read_frames": str(frames),
            }],
            "format": {"duration": str(duration)},
        }

    def test_duration_must_be_positive(self):
        with self.assertRaises(ValueError):
            self.capture_screen.parse_duration("0")
        with self.assertRaises(ValueError):
            self.capture_screen.parse_duration("-1")
        with self.assertRaises(ValueError):
            self.capture_screen.parse_duration("nan")
        with self.assertRaises(ValueError):
            self.capture_screen.parse_duration("inf")
        self.assertEqual(self.capture_screen.parse_duration("2.5"), 2.5)

    def test_region_accepts_odd_dimensions_and_rejects_nonpositive_size(self):
        region = self.capture_screen.parse_region("10,20,321,241")
        self.assertEqual(region, (10, 20, 321, 241))
        for value in ("1,2,0,4", "1,2,4,-1", "1,2,3", "x,2,3,4"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.capture_screen.parse_region(value)

    def test_detects_wsl_before_generic_linux(self):
        with mock.patch.dict(os.environ, {"WSL_DISTRO_NAME": "Ubuntu", "DISPLAY": ":0"},
                             clear=True):
            backend = self.capture_screen.detect_backend(
                platform_name="linux", os_release="Linux microsoft-standard-WSL2")
        self.assertEqual(backend, "wsl")

    def test_builds_macos_native_command_without_audio_flags(self):
        command = self.capture_screen.build_capture_command(
            "macos", 2.5, (10, 20, 321, 241), Path("raw.mov"), {})
        self.assertEqual(command[0], "screencapture")
        self.assertIn("-v", command)
        self.assertIn("-V2.5", command)
        self.assertIn("-R10,20,321,241", command)
        self.assertNotIn("-g", command)
        self.assertNotIn("-A", command)

    def test_builds_windows_gdigrab_region_command(self):
        command = self.capture_screen.build_capture_command(
            "windows", 3, (5, 7, 321, 241), Path("raw.mkv"), {})
        self.assertIn("gdigrab", command)
        self.assertIn("desktop", command)
        self.assertIn("-offset_x", command)
        self.assertIn("5", command)
        self.assertIn("-video_size", command)
        self.assertIn("321x241", command)
        self.assertIn("-an", command)

    def test_builds_x11grab_region_command_from_display(self):
        command = self.capture_screen.build_capture_command(
            "x11", 3, (5, 7, 321, 241), Path("raw.mkv"), {"DISPLAY": ":1"})
        self.assertIn("x11grab", command)
        self.assertIn(":1+5,7", command)
        self.assertIn("321x241", command)
        self.assertIn("-an", command)

    def test_wayland_uses_wf_recorder_only_when_available(self):
        with mock.patch.object(self.capture_screen.shutil, "which",
                               side_effect=lambda name: f"/usr/bin/{name}"
                               if name in {"wf-recorder", "ffmpeg", "ffprobe"} else None):
            self.capture_screen.ensure_backend_available("wayland", {"WAYLAND_DISPLAY": "wayland-0"})
        command = self.capture_screen.build_capture_command(
            "wayland", 3, (5, 7, 321, 241), Path("raw.mkv"),
            {"WAYLAND_DISPLAY": "wayland-0"})
        self.assertEqual(command[0], "wf-recorder")
        self.assertIn("--geometry", command)
        self.assertIn("5,7 321x241", command)
        self.assertNotIn("--audio", command)

    def test_wayland_without_wf_recorder_is_actionable_handoff(self):
        with mock.patch.object(self.capture_screen.shutil, "which", return_value=None):
            with self.assertRaisesRegex(
                    self.capture_screen.CaptureError,
                    "wf-recorder.*record.*Wayland"):
                self.capture_screen.ensure_backend_available(
                    "wayland", {"WAYLAND_DISPLAY": "wayland-0"})

    def test_wayland_duration_is_bounded_with_sigint_without_shell(self):
        process = mock.Mock()
        process.communicate.side_effect = [
            subprocess.TimeoutExpired(["wf-recorder"], 2),
            ("", ""),
        ]
        process.returncode = 0
        with mock.patch.object(self.capture_screen.subprocess, "Popen",
                               return_value=process) as popen:
            self.capture_screen.execute_capture(
                ["wf-recorder", "--file", "raw.mkv"], "wayland", 2)

        process.send_signal.assert_called_once_with(signal.SIGINT)
        self.assertEqual(
            process.communicate.call_args_list[0],
            mock.call(timeout=2 + self.capture_screen.WAYLAND_STARTUP_MARGIN_S))
        self.assertEqual(process.communicate.call_args_list[1], mock.call(timeout=10))
        self.assertIs(popen.call_args.kwargs["shell"], False)

    def test_wayland_recording_window_covers_compositor_startup(self):
        """The raw capture must be LONGER than requested, never shorter.

        wf-recorder has no duration flag; the communicate() timeout is the
        recording window, and it starts at Popen — before the compositor
        stream opens. A window equal to the requested duration yields a raw
        clip that is duration − startup long; the downstream trim cannot
        lengthen it, and the ±1-frame validation then refuses every Wayland
        capture. Startup latency must come out of a margin, not the media.
        """
        process = mock.Mock()
        process.communicate.side_effect = [
            subprocess.TimeoutExpired(["wf-recorder"], 2),
            ("", ""),
        ]
        process.returncode = 0
        with mock.patch.object(self.capture_screen.subprocess, "Popen",
                               return_value=process):
            self.capture_screen.execute_capture(
                ["wf-recorder", "--file", "raw.mkv"], "wayland", 2)
        window = process.communicate.call_args_list[0].kwargs["timeout"]
        self.assertGreaterEqual(window - 2, 1.0,
                                "the recording window must exceed the request "
                                "by a real startup margin")

    def test_wayland_terminate_success_is_bounded_and_actionable(self):
        process = mock.Mock()
        process.communicate.side_effect = [
            subprocess.TimeoutExpired(["wf-recorder"], 2),
            subprocess.TimeoutExpired(["wf-recorder"], 10),
            ("", ""),
        ]
        with mock.patch.object(self.capture_screen.subprocess, "Popen",
                               return_value=process):
            with self.assertRaisesRegex(
                    self.capture_screen.CaptureError,
                    "ignored SIGINT and was terminated"):
                self.capture_screen.execute_capture(
                    ["wf-recorder", "--file", "raw.mkv"], "wayland", 2)

        process.send_signal.assert_called_once_with(signal.SIGINT)
        process.terminate.assert_called_once_with()
        process.kill.assert_not_called()
        self.assertEqual(
            process.communicate.call_args_list,
            [mock.call(timeout=2 + self.capture_screen.WAYLAND_STARTUP_MARGIN_S),
             mock.call(timeout=10), mock.call(timeout=10)])

    def test_wayland_kill_fallback_is_bounded_and_actionable(self):
        process = mock.Mock()
        process.communicate.side_effect = [
            subprocess.TimeoutExpired(["wf-recorder"], 2),
            subprocess.TimeoutExpired(["wf-recorder"], 10),
            subprocess.TimeoutExpired(["wf-recorder"], 10),
            ("", ""),
        ]
        with mock.patch.object(self.capture_screen.subprocess, "Popen",
                               return_value=process):
            with self.assertRaisesRegex(
                    self.capture_screen.CaptureError,
                    "ignored SIGINT and SIGTERM and was killed"):
                self.capture_screen.execute_capture(
                    ["wf-recorder", "--file", "raw.mkv"], "wayland", 2)

        process.send_signal.assert_called_once_with(signal.SIGINT)
        process.terminate.assert_called_once_with()
        process.kill.assert_called_once_with()
        self.assertEqual(
            process.communicate.call_args_list,
            [mock.call(timeout=2 + self.capture_screen.WAYLAND_STARTUP_MARGIN_S),
             mock.call(timeout=10), mock.call(timeout=10), mock.call(timeout=10)])

    def test_wsl_is_explicit_nonzero_handoff(self):
        with self.assertRaisesRegex(
                self.capture_screen.CaptureError,
                "Windows host.*stitch_clip.py"):
            self.capture_screen.ensure_backend_available("wsl", {})

    def test_missing_backend_command_has_remediation(self):
        with mock.patch.object(self.capture_screen.shutil, "which", return_value=None):
            with self.assertRaisesRegex(
                    self.capture_screen.CaptureError,
                    "screencapture.*Screen Recording"):
                self.capture_screen.ensure_backend_available("macos", {})

    def test_missing_ffmpeg_is_not_misreported_as_missing_native_backend(self):
        def available(name):
            return "/usr/sbin/screencapture" if name == "screencapture" else None

        with mock.patch.object(self.capture_screen.shutil, "which",
                               side_effect=available):
            with self.assertRaisesRegex(
                    self.capture_screen.CaptureError,
                    "ffmpeg.*including ffprobe"):
                self.capture_screen.ensure_backend_available("macos", {})

    def test_command_execution_never_uses_a_shell(self):
        completed = subprocess.CompletedProcess(["tool"], 0, "", "")
        with mock.patch.object(self.capture_screen.subprocess, "run",
                               return_value=completed) as run:
            self.capture_screen.run_command(["tool", "arg"])
        _, kwargs = run.call_args
        self.assertIs(kwargs.get("shell", False), False)

    def test_normalizer_uses_sibling_script_via_current_python(self):
        completed = subprocess.CompletedProcess(["tool"], 0, "", "")
        with mock.patch.object(self.capture_screen, "run_command",
                               return_value=completed) as run:
            self.capture_screen.normalize_capture(
                Path("raw.mkv"), Path("candidate.mp4"), 2.5)
        command = run.call_args.args[0]
        self.assertEqual(command[0], sys.executable)
        self.assertEqual(Path(command[1]).name, "stitch_clip.py")
        self.assertEqual(command[2], "raw.mkv::0::2.5")
        self.assertEqual(command[-2:], ["-o", "candidate.mp4"])

    def test_capture_failure_preserves_old_state_and_marks_retake_pending(self):
        output = self.work / "clip.mp4"
        sidecar = self.capture_screen.metadata_path_for(output)
        output.write_bytes(b"previous")
        sidecar.write_text('{"old": true}\n', encoding="utf-8")

        def fail_capture(command, backend, duration):
            Path(command[-1]).write_bytes(b"partial raw")
            raise self.capture_screen.CaptureError("permission denied")

        with mock.patch.object(self.capture_screen, "ensure_backend_available"), \
                mock.patch.object(self.capture_screen, "execute_capture",
                                  side_effect=fail_capture):
            result = self.capture_screen.main([
                "--duration", "1", "--output", str(output), "--backend", "macos"])

        self.assertEqual(result, 1)
        self.assertEqual(output.read_bytes(), b"previous")
        self.assertEqual(sidecar.read_text(encoding="utf-8"), '{"old": true}\n')
        pending = self.capture_screen.pending_path_for(output)
        state = json.loads(pending.read_text(encoding="utf-8"))
        self.assertEqual(state["schema_version"], 1)
        self.assertEqual(state["state"], "pending")
        self.assertEqual(state["requested"]["duration_seconds"], 1.0)
        self.assertIsNone(state["requested"]["region"])
        self.assertEqual(state["requested"]["backend"], "macos")
        self.assertEqual(state["requested"]["output"], str(output))
        self.assertEqual(len(list(self.work.glob("*.raw-*.mov"))), 1)

    def test_pending_marker_exists_before_capture_starts(self):
        output = self.work / "clip.mp4"

        def inspect_pending(command, backend, duration):
            pending = self.capture_screen.pending_path_for(output)
            self.assertTrue(pending.is_file())
            state = json.loads(pending.read_text(encoding="utf-8"))
            self.assertEqual(state["requested"]["region"], [1, 2, 3, 4])
            raise self.capture_screen.CaptureError("stop after inspection")

        with mock.patch.object(self.capture_screen, "ensure_backend_available"), \
                mock.patch.object(self.capture_screen, "execute_capture",
                                  side_effect=inspect_pending):
            result = self.capture_screen.main([
                "--duration", "1", "--region", "1,2,3,4",
                "--output", str(output), "--backend", "macos"])

        self.assertEqual(result, 1)
        self.assertTrue(self.capture_screen.pending_path_for(output).exists())

    def test_concurrent_attempt_fails_without_altering_first_attempt_state(self):
        output = self.work / "clip.mp4"
        sidecar = self.capture_screen.metadata_path_for(output)
        pending = self.capture_screen.pending_path_for(output)
        raw = self.work / ".clip.raw-first.mov"
        candidate = self.work / ".clip.normalized-first.mp4"
        output.write_bytes(b"previous")
        sidecar.write_bytes(b"previous metadata")
        pending.write_bytes(b"first pending")
        raw.write_bytes(b"first raw")
        candidate.write_bytes(b"first candidate")
        first_lock = self.capture_screen.acquire_attempt_lock(output)
        lock_path = self.capture_screen.lock_path_for(output)
        original = {
            path: path.read_bytes()
            for path in (output, sidecar, pending, raw, candidate, lock_path)
        }

        stderr = StringIO()
        contended_lock_contents = None
        try:
            with redirect_stderr(stderr), \
                    mock.patch.object(
                        self.capture_screen, "ensure_backend_available") as ensure:
                result = self.capture_screen.main([
                    "--duration", "1", "--output", str(output),
                    "--backend", "macos"])
            contended_lock_contents = lock_path.read_bytes()
        finally:
            self.capture_screen.release_attempt_lock(first_lock)

        self.assertEqual(result, 1)
        ensure.assert_not_called()
        self.assertIn("already in progress", stderr.getvalue())
        self.assertIn("PID", stderr.getvalue())
        self.assertIn("old", stderr.getvalue())
        self.assertIn("remove this lock manually", stderr.getvalue())
        self.assertEqual(contended_lock_contents, original[lock_path])
        for path, contents in original.items():
            if path == lock_path:
                self.assertFalse(path.exists())
            else:
                self.assertEqual(path.read_bytes(), contents)
        self.assertEqual(
            sorted(path.name for path in self.work.iterdir()),
            sorted(path.name for path in (output, sidecar, pending, raw, candidate)))

    def test_lock_cleanup_refuses_to_remove_another_owner(self):
        output = self.work / "clip.mp4"
        attempt_lock = self.capture_screen.acquire_attempt_lock(output)
        lock_path = self.capture_screen.lock_path_for(output)
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        payload["owner_token"] = "different-owner"
        lock_path.write_text(json.dumps(payload), encoding="utf-8")

        with self.assertRaisesRegex(
                self.capture_screen.CaptureError,
                "ownership changed"):
            self.capture_screen.release_attempt_lock(attempt_lock)

        self.assertTrue(lock_path.exists())
        self.assertEqual(
            json.loads(lock_path.read_text(encoding="utf-8"))["owner_token"],
            "different-owner")

    def test_capture_failure_releases_attempt_lock(self):
        output = self.work / "clip.mp4"

        def fail_capture(command, backend, duration):
            Path(command[-1]).write_bytes(b"partial raw")
            raise self.capture_screen.CaptureError("permission denied")

        with mock.patch.object(self.capture_screen, "ensure_backend_available"), \
                mock.patch.object(self.capture_screen, "execute_capture",
                                  side_effect=fail_capture):
            result = self.capture_screen.main([
                "--duration", "1", "--output", str(output),
                "--backend", "macos"])

        self.assertEqual(result, 1)
        self.assertFalse(self.capture_screen.lock_path_for(output).exists())
        self.assertTrue(self.capture_screen.pending_path_for(output).exists())
        self.assertEqual(len(list(self.work.glob("*.raw-*.mov"))), 1)

    def test_capture_success_releases_attempt_lock(self):
        output = self.work / "clip.mp4"

        def capture(command, backend, duration):
            Path(command[-1]).write_bytes(b"raw")

        def normalize(raw, candidate, duration):
            candidate.write_bytes(b"normalized")

        with mock.patch.object(self.capture_screen, "ensure_backend_available"), \
                mock.patch.object(self.capture_screen, "execute_capture",
                                  side_effect=capture), \
                mock.patch.object(self.capture_screen, "normalize_capture",
                                  side_effect=normalize), \
                mock.patch.object(
                    self.capture_screen, "validate_clip_contract",
                    return_value=self.probe()):
            result = self.capture_screen.main([
                "--duration", "1", "--output", str(output),
                "--backend", "macos"])

        self.assertEqual(result, 0)
        self.assertFalse(self.capture_screen.lock_path_for(output).exists())
        self.assertFalse(self.capture_screen.pending_path_for(output).exists())

    def test_normalize_failure_preserves_previous_output_and_keeps_raw(self):
        output = self.work / "clip.mp4"
        output.write_bytes(b"previous")

        def capture(command, backend, duration):
            Path(command[-1]).write_bytes(b"raw")

        with mock.patch.object(self.capture_screen, "ensure_backend_available"), \
                mock.patch.object(self.capture_screen, "execute_capture",
                                  side_effect=capture), \
                mock.patch.object(self.capture_screen, "normalize_capture",
                                  side_effect=self.capture_screen.CaptureError(
                                      "normalization failed")):
            result = self.capture_screen.main([
                "--duration", "1", "--output", str(output), "--backend", "macos"])

        self.assertEqual(result, 1)
        self.assertEqual(output.read_bytes(), b"previous")
        self.assertTrue(self.capture_screen.pending_path_for(output).exists())
        self.assertEqual(len(list(self.work.glob("*.raw-*.mov"))), 1)

    def test_success_replaces_output_and_sidecar_then_removes_pending_and_raw(self):
        output = self.work / "clip.mp4"
        sidecar = self.capture_screen.metadata_path_for(output)
        output.write_bytes(b"previous")
        sidecar.write_text('{"old": true}\n', encoding="utf-8")

        def capture(command, backend, duration):
            Path(command[-1]).write_bytes(b"raw")

        def normalize(raw, candidate, duration):
            self.assertTrue(raw.is_file())
            self.assertEqual(duration, 1.0)
            candidate.write_bytes(b"normalized")

        real_replace = os.replace
        with mock.patch.object(self.capture_screen, "ensure_backend_available"), \
                mock.patch.object(self.capture_screen, "execute_capture",
                                  side_effect=capture), \
                mock.patch.object(self.capture_screen, "normalize_capture",
                                  side_effect=normalize), \
                mock.patch.object(
                    self.capture_screen, "validate_clip_contract",
                    return_value=self.probe()), \
                mock.patch.object(self.capture_screen.os, "replace",
                                  side_effect=real_replace) as replace:
            result = self.capture_screen.main([
                "--duration", "1", "--output", str(output), "--backend", "macos"])

        self.assertEqual(result, 0)
        self.assertEqual(output.read_bytes(), b"normalized")
        state = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual(state["state"], "complete")
        self.assertEqual(state["requested"]["output"], str(output))
        self.assertEqual(
            state["media"]["fingerprint"]["value"],
            self.capture_screen._sha256(output))
        self.assertFalse(self.capture_screen.pending_path_for(output).exists())
        self.assertGreaterEqual(replace.call_count, 4)
        self.assertEqual(list(self.work.glob("*.raw-*.mov")), [])

    def test_keep_raw_retains_intermediate_after_success(self):
        output = self.work / "clip.mp4"

        def capture(command, backend, duration):
            Path(command[-1]).write_bytes(b"raw")

        def normalize(raw, candidate, duration):
            self.assertEqual(duration, 1.0)
            candidate.write_bytes(b"normalized")

        with mock.patch.object(self.capture_screen, "ensure_backend_available"), \
                mock.patch.object(self.capture_screen, "execute_capture",
                                  side_effect=capture), \
                mock.patch.object(self.capture_screen, "normalize_capture",
                                  side_effect=normalize), \
                mock.patch.object(
                    self.capture_screen, "validate_clip_contract",
                    return_value=self.probe()):
            result = self.capture_screen.main([
                "--duration", "1", "--output", str(output), "--backend", "macos",
                "--keep-raw"])

        self.assertEqual(result, 0)
        self.assertEqual(len(list(self.work.glob("*.raw-*.mov"))), 1)

    def test_metadata_replace_failure_rolls_back_old_clip_and_metadata(self):
        output = self.work / "clip.mp4"
        sidecar = self.capture_screen.metadata_path_for(output)
        pending = self.capture_screen.pending_path_for(output)
        output.write_bytes(b"previous")
        sidecar.write_bytes(b"previous metadata")
        pending.write_bytes(b"pending")
        candidate = self.work / ".candidate.mp4"
        metadata_candidate = self.work / ".candidate.json"
        candidate.write_bytes(b"normalized")
        metadata_candidate.write_bytes(b"new metadata")

        real_replace = os.replace

        def fail_metadata_replace(source, destination):
            if Path(destination) == sidecar and Path(source) == metadata_candidate:
                raise OSError("metadata replace failed")
            return real_replace(source, destination)

        with mock.patch.object(
                self.capture_screen.os, "replace",
                side_effect=fail_metadata_replace):
            attempt_lock = self.capture_screen.acquire_attempt_lock(output)
            try:
                with self.assertRaisesRegex(
                        self.capture_screen.CaptureError,
                        "Atomic publication failed"):
                    self.capture_screen.publish_capture(
                        candidate, metadata_candidate, output, sidecar, pending,
                        attempt_lock)
            finally:
                self.capture_screen.release_attempt_lock(attempt_lock)

        self.assertEqual(output.read_bytes(), b"previous")
        self.assertEqual(sidecar.read_bytes(), b"previous metadata")
        self.assertTrue(pending.exists())
        self.assertTrue(metadata_candidate.exists())

    def test_ownership_failure_after_replace_rolls_back_clip_and_metadata(self):
        output = self.work / "clip.mp4"
        sidecar = self.capture_screen.metadata_path_for(output)
        pending = self.capture_screen.pending_path_for(output)
        output.write_bytes(b"previous")
        sidecar.write_bytes(b"previous metadata")
        pending.write_bytes(b"pending")
        candidate = self.work / ".candidate.mp4"
        metadata_candidate = self.work / ".candidate.json"
        candidate.write_bytes(b"normalized")
        metadata_candidate.write_bytes(b"new metadata")
        attempt_lock = self.capture_screen.acquire_attempt_lock(output)
        lock_payload = json.loads(
            attempt_lock.path.read_text(encoding="utf-8"))
        real_replace = os.replace

        def steal_lock_after_replace(source, destination):
            result = real_replace(source, destination)
            if (Path(source) == metadata_candidate
                    and Path(destination) == sidecar):
                stolen = dict(lock_payload)
                stolen["owner_token"] = "different-owner"
                attempt_lock.path.write_text(
                    json.dumps(stolen), encoding="utf-8")
            return result

        try:
            with mock.patch.object(
                    self.capture_screen.os, "replace",
                    side_effect=steal_lock_after_replace):
                with self.assertRaisesRegex(
                        self.capture_screen.CaptureError,
                        "Atomic publication failed.*ownership changed"):
                    self.capture_screen.publish_capture(
                        candidate, metadata_candidate, output, sidecar, pending,
                        attempt_lock)
        finally:
            attempt_lock.path.write_text(
                json.dumps(lock_payload), encoding="utf-8")
            self.capture_screen.release_attempt_lock(attempt_lock)

        self.assertEqual(output.read_bytes(), b"previous")
        self.assertEqual(sidecar.read_bytes(), b"previous metadata")
        self.assertTrue(pending.exists())

    def test_ownership_failure_retains_backup_when_rollback_fails(self):
        output = self.work / "clip.mp4"
        sidecar = self.capture_screen.metadata_path_for(output)
        pending = self.capture_screen.pending_path_for(output)
        output.write_bytes(b"previous")
        sidecar.write_bytes(b"previous metadata")
        pending.write_bytes(b"pending")
        candidate = self.work / ".candidate.mp4"
        metadata_candidate = self.work / ".candidate.json"
        candidate.write_bytes(b"normalized")
        metadata_candidate.write_bytes(b"new metadata")
        attempt_lock = self.capture_screen.acquire_attempt_lock(output)
        lock_payload = json.loads(
            attempt_lock.path.read_text(encoding="utf-8"))
        real_replace = os.replace

        def fail_clip_rollback(source, destination):
            source = Path(source)
            destination = Path(destination)
            if destination == output and ".previous-" in source.name:
                raise OSError("clip rollback failed")
            result = real_replace(source, destination)
            if source == metadata_candidate and destination == sidecar:
                stolen = dict(lock_payload)
                stolen["owner_token"] = "different-owner"
                attempt_lock.path.write_text(
                    json.dumps(stolen), encoding="utf-8")
            return result

        try:
            with mock.patch.object(
                        self.capture_screen.os, "replace",
                        side_effect=fail_clip_rollback):
                with self.assertRaisesRegex(
                        self.capture_screen.CaptureError,
                        "clip rollback failed.*retained backups"):
                    self.capture_screen.publish_capture(
                        candidate, metadata_candidate, output, sidecar, pending,
                        attempt_lock)
        finally:
            attempt_lock.path.write_text(
                json.dumps(lock_payload), encoding="utf-8")
            self.capture_screen.release_attempt_lock(attempt_lock)

        self.assertEqual(output.read_bytes(), b"normalized")
        self.assertEqual(sidecar.read_bytes(), b"previous metadata")
        retained = list(self.work.glob(".clip.previous-*.mp4"))
        self.assertEqual(len(retained), 1)
        self.assertEqual(retained[0].read_bytes(), b"previous")
        self.assertTrue(pending.exists())

    def test_validate_rejects_early_ended_output(self):
        output = self.work / "clip.mp4"
        output.write_bytes(b"not-empty")
        completed = subprocess.CompletedProcess(
            ["ffprobe"], 0, json.dumps(self.probe(0.5, 15)), "")
        with mock.patch.object(
                self.capture_screen, "run_command", return_value=completed), \
                mock.patch.object(
                    self.capture_screen, "_has_faststart", return_value=True):
            with self.assertRaisesRegex(
                    self.capture_screen.CaptureError, "duration .*requested"):
                self.capture_screen.validate_clip_contract(output, 1.0)

    def test_validate_accepts_requested_duration_with_one_frame_tolerance(self):
        output = self.work / "clip.mp4"
        output.write_bytes(b"not-empty")
        completed = subprocess.CompletedProcess(
            ["ffprobe"], 0, json.dumps(self.probe(29 / 30, 29)), "")
        with mock.patch.object(
                self.capture_screen, "run_command", return_value=completed), \
                mock.patch.object(
                    self.capture_screen, "_has_faststart", return_value=True):
            metadata = self.capture_screen.validate_clip_contract(output, 1.0)
        self.assertEqual(metadata["streams"][0]["nb_read_frames"], "29")

    def test_check_capture_state_detects_storyboard_duration_and_region_mismatch(self):
        output = self.work / "clip.mp4"
        output.write_bytes(b"clip")
        sidecar = self.capture_screen.metadata_path_for(output)
        sidecar.write_text(json.dumps({
            "schema_version": 1,
            "state": "complete",
            "requested": {
                "duration_seconds": 2.0,
                "region": [10, 20, 30, 40],
                "backend": "auto",
                "output": str(output),
            },
            "resolved_backend": "macos",
            "media": {},
        }), encoding="utf-8")

        with self.assertRaisesRegex(
                self.capture_screen.CaptureError, "duration, region"):
            self.capture_screen.check_capture_state(
                output, 3.0, (1, 2, 3, 4))

    def test_check_capture_state_rejects_pending_even_with_old_valid_files(self):
        output = self.work / "clip.mp4"
        output.write_bytes(b"old clip")
        self.capture_screen.metadata_path_for(output).write_text(
            '{"state":"complete"}', encoding="utf-8")
        self.capture_screen.pending_path_for(output).write_text(
            '{"state":"pending"}', encoding="utf-8")

        with self.assertRaisesRegex(
                self.capture_screen.CaptureError, "pending marker exists"):
            self.capture_screen.check_capture_state(output, 1.0, None)

    def test_check_capture_state_rejects_lock_only_active_attempt(self):
        output = self.work / "clip.mp4"
        attempt_lock = self.capture_screen.acquire_attempt_lock(output)

        try:
            with self.assertRaisesRegex(
                    self.capture_screen.CaptureError,
                    "incomplete.*PID.*old.*appears to be active.*Do not remove"):
                self.capture_screen.check_capture_state(output, 1.0, None)
        finally:
            self.capture_screen.release_attempt_lock(attempt_lock)

    def test_check_capture_state_rejects_lock_only_stale_attempt(self):
        output = self.work / "clip.mp4"
        lock = self.capture_screen.lock_path_for(output)
        lock.write_text(json.dumps({
            "attempt_id": "stale-attempt",
            "owner_token": "stale-owner",
            "pid": 99999999,
            "hostname": self.capture_screen.socket.gethostname(),
            "created_at": "2020-01-01T00:00:00+00:00",
            "created_at_epoch": 1577836800,
            "output": str(output),
        }), encoding="utf-8")

        with mock.patch.object(
                self.capture_screen.os, "kill",
                side_effect=ProcessLookupError), \
                self.assertRaisesRegex(
                    self.capture_screen.CaptureError,
                    "incomplete.*stale-attempt.*old.*not running.*remove this lock"):
            self.capture_screen.check_capture_state(output, 1.0, None)

    def test_check_capture_state_detects_clip_fingerprint_mismatch(self):
        output = self.work / "clip.mp4"
        output.write_bytes(b"changed clip")
        sidecar = self.capture_screen.metadata_path_for(output)
        sidecar.write_text(json.dumps({
            "schema_version": 1,
            "state": "complete",
            "requested": {
                "duration_seconds": 1.0,
                "region": None,
                "backend": "auto",
                "output": str(output),
            },
            "resolved_backend": "macos",
            "media": {"fingerprint": {"algorithm": "sha256", "value": "old"}},
        }), encoding="utf-8")

        with mock.patch.object(
                self.capture_screen, "validate_clip_contract",
                return_value=self.probe()), \
                mock.patch.object(
                    self.capture_screen, "_media_state",
                    return_value={
                        "fingerprint": {
                            "algorithm": "sha256",
                            "value": "new",
                        },
                    }):
            with self.assertRaisesRegex(
                    self.capture_screen.CaptureError,
                    "fingerprint/properties"):
                self.capture_screen.check_capture_state(output, 1.0, None)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "ffmpeg and ffprobe are required")
class CaptureScreenIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture_screen = load_module()

    def setUp(self):
        self.work = WORK_ROOT / uuid.uuid4().hex
        self.work.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)

    def test_stitch_normalizes_synthetic_video_to_capture_contract(self):
        raw = self.work / "synthetic.mkv"
        output = self.work / "normalized.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            "testsrc=size=321x241:rate=17", "-t", "0.4",
            "-c:v", "ffv1", "-an", str(raw),
        ], check=True, capture_output=True, text=True, shell=False)
        subprocess.run([
            sys.executable, str(STITCH), str(raw), "-o", str(output),
        ], check=True, capture_output=True, text=True, shell=False)

        metadata = self.capture_screen.validate_clip_contract(output, 0.4)
        video = next(stream for stream in metadata["streams"]
                     if stream["codec_type"] == "video")
        self.assertEqual(video["codec_name"], "h264")
        self.assertEqual(video["profile"], "High")
        self.assertEqual(video["pix_fmt"], "yuv420p")
        self.assertEqual(video["avg_frame_rate"], "30/1")
        self.assertEqual(video["width"] % 2, 0)
        self.assertEqual(video["height"] % 2, 0)
        self.assertFalse(any(stream["codec_type"] == "audio"
                             for stream in metadata["streams"]))


if __name__ == "__main__":
    unittest.main()
