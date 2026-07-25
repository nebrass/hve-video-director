#!/usr/bin/env python3
"""
example/voiceover.py — Voiceover generation for THIS example project.

Self-contained instantiation of the canonical scripts/generate_voiceover.py
with the (start, text) sections for the 53s blog.nebrass.fr reference promo.

Usage:
    cd example
    ELEVENLABS_API_KEY=<rotated-key> python3 voiceover.py

Output:
    voiceover.mp3      — final concatenated voiceover (silence padding included)
    transcript.json    — timing data from `npx hyperframes transcribe` (default),
                         OR voiceover.json from the standalone-whisper fallback
    vo_section_NN.mp3  — per-section intermediate files (kept for debugging)

Note:
    index.html's <audio src> is voiceover-with-music.mp3 (the loudnorm +
    music mix), NOT voiceover.mp3. Running only this script then
    `npx hyperframes render` produces a SILENT video. See README.md for the
    normalize + music-mix ffmpeg steps that create voiceover-with-music.mp3.

Environment:
    ELEVENLABS_API_KEY — Required.
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests not found — auto-installing into the current Python "
          "environment (Ctrl-C to abort)...", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# ─── Configuration ────────────────────────────────────────────────────────────

API_KEY = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("ELEVEN_LABS_API_KEY")
if not API_KEY:
    print("Error: ELEVENLABS_API_KEY not set")
    sys.exit(1)

VOICE_ID = "XrExE9yKIg1WjnnlVkGX"  # Matilda — warm, confident female
VIDEO_DURATION = 53

# (start_time_seconds, text)
# Aligned to scenes in storyboard.md. Each section starts 1s after its
# scene starts (entry buffer) and ends ≥0.5s before the scene ends.
# Pronunciation: written as "Aitch Vee Ee Video Director" — phonetic spelling
# is the most reliable way to force ElevenLabs to pronounce H-V-E as
# individual letters. Plain "H V E" gets interpreted as a phonetic blob
# (the first render produced "Sage V E" — Matilda was running the letters
# together as a single word). The on-screen wordmark always shows
# "hve-video-director" in full, so what the viewer reads and what they hear
# match (letters spelled out).
sections = [
    # Scene 0 Establishing (0–8.4s) — VO 1.0–~7  : the blog, framed (real homepage hero).
    (1.0,
     "This is Nebrass's blog — software engineering, the cloud, and Java, "
     "written by someone who actually ships."),

    # Scene 1 Depth (8–20.4s) — VO 9.0–~18.5 : a real post's code + a real merged fix.
    # The Puppeteer claim is verifiable (the post + merged PR #15112).
    (9.0,
     "Every post goes deep. Real bugs, real fixes — "
     "like the two compounding bugs that were slowing Puppeteer's screencasts, "
     "traced and merged upstream."),

    # Scene 2 Breadth (20–30.4s) — VO 21.0–~28 : the real categories index.
    (21.0,
     "Kubernetes, security, Azure, machine learning — "
     "dozens of topics, all in one place."),

    # Scene 3 Volume (30–42.4s) — VO 31.0–~36 : the homepage post list scrolling.
    (31.0,
     "Years of write-ups. Free to read, and always something new."),

    # Scene 4 CTA (42–53s) — VO 43.0–~52 : URL + made-with sign-off (dogfood hook).
    # Pronunciation: "eff arr" forces the .fr TLD letter-by-letter; "Aitch Vee Ee
    # Video Director" forces the HVE prefix as individual letters (plain "H V E" blobs).
    (43.0,
     "Find it at blog dot nebrass dot eff arr. "
     "This whole video? Made with one command — slash Aitch Vee Ee Video Director."),
]

# ─── ElevenLabs TTS ──────────────────────────────────────────────────────────

ELEVENLABS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

VOICE_SETTINGS = {
    "stability": 0.65,
    "similarity_boost": 0.85,
    "style": 0.20,
    "use_speaker_boost": True,
}


def generate_section(text: str, output_path: str) -> bool:
    response = requests.post(
        ELEVENLABS_URL,
        headers={"xi-api-key": API_KEY, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": VOICE_SETTINGS,
        },
        timeout=60,
    )
    if response.status_code != 200:
        print(f"  ElevenLabs error {response.status_code}: {response.text[:200]}")
        return False
    with open(output_path, "wb") as f:
        f.write(response.content)
    return True


def get_audio_duration(path: str) -> float:
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
        raise RuntimeError(f"ffprobe returned no usable duration for {path}")
    return float(out)


def _make_silence(duration_s: float) -> str:
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        "anullsrc=r=44100:cl=mono", "-t", str(duration_s), path,
    ], capture_output=True, check=True)
    return path


def assemble_voiceover(section_files: list, output_path: str = "voiceover.mp3"):
    # ffmpeg concat resolves `file '...'` paths relative to the concat-list's
    # location, NOT the cwd. The concat-list lives in /tmp, so relative paths
    # like "vo_section_00.mp3" silently fail to resolve, producing a near-empty
    # output. Use absolute paths everywhere.
    # try/finally wraps BOTH the build loop and the concat so the concat-list
    # and silence tempfiles are unlinked even if get_audio_duration or
    # _make_silence raises mid-loop (the loop runs before the concat).
    silence_paths: list = []
    concat_list = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            concat_list = f.name
            for i, (start_time, audio_path) in enumerate(section_files):
                audio_abs = os.path.abspath(audio_path)
                duration = get_audio_duration(audio_abs)
                if i == 0 and start_time > 0:
                    sp = _make_silence(start_time)
                    silence_paths.append(sp)
                    f.write(f"file '{sp}'\n")
                f.write(f"file '{audio_abs}'\n")
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
                              "— later sections start early and desync. "
                              "Shorten this section's text.", file=sys.stderr)
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

    # Pad to exact VIDEO_DURATION (mirror of scripts/generate_voiceover.py).
    # Without this, the last section ends ~1-2s before the composition's
    # data-duration. HyperFrames render finds no audio for the trailing
    # frames and may truncate the video. See workflows/phase-5-audio.md
    # § "Pad voiceover to VIDEO_DURATION".
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


def _load_segments(path: Path) -> list:
    """Read a transcript JSON and normalize to a flat WORD-level list.

    Both transcribers are reconciled to one shape (a flat list of
    `{start, end, ...}` words) so check_overlaps can detect a single word
    crossing a section boundary:
      - `hyperframes transcribe` already returns a flat word list.
      - `whisper --word_timestamps True` nests words under segments
        (`{"segments": [{"words": [...]}]}`); we flatten them. Without
        word-level timing, whisper segments are whole sentences and
        check_overlaps would flag a later section's sentence as the previous
        section overrunning.

    Falls back to segment-level if no words are present; tolerates UTF-8
    transcripts on Windows and truncated/corrupt files (returns []).
    """
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"  Could not parse {path}: {e}")
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        segments = data.get("segments", [])
        words = [w for seg in segments for w in seg.get("words", [])]
        if words:
            return words
        return segments or data.get("words", [])
    return []


def verify_with_hyperframes(voiceover_path: str) -> list:
    """Transcribe for timing verification.

    Prefers `npx hyperframes transcribe`; falls back to standalone `whisper`
    (mirrors scripts/generate_voiceover.py). Stale transcript.json from a
    prior run is deleted up-front so a failed transcribe can't be misread
    as a successful one.
    """
    candidates = [
        Path("transcript.json"),
        Path(voiceover_path).with_suffix(".json"),
    ]
    for c in candidates:
        if c.exists():
            try:
                c.unlink()
            except OSError:
                pass

    try:
        proc = subprocess.run(
            ["npx", "--yes", "hyperframes", "transcribe", voiceover_path,
             "--model", "tiny"],
            capture_output=True, text=True, timeout=300,
        )
        if proc.returncode == 0:
            for p in candidates:
                if p.exists():
                    segments = _load_segments(p)
                    if segments:
                        return segments
        else:
            print(f"  hyperframes transcribe exit {proc.returncode}: "
                  f"{proc.stderr[:200]}")
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"  hyperframes transcribe unavailable ({type(e).__name__}); "
              "trying whisper fallback")

    try:
        proc = subprocess.run(
            ["whisper", voiceover_path, "--model", "tiny",
             "--output_format", "json", "--word_timestamps", "True",
             "--output_dir", "."],
            capture_output=True, text=True, timeout=180, check=False,
        )
        if proc.returncode != 0:
            print(f"  whisper exit {proc.returncode}: {proc.stderr[:200]}")
            return []
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"  whisper unavailable ({type(e).__name__}) — "
              "skipping transcript verification")
        return []

    json_path = Path(voiceover_path).with_suffix(".json")
    if not json_path.exists():
        print("  Transcript output not found — skipping verification")
        return []
    return _load_segments(json_path)


def check_overlaps(segments: list, sections: list) -> list:
    # Whisper's tiny model gives imprecise word-level timestamps — words often
    # extend ~0.5s past their actual audio end into adjacent silence. We use
    # ffmpeg silencedetect for precise gap analysis instead; this function is
    # kept as a sanity check that complements but doesn't replace it.
    overlaps = []
    for i in range(len(sections) - 1):
        next_start, _ = sections[i + 1]
        for seg in segments:
            seg_start = seg.get("start", seg.get("startTime"))
            seg_end = seg.get("end", seg.get("endTime"))
            if seg_start is None or seg_end is None:
                continue  # word lacks usable timing (e.g. a null start/end)
            if seg_start < next_start and seg_end > next_start + 0.5:
                # Tolerate 0.5s of Whisper imprecision before flagging.
                overlaps.append({
                    "section": i,
                    "segment_end": seg_end,
                    "next_section_start": next_start,
                    "overlap_seconds": seg_end - next_start,
                })
    return overlaps


def main():
    print("blog.nebrass.fr promo — voiceover generation")
    print("=" * 50)

    print("\n[1/3] Generating voiceover sections via ElevenLabs (Matilda)...")
    section_files = []
    for i, (start, text) in enumerate(sections):
        preview = text[:70].replace("\n", " ")
        print(f"  Section {i + 1}/{len(sections)} (t={start}s): {preview}...")
        output = f"vo_section_{i:02d}.mp3"
        if generate_section(text, output):
            section_files.append((start, output))
            duration = get_audio_duration(output)
            print(f"    Duration: {duration:.2f}s")
        else:
            print(f"    FAILED")
            sys.exit(2)

    print("\n[2/3] Assembling voiceover with silence padding...")
    assemble_voiceover(section_files)

    print("\n[3/3] Verifying transcript (hyperframes transcribe, then whisper)...")
    segments = verify_with_hyperframes("voiceover.mp3")
    if segments:
        overlaps = check_overlaps(segments, sections)
        if overlaps:
            print(f"\n  WARNING: {len(overlaps)} overlap(s) detected:")
            for o in overlaps:
                print(f"    Section {o['section']}: ends {o['segment_end']:.2f}s, "
                      f"next starts {o['next_section_start']:.2f}s "
                      f"(overlap {o['overlap_seconds']:.2f}s)")
            print("\n  Fix: shorten text or push next section later, then re-run.")
        else:
            print("  No overlaps. Voiceover timing is clean.")
    else:
        print("  Transcript verification skipped (no transcribe output).")

    total = get_audio_duration("voiceover.mp3")
    print(f"\nDone. voiceover.mp3 — {total:.2f}s (target: {VIDEO_DURATION}s)")


if __name__ == "__main__":
    main()
