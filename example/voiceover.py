#!/usr/bin/env python3
"""
hve-video-director — Voiceover Timeline Assembler

Places already-synthesized voiceover sections at their exact start times,
separates them with silence, pads the result to `VIDEO_DURATION`, and warns
when a section overruns its slot.

**Both audio paths use this.** Whoever produced the section audio — the
delegated audio engine (`AUDIO_ENGINE`), local Kokoro TTS via the HyperFrames
CLI, or a hand-recorded take — hands it here as `vo_section_NN.mp3` and this
script builds the composition-absolute timeline. Acquisition is delegated;
placement is not.

The ElevenLabs *acquisition* path and its Whisper verification pass were removed
in M6. Synthesis now happens before this script runs, and timing verification is
a separate Phase-5 step against the assembled `voiceover.mp3` (`hyperframes
transcribe`, or standalone `whisper` as a fallback) — see
`workflows/phase-5-audio.md`. Nothing about assembly changed.

This script is pure standard library. It shells out to `ffmpeg` / `ffprobe` with
argv (never a shell) and needs no API key, no network, and no pip install.

Usage:
    python3 generate_voiceover.py --assemble-only
    python3 generate_voiceover.py               # same thing; the flag is optional

Configuration (edit the project-local copy, never $SKILL_DIR's):
    VIDEO_DURATION   — Total video duration in seconds
    sections         — List of (start_time, text) tuples, one per scene beat.
                       `text` is the narration that was synthesized into the
                       matching `vo_section_NN.mp3`; it is kept here so the
                       script doubles as the project's timing record.

Input:  vo_section_00.mp3, vo_section_01.mp3, … (one per `sections` entry,
        mono 44.1 kHz MP3 to match the silence spacers)
Output: voiceover.mp3

Pitfalls handled (each one a real failure mode you'd otherwise hit silently):
  - ffmpeg concat resolves relative paths to the concat-list's location, not
    cwd. Always use absolute paths in concat lists.
  - Voiceover must be padded to VIDEO_DURATION (`apad=whole_dur=N`). Otherwise
    HyperFrames render finds no audio for the trailing frames.
  - Word count is a poor proxy for spoken duration — comma density inflates
    the duration significantly (a 22-word sentence with 5 commas can be 15s;
    the same idea in 26 commaless words takes 10s). When a section overruns
    its slot, drop commas before dropping words.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

VIDEO_DURATION = 60  # seconds

# (start_time_seconds, text_that_was_spoken)
sections = [
    (0.0, "You can always tell when a video was made by an AI."),
    (5.0, "By hand, that means learning a renderer, a timeline model and an animation library first."),
    (13.0, "This one is different. It decides how the idea should be shown."),
    (19.0, "For every scene it asks what you must understand, how it should feel, and what it would take to show it."),
    (28.0, "It owns the thinking. Everything that draws a pixel belongs to HyperFrames."),
    (36.0, "This video was planned, built and rendered by the skill it is describing."),
    (44.0, "Motion, transitions, narration and music belong to the ecosystem. It inherits every improvement for free."),
    (53.0, "Install it, and point it at something you built."),
]


def get_audio_duration(path: str) -> float:
    """Get duration of an audio file in seconds using ffprobe.

    Surfaces a clear error on the two common failure modes (ffprobe missing
    or input file empty/corrupt) instead of crashing with a generic
    ValueError from float("").
    """
    try:
        result = subprocess.run(
            ["ffprobe", "-i", path, "-show_entries", "format=duration",
             "-v", "quiet", "-of", "csv=p=0"],
            capture_output=True, text=True, check=True,
        )
    except FileNotFoundError:
        raise RuntimeError("ffprobe not installed — install ffmpeg")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffprobe failed for {path} (file may be corrupt): "
                           f"{(e.stderr or '').strip()[:200]}")
    out = result.stdout.strip()
    if not out or out == "N/A":
        raise RuntimeError(f"ffprobe returned no usable duration for {path} "
                           "(file may be 0 bytes, corrupt, or lack a duration "
                           "header)")
    return float(out)


# ─── Assembly ────────────────────────────────────────────────────────────────

def _make_silence(duration_s: float) -> str:
    """Write a silence MP3 of `duration_s` seconds; return its absolute path."""
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        "anullsrc=r=44100:cl=mono", "-t", str(duration_s), path,
    ], capture_output=True, check=True)
    return path


def assemble_voiceover(section_files: list, output_path: str = "voiceover.mp3"):
    """Combine section audio files with silence gaps into final voiceover.

    Two pitfalls this implementation handles:

    1. ffmpeg's concat demuxer resolves `file '...'` paths relative to the
       concat-list's location, NOT the cwd. The concat-list lives in /tmp,
       so relative paths like "vo_section_00.mp3" silently fail to resolve
       and produce a near-empty output. Use absolute paths everywhere.

    2. `tempfile.mktemp` is deprecated since Python 2.3 (race-prone). Use
       `mkstemp` instead — wrapped in `_make_silence` above.
    """
    # try/finally wraps BOTH the build loop and the concat so the concat-list
    # and every silence tempfile are unlinked even if get_audio_duration or
    # _make_silence raises mid-loop — the loop runs before the concat, so a
    # finally placed only around the concat would leak on a loop failure.
    silence_paths: list = []
    concat_list = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            concat_list = f.name

            for i, (start_time, audio_path) in enumerate(section_files):
                audio_abs = os.path.abspath(audio_path)
                duration = get_audio_duration(audio_abs)

                # Initial silence before the first section's start time
                if i == 0 and start_time > 0:
                    sp = _make_silence(start_time)
                    silence_paths.append(sp)
                    f.write(f"file '{sp}'\n")

                f.write(f"file '{audio_abs}'\n")

                # Gap between this section and the next
                if i < len(section_files) - 1:
                    next_start = section_files[i + 1][0]
                    gap = next_start - start_time - duration
                    if gap > 0:
                        sp = _make_silence(gap)
                        silence_paths.append(sp)
                        f.write(f"file '{sp}'\n")
                    elif gap < 0:
                        print(f"  WARNING: section {i} audio overruns its "
                              f"{next_start - start_time:.1f}s slot by {-gap:.1f}s "
                              "— every later section starts early and desyncs from "
                              "its scene. Shorten this section's text.",
                              file=sys.stderr)

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list, "-c:a", "libmp3lame", "-q:a", "2",
            output_path,
        ], capture_output=True, check=True)
    finally:
        for p in [concat_list, *silence_paths]:
            if p:
                try:
                    os.unlink(p)
                except OSError:
                    pass

    # Pad to exact VIDEO_DURATION so HyperFrames render finds audio for every
    # frame. Without this, a short voiceover ends early and the trailing
    # frames render with no audio (HyperFrames may even truncate the video).
    fd, padded = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", output_path,
            "-af", f"apad=whole_dur={VIDEO_DURATION}",
            "-c:a", "libmp3lame", "-q:a", "2", padded,
        ], capture_output=True, check=True)
        os.replace(padded, output_path)
    except Exception:
        try:
            os.unlink(padded)
        except OSError:
            pass
        raise

    final_dur = get_audio_duration(output_path)
    if final_dur > VIDEO_DURATION + 0.1:
        print(f"  WARNING: voiceover is {final_dur:.2f}s but VIDEO_DURATION is "
              f"{VIDEO_DURATION}s. apad only extends — it cannot trim — so the "
              "narration overruns the composition. Shorten the script.",
              file=sys.stderr)
    print(f"  Assembled + padded: {output_path} ({final_dur:.2f}s)")


# ─── Main ────────────────────────────────────────────────────────────────────

def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    # `--assemble-only` is retained as the documented spelling — assembly is now
    # the only mode, so the flag is accepted and optional rather than removed,
    # and every invocation already written into a workflow keeps working.
    if args not in ([], ["--assemble-only"]):
        print("Usage: generate_voiceover.py [--assemble-only]", file=sys.stderr)
        return 2

    print("hve-video-director — Voiceover Assembly")
    print("=" * 50)

    section_files = []
    print("\n[1/2] Loading generated voiceover sections...")
    for i, (start, _) in enumerate(sections):
        output = f"vo_section_{i:02d}.mp3"
        if not Path(output).is_file() or Path(output).stat().st_size == 0:
            print(
                f"Missing or empty section file: {output}",
                file=sys.stderr,
            )
            return 2
        section_files.append((start, output))
        duration = get_audio_duration(output)
        print(f"    Duration: {duration:.1f}s (starts at {start}s)")

    if not section_files:
        print("No sections configured — set the `sections` list in this file.",
              file=sys.stderr)
        return 1

    print("\n[2/2] Assembling voiceover...")
    assemble_voiceover(section_files)

    print("\nDone! Output: voiceover.mp3")
    total_dur = get_audio_duration("voiceover.mp3")
    print(f"Total duration: {total_dur:.1f}s (video: {VIDEO_DURATION}s)")
    print("Next: verify timing against the assembled file "
          "(`npx hyperframes transcribe voiceover.mp3`) — Phase 5 marks that "
          "check CRITICAL.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
