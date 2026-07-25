#!/usr/bin/env python3
"""
hve-spielberg — Native Screen Capture Orchestrator

Capture a desktop or region with a platform-native adapter, then invoke the
sibling stitch_clip.py normalizer. The destination is replaced atomically only
after ffprobe confirms the Phase-2 clip contract and requested duration. A
pending marker plus fingerprinted metadata sidecar make failed retakes
unambiguously incomplete without deleting the prior valid capture.

Supported adapters:
  macOS        built-in screencapture video capture
  Windows      ffmpeg gdigrab
  Linux/X11    ffmpeg x11grab
  Wayland      wf-recorder, when installed

WSL cannot capture the Windows host desktop and exits with an explicit handoff.
No adapter records audio by default.

Examples:
  python3 capture_screen.py --duration 6 -o public/clips/scene-02-demo.mp4
  python3 capture_screen.py --duration 4 --region 100,80,1280,720 \
      -o public/clips/scene-03-flow.mp4
"""

import argparse
import hashlib
import json
import math
import os
import platform
import re
import shutil
import signal
import socket
import struct
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path


FPS = 30
CAPTURE_STATE_SCHEMA_VERSION = 1
FRAME_TOLERANCE = 1
BACKENDS = ("auto", "macos", "windows", "x11", "wayland")


class CaptureError(RuntimeError):
    pass


@dataclass(frozen=True)
class AttemptLock:
    path: Path
    attempt_id: str
    owner_token: str
    device: int
    inode: int


def parse_duration(value):
    try:
        duration = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("duration must be a number") from exc
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be a finite positive number")
    return duration


def parse_region(value):
    parts = value.split(",")
    if len(parts) != 4:
        raise ValueError("region must be x,y,w,h")
    try:
        x, y, width, height = (int(part.strip()) for part in parts)
    except ValueError as exc:
        raise ValueError("region must contain four integers: x,y,w,h") from exc
    if width <= 0 or height <= 0:
        raise ValueError("region width and height must be positive")
    return x, y, width, height


def _is_wsl(os_release, env):
    release = os_release.lower()
    return bool(env.get("WSL_DISTRO_NAME") or env.get("WSL_INTEROP")
                or "microsoft" in release or "wsl" in release)


def detect_backend(platform_name=None, os_release=None, env=None):
    platform_name = platform_name or sys.platform
    os_release = os_release if os_release is not None else platform.release()
    env = os.environ if env is None else env

    if platform_name.startswith("linux") and _is_wsl(os_release, env):
        return "wsl"
    if platform_name == "darwin":
        return "macos"
    if platform_name.startswith(("win", "cygwin", "msys")):
        return "windows"
    if platform_name.startswith("linux"):
        if env.get("WAYLAND_DISPLAY"):
            return "wayland"
        if env.get("DISPLAY"):
            return "x11"
        raise CaptureError(
            "No graphical capture session detected. Set DISPLAY for X11, or "
            "WAYLAND_DISPLAY and install wf-recorder for Wayland.")
    raise CaptureError(f"Unsupported platform: {platform_name}")


def _missing_message(backend, tool):
    if tool in ("ffmpeg", "ffprobe"):
        return (
            f"`{tool}` was not found. Install ffmpeg (including ffprobe); both "
            "are required to normalize and validate the capture.")
    if backend == "macos" and tool == "screencapture":
        return (
            f"`{tool}` was not found. macOS screen capture requires the built-in "
            "`screencapture` command. Verify /usr/sbin is on PATH, then grant the "
            "terminal or agent Screen Recording permission in System Settings > "
            "Privacy & Security > Screen Recording.")
    if backend == "wayland" and tool == "wf-recorder":
        return (
            "`wf-recorder` was not found. Install wf-recorder with your Linux "
            "package manager, or record through your Wayland compositor/desktop "
            "recorder and normalize the saved file with scripts/stitch_clip.py. "
            "Generic FFmpeg PipeWire capture is not assumed.")
    return f"`{tool}` was not found; the {backend} capture adapter cannot run."


