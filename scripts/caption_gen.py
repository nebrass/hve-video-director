#!/usr/bin/env python3
"""
hve-spielberg — Caption Sidecar Generator

Reads the word-timing transcript produced in Phase 5 and emits toggleable
subtitle sidecars next to the render:

    voiceover.srt   (SubRip)
    voiceover.vtt   (WebVTT)

Usage (from inside a generated project, after Phase 5 produced a transcript):
    python3 caption_gen.py                      # auto-detect transcript.json / voiceover.json
    python3 caption_gen.py --input transcript.json
    python3 caption_gen.py --srt voiceover.srt --vtt voiceover.vtt

Input formats (both handled):
  - `transcript.json` from `npx hyperframes transcribe` — a FLAT list of word
    objects: [{"text": "Take", "start": 0.0, "end": 0.66}, ...].
  - `voiceover.json` from standalone `whisper --output_format json` — a dict
    with a "segments" list; each segment may carry per-word timing under
    "words" (present when `--word_timestamps True` was passed). When word
    timing is absent, segment text is distributed proportionally across the
    segment duration so both paths group identically.

Scope note (accessibility):
    These are ASR-derived **draft subtitles** of the spoken voiceover. They are
    NOT yet WCAG 2.1 closed captions — true closed captions also transcribe
    meaningful non-speech audio (music/sfx cues, speaker IDs) and require human
    review of the ASR output. Treat the output as a reviewable starting point.

Pure standard library — no third-party dependencies.
"""

import argparse
import json
import sys
from pathlib import Path

# ─── Cue grouping defaults ──────────────────────────────────────────────────
MAX_CHARS = 42     # readable single-line width for video subtitles
MAX_DURATION = 5.0  # seconds a single cue stays on screen
MAX_GAP = 0.8      # a pause longer than this forces a new cue
MAX_WORDS = 14     # hard cap on words per cue


def load_words(data):
    """Normalize either transcript format to a flat list of {text, start, end}."""
    if isinstance(data, list):
        return _words_from_list(data)

    if isinstance(data, dict):
        segments = data.get("segments")
        if segments:
            if all(seg.get("words") for seg in segments):
                words = []
                for seg in segments:
                    words.extend(_words_from_list(seg["words"]))
                return words
            return _segments_to_words(segments)
        if data.get("words"):
            return _words_from_list(data["words"])

    raise ValueError(
        "Unrecognized transcript shape — expected a list of word objects or a "
        "Whisper dict with a 'segments' key."
    )


def _words_from_list(items):
    words = []
    for w in items:
        text = (w.get("text") or w.get("word") or "").strip()
        if not text:
            continue
        start = float(w.get("start", 0.0))
        end = float(w.get("end", start))
        words.append({"text": text, "start": start, "end": max(end, start)})
    return words


def _segments_to_words(segments):
    """Synthesize word timings by distributing segment text over its duration."""
    words = []
    for seg in segments:
        text = (seg.get("text") or "").strip()
        tokens = text.split()
        if not tokens:
            continue
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        duration = max(end - start, 0.001)
        char_total = sum(len(t) for t in tokens)
        cursor = start
        for token in tokens:
            frac = (len(token) / char_total) if char_total else (1.0 / len(tokens))
            nxt = cursor + duration * frac
            words.append({"text": token, "start": cursor, "end": nxt})
            cursor = nxt
    return words


def group_cues(words, max_chars=MAX_CHARS, max_dur=MAX_DURATION,
               max_gap=MAX_GAP, max_words=MAX_WORDS):
    """Group words into readable caption cues."""
    cues = []
    current = []

    def flush():
        if current:
            text = " ".join(w["text"] for w in current).strip()
            cues.append({"start": current[0]["start"],
                         "end": current[-1]["end"], "text": text})
            current.clear()

    for word in words:
        if current:
            prospective_len = len(" ".join(w["text"] for w in current)) + 1 + len(word["text"])
            gap = word["start"] - current[-1]["end"]
            span = word["end"] - current[0]["start"]
            if (prospective_len > max_chars or span > max_dur
                    or gap > max_gap or len(current) >= max_words):
                flush()
        current.append(word)
        if word["text"][-1] in ".!?":
            flush()
    flush()

    # No zero/negative durations, and no overlap between adjacent cues.
    for a, b in zip(cues, cues[1:]):
        if a["end"] > b["start"]:
            a["end"] = b["start"]
    for cue in cues:
        if cue["end"] <= cue["start"]:
            cue["end"] = cue["start"] + 0.4
    return cues


def _fmt(t, sep):
    total_ms = int(round(max(t, 0.0) * 1000))
    h, rem = divmod(total_ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def write_srt(cues, path):
    blocks = []
    for i, cue in enumerate(cues, 1):
        blocks.append(f"{i}\n{_fmt(cue['start'], ',')} --> {_fmt(cue['end'], ',')}\n{cue['text']}")
    Path(path).write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def write_vtt(cues, path):
    blocks = ["WEBVTT"]
    for cue in cues:
        blocks.append(f"{_fmt(cue['start'], '.')} --> {_fmt(cue['end'], '.')}\n{cue['text']}")
    Path(path).write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def _detect_input():
    for candidate in ("transcript.json", "voiceover.json"):
        if Path(candidate).is_file():
            return candidate
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate voiceover.srt/.vtt caption sidecars.")
    parser.add_argument("--input", help="Transcript JSON (default: auto-detect transcript.json, then voiceover.json).")
    parser.add_argument("--srt", default="voiceover.srt", help="Output SRT path (default: voiceover.srt).")
    parser.add_argument("--vtt", default="voiceover.vtt", help="Output VTT path (default: voiceover.vtt).")
    parser.add_argument("--max-chars", type=int, default=MAX_CHARS, help="Max characters per cue.")
    args = parser.parse_args(argv)

    input_path = args.input or _detect_input()
    if not input_path:
        print("Error: no transcript found. Run `npx hyperframes transcribe voiceover.mp3` "
              "(writes transcript.json) or standalone whisper (writes voiceover.json) first, "
              "or pass --input.", file=sys.stderr)
        return 1
    if not Path(input_path).is_file():
        print(f"Error: transcript not found: {input_path}", file=sys.stderr)
        return 1

    try:
        data = json.loads(Path(input_path).read_text(encoding="utf-8"))
        words = load_words(data)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Error reading {input_path}: {exc}", file=sys.stderr)
        return 1

    if not words:
        print(f"Error: no word timings found in {input_path}.", file=sys.stderr)
        return 1

    cues = group_cues(words, max_chars=args.max_chars)
    write_srt(cues, args.srt)
    write_vtt(cues, args.vtt)
    print(f"Wrote {len(cues)} caption cues from {input_path}:")
    print(f"  {args.srt}")
    print(f"  {args.vtt}")
    print("Note: ASR draft subtitles — review before shipping as accessibility captions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
