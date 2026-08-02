#!/usr/bin/env python3
"""
hve-video-director — Clip-Own Audio Mixer (Phase 5, Step 5.3a)

Mixes one clip's own sound into the canonical soundtrack
(`voiceover-with-music.mp3`), ducking the voice+music under it, and replaces
the soundtrack atomically only after the mix has been verified. Run it once per
scene whose storyboard row sets `Clip audio: <volume>` (not `none`).

Portable: pure Python standard library wrapping `ffmpeg`/`ffprobe` — the same
dependency the rest of Phase 5 already needs. Every external call is an argv
list; no shell is ever invoked.

Usage (from inside a generated project):
    python3 mix_clip_audio.py public/clips/scene-03-demo.mp4 \\
        --clip-in 2.0 --clip-out 8.0 --speed 1.0 \\
        --at 18.5 --volume 0.6 \\
        --soundtrack voiceover-with-music.mp3

`--at` is the scene's `data-start` **in seconds**, copied verbatim from
`index.html` — the same unit the composition uses. The milliseconds `adelay`
needs are computed here.

Why this is a script and not a bash block in the workflow. The prose version
carried three defects, and each one is now a guard with a test:

(a) UNIT CONFUSION. The block asked for `AT_MS` (milliseconds) while
    `index.html` states `data-start` in seconds, so copying `data-start="18.5"`
    placed the clip 18 ms in instead of 18.5 s in — silently wrong audio, a
    correct-looking render. `--at` takes seconds and converts internally.

(b) A VERIFICATION THAT COULD NOT FAIL. The block compared the mix duration
    against the soundtrack duration, but `amix=…:duration=first` *defines* the
    output length as the first input's, so the check was tautological. The
    failure it was reaching for is a clip placed so late that its audio is
    truncated at the end of the film. That is now a **pre-flight** check:
    `--at` + play duration must fit inside the soundtrack. The duration compare
    is kept, honestly labelled as a pipeline sanity assert.

    The second post-mix check is the no-op detector: `volumedetect` measures
    mean volume over the placed window before and after, and the mix must move
    it. A byte/hash compare could not do this job — the output is a fresh MP3
    encode, so its bytes always differ even when nothing audible was added.

(c) NO INPUT VALIDATION. `clip-out > clip-in`, `0.1 <= speed <= 5.0`,
    `0 < volume <= 1`, `at >= 0`, non-empty inputs, and an actual audio stream
    in the clip are all enforced before any work starts.

Filter design (preserved from the reviewed workflow recipe, constants intact):
trim → `atempo` → `loudnorm` → `volume` → `adelay`, then the voice+music leg is
sidechain-ducked *keyed by the clip* (the Step 5.2 music duck with the roles
swapped) and the two are mixed. `sidechaincompress` thresholds, the
`alimiter=limit=0.89` ceiling and the stereo `-ac 2` clip leg were each learned
from a real failure — do not tune them casually. Deliberately **no** dynamic
`loudnorm` master: Step 5.2 documents that it rides gain and undoes the duck.
Correct loudness afterwards with a constant `volume=<delta>dB` instead.

Both `sidechaincompress` legs are pinned with `aformat` to fltp/44100/stereo —
the same pin Step 5.2 applies to the music mix, and for the same reason: the
filter needs its inputs to share sample format, rate **and** channel layout,
and the no-music path copies a possibly **mono** voiceover into the canonical
soundtrack. Step 5.2 records the layout mismatch aborting with `Failed to inject
frame into filter network`; measured here on ffmpeg 8.1.2 with a mono
soundtrack, the unpinned graph instead survives and silently publishes a **mono**
44.1 kHz mix, while the pinned graph publishes stereo. Either way the pin is what
keeps the outcome deterministic across ffmpeg versions.

`atempo` accepts a limited factor per stage, so the requested speed is emitted
as N equal stages whose product is the speed (e.g. 3.0 → two stages of
1.732051).

The placed clip audio lands in a scratch **WAV** beside the soundtrack rather
than the workflow's intermediate MP3: it is thrown away after the mix, and a
lossless hand-off spares the clip one generation of MP3 encoding.

A failed run leaves the soundtrack byte-identical and says so: a failed retake
must never count as complete (the same invariant the sibling `capture_screen.py`
enforces for captures).
"""

import argparse
import math
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

# `atempo` is only well-defined per stage inside this range on the ffmpeg
# versions this skill targets; chain stages to reach anything outside it.
ATEMPO_MIN = 0.5
ATEMPO_MAX = 2.0
MAX_ATEMPO_STAGES = 8