def ensure_backend_available(backend, env):
    if backend == "wsl":
        raise CaptureError(
            "WSL cannot capture the Windows host desktop. Record on the Windows "
            "host with Xbox Game Bar, OBS, or ffmpeg gdigrab; save the recording "
            "where WSL can read it, then run scripts/stitch_clip.py on that file.")

    if backend == "x11" and not env.get("DISPLAY"):
        raise CaptureError(
            "X11 capture requires DISPLAY. Run from the graphical session and "
            "confirm Xauthority access, or pass a recording to stitch_clip.py.")
    if backend == "wayland" and not env.get("WAYLAND_DISPLAY"):
        raise CaptureError(
            "Wayland capture requires WAYLAND_DISPLAY. Run from the graphical "
            "session, or use the desktop recorder and then stitch_clip.py.")

    backend_tool = {
        "macos": "screencapture",
        "windows": "ffmpeg",
        "x11": "ffmpeg",
        "wayland": "wf-recorder",
    }[backend]
    if shutil.which(backend_tool) is None:
        raise CaptureError(_missing_message(backend, backend_tool))

    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise CaptureError(_missing_message(backend, tool))

    stitch = Path(__file__).resolve().with_name("stitch_clip.py")
    if not stitch.is_file():
        raise CaptureError(
            f"Normalizer not found at {stitch}. Keep capture_screen.py beside "
            "the canonical scripts/stitch_clip.py helper.")


def _duration_arg(duration):
    return format(duration, "g")


def run_command(command):
    return subprocess.run(
        command, capture_output=True, text=True, shell=False)


def _x11_screen_size(env):
    if shutil.which("xdpyinfo"):
        result = run_command(["xdpyinfo", "-display", env["DISPLAY"]])
        if result.returncode == 0:
            match = re.search(r"dimensions:\s+(\d+)x(\d+)\s+pixels", result.stdout)
            if match:
                return int(match.group(1)), int(match.group(2))
    if shutil.which("xrandr"):
        result = run_command(["xrandr", "--current", "--display", env["DISPLAY"]])
        if result.returncode == 0:
            match = re.search(r"\bcurrent\s+(\d+)\s+x\s+(\d+)", result.stdout)
            if match:
                return int(match.group(1)), int(match.group(2))
    raise CaptureError(
        "Could not determine the X11 desktop size. Pass --region x,y,w,h, "
        "or install xdpyinfo/xrandr and confirm DISPLAY access.")


def build_capture_command(backend, duration, region, raw_path, env):
    seconds = _duration_arg(duration)
    if backend == "macos":
        command = ["screencapture", "-v", f"-V{seconds}"]
        if region:
            command.append(f"-R{','.join(str(part) for part in region)}")
        return command + [str(raw_path)]

    if backend == "windows":
        command = ["ffmpeg", "-y", "-f", "gdigrab", "-framerate", str(FPS)]
        if region:
            x, y, width, height = region
            command += [
                "-offset_x", str(x), "-offset_y", str(y),
                "-video_size", f"{width}x{height}",
            ]
        command += ["-i", "desktop", "-t", seconds]
        return command + ["-c:v", "ffv1", "-an", str(raw_path)]

    if backend == "x11":
        display = env.get("DISPLAY")
        if not display:
            raise CaptureError("X11 capture requires DISPLAY.")
        if region:
            x, y, width, height = region
        else:
            x, y = 0, 0
            width, height = _x11_screen_size(env)
        return [
            "ffmpeg", "-y", "-f", "x11grab", "-framerate", str(FPS),
            "-video_size", f"{width}x{height}", "-i", f"{display}+{x},{y}",
            "-t", seconds, "-c:v", "ffv1", "-an", str(raw_path),
        ]

    if backend == "wayland":
        command = ["wf-recorder"]
        if region:
            x, y, width, height = region
            command += ["--geometry", f"{x},{y} {width}x{height}"]
        return command + ["--file", str(raw_path)]

    raise CaptureError(f"No capture command for backend: {backend}")


def _failure_remediation(backend, stderr):
    detail = stderr.strip() or "the capture command exited without diagnostics"
    if backend == "macos":
        remedy = (
            "Grant the terminal or agent Screen Recording permission in System "
            "Settings > Privacy & Security > Screen Recording, then retry.")
    elif backend == "windows":
        remedy = (
            "Confirm this ffmpeg build includes gdigrab and that the session has "
            "access to the interactive Windows desktop.")
    elif backend == "x11":
        remedy = (
            "Confirm DISPLAY and Xauthority belong to the current graphical "
            "session; pass --region if desktop-size detection is unavailable.")
    else:
        remedy = (
            "Allow screen capture in the Wayland compositor. If unattended "
            "capture is blocked, use the desktop recorder and normalize its file "
            "with scripts/stitch_clip.py.")
    return f"Capture failed: {detail}\n{remedy}"


