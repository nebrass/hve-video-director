#!/usr/bin/env python3
"""
hve-video-director — Clip Normalizer / Stitcher

Canonical, reviewed helper that turns raw capture(s) into the Phase-2 clip
contract the seek-driven `<video>` sync requires: constant 30fps, H.264
high / yuv420p, even dimensions, `+faststart`. Trims and concatenates when
given several inputs. Ships in the repo so the agent *invokes* it instead of
re-authoring a throwaway `stitch-clip` each run (issue #19).

Portable: pure Python standard library wrapping `ffmpeg`/`ffprobe` (the same
dependency the rest of Phase 5 already needs), so one script runs on
macOS / Linux / Windows.

Usage (from inside a generated project):
    # single clip → normalize to CFR30 in place under public/clips/
    python3 stitch_clip.py raw.mp4 -o public/clips/scene-02-dashboard.mp4

    # trim a sub-range (seconds): path::START::DURATION
    python3 stitch_clip.py raw.mov::1.5::6 -o public/clips/scene-02-dashboard.mp4

    # stitch several takes into one clip (scaled+padded to a common canvas)
    python3 stitch_clip.py a.mp4 b.mp4::0::4 c.webm \\
        --width 1920 --height 1080 -o public/clips/scene-03-flow.mp4

Concatenation uses the ffmpeg **concat filter** (re-encodes every segment),
NOT the concat demuxer / `.ffconcat` list. The demuxer needs byte-identical
codecs/params and mishandles the sparse VFR that screen/screencast captures
produce; the filter graph normalizes each segment first, so heterogeneous
inputs stitch cleanly.

For a fixed-duration native desktop or region recording, use the sibling
`capture_screen.py` orchestrator. It selects a truthful platform adapter
(macOS `screencapture`, Windows `gdigrab`, X11 `x11grab`, or feature-detected
Wayland `wf-recorder`) and invokes this script for normalization. WSL and
Wayland without `wf-recorder` return explicit recording handoffs instead of
claiming an unsupported backend.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

FPS = 30
# The canonical encode settings — keep in parity with the normalize recipe in
# workflows/phase-2-capture.md and patterns/cli-terminal-capture.md.
ENCODE = ["-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
          # One keyframe per second. agg emits change-only frames, so without an
          # explicit GOP ffmpeg can leave keyframes many seconds apart and the
          # HyperFrames renderer reports "sparse keyframes … causes seek failures
          # and frame freezing" — the clip then renders black or frozen while every
          # gate still passes. Tied to FPS so the two cannot drift apart.
          "-g", str(FPS), "-keyint_min", str(FPS),
          "-movflags", "+faststart"]


def _require(tool):
    if shutil.which(tool) is None:
        print(f"Error: `{tool}` not found on PATH — install ffmpeg (bundles ffprobe).",
              file=sys.stderr)
        sys.exit(1)


def _parse_segment(spec):
    """`path` or `path::START::DURATION` → (path, start|None, duration|None)."""
    parts = spec.split("::")
    path = parts[0]
    start = float(parts[1]) if len(parts) > 1 and parts[1] != "" else None
    dur = float(parts[2]) if len(parts) > 2 and parts[2] != "" else None
    if not Path(path).is_file():
        print(f"Error: input not found: {path}", file=sys.stderr)
        sys.exit(1)
    return path, start, dur


def _probe_size(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "json", path],
        capture_output=True, text=True, check=True).stdout
    stream = json.loads(out)["streams"][0]
    return int(stream["width"]), int(stream["height"])


def _even(n):
    return n - (n % 2)


def _scale_filter(width, height):
    if width and height:
        # Fit within the canvas, then letterbox-pad to the exact size.
        return (f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1")
    # No explicit canvas: just guarantee even dimensions for yuv420p.
    return "scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1"


def build_command(segments, output, fps, width, height):
    cmd = ["ffmpeg", "-y"]
    for path, start, dur in segments:
        if start is not None:
            cmd += ["-ss", str(start)]
        if dur is not None:
            cmd += ["-t", str(dur)]
        cmd += ["-i", path]

    scale = _scale_filter(width, height)
    labels = []
    graph = []
    for i in range(len(segments)):
        graph.append(f"[{i}:v]fps={fps},{scale}[v{i}]")
        labels.append(f"[v{i}]")

    if len(segments) > 1:
        graph.append(f"{''.join(labels)}concat=n={len(segments)}:v=1:a=0[outv]")
        out_label = "[outv]"
    else:
        out_label = "[v0]"

    cmd += ["-filter_complex", ";".join(graph), "-map", out_label]
    cmd += ENCODE + ["-an", output]
    return cmd


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Normalize/stitch capture(s) into a CFR30 H.264 clip.")
    parser.add_argument("inputs", nargs="+",
                        help="Input clips; each `path` or `path::START::DURATION` (seconds).")
    parser.add_argument("-o", "--output", required=True,
                        help="Output MP4 (e.g. public/clips/scene-NN-slug.mp4).")
    parser.add_argument("--fps", type=int, default=FPS, help="Constant output fps (default: 30).")
    parser.add_argument("--width", type=int, help="Target canvas width (with --height).")
    parser.add_argument("--height", type=int, help="Target canvas height (with --width).")
    args = parser.parse_args(argv)

    _require("ffmpeg")
    _require("ffprobe")

    segments = [_parse_segment(s) for s in args.inputs]

    width, height = args.width, args.height
    if bool(width) != bool(height):
        print("Error: pass --width and --height together (or neither).", file=sys.stderr)
        return 1
    # Multiple inputs must share a canvas; derive it from the first input if unset.
    if len(segments) > 1 and not width:
        width, height = _probe_size(segments[0][0])
    if width and height:
        width, height = _even(width), _even(height)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = build_command(segments, str(out_path), args.fps, width, height)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        print("Error: ffmpeg failed.", file=sys.stderr)
        return 1

    if not out_path.is_file() or out_path.stat().st_size == 0:
        print(f"Error: no output produced at {out_path}.", file=sys.stderr)
        return 1

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=nb_frames,avg_frame_rate,width,height",
         "-of", "default=noprint_wrappers=1", str(out_path)],
        capture_output=True, text=True).stdout.strip()
    print(f"Wrote {out_path} from {len(segments)} segment(s):")
    print(probe)
    return 0


if __name__ == "__main__":
    sys.exit(main())
