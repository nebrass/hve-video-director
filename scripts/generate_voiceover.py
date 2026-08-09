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
  - Word count is a poor proxy for spoken duration — syllable density and comma
    pauses both inflate it. When a section overruns its slot, drop commas before
    dropping words. `validate_brief.py vo-budget` owns the estimate and its
    numbers; Phase 1 runs it before the storyboard is approved.
"""

import hashlib
import json
import os
import sys
import subprocess
import tempfile
import uuid
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

VIDEO_DURATION = 60  # seconds

# (start_time_seconds, text_that_was_spoken)
sections = [
    (1.0, "Your opening hook goes here."),
    (6.0, "Describe the problem your audience faces."),
    (16.0, "Introduce your solution."),
    (21.0, "Walk through the key features."),
    (46.0, "Share the results and impact."),
    (53.0, "Your call to action."),
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


def _concat_quote(path: str) -> str:
    """Quote a path for an ffmpeg concat list entry.

    The concat demuxer parses `file '...'` with shell-like quoting, so a
    literal apostrophe inside the quoted path must be written `'\\''` or the
    path is truncated at the quote (e.g. under `~/Bob's Videos/`).
    """
    return path.replace("'", "'\\''")


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
                    f.write(f"file '{_concat_quote(sp)}'\n")

                f.write(f"file '{_concat_quote(audio_abs)}'\n")

                # Gap between this section and the next
                if i < len(section_files) - 1:
                    next_start = section_files[i + 1][0]
                    gap = next_start - start_time - duration
                    if gap > 0:
                        sp = _make_silence(gap)
                        silence_paths.append(sp)
                        f.write(f"file '{_concat_quote(sp)}'\n")
                    elif gap < 0:
                        print(f"  WARNING: section {i} audio overruns its "
                              f"{next_start - start_time:.1f}s slot by {-gap:.1f}s "
                              "— no spacer is inserted, so every later section starts late "
                              "and desyncs from its scene. Shorten this section's text.",
                              file=sys.stderr)

        try:
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", concat_list, "-c:a", "libmp3lame", "-q:a", "2",
                output_path,
            ], capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr or b""
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", "replace")
            # `from e` keeps the command and returncode reachable while the message
            # surfaces ffmpeg's own words, which is what a caller actually needs first.
            raise RuntimeError(
                f"ffmpeg concat failed assembling {output_path}: "
                f"{stderr.strip()[-400:]}"
            ) from e
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


# ─── Freshness gate ──────────────────────────────────────────────────────────

MANIFEST = Path(".hve/vo-sections.json")


def verify_sections_are_fresh(section_files):
    """Refuse to assemble a section whose bytes nobody vouched for.

    The delegated TTS engine leaves a failed line's PREVIOUS audio in place, so a
    section file can exist, be non-empty and be entirely the wrong take. Existence
    is therefore not evidence. `verify_vo_sections.py seal` records the bytes that
    were actually produced for this script; this compares against that record.

    Deliberately narrow: a sha256 against a manifest whose schema this repo owns.
    This file is copied into every project and edited there, so it must never learn
    the engine's formats — that knowledge lives in the skill-resident verifier.

    Returns a list of complaints; empty means every section is accounted for.
    """
    if not MANIFEST.is_file():
        return ["no .hve/vo-sections.json — run `verify_vo_sections.py seal` first"]
    try:
        recorded = json.loads(MANIFEST.read_text(encoding="utf-8")).get("sections", {})
    except (json.JSONDecodeError, OSError) as error:
        return [f"unreadable .hve/vo-sections.json ({error})"]

    problems = []
    for i, (_, path) in enumerate(section_files):
        section_id = f"{i:02d}"
        entry = recorded.get(section_id)
        if not entry:
            problems.append(f"section {section_id} is not in the manifest")
            continue
        digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        if digest != entry.get("audio_sha256"):
            problems.append(
                f"section {section_id} does not match the sealed bytes — it is a "
                "different take than the one recorded"
            )
    return problems


def verify_script_unchanged():
    """Refuse if the script changed since these takes were assembled.

    Matching audio hashes prove the bytes are the ones that were sealed. They cannot
    prove those bytes still say what `sections` now says: edit a line here without
    re-synthesizing and the old take still matches the old manifest, so assembly would
    succeed with narration the script no longer asks for.

    Compared sections-to-sections, never sections-to-request. Those two legitimately
    diverge — a retry synthesizes from a filtered request file, so `audio_request.json`
    can describe text that is no longer what was spoken, and binding to it would fail
    closed on a normal recovery. The hash is recorded on the first verified assembly
    after a seal and re-checked afterwards; `seal` rewrites the manifest, which clears
    it, so a genuine re-synthesis re-anchors instead of tripping.
    """
    if not MANIFEST.is_file():
        return []
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    current = {
        f"{i:02d}": hashlib.sha256(text.encode("utf-8")).hexdigest()
        for i, (_, text) in enumerate(sections)
    }
    recorded = manifest.get("script_sha256")
    if recorded is None:
        # Anchoring happens on an ORDINARY assembly, so this write must not be
        # able to truncate the seal it is annotating: publish via tmp + rename.
        manifest["script_sha256"] = current
        tmp = MANIFEST.parent / f".{MANIFEST.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
        try:
            with tmp.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, MANIFEST)
            # Durability of the rename itself, not just of the bytes. The sibling
            # writer in verify_vo_sections.py already does this; publishing the
            # anchor any less safely would make the weaker of two atomic writers
            # in the same repo the one guarding the freshness claim.
            dir_fd = os.open(MANIFEST.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass
            raise
        return []
    changed = [k for k, v in current.items() if recorded.get(k) != v]
    if not changed:
        return []
    return [
        f"section {k} was sealed against different narration — this script says "
        "something the recorded audio does not"
        for k in sorted(changed)
    ]


# ─── Main ────────────────────────────────────────────────────────────────────

def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    # `--assemble-only` is retained as the documented spelling — assembly is now
    # the only mode, so the flag is accepted and optional rather than removed,
    # and every invocation already written into a workflow keeps working.
    # `--allow-unverified` is an escape hatch, never an enabler: the freshness check
    # is on by default so the invocation already written into every workflow is the
    # guarded one. A flag that had to be *added* to get the check would leave the
    # default path exactly as exposed as it is today.
    allow_unverified = "--allow-unverified" in args
    args = [a for a in args if a != "--allow-unverified"]
    if args not in ([], ["--assemble-only"]):
        print("Usage: generate_voiceover.py [--assemble-only] [--allow-unverified]",
              file=sys.stderr)
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

    if not section_files:
        print("No sections configured — set the `sections` list in this file.",
              file=sys.stderr)
        return 1

    problems = verify_sections_are_fresh(section_files)
    problems += verify_script_unchanged()
    if problems:
        if allow_unverified:
            print("\n  WARNING: assembling UNVERIFIED sections —", file=sys.stderr)
            for problem in problems:
                print(f"    - {problem}", file=sys.stderr)
            print("  A section left over from an earlier run is indistinguishable "
                  "from a fresh one here.", file=sys.stderr)
        else:
            print("\nRefusing to assemble unverified sections:", file=sys.stderr)
            for problem in problems:
                print(f"  - {problem}", file=sys.stderr)
            print(
                "\nThe TTS engine leaves a failed line's previous audio in place, so "
                "an existing section file is not evidence it is the right take.\n"
                "Run:  python3 \"$SKILL_DIR/scripts/verify_vo_sections.py\" "
                "--project-dir . seal\n"
                "For narration this engine did not make (a confirmed local voice, or "
                "your own recording), seal it with --attest local-tts or "
                "--attest user-supplied.\n"
                "To assemble anyway, pass --allow-unverified.",
                file=sys.stderr,
            )
            return 2

    # Durations are probed only once the set is proven, so a stale or unsealed
    # project fails before spending an ffprobe call per section.
    for start, output in section_files:
        duration = get_audio_duration(output)
        print(f"    Duration: {duration:.1f}s (starts at {start}s)")

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