def _execute_wayland(command, duration):
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        shell=False)
    try:
        stdout, stderr = process.communicate(timeout=duration)
    except subprocess.TimeoutExpired:
        process.send_signal(signal.SIGINT)
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    process.communicate(timeout=10)
                except subprocess.TimeoutExpired as exc:
                    raise CaptureError(
                        "wf-recorder ignored SIGINT and SIGTERM, and could not "
                        "be reaped within 10 seconds after kill. Its partial raw "
                        "capture was retained; end the process manually before "
                        "retrying with the desktop recorder.") from exc
                raise CaptureError(
                    "wf-recorder ignored SIGINT and SIGTERM and was killed. Its "
                    "partial raw capture was retained; retry with the desktop "
                    "recorder.")
            raise CaptureError(
                "wf-recorder ignored SIGINT and was terminated. Its partial raw "
                "capture was retained; retry with the desktop recorder.")
    if process.returncode not in (0, 130, -signal.SIGINT):
        raise CaptureError(_failure_remediation("wayland", stderr))
    return stdout, stderr


def execute_capture(command, backend, duration):
    if backend == "wayland":
        return _execute_wayland(command, duration)
    result = run_command(command)
    if result.returncode != 0:
        raise CaptureError(_failure_remediation(backend, result.stderr))
    return result.stdout, result.stderr


def normalize_capture(raw_path, candidate_path, duration):
    stitch = Path(__file__).resolve().with_name("stitch_clip.py")
    command = [
        sys.executable, str(stitch),
        f"{raw_path}::0::{_duration_arg(duration)}",
        "-o", str(candidate_path),
    ]
    result = run_command(command)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise CaptureError(
            f"Normalization with stitch_clip.py failed: {detail or 'unknown error'}")


def _has_faststart(path):
    moov_offset = None
    mdat_offset = None
    file_size = path.stat().st_size
    with path.open("rb") as stream:
        offset = 0
        while offset + 8 <= file_size:
            stream.seek(offset)
            header = stream.read(8)
            size, atom_type = struct.unpack(">I4s", header)
            header_size = 8
            if size == 1:
                extended = stream.read(8)
                if len(extended) != 8:
                    break
                size = struct.unpack(">Q", extended)[0]
                header_size = 16
            elif size == 0:
                size = file_size - offset
            if size < header_size or offset + size > file_size:
                break
            if atom_type == b"moov":
                moov_offset = offset
            elif atom_type == b"mdat":
                mdat_offset = offset
            if moov_offset is not None and mdat_offset is not None:
                break
            offset += size
    return (moov_offset is not None and mdat_offset is not None
            and moov_offset < mdat_offset)


def _validated_timing(video, expected_duration):
    try:
        actual_duration = float(video.get("duration"))
    except (TypeError, ValueError):
        actual_duration = 0.0
    frame_value = video.get("nb_read_frames") or video.get("nb_frames")
    try:
        actual_frames = int(frame_value)
    except (TypeError, ValueError):
        actual_frames = 0

    expected_frames = round(expected_duration * FPS)
    duration_tolerance = FRAME_TOLERANCE / FPS
    failures = []
    if actual_duration <= 0:
        failures.append("duration is missing or non-positive")
    elif abs(actual_duration - expected_duration) > duration_tolerance + 1e-9:
        failures.append(
            f"duration {actual_duration:g}s differs from requested "
            f"{expected_duration:g}s by more than {duration_tolerance:g}s")
    if actual_frames <= 0:
        failures.append("frame count is missing or non-positive")
    elif abs(actual_frames - expected_frames) > FRAME_TOLERANCE:
        failures.append(
            f"frame count {actual_frames} differs from requested "
            f"{expected_frames} by more than {FRAME_TOLERANCE} frame")
    return actual_duration, actual_frames, failures