# Storyboard `Speed` bounds — outside these the footage is unusable anyway.
SPEED_MIN = 0.1
SPEED_MAX = 5.0

# The placed clip may overshoot the soundtrack by at most this much (seconds)
# before ffmpeg would silently truncate audible audio at the end of the film.
TRUNCATION_TOLERANCE = 0.05

# MP3 encoding pads by a frame or so; a real length change is far larger.
DURATION_TOLERANCE = 0.25

# Below this the mix changed nothing audible in the placed window (a --volume too
# low to register, or a chain that produced nothing there) — a no-op run, which
# must not publish. It does NOT reliably catch a digitally silent clip: measured
# on ffmpeg 8.1.2, `loudnorm` lifts even a silent clip's dither far enough to
# drive the duck, so the window does move. See the report note on that hazard.
MIN_WINDOW_DELTA_DB = 0.1

# Never ask volumedetect to measure a degenerate window.
MIN_WINDOW_SECONDS = 0.05

# volumedetect reports -inf dB for digital silence; floor it so arithmetic works.
SILENCE_FLOOR_DB = -120.0

# Pinning both sidechain legs — see the module docstring.
STEREO = "aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo"

# Reviewed constants. Changing any of these changes the sound of every video.
CLIP_LOUDNORM = "loudnorm=I=-18:TP=-2:LRA=11"
SIDECHAIN = "sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300"
LIMITER = "alimiter=limit=0.89"

MEAN_VOLUME = re.compile(r"mean_volume:\s*(-?(?:\d+(?:\.\d+)?|inf))\s*dB")


class MixError(Exception):
    """Any refusal or failure that must leave the soundtrack untouched."""


def _fmt(value):
    """Format a float for an ffmpeg argument without exponent notation."""
    text = f"{float(value):.6f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


def delay_ms(at_seconds):
    """Scene `data-start` in SECONDS → the milliseconds `adelay` wants."""
    return int(round(float(at_seconds) * 1000))


def atempo_chain(speed):
    """Equal `atempo` stages whose product is `speed`.

    A single stage does not accept every factor, so pick the fewest stages N
    with `speed ** (1/N)` inside the accepted range: 1.0/2.0 → one stage,
    3.0 → two stages of 1.732051, 0.1 → four stages of 0.562341.
    """
    speed = float(speed)
    if speed <= 0:
        raise MixError(f"--speed must be positive (got {speed}).")
    for stages in range(1, MAX_ATEMPO_STAGES + 1):
        factor = speed ** (1.0 / stages)
        if ATEMPO_MIN <= factor <= ATEMPO_MAX:
            return [factor] * stages
    raise MixError(f"--speed {speed} cannot be expressed as atempo stages.")


def run_command(command):
    """Run an argv list, capturing output. Never a shell string."""
    return subprocess.run(command, capture_output=True, text=True)


def require_tools():
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise MixError(
                f"`{tool}` not found on PATH — install ffmpeg (bundles ffprobe).")


def probe_duration(path):
    result = run_command([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)])
    text = (result.stdout or "").strip()
    try:
        duration = float(text)
    except ValueError:
        raise MixError(f"could not read a duration from {path} "
                       f"(ffprobe said {text or (result.stderr or '').strip()!r}).")
    if not math.isfinite(duration) or duration <= 0:
        raise MixError(f"{path} reports a non-usable duration ({text}).")
    return duration


