#!/usr/bin/env python3
"""
hve-video-director — Caption Sidecar Generator

Reads the word-timing transcript produced in Phase 5. The legacy invocation
still emits ASR draft subtitles:

    voiceover.srt   (SubRip)
    voiceover.vtt   (WebVTT)

The accessibility workflow binds a human-reviewed cue manifest to the final
mixed-audio fingerprint, then emits delivery sidecars beside the video:

    captions-review.json
    out/final.srt
    out/final.vtt
    .hve/captions-state.json

Usage (from inside a generated project, after Phase 5 produced a transcript):
    python3 caption_gen.py                      # backward-compatible ASR drafts
    python3 caption_gen.py --input transcript.json
    # NARRATION_LANGUAGE is the confirmed canonical locale in the checked profile.
    python3 caption_gen.py draft --language "$NARRATION_LANGUAGE"
    # Review captions-review.json; add speakers/sounds; set review fields.
    python3 caption_gen.py approve --expected-language "$NARRATION_LANGUAGE"
    python3 caption_gen.py finalize --expected-language "$NARRATION_LANGUAGE"
    python3 caption_gen.py validate --expected-language "$NARRATION_LANGUAGE"

Input formats (both handled):
  - `transcript.json` from `npx hyperframes transcribe` — a FLAT list of word
    objects: [{"text": "Take", "start": 0.0, "end": 0.66}, ...].
  - `voiceover.json` from standalone `whisper --output_format json` — a dict
    with a "segments" list; each segment may carry per-word timing under
    "words" (present when `--word_timestamps True` was passed). When word
    timing is absent, segment text is distributed proportionally across the
    segment duration so both paths group identically.

Accessibility contract:
    `draft` is not approval. After the user reviews speech, speaker identity,
    and meaningful non-speech audio, `approve` binds that exact review content
    to an approval fingerprint. `finalize` rejects stale audio, changed approval
    content, and malformed/unreadable cues. `validate` rechecks the audio,
    reviewed manifest, outputs, and exact state before Phase 5 can complete.

Pure standard library; final-audio duration is read with the required ffprobe.
Unicode locale/word/grapheme handling uses the sibling language_tools.mjs with
the already-required Node runtime. These ceilings do not certify readability
in every language; the exact cues still need human review.
"""

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import unicodedata
import uuid
from bisect import bisect_left
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

# ─── Cue grouping defaults ──────────────────────────────────────────────────
MAX_CHARS = 42     # grapheme ceiling, not a language-specific readability guarantee
MAX_DURATION = 5.0  # seconds a single cue stays on screen
MAX_GAP = 0.8      # a pause longer than this forces a new cue
MAX_WORDS = 14     # hard cap on words per cue
MAX_LINES = 2
MAX_CPS = 25.0
MIN_DURATION = 0.4
SCHEMA_VERSION = 1

DEFAULT_AUDIO = "voiceover-with-music.mp3"
DEFAULT_MANIFEST = "captions-review.json"
DEFAULT_DRAFT_SRT = "voiceover.srt"
DEFAULT_DRAFT_VTT = "voiceover.vtt"
DEFAULT_FINAL_SRT = "out/final.srt"
DEFAULT_FINAL_VTT = "out/final.vtt"
DEFAULT_STATE = ".hve/captions-state.json"