def validate_clip_contract(path, expected_duration):
    if not path.is_file() or path.stat().st_size == 0:
        raise CaptureError(f"Normalized output is missing or empty: {path}")
    result = run_command([
        "ffprobe", "-v", "error", "-count_frames", "-show_streams",
        "-show_format", "-of", "json", str(path),
    ])
    if result.returncode != 0:
        raise CaptureError(
            f"ffprobe could not validate {path}: {result.stderr.strip()}")
    try:
        metadata = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CaptureError("ffprobe returned invalid JSON.") from exc

    streams = metadata.get("streams", [])
    videos = [stream for stream in streams if stream.get("codec_type") == "video"]
    audios = [stream for stream in streams if stream.get("codec_type") == "audio"]
    if len(videos) != 1:
        raise CaptureError("Output must contain exactly one video stream.")
    video = videos[0]

    failures = []
    if video.get("codec_name") != "h264":
        failures.append("codec is not H.264")
    if video.get("profile") != "High":
        failures.append("H.264 profile is not High")
    if video.get("pix_fmt") != "yuv420p":
        failures.append("pixel format is not yuv420p")
    try:
        width = int(video.get("width", 0))
        height = int(video.get("height", 0))
    except (TypeError, ValueError):
        width = height = 0
    if width <= 0 or height <= 0 or width % 2 or height % 2:
        failures.append("dimensions are not even")
    try:
        average = Fraction(video.get("avg_frame_rate", "0/1"))
        nominal = Fraction(video.get("r_frame_rate", "0/1"))
    except (ValueError, ZeroDivisionError):
        average = nominal = Fraction(0, 1)
    if average != FPS or nominal != FPS:
        failures.append("frame rate is not CFR30")
    if audios:
        failures.append("audio stream is present")
    if not _has_faststart(path):
        failures.append("MP4 moov atom is not before mdat (+faststart missing)")
    _, _, timing_failures = _validated_timing(video, expected_duration)
    failures.extend(timing_failures)
    if failures:
        raise CaptureError("Output contract validation failed: " + "; ".join(failures))
    return metadata


def pending_path_for(output):
    return Path(f"{output}.capture.pending")


def metadata_path_for(output):
    return Path(f"{output}.capture.json")


def lock_path_for(output):
    return Path(f"{output}.capture.lock")


def _lock_owner_status(payload):
    hostname = payload.get("hostname")
    pid = payload.get("pid")
    if hostname != socket.gethostname() or not isinstance(pid, int) or pid <= 0:
        return "owner process status cannot be checked from this host"
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return "owner PID is not running on this host"
    except PermissionError:
        return "owner PID exists but cannot be inspected by this user"
    except OSError as exc:
        return f"owner PID status check failed: {exc}"
    return "owner PID appears to be active on this host"


def _lock_contention_message(output, path):
    owner = _lock_owner_details(path)
    return (
        f"A capture attempt is already in progress for {output}. "
        f"Existing lock: {path} ({owner}). No capture files were changed. "
        "Do not remove an active lock. If the owner is confirmed stopped, "
        f"remove this lock manually and retry: {path}")


def _lock_owner_details(path):
    try:
        modified_age = max(0.0, time.time() - path.lstat().st_mtime)
        fallback_age = f"{modified_age:.1f}s old by file modification time"
    except OSError:
        fallback_age = "age unknown"
    try:
        payload = _read_json(path, "Capture attempt lock")
    except CaptureError as exc:
        return f"owner details unavailable ({exc}); {fallback_age}"
    else:
        created_epoch = payload.get("created_at_epoch")
        try:
            age = max(0.0, time.time() - float(created_epoch))
            age_text = f"{age:.1f}s old"
        except (TypeError, ValueError):
            age_text = fallback_age
        return (
            f"attempt {payload.get('attempt_id', 'unknown')}, "
            f"PID {payload.get('pid', 'unknown')} on "
            f"{payload.get('hostname', 'unknown')}, "
            f"created {payload.get('created_at', 'unknown')} "
            f"({age_text}); {_lock_owner_status(payload)}")


def _incomplete_lock_message(output, path):
    owner = _lock_owner_details(path)
    return (
        f"Capture is incomplete because a capture attempt lock exists for "
        f"{output}: {path} ({owner}). "
        "Do not remove an active lock. If the owner is confirmed stopped, "
        f"remove this lock manually and retry: {path}")