def probe_has_audio(path):
    result = run_command([
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=codec_type",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)])
    return "audio" in (result.stdout or "")


def probe_window_mean_volume(path, start, duration):
    """Mean volume (dB) over one window — the no-op detector's measurement."""
    result = run_command([
        "ffmpeg", "-hide_banner", "-nostats",
        "-ss", _fmt(start), "-t", _fmt(duration), "-i", str(path),
        "-af", "volumedetect", "-f", "null", "-"])
    if result.returncode != 0:
        raise MixError(f"could not measure {path}:\n{(result.stderr or '').strip()}")
    match = MEAN_VOLUME.search(result.stderr or "")
    if not match:
        raise MixError(f"volumedetect reported no mean_volume for {path}.")
    value = float(match.group(1))
    return SILENCE_FLOOR_DB if math.isinf(value) else value


def build_clip_command(clip, clip_in, clip_out, speed, volume, at_seconds, output):
    """Trim → atempo → loudnorm → volume → adelay, as stereo 44.1 kHz audio."""
    at = delay_ms(at_seconds)
    tempo = ",".join(f"atempo={_fmt(factor)}" for factor in atempo_chain(speed))
    filters = f"{tempo},{CLIP_LOUDNORM},volume={_fmt(volume)},adelay={at}|{at}"
    return [
        "ffmpeg", "-y",
        "-ss", _fmt(clip_in), "-to", _fmt(clip_out), "-i", str(clip),
        "-af", filters, "-vn", "-ac", "2", "-ar", "44100",
        "-c:a", "pcm_s16le", str(output),
    ]


def build_mix_command(soundtrack, clip_audio, duration, output):
    """Duck the voice+music under the clip (sidechain), then mix the clip on top."""
    span = _fmt(duration)
    graph = (
        f"[0:a]{STEREO}[base];"
        f"[1:a]{STEREO},asplit=2[clip][key-raw];"
        f"[key-raw]apad=whole_dur={span},atrim=duration={span}[key];"
        f"[base][key]{SIDECHAIN}[ducked];"
        f"[ducked][clip]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
        f"{LIMITER}[out]"
    )
    return [
        "ffmpeg", "-y", "-i", str(soundtrack), "-i", str(clip_audio),
        "-filter_complex", graph, "-map", "[out]",
        "-c:a", "libmp3lame", "-q:a", "2", str(output),
    ]


def _readable_media(path, label):
    target = Path(path)
    if not target.is_file():
        raise MixError(f"{label} not found: {target}")
    if target.stat().st_size == 0:
        raise MixError(f"{label} is empty: {target}")
    return target


def validate_request(clip, soundtrack, clip_in, clip_out, speed, volume, at):
    """Reject every bad request before touching ffmpeg. Names the bad value."""
    if not math.isfinite(clip_in) or clip_in < 0:
        raise MixError(f"--clip-in must be >= 0 seconds (got {clip_in}).")
    if not math.isfinite(clip_out) or clip_out <= clip_in:
        raise MixError(
            f"--clip-out must be greater than --clip-in "
            f"(got --clip-in {clip_in}, --clip-out {clip_out}).")
    if not math.isfinite(speed) or not SPEED_MIN <= speed <= SPEED_MAX:
        raise MixError(
            f"--speed must be between {SPEED_MIN} and {SPEED_MAX} (got {speed}).")
    if not math.isfinite(volume) or not 0 < volume <= 1:
        raise MixError(f"--volume must be greater than 0 and at most 1 (got {volume}).")
    if not math.isfinite(at) or at < 0:
        raise MixError(f"--at must be >= 0 seconds (got {at}).")
    return _readable_media(clip, "clip"), _readable_media(soundtrack, "soundtrack")


def _scratch_path(soundtrack, role, suffix):
    """A sibling scratch file — `os.replace` is only atomic within one filesystem."""
    unique = f"{os.getpid()}-{uuid.uuid4().hex[:8]}"
    return soundtrack.parent / f".{soundtrack.stem}.{role}-{unique}{suffix}"


def mix(clip, soundtrack, clip_in, clip_out, speed, volume, at):
    clip, soundtrack = validate_request(
        clip, soundtrack, clip_in, clip_out, speed, volume, at)

    if not probe_has_audio(clip):
        raise MixError(
            f"{clip} has no audio stream — the storyboard row asks for clip audio "
            f"the footage does not carry. Set `Clip audio: none` or recapture with sound.")

    clip_duration = probe_duration(clip)
    if clip_out > clip_duration + TRUNCATION_TOLERANCE:
        raise MixError(
            f"--clip-out {clip_out}s is past the end of {clip} ({_fmt(clip_duration)}s); "
            f"the placed audio would be {_fmt(clip_out - clip_duration)}s short of the "
            f"storyboard window.")

    play_duration = (clip_out - clip_in) / speed
    soundtrack_duration = probe_duration(soundtrack)
    if at >= soundtrack_duration:
        raise MixError(
            f"--at {at}s starts at or after the end of the {_fmt(soundtrack_duration)}s "
            f"soundtrack; none of the clip audio would be heard. --at is the scene's "
            f"data-start in SECONDS.")
    overshoot = (at + play_duration) - soundtrack_duration
    if overshoot > TRUNCATION_TOLERANCE:
        raise MixError(
            f"the clip does not fit: placed at {at}s it plays for "
            f"{_fmt(play_duration)}s and ends at {_fmt(at + play_duration)}s, past the "
            f"{_fmt(soundtrack_duration)}s soundtrack — {_fmt(overshoot)}s of clip audio "
            f"would be truncated. Check --at against the scene's data-start (SECONDS), "
            f"and the clip window/speed against the storyboard.")

    # Measure only the placed window, and never past the end of the file.
    window = max(min(play_duration, soundtrack_duration - at), MIN_WINDOW_SECONDS)
    before = probe_window_mean_volume(soundtrack, at, window)

    clip_audio = _scratch_path(soundtrack, "clip-audio", ".wav")
    candidate = _scratch_path(soundtrack, "mixed", soundtrack.suffix or ".mp3")
    try:
        extract = build_clip_command(
            clip, clip_in, clip_out, speed, volume, at, clip_audio)
        result = run_command(extract)
        if result.returncode != 0 or not clip_audio.is_file() or clip_audio.stat().st_size == 0:
            raise MixError(
                f"extracting the clip audio failed:\n{(result.stderr or '').strip()}")

        result = run_command(
            build_mix_command(soundtrack, clip_audio, soundtrack_duration, candidate))
        if result.returncode != 0 or not candidate.is_file() or candidate.stat().st_size == 0:
            raise MixError(f"the mix failed:\n{(result.stderr or '').strip()}")

        # Sanity assert, not a discriminating test: `amix=…:duration=first` makes
        # this hold by construction, so it only catches a broken pipeline.
        mixed_duration = probe_duration(candidate)
        if abs(mixed_duration - soundtrack_duration) > DURATION_TOLERANCE:
            raise MixError(
                f"the mix changed the soundtrack length "
                f"({_fmt(soundtrack_duration)}s → {_fmt(mixed_duration)}s); "
                f"refusing to publish it.")

        # The discriminating check: the placed window must actually change.
        after = probe_window_mean_volume(candidate, at, window)
        delta = after - before
        if abs(delta) < MIN_WINDOW_DELTA_DB:
            raise MixError(
                f"the mix is a no-op: mean volume over {_fmt(at)}–"
                f"{_fmt(at + window)}s is unchanged ({_fmt(before)} dB), so nothing was "
                f"added or ducked there. Check --volume ({volume}) and that the clip "
                f"window carries sound. Nothing was published.")

        os.replace(candidate, soundtrack)
    finally:
        for scratch in (clip_audio, candidate):
            try:
                scratch.unlink()
            except FileNotFoundError:
                pass

    return {
        "soundtrack": str(soundtrack),
        "at": at,
        "play_duration": play_duration,
        "soundtrack_duration": soundtrack_duration,
        "window_delta_db": delta,
    }


def _parser():
    parser = argparse.ArgumentParser(
        description=("Mix one clip's own audio into the canonical soundtrack, ducking "
                     "the voiceover+music under it (Phase 5, Step 5.3a)."))
    parser.add_argument("clip", help="Clip file — the storyboard `Clip:` path.")
    parser.add_argument(
        "--soundtrack", required=True,
        help=("Canonical soundtrack to mix into, e.g. voiceover-with-music.mp3. "
              "Replaced atomically, and only after the mix verifies."))
    parser.add_argument(
        "--clip-in", type=float, default=0.0,
        help=("Storyboard `Clip in`, in SECONDS. Must equal the scene <video>'s "
              "data-media-start, or the audio desyncs from the picture (default: 0)."))
    parser.add_argument(
        "--clip-out", type=float, required=True,
        help="Storyboard `Clip out`, in SECONDS. Must be greater than --clip-in.")
    parser.add_argument(
        "--speed", type=float, default=1.0,
        help=f"Storyboard `Speed` ({SPEED_MIN}–{SPEED_MAX}, default: 1.0).")
    parser.add_argument(
        "--at", type=float, required=True,
        help=("Where the scene starts, in SECONDS — the scene's data-start from "
              "index.html, copied verbatim (18.5 means 18.5 seconds, NOT 18.5 "
              "milliseconds). Milliseconds are computed internally."))
    parser.add_argument(
        "--volume", type=float, required=True,
        help="Storyboard `Clip audio` value: greater than 0, at most 1.")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        require_tools()
        summary = mix(
            clip=args.clip, soundtrack=args.soundtrack, clip_in=args.clip_in,
            clip_out=args.clip_out, speed=args.speed, volume=args.volume, at=args.at)
    except MixError as error:
        print(f"Error: {error}", file=sys.stderr)
        print(f"Soundtrack left unchanged: {args.soundtrack}", file=sys.stderr)
        return 1

    print(f"Mixed {args.clip} into {summary['soundtrack']}: "
          f"{_fmt(summary['at'])}s → {_fmt(summary['at'] + summary['play_duration'])}s "
          f"of a {_fmt(summary['soundtrack_duration'])}s soundtrack "
          f"(window mean volume moved {_fmt(summary['window_delta_db'])} dB).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