def _language_tool(operation: str, payload: object) -> object:
    try:
        result = subprocess.run(
            ["node", str(Path(__file__).with_name("language_tools.mjs")), operation],
            input=json.dumps(payload, ensure_ascii=True), encoding="utf-8",
            capture_output=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError(
            f"caption language handling requires working Node/Intl support: {error}"
        ) from error
    if result.returncode:
        raise ValueError(
            f"caption language handling failed: {result.stderr.strip() or result.returncode}"
        )
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("language_tools.mjs returned invalid JSON") from error


@lru_cache(maxsize=128)
def _locale_info(language: str) -> dict:
    data = _language_tool("locales", [language])
    if (not isinstance(data, list) or len(data) != 1
            or not isinstance(data[0], dict)
            or not all(isinstance(data[0].get(key), str) and data[0][key]
                       for key in ("tag", "language", "script"))
            or data[0].get("direction") not in ("ltr", "rtl")
            or data[0].get("word_separator") not in ("", " ")):
        raise ValueError("language_tools.mjs returned invalid locale data")
    return data[0]


def _validate_language(language: str) -> str:
    if not isinstance(language, str) or not language.strip():
        raise ValueError("language must be a nonempty BCP 47 string")
    return _locale_info(language)["tag"]


class CaptionText:
    """Batch ICU segmentation and cache it for one caption operation."""

    def __init__(self, language: str) -> None:
        self.language = _validate_language(language)
        self.locale = _locale_info(self.language)
        self._cache: dict[str, dict] = {}

    def prime(self, texts: list[str]) -> None:
        """Segment uncached text in one Node call; never fall back to English."""
        missing = list(dict.fromkeys(text for text in texts if text not in self._cache))
        if not missing:
            return
        result = _language_tool("segment", {"language": self.language, "texts": missing})
        if (not isinstance(result, dict) or result.get("locale") != self.locale
                or not isinstance(result.get("texts"), list)
                or len(result["texts"]) != len(missing)):
            raise ValueError("language_tools.mjs returned invalid segmentation data")
        for text, entry in zip(missing, result["texts"]):
            if not isinstance(entry, dict):
                raise ValueError("language_tools.mjs returned an invalid text entry")
            graphemes, words = entry.get("graphemes"), entry.get("words")
            if (not isinstance(graphemes, list)
                    or not all(isinstance(g, str) and g for g in graphemes)
                    or "".join(graphemes) != text
                    or not isinstance(words, list)
                    or not all(isinstance(w, dict) and isinstance(w.get("text"), str)
                               and w["text"] and isinstance(w.get("word"), bool)
                               for w in words)
                    or "".join(w["text"] for w in words) != text):
                raise ValueError("language_tools.mjs did not preserve the input text")
            self._cache[text] = entry

    def segments(self, text: str) -> dict:
        """Return exact grapheme and word segments for text."""
        self.prime([text])
        return self._cache[text]

    def separator(self, left: str, right: str) -> str:
        """Keep supplied spacing and grapheme joins; separate unspaced Latin words."""
        if (not left or not right or left[-1].isspace() or right[0].isspace()
                or left.endswith("\u200d") or right.startswith("\u200d")):
            return ""
        offset = 0
        for grapheme in self.segments(left + right)["graphemes"]:
            offset += len(grapheme)
            if offset >= len(left):
                if offset != len(left):
                    return ""
                break
        if self.locale["word_separator"]:
            return self.locale["word_separator"]
        left_words = [w["text"] for w in self.segments(left)["words"] if w["word"]]
        right_words = [w["text"] for w in self.segments(right)["words"] if w["word"]]
        if left_words and right_words:
            # ICU owns token boundaries; this only preserves Latin word spacing in
            # mixed-script ASR whose main language does not separate words.
            def latin_word(word):
                letters = [char for char in word if char.isalpha()]
                return bool(letters) and all(
                    unicodedata.name(char, "").startswith("LATIN ") for char in letters
                )
            if latin_word(left_words[-1]) and latin_word(right_words[0]):
                return " "
        return ""


def load_words(data, language="en", *, text_tools=None):
    """Normalize either transcript format to a flat list of {text, start, end}."""
    if isinstance(data, list):
        return _words_from_list(data)

    if isinstance(data, dict):
        segments = data.get("segments")
        if segments:
            if not isinstance(segments, list) or not all(isinstance(seg, dict) for seg in segments):
                raise ValueError("transcript segments must be a list of objects")
            if all(seg.get("words") for seg in segments):
                words = []
                for seg in segments:
                    words.extend(_words_from_list(seg["words"]))
                return words
            return _segments_to_words(segments, text_tools or CaptionText(language))
        if data.get("words"):
            return _words_from_list(data["words"])

    raise ValueError(
        "Unrecognized transcript shape — expected a list of word objects or a "
        "Whisper dict with a 'segments' key."
    )


def _words_from_list(items):
    if not isinstance(items, list):
        raise ValueError("transcript words must be a list")
    words = []
    prefix = ""
    for w in items:
        if not isinstance(w, dict):
            raise ValueError("every transcript word must be an object")
        text = w.get("text") or w.get("word") or ""
        if not isinstance(text, str):
            raise ValueError("transcript text must be a string")
        if not text:
            continue
        if text.isspace():
            if words:
                words[-1]["text"] += text
            else:
                prefix += text
            continue
        start = float(w.get("start", 0.0))
        end = float(w.get("end", start))
        if not math.isfinite(start) or not math.isfinite(end):
            raise ValueError("transcript word times must be finite")
        words.append({"text": prefix + text, "start": start, "end": max(end, start)})
        prefix = ""
    return words


def _segments_to_words(segments, text_tools):
    """Synthesize word timings by distributing segment text over its duration."""
    words = []
    texts = [seg.get("text") or "" for seg in segments]
    if not all(isinstance(text, str) for text in texts):
        raise ValueError("transcript segment text must be a string")
    text_tools.prime(texts)
    token_groups = []
    for text in texts:
        tokens = []
        prefix = ""
        for part in text_tools.segments(text)["words"]:
            if part["word"]:
                tokens.append(prefix + part["text"])
                prefix = ""
            elif tokens:
                tokens[-1] += part["text"]
            else:
                prefix += part["text"]
        if prefix:
            tokens.append(prefix)
        token_groups.append(tokens)
    text_tools.prime([token for tokens in token_groups for token in tokens])
    for seg, tokens in zip(segments, token_groups):
        if not tokens:
            continue
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        if not math.isfinite(start) or not math.isfinite(end):
            raise ValueError("transcript segment times must be finite")
        duration = max(end - start, 0.001)
        weights = [
            sum(not g.isspace() for g in text_tools.segments(token)["graphemes"])
            for token in tokens
        ]
        char_total = sum(weights)
        cursor = start
        for token, weight in zip(tokens, weights):
            frac = (weight / char_total) if char_total else (1.0 / len(tokens))
            nxt = cursor + duration * frac
            words.append({"text": token, "start": cursor, "end": nxt})
            cursor = nxt
    return words


def _wrap_caption(text, max_chars, language="en", *, text_tools=None):
    """Wrap drafts at ICU words/whitespace, splitting only whole graphemes."""
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    tools = text_tools or CaptionText(language)
    source_lines = text.splitlines()
    tools.prime(source_lines)
    lines = []
    for line in source_lines:
        segmented = tools.segments(line)
        graphemes = segmented["graphemes"]
        boundaries = {0: 0}
        offset = 0
        for index, grapheme in enumerate(graphemes, 1):
            offset += len(grapheme)
            boundaries[offset] = index
        breaks = {i for i, g in enumerate(graphemes) if g.isspace()}
        if not tools.locale["word_separator"]:
            offset = 0
            for part in segmented["words"]:
                if part["word"] and offset in boundaries:
                    breaks.add(boundaries[offset])
                offset += len(part["text"])
        start = 0
        while len(graphemes) - start > max_chars:
            stop = max((i for i in breaks if start < i <= start + max_chars),
                       default=start + max_chars)
            end = stop
            while end > start and graphemes[end - 1].isspace():
                end -= 1
            if end > start:
                lines.append("".join(graphemes[start:end]))
            start = stop
            while start < len(graphemes) and graphemes[start].isspace():
                start += 1
        if start < len(graphemes):
            lines.append("".join(graphemes[start:]))
    return "\n".join(lines)


def group_cues(words, max_chars=MAX_CHARS, max_dur=MAX_DURATION,
               max_gap=MAX_GAP, max_words=MAX_WORDS, audio_end=None,
               *, language="en", text_tools=None):
    """Group timed text with Unicode-safe boundaries; readability still needs review."""
    if max_chars < 1 or max_words < 1:
        raise ValueError("max_chars and max_words must be positive")
    tools = text_tools or CaptionText(language)
    if not words:
        return []
    texts = [w["text"] for w in words]
    tools.prime(texts + [a + b for a, b in zip(texts, texts[1:])])
    pieces, spans = [], []
    offset = 0
    for index, word in enumerate(words):
        separator = tools.separator(texts[index - 1], word["text"]) if index else ""
        pieces.extend((separator, word["text"]))
        left = offset + len(separator)
        offset = left + len(word["text"])
        spans.append({**word, "_left": left, "_right": offset})
    joined = "".join(pieces)
    segmented = tools.segments(joined)
    graphemes = segmented["graphemes"]
    boundaries = [0]
    for grapheme in graphemes:
        boundaries.append(boundaries[-1] + len(grapheme))
    word_starts = []
    offset = 0
    for part in segmented["words"]:
        if part["word"]:
            word_starts.append(offset)
        offset += len(part["text"])

    # An ASR token boundary is not necessarily a grapheme boundary (marks/ZWJ).
    # Merge such tokens before any timing or width decision can split that cluster.
    safe_words = []
    boundary_set = set(boundaries)
    for word in spans:
        if safe_words and safe_words[-1]["_right"] not in boundary_set:
            safe_words[-1]["_right"] = word["_right"]
            safe_words[-1]["end"] = word["end"]
        else:
            safe_words.append(dict(word))
    for word in safe_words:
        lo = bisect_left(boundaries, word["_left"])
        hi = bisect_left(boundaries, word["_right"])
        while lo < hi and graphemes[lo].isspace():
            lo += 1
        while hi > lo and graphemes[hi - 1].isspace():
            hi -= 1
        word["_lo"], word["_hi"] = lo, hi

    cues = []
    current = []

    def cue_for(start, end, lo, hi):
        return {"start": start, "end": end, "_lo": lo, "_hi": hi,
                "text": "".join(graphemes[lo:hi])}

    def flush():
        if current:
            cues.append(cue_for(current[0]["start"], current[-1]["end"],
                                current[0]["_lo"], current[-1]["_hi"]))
            current.clear()

    for word in safe_words:
        if current:
            lo, hi = current[0]["_lo"], word["_hi"]
            count = (bisect_left(word_starts, boundaries[hi])
                     - bisect_left(word_starts, boundaries[lo]))
            gap = word["start"] - current[-1]["end"]
            span = word["end"] - current[0]["start"]
            if (hi - lo > max_chars or span > max_dur
                    or gap > max_gap or count > max_words):
                flush()
        current.append(word)
        if word["_hi"] > word["_lo"] and graphemes[word["_hi"] - 1] in ".!?。！？":
            flush()
    flush()

    # ── Deliver what approve/finalize will accept ────────────────────────
    # The draft is machine-generated, so every invariant the validator
    # enforces must hold by construction: the reviewer corrects CONTENT,
    # never machine formatting against the machine's own gate.

    # No overlap between adjacent cues.
    for a, b in zip(cues, cues[1:]):
        if a["end"] > b["start"]:
            a["end"] = b["start"]

    # A cue shorter than MIN_DURATION extends into the following gap, then
    # borrows from the preceding one — never past a neighbour or the audio.
    for i, cue in enumerate(cues):
        if cue["end"] - cue["start"] >= MIN_DURATION:
            continue
        forward_limit = cues[i + 1]["start"] if i + 1 < len(cues) else audio_end
        if forward_limit is None:
            forward_limit = cue["start"] + MIN_DURATION
        cue["end"] = max(cue["end"], min(cue["start"] + MIN_DURATION, forward_limit))
        if cue["end"] - cue["start"] >= MIN_DURATION:
            continue
        backward_limit = cues[i - 1]["end"] if i > 0 else 0.0
        cue["start"] = min(cue["start"],
                           max(cue["end"] - MIN_DURATION, backward_limit))

    # A cue its gaps cannot cover merges with a neighbour.
    merged = []
    for cue in cues:
        if merged and merged[-1]["end"] - merged[-1]["start"] < MIN_DURATION:
            prev = merged[-1]
            merged[-1] = cue_for(prev["start"], cue["end"], prev["_lo"], cue["_hi"])
        else:
            merged.append(dict(cue))
    if len(merged) >= 2 and merged[-1]["end"] - merged[-1]["start"] < MIN_DURATION:
        last = merged.pop()
        prev = merged[-1]
        merged[-1] = cue_for(prev["start"], last["end"], prev["_lo"], last["_hi"])
    cues = merged

    # Last resort for a single degenerate cue with no neighbour to lean on.
    for cue in cues:
        if cue["end"] <= cue["start"]:
            cue["end"] = cue["start"] + MIN_DURATION

    # No line wider than the validator's cap.
    tools.prime([line for cue in cues for line in cue["text"].splitlines()])
    for cue in cues:
        if any(len(tools.segments(line)["graphemes"]) > max_chars
               for line in cue["text"].splitlines()):
            cue["text"] = _wrap_caption(cue["text"], max_chars, text_tools=tools)
    return [{key: cue[key] for key in ("start", "end", "text")} for cue in cues]


def _fmt(t, sep):
    total_ms = int(round(max(t, 0.0) * 1000))
    h, rem = divmod(total_ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def _srt_content(cues):
    blocks = []
    for i, cue in enumerate(cues, 1):
        blocks.append(f"{i}\n{_fmt(cue['start'], ',')} --> {_fmt(cue['end'], ',')}\n{cue['text']}")
    return "\n\n".join(blocks) + "\n"


def _vtt_content(cues):
    blocks = ["WEBVTT"]
    for cue in cues:
        blocks.append(f"{_fmt(cue['start'], '.')} --> {_fmt(cue['end'], '.')}\n{cue['text']}")
    return "\n\n".join(blocks) + "\n"


def _write_text_atomic(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _publish_text_bundle_transactionally(items):
    items = list(items)
    paths = [Path(path) for path, _ in items]
    if len(paths) != len(set(paths)):
        raise ValueError("caption delivery paths must be distinct")

    staged = {}
    backups = {}
    published = set()
    try:
        for path, (_, content) in zip(paths, items):
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
            with temporary.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            staged[path] = temporary

        for path in paths:
            if path.exists():
                backup = path.with_name(f".{path.name}.{uuid.uuid4().hex}.bak")
                os.replace(path, backup)
                backups[path] = backup

        for path in paths:
            os.replace(staged[path], path)
            published.add(path)
            staged.pop(path)
    except BaseException as exc:
        rollback_errors = []
        for path in reversed(paths):
            backup = backups.get(path)
            try:
                if backup is not None and backup.exists():
                    os.replace(backup, path)
                elif path in published:
                    path.unlink(missing_ok=True)
            except OSError as rollback_exc:
                rollback_errors.append(f"{path}: {rollback_exc}")
        if rollback_errors:
            detail = "; ".join(rollback_errors)
            raise OSError(
                f"caption delivery failed and rollback was incomplete: {detail}"
            ) from exc
        raise
    else:
        cleanup_errors = []
        for backup in backups.values():
            try:
                backup.unlink()
            except OSError as cleanup_exc:
                cleanup_errors.append(f"{backup}: {cleanup_exc}")
        if cleanup_errors:
            detail = "; ".join(cleanup_errors)
            raise OSError(
                f"caption delivery succeeded but backup cleanup failed: {detail}"
            )
    finally:
        for temporary in staged.values():
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def write_srt(cues, path):
    _write_text_atomic(path, _srt_content(cues))


def write_vtt(cues, path):
    _write_text_atomic(path, _vtt_content(cues))


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _sha256_content(content):
    return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"


def _probe_audio_duration(path):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nk=1:nw=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise ValueError("ffprobe is required to validate final captions") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()[:200]
        raise ValueError(f"ffprobe failed for {path}: {detail}") from exc
    value = result.stdout.strip()
    try:
        duration = float(value)
    except ValueError as exc:
        raise ValueError(f"ffprobe returned no usable duration for {path}") from exc
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"audio duration must be positive: {duration}")
    return duration


def _now_utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {path}") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def _write_json_atomic(path, value):
    _write_text_atomic(
        path,
        _json_content(value),
    )


def _json_content(value):
    return json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def _draft_manifest(cues, audio_path, duration, language):
    language = _validate_language(language)
    return {
        "schema_version": SCHEMA_VERSION,
        "language": language,
        "audio": {
            "path": str(audio_path),
            "sha256": _sha256(audio_path),
            "duration": round(duration, 3),
        },
        "reviewed": False,
        "speech_review": "pending",
        "speaker_review": "pending",
        "sound_review": "pending",
        "approval": None,
        "review_notes": [
            "Correct every spoken caption against the final soundtrack.",
            "Set speaker_review to single-obvious or included; add speaker labels when needed.",
            "Set sound_review to none-meaningful or included; add meaningful music/SFX cues.",
            "Grapheme/rate ceilings do not certify readability in this language; review it.",
            "Run the approve command only after the user approves the complete cue list.",
        ],
        "cues": [
            {
                "start": cue["start"],
                "end": cue["end"],
                "text": cue["text"],
                "speaker": "",
                "sound": "",
            }
            for cue in cues
        ],
    }


def create_review_draft(
    input_path,
    audio_path,
    manifest_path=DEFAULT_MANIFEST,
    srt_path=DEFAULT_DRAFT_SRT,
    vtt_path=DEFAULT_DRAFT_VTT,
    language="en",
    max_chars=MAX_CHARS,
    force=False,
):
    manifest_path = Path(manifest_path)
    if manifest_path.exists() and not force:
        raise ValueError(
            f"{manifest_path} already exists; preserve the reviewed work or "
            "pass --force only after explicit approval"
        )
    if not Path(audio_path).is_file():
        raise ValueError(f"final mixed audio not found: {audio_path}")
    tools = CaptionText(language)
    data = _load_json(input_path)
    words = load_words(data, text_tools=tools)
    if not words:
        raise ValueError(f"no word timings found in {input_path}")
    # Probe before grouping: the min-duration repair extends cues into gaps
    # and must know where the audio ends so it never extends past it.
    duration = _probe_audio_duration(audio_path)
    cues = group_cues(words, max_chars=max_chars, audio_end=duration, text_tools=tools)
    if cues and cues[-1]["end"] > duration + 0.05:
        raise ValueError(
            "transcript extends beyond the final mixed audio; regenerate the transcript"
        )
    manifest = _draft_manifest(cues, audio_path, duration, tools.language)
    write_srt(cues, srt_path)
    write_vtt(cues, vtt_path)
    _write_json_atomic(manifest_path, manifest)
    return manifest


def _number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def _render_review_cue(cue):
    lines = []
    text = cue["text"].strip()
    speaker = cue["speaker"].strip()
    sound = cue["sound"].strip()
    if text:
        lines.extend(text.splitlines())
        if speaker:
            lines[0] = f"{speaker}: {lines[0]}"
    if sound:
        lines.append(f"[{sound}]")
    return "\n".join(lines)


def _review_content_hash(manifest):
    payload = {
        "schema_version": manifest["schema_version"],
        "language": manifest["language"],
        "audio": manifest["audio"],
        "speech_review": manifest["speech_review"],
        "speaker_review": manifest["speaker_review"],
        "sound_review": manifest["sound_review"],
        "cues": manifest["cues"],
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return _sha256_content(canonical)


def _validate_approval(manifest):
    approval = manifest.get("approval")
    if not isinstance(approval, dict):
        raise ValueError(
            "caption approval is missing; run `caption_gen.py approve` "
            "after the user approves the exact cue list"
        )
    expected_fields = {"approved_at", "content_sha256"}
    if set(approval) != expected_fields:
        raise ValueError("caption approval fields are invalid")
    approved_at = approval["approved_at"]
    if not isinstance(approved_at, str) or not approved_at.endswith("Z"):
        raise ValueError("caption approval approved_at must be a UTC timestamp")
    try:
        timestamp = datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            "caption approval approved_at must be a UTC timestamp"
        ) from exc
    if timestamp.tzinfo is None:
        raise ValueError("caption approval approved_at must include UTC")
    if approval["content_sha256"] != _review_content_hash(manifest):
        raise ValueError(
            "caption cues or review decisions changed after user approval; "
            "review and approve the exact content again"
        )


def validate_review_manifest(
    manifest,
    audio_path,
    duration,
    *,
    require_approval=True,
    expected_language=None,
):
    if not isinstance(manifest, dict):
        raise ValueError("caption review manifest must be a JSON object")
    expected_manifest_fields = {
        "schema_version",
        "language",
        "audio",
        "reviewed",
        "speech_review",
        "speaker_review",
        "sound_review",
        "approval",
        "review_notes",
        "cues",
    }
    if set(manifest) != expected_manifest_fields:
        raise ValueError("caption review manifest fields are invalid")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"caption review schema_version must be {SCHEMA_VERSION}"
        )
    language = manifest.get("language")
    if not isinstance(language, str):
        raise ValueError("language must be a string")
    canonical_language = _validate_language(language)
    if (expected_language is not None
            and canonical_language != _validate_language(expected_language)):
        raise ValueError(
            f"caption language {language!r} does not match expected narration "
            f"language {expected_language!r}; review the correctly labelled captions"
        )
    reviewed = manifest.get("reviewed")
    if not isinstance(reviewed, bool):
        raise ValueError("reviewed must be a boolean")
    if require_approval and reviewed is not True:
        raise ValueError("captions are not human-reviewed (`reviewed` must be true)")

    speech_review = manifest.get("speech_review")
    if speech_review != "verified":
        raise ValueError(
            "speech_review must be verified after every spoken cue is corrected"
        )
    speaker_review = manifest.get("speaker_review")
    if speaker_review not in {"single-obvious", "included"}:
        raise ValueError(
            "speaker_review must be single-obvious or included after review"
        )
    sound_review = manifest.get("sound_review")
    if sound_review not in {"none-meaningful", "included"}:
        raise ValueError(
            "sound_review must be none-meaningful or included after review"
        )

    audio = manifest.get("audio")
    if not isinstance(audio, dict):
        raise ValueError("audio fingerprint record is missing")
    if set(audio) != {"path", "sha256", "duration"}:
        raise ValueError("audio fingerprint fields are invalid")
    if audio.get("path") != str(audio_path):
        raise ValueError(
            "caption review audio path does not match the final mixed audio"
        )
    if audio.get("sha256") != _sha256(audio_path):
        raise ValueError(
            "final mixed audio changed after the caption draft; captions are stale"
        )
    recorded_duration = _number(audio.get("duration"), "audio.duration")
    if abs(recorded_duration - duration) > 0.05:
        raise ValueError(
            "final mixed audio duration changed after the caption draft"
        )
    review_notes = manifest.get("review_notes")
    if (
        not isinstance(review_notes, list)
        or not all(isinstance(note, str) for note in review_notes)
    ):
        raise ValueError("review_notes must be a list of strings")

    raw_cues = manifest.get("cues")
    if not isinstance(raw_cues, list) or not raw_cues:
        raise ValueError("cues must be a non-empty list")

    cues = []
    previous_end = 0.0
    has_speaker = False
    has_sound = False
    required_fields = {"start", "end", "text", "speaker", "sound"}
    for index, raw in enumerate(raw_cues, 1):
        if not isinstance(raw, dict):
            raise ValueError(f"cue {index} must be an object")
        actual_fields = set(raw)
        if actual_fields != required_fields:
            missing = ", ".join(sorted(required_fields - actual_fields))
            extra = ", ".join(sorted(actual_fields - required_fields))
            detail = "; ".join(
                part
                for part in (
                    f"missing {missing}" if missing else "",
                    f"unexpected {extra}" if extra else "",
                )
                if part
            )
            raise ValueError(f"cue {index} fields are invalid: {detail}")

        start = _number(raw["start"], f"cue {index}.start")
        end = _number(raw["end"], f"cue {index}.end")
        if start < 0 or end <= start:
            raise ValueError(f"cue {index} must have 0 <= start < end")
        if end - start < MIN_DURATION:
            raise ValueError(
                f"cue {index} is shorter than {MIN_DURATION:.1f}s"
            )
        if end > duration + 0.05:
            raise ValueError(f"cue {index} extends beyond the final audio")
        if start < previous_end - 0.001:
            raise ValueError(f"cue {index} overlaps the previous cue")

        for field in ("text", "speaker", "sound"):
            if not isinstance(raw[field], str):
                raise ValueError(f"cue {index}.{field} must be a string")
            if "-->" in raw[field]:
                raise ValueError(
                    f"cue {index}.{field} contains a timestamp delimiter"
                )
        if "\n" in raw["speaker"] or "\n" in raw["sound"]:
            raise ValueError(
                f"cue {index} speaker and sound must each be one line"
            )
        if raw["speaker"].strip() and not raw["text"].strip():
            raise ValueError(f"cue {index} has a speaker but no speech")

        rendered = _render_review_cue(raw)
        lines = rendered.splitlines()
        if not lines:
            raise ValueError(f"cue {index} has no speech or sound")
        if len(lines) > MAX_LINES:
            raise ValueError(
                f"cue {index} exceeds the {MAX_LINES}-line caption limit"
            )
        if any(not line.strip() for line in lines):
            raise ValueError(f"cue {index} contains a blank caption line")
        has_speaker = has_speaker or bool(raw["speaker"].strip())
        has_sound = has_sound or bool(raw["sound"].strip())
        cues.append({"start": start, "end": end, "text": rendered})
        previous_end = end

    tools = CaptionText(canonical_language)
    tools.prime([line for cue in cues for line in cue["text"].splitlines()])
    for index, cue in enumerate(cues, 1):
        segmented_lines = [
            tools.segments(line)["graphemes"] for line in cue["text"].splitlines()
        ]
        if any(len(line) > MAX_CHARS for line in segmented_lines):
            raise ValueError(
                f"cue {index} exceeds {MAX_CHARS} characters (graphemes) on one line"
            )
        characters = sum(not g.isspace() for line in segmented_lines for g in line)
        cps = characters / (cue["end"] - cue["start"])
        if cps > MAX_CPS:
            raise ValueError(
                f"cue {index} reads at {cps:.1f} characters/s (graphemes); "
                f"maximum is {MAX_CPS:.1f}"
            )

    if speaker_review == "included" and not has_speaker:
        raise ValueError(
            "speaker_review is included but no cue has a speaker label"
        )
    if sound_review == "included" and not has_sound:
        raise ValueError(
            "sound_review is included but no cue has a meaningful sound"
        )
    if sound_review == "none-meaningful" and has_sound:
        raise ValueError(
            "sound_review is none-meaningful but sound cues are present"
        )
    if require_approval:
        _validate_approval(manifest)
    return cues


def approve_reviewed_captions(
    audio_path=DEFAULT_AUDIO,
    manifest_path=DEFAULT_MANIFEST,
    *,
    expected_language=None,
):
    """Bind explicit approval to unchanged cues in the expected narration locale."""
    if not Path(audio_path).is_file():
        raise ValueError(f"final mixed audio not found: {audio_path}")
    manifest = _load_json(manifest_path)
    duration = _probe_audio_duration(audio_path)
    validate_review_manifest(
        manifest,
        audio_path,
        duration,
        require_approval=False,
        expected_language=expected_language,
    )
    manifest["reviewed"] = True
    manifest["approval"] = {
        "approved_at": _now_utc(),
        "content_sha256": _review_content_hash(manifest),
    }
    _write_json_atomic(manifest_path, manifest)
    return manifest


def _delivery_state(
    *,
    manifest,
    audio_path,
    manifest_path,
    srt_path,
    vtt_path,
    duration,
    srt_content,
    vtt_content,
):
    return {
        "schema_version": SCHEMA_VERSION,
        "language": manifest["language"],
        "audio": {
            "path": str(audio_path),
            "sha256": _sha256(audio_path),
            "duration": round(duration, 3),
        },
        "manifest": {
            "path": str(manifest_path),
            "sha256": _sha256(manifest_path),
        },
        "outputs": {
            "srt": {
                "path": str(srt_path),
                "sha256": _sha256_content(srt_content),
            },
            "vtt": {
                "path": str(vtt_path),
                "sha256": _sha256_content(vtt_content),
            },
        },
    }


def finalize_reviewed_captions(
    audio_path=DEFAULT_AUDIO,
    manifest_path=DEFAULT_MANIFEST,
    srt_path=DEFAULT_FINAL_SRT,
    vtt_path=DEFAULT_FINAL_VTT,
    state_path=DEFAULT_STATE,
    *,
    expected_language=None,
):
    """Publish the reviewed delivery set only for the expected narration locale."""
    if not Path(audio_path).is_file():
        raise ValueError(f"final mixed audio not found: {audio_path}")
    manifest = _load_json(manifest_path)
    duration = _probe_audio_duration(audio_path)
    cues = validate_review_manifest(
        manifest, audio_path, duration, expected_language=expected_language
    )
    srt_content = _srt_content(cues)
    vtt_content = _vtt_content(cues)
    state = _delivery_state(
        manifest=manifest,
        audio_path=audio_path,
        manifest_path=manifest_path,
        srt_path=srt_path,
        vtt_path=vtt_path,
        duration=duration,
        srt_content=srt_content,
        vtt_content=vtt_content,
    )
    _publish_text_bundle_transactionally(
        (
            (srt_path, srt_content),
            (vtt_path, vtt_content),
            (state_path, _json_content(state)),
        )
    )
    return state


def validate_final_captions(
    audio_path=DEFAULT_AUDIO,
    manifest_path=DEFAULT_MANIFEST,
    srt_path=DEFAULT_FINAL_SRT,
    vtt_path=DEFAULT_FINAL_VTT,
    state_path=DEFAULT_STATE,
    *,
    expected_language=None,
):
    """Check exact delivery bytes, approval and the expected narration locale."""
    if not Path(audio_path).is_file():
        raise ValueError(f"final mixed audio not found: {audio_path}")
    manifest = _load_json(manifest_path)
    duration = _probe_audio_duration(audio_path)
    cues = validate_review_manifest(
        manifest, audio_path, duration, expected_language=expected_language
    )
    srt_content = _srt_content(cues)
    vtt_content = _vtt_content(cues)
    for label, path in (("SRT", srt_path), ("VTT", vtt_path)):
        if not Path(path).is_file():
            raise ValueError(f"final {label} is missing: {path}")
    state = _load_json(state_path)
    expected_state = _delivery_state(
        manifest=manifest,
        audio_path=audio_path,
        manifest_path=manifest_path,
        srt_path=srt_path,
        vtt_path=vtt_path,
        duration=duration,
        srt_content=srt_content,
        vtt_content=vtt_content,
    )
    if state != expected_state:
        raise ValueError("caption delivery state is stale or was modified")

    if Path(srt_path).read_text(encoding="utf-8") != srt_content:
        raise ValueError("final SRT does not match the reviewed cue manifest")
    if Path(vtt_path).read_text(encoding="utf-8") != vtt_content:
        raise ValueError("final VTT does not match the reviewed cue manifest")
    return state


def _detect_input():
    for candidate in ("transcript.json", "voiceover.json"):
        if Path(candidate).is_file():
            return candidate
    return None


def _legacy_main(argv):
    parser = argparse.ArgumentParser(description="Generate voiceover.srt/.vtt caption sidecars.")
    parser.add_argument("--input", help="Transcript JSON (default: auto-detect transcript.json, then voiceover.json).")
    parser.add_argument("--srt", default="voiceover.srt", help="Output SRT path (default: voiceover.srt).")
    parser.add_argument("--vtt", default="voiceover.vtt", help="Output VTT path (default: voiceover.vtt).")
    parser.add_argument("--max-chars", type=int, default=MAX_CHARS, help="Max graphemes per caption line.")
    parser.add_argument("--language", default="en", help="Transcript BCP 47 locale (legacy default: en).")
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
        tools = CaptionText(args.language)
        words = load_words(data, text_tools=tools)
        if not words:
            raise ValueError("no word timings found")
        cues = group_cues(words, max_chars=args.max_chars, text_tools=tools)
        write_srt(cues, args.srt)
        write_vtt(cues, args.vtt)
    except (OSError, ValueError) as exc:
        print(f"Error reading {input_path}: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {len(cues)} caption cues from {input_path}:")
    print(f"  {args.srt}")
    print(f"  {args.vtt}")
    print("Note: ASR draft subtitles — review before shipping as accessibility captions.")
    return 0


def _workflow_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Create, approve, finalize, and validate reviewed "
            "closed-caption sidecars."
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)

    draft = commands.add_parser(
        "draft",
        help="Create ASR drafts plus a human-review cue manifest.",
    )
    draft.add_argument("--input", help="Transcript JSON (default: auto-detect).")
    draft.add_argument("--audio", default=DEFAULT_AUDIO)
    draft.add_argument("--manifest", default=DEFAULT_MANIFEST)
    draft.add_argument("--srt", default=DEFAULT_DRAFT_SRT)
    draft.add_argument("--vtt", default=DEFAULT_DRAFT_VTT)
    draft.add_argument("--language", default="en")
    draft.add_argument("--max-chars", type=int, default=MAX_CHARS)
    draft.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing review manifest after explicit approval.",
    )

    approve = commands.add_parser(
        "approve",
        help="Fingerprint the exact cue content after explicit user approval.",
    )
    approve.add_argument("--audio", default=DEFAULT_AUDIO)
    approve.add_argument("--manifest", default=DEFAULT_MANIFEST)
    approve.add_argument("--expected-language", help="Confirmed narration BCP 47 locale.")

    for name, help_text in (
        ("finalize", "Emit reviewed delivery sidecars and fingerprint state."),
        ("validate", "Verify reviewed captions against final mixed audio."),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--audio", default=DEFAULT_AUDIO)
        command.add_argument("--manifest", default=DEFAULT_MANIFEST)
        command.add_argument("--srt", default=DEFAULT_FINAL_SRT)
        command.add_argument("--vtt", default=DEFAULT_FINAL_VTT)
        command.add_argument("--state", default=DEFAULT_STATE)
        command.add_argument("--expected-language", help="Confirmed narration BCP 47 locale.")
    return parser


def _workflow_main(argv):
    args = _workflow_parser().parse_args(argv)
    try:
        if args.command == "draft":
            input_path = args.input or _detect_input()
            if not input_path:
                raise ValueError(
                    "no transcript found; run HyperFrames transcribe/Whisper "
                    "or pass --input"
                )
            manifest = create_review_draft(
                input_path=input_path,
                audio_path=args.audio,
                manifest_path=args.manifest,
                srt_path=args.srt,
                vtt_path=args.vtt,
                language=args.language,
                max_chars=args.max_chars,
                force=args.force,
            )
            print(
                f"Wrote {len(manifest['cues'])} ASR draft cues and review manifest:"
            )
            print(f"  {args.srt}")
            print(f"  {args.vtt}")
            print(f"  {args.manifest}")
            print(
                "Human review required: correct speech, review speakers and "
                "meaningful sounds, then run approve after user approval."
            )
            return 0
        if args.command == "approve":
            manifest = approve_reviewed_captions(
                audio_path=args.audio,
                manifest_path=args.manifest,
                expected_language=args.expected_language,
            )
            print(
                "Approved exact caption review content for "
                f"{manifest['audio']['sha256']}:"
            )
            print(f"  {args.manifest}")
            return 0
        if args.command == "finalize":
            state = finalize_reviewed_captions(
                audio_path=args.audio,
                manifest_path=args.manifest,
                srt_path=args.srt,
                vtt_path=args.vtt,
                state_path=args.state,
                expected_language=args.expected_language,
            )
            print(
                f"Finalized reviewed {state['language']} captions bound to "
                f"{state['audio']['sha256']}:"
            )
            print(f"  {args.srt}")
            print(f"  {args.vtt}")
            print(f"  {args.state}")
            return 0
        state = validate_final_captions(
            audio_path=args.audio,
            manifest_path=args.manifest,
            srt_path=args.srt,
            vtt_path=args.vtt,
            state_path=args.state,
            expected_language=args.expected_language,
        )
        print(
            f"Reviewed captions are current for {state['audio']['sha256']} "
            f"({state['language']})."
        )
        return 0
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in {"draft", "approve", "finalize", "validate"}:
        return _workflow_main(args)
    return _legacy_main(args)


if __name__ == "__main__":
    sys.exit(main())