def acquire_attempt_lock(output):
    path = lock_path_for(output)
    attempt_id = uuid.uuid4().hex
    owner_token = uuid.uuid4().hex
    created_at_epoch = time.time()
    payload = {
        "schema_version": 1,
        "attempt_id": attempt_id,
        "owner_token": owner_token,
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "created_at": datetime.fromtimestamp(
            created_at_epoch, timezone.utc).isoformat(),
        "created_at_epoch": created_at_epoch,
        "output": str(output),
    }
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise CaptureError(_lock_contention_message(output, path)) from exc
    except OSError as exc:
        raise CaptureError(
            f"Could not create capture attempt lock {path}: {exc}") from exc

    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
            stat = os.fstat(stream.fileno())
    except OSError as exc:
        raise CaptureError(
            f"Created capture lock {path}, but could not initialize it: {exc}. "
            "Inspect the lock and remove it manually only after confirming no "
            "capture process owns it.") from exc
    return AttemptLock(
        path, attempt_id, owner_token, stat.st_dev, stat.st_ino)


def assert_attempt_lock_owned(attempt_lock):
    try:
        payload = _read_json(attempt_lock.path, "Capture attempt lock")
        stat = attempt_lock.path.stat()
    except (CaptureError, OSError) as exc:
        raise CaptureError(
            f"Capture lock ownership changed or cannot be verified: "
            f"{attempt_lock.path}. Refusing to modify capture state.") from exc
    if (payload.get("attempt_id") != attempt_lock.attempt_id
            or payload.get("owner_token") != attempt_lock.owner_token
            or stat.st_dev != attempt_lock.device
            or stat.st_ino != attempt_lock.inode):
        raise CaptureError(
            f"Capture lock ownership changed: {attempt_lock.path}. "
            "Refusing to remove another attempt's lock or modify capture state.")
    return payload


def release_attempt_lock(attempt_lock):
    assert_attempt_lock_owned(attempt_lock)
    try:
        attempt_lock.path.unlink()
    except OSError as exc:
        raise CaptureError(
            f"Could not remove owned capture lock {attempt_lock.path}: {exc}") from exc


def _request_state(output, duration, region, backend):
    return {
        "duration_seconds": duration,
        "region": list(region) if region is not None else None,
        "backend": backend,
        "output": str(output),
    }


def _atomic_write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = _unique_path(path, "write", ".json")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_pending_state(output, duration, region, backend):
    path = pending_path_for(output)
    _atomic_write_json(path, {
        "schema_version": CAPTURE_STATE_SCHEMA_VERSION,
        "state": "pending",
        "requested": _request_state(output, duration, region, backend),
    })
    return path


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _media_state(path, probe):
    video = next(
        stream for stream in probe["streams"]
        if stream.get("codec_type") == "video")
    actual_duration, actual_frames, _ = _validated_timing(
        video, float(video["duration"]))
    return {
        "codec": video["codec_name"],
        "profile": video["profile"],
        "pixel_format": video["pix_fmt"],
        "width": int(video["width"]),
        "height": int(video["height"]),
        "average_frame_rate": video["avg_frame_rate"],
        "nominal_frame_rate": video["r_frame_rate"],
        "duration_seconds": actual_duration,
        "frame_count": actual_frames,
        "audio_stream_count": sum(
            stream.get("codec_type") == "audio"
            for stream in probe["streams"]),
        "faststart": True,
        "file_size_bytes": path.stat().st_size,
        "fingerprint": {
            "algorithm": "sha256",
            "value": _sha256(path),
        },
    }


def build_success_state(output, media_path, duration, region, requested_backend,
                        resolved_backend, probe):
    return {
        "schema_version": CAPTURE_STATE_SCHEMA_VERSION,
        "state": "complete",
        "requested": _request_state(
            output, duration, region, requested_backend),
        "resolved_backend": resolved_backend,
        "media": _media_state(media_path, probe),
    }


def _read_json(path, label):
    try:
        if not path.is_file() or path.stat().st_size == 0:
            raise CaptureError(f"{label} is missing or empty: {path}")
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)
    except CaptureError:
        raise
    except (OSError, json.JSONDecodeError) as exc:
        raise CaptureError(f"{label} is not valid JSON: {path}") from exc


def check_capture_state(output, duration, region):
    lock = lock_path_for(output)
    if os.path.lexists(lock):
        raise CaptureError(_incomplete_lock_message(output, lock))
    pending = pending_path_for(output)
    if pending.exists():
        raise CaptureError(
            f"Capture is incomplete because the pending marker exists: {pending}")
    if not output.is_file() or output.stat().st_size == 0:
        raise CaptureError(f"Capture output is missing or empty: {output}")

    sidecar_path = metadata_path_for(output)
    sidecar = _read_json(sidecar_path, "Capture metadata sidecar")
    if sidecar.get("schema_version") != CAPTURE_STATE_SCHEMA_VERSION:
        raise CaptureError("Capture metadata schema version does not match.")
    if sidecar.get("state") != "complete":
        raise CaptureError("Capture metadata state is not complete.")

    requested = sidecar.get("requested", {})
    expected_region = list(region) if region is not None else None
    try:
        recorded_duration = float(requested.get("duration_seconds"))
    except (TypeError, ValueError):
        recorded_duration = 0.0
    mismatches = []
    if not math.isclose(recorded_duration, duration, rel_tol=0, abs_tol=1e-9):
        mismatches.append("duration")
    if requested.get("region") != expected_region:
        mismatches.append("region")
    if requested.get("output") != str(output):
        mismatches.append("output")
    if mismatches:
        raise CaptureError(
            "Capture metadata does not match the storyboard: "
            + ", ".join(mismatches))

    probe = validate_clip_contract(output, duration)
    current_media = _media_state(output, probe)
    if sidecar.get("media") != current_media:
        raise CaptureError(
            "Capture metadata fingerprint/properties do not match the clip.")
    return sidecar


def _backup_file(path, role):
    if not path.exists():
        return None
    backup = _unique_path(path, role, path.suffix)
    shutil.copy2(path, backup)
    return backup


def publish_capture(candidate, metadata_candidate, output, sidecar, pending,
                    attempt_lock):
    assert_attempt_lock_owned(attempt_lock)
    output_backup = _backup_file(output, "previous")
    sidecar_backup = _backup_file(sidecar, "previous")
    output_replaced = False
    sidecar_replaced = False
    retain_backups = False
    try:
        os.replace(candidate, output)
        output_replaced = True
        os.replace(metadata_candidate, sidecar)
        sidecar_replaced = True
        assert_attempt_lock_owned(attempt_lock)
        pending.unlink()
    except (CaptureError, OSError) as exc:
        retain_backups = True
        rollback_failures = []
        if sidecar_replaced:
            try:
                if sidecar_backup is None:
                    sidecar.unlink(missing_ok=True)
                else:
                    os.replace(sidecar_backup, sidecar)
                    sidecar_backup = None
            except OSError as rollback_exc:
                rollback_failures.append(f"metadata rollback failed: {rollback_exc}")
        if output_replaced:
            try:
                if output_backup is None:
                    output.unlink(missing_ok=True)
                else:
                    os.replace(output_backup, output)
                    output_backup = None
            except OSError as rollback_exc:
                rollback_failures.append(f"clip rollback failed: {rollback_exc}")
        detail = f"Atomic publication failed: {exc}"
        if rollback_failures:
            detail += "; " + "; ".join(rollback_failures)
        retained = [
            str(path) for path in (output_backup, sidecar_backup)
            if path is not None and path.exists()
        ]
        if retained:
            detail += "; retained backups: " + ", ".join(retained)
        raise CaptureError(detail) from exc
    finally:
        if not retain_backups:
            for backup in (output_backup, sidecar_backup):
                if backup is not None:
                    try:
                        backup.unlink(missing_ok=True)
                    except OSError:
                        pass


def _unique_path(output, role, suffix):
    while True:
        token = uuid.uuid4().hex
        candidate = output.parent / f".{output.stem}.{role}-{token}{suffix}"
        if not candidate.exists():
            return candidate


def _raw_suffix(backend):
    return ".mov" if backend == "macos" else ".mkv"


def _duration_type(value):
    try:
        return parse_duration(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _region_type(value):
    try:
        return parse_region(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _parser():
    parser = argparse.ArgumentParser(
        description=(
            "Capture a desktop/region, normalize through stitch_clip.py, and "
            "atomically publish a silent CFR30 H.264 MP4."))
    parser.add_argument(
        "--duration", required=True, type=_duration_type,
        help="Capture duration in seconds; must be positive.")
    parser.add_argument(
        "--region", type=_region_type,
        help="Optional capture rectangle x,y,w,h; width/height must be positive.")
    parser.add_argument(
        "-o", "--output", required=True,
        help="Destination MP4, replaced atomically only after validation.")
    parser.add_argument(
        "--backend", choices=BACKENDS, default="auto",
        help="Capture adapter (default: auto-detect).")
    parser.add_argument(
        "--keep-raw", action="store_true",
        help="Keep the output-local raw capture after successful normalization.")
    parser.add_argument(
        "--check", action="store_true",
        help="Check output, pending marker, sidecar, fingerprint, duration, and region.")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    output = Path(args.output).expanduser()
    if output.suffix.lower() != ".mp4":
        print("Error: --output must end in .mp4.", file=sys.stderr)
        return 2

    if args.check:
        try:
            check_capture_state(output, args.duration, args.region)
            print(f"Capture state is complete and matches: {output}")
            return 0
        except (CaptureError, OSError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        attempt_lock = acquire_attempt_lock(output)
    except (CaptureError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    env = dict(os.environ)
    raw_path = None
    candidate_path = None
    metadata_candidate = None
    pending_path = None
    backend = None
    kept_raw = False
    result = 1
    try:
        assert_attempt_lock_owned(attempt_lock)
        pending_path = write_pending_state(
            output, args.duration, args.region, args.backend)
        backend = detect_backend(env=env) if args.backend == "auto" else args.backend
        ensure_backend_available(backend, env)
        raw_path = _unique_path(output, "raw", _raw_suffix(backend))
        candidate_path = _unique_path(output, "normalized", ".mp4")
        command = build_capture_command(
            backend, args.duration, args.region, raw_path, env)
        execute_capture(command, backend, args.duration)
        if not raw_path.is_file() or raw_path.stat().st_size == 0:
            raise CaptureError(
                f"Capture command produced no raw video at {raw_path}. "
                + _failure_remediation(backend, "empty output"))
        normalize_capture(raw_path, candidate_path, args.duration)
        probe = validate_clip_contract(candidate_path, args.duration)
        success_state = build_success_state(
            output, candidate_path, args.duration, args.region,
            args.backend, backend, probe)
        metadata_candidate = _unique_path(
            metadata_path_for(output), "complete", ".json")
        _atomic_write_json(metadata_candidate, success_state)
        publish_capture(
            candidate_path, metadata_candidate, output,
            metadata_path_for(output), pending_path, attempt_lock)
        if not args.keep_raw:
            try:
                raw_path.unlink()
            except OSError as exc:
                print(
                    f"Warning: published successfully but could not remove raw "
                    f"capture {raw_path}: {exc}", file=sys.stderr)
        else:
            kept_raw = True
        result = 0
    except (CaptureError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if raw_path is not None and raw_path.exists():
            print(f"Raw capture retained: {raw_path}", file=sys.stderr)
        if candidate_path is not None and candidate_path.exists():
            print(f"Normalized candidate retained: {candidate_path}", file=sys.stderr)
        if metadata_candidate is not None and metadata_candidate.exists():
            print(
                f"Metadata candidate retained: {metadata_candidate}",
                file=sys.stderr)
        if pending_path is not None and pending_path.exists():
            print(
                f"Pending marker retained: {pending_path}", file=sys.stderr)
        print(f"Capture state remains incomplete: {output}", file=sys.stderr)
    finally:
        try:
            release_attempt_lock(attempt_lock)
        except (CaptureError, OSError) as exc:
            print(
                f"Error: capture attempt lock cleanup failed: {exc}",
                file=sys.stderr)
            result = 1

    if result == 0:
        if kept_raw:
            print(f"Kept raw capture: {raw_path}")
        print(f"Wrote {output} using the {backend} adapter (silent CFR30 H.264).")
    return result


if __name__ == "__main__":
    sys.exit(main())
