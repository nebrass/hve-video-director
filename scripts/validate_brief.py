#!/usr/bin/env python3
"""Validate and fingerprint an hve-video-director creative brief.

The generated project's ``project-plan.md`` must contain the exact two-column
``## Creative Brief`` table documented in ``templates/project-plan.md``.
Confirmation state is stored atomically in ``.hve/brief-state.json``.

It also reads ``storyboard.md`` in the official HyperFrames shape — read-only,
and deliberately outside every fingerprint: the storyboard describes the film,
the Creative Brief records consent. A storyboard in the older bespoke shape is
read too, so an in-flight project keeps resuming without touching a file.

Examples:
    python3 validate_brief.py --project-dir ./my-video status --json
    python3 validate_brief.py --project-dir ./my-video migrate
    python3 validate_brief.py --project-dir ./my-video storyboard --json
    python3 validate_brief.py --project-dir ./my-video migrate-storyboard
    python3 validate_brief.py --project-dir ./my-video confirm-story
    python3 validate_brief.py --project-dir ./my-video confirm-audio
    python3 validate_brief.py --project-dir ./my-video stamp phase-1
    python3 validate_brief.py --project-dir ./my-video require phase-1

Exit codes:
    0: command succeeded (``status`` means the table is complete)
    1: brief incomplete, confirmation missing, or requested phase stale
    2: malformed project plan/state or invalid command input
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


SCHEMA_VERSION = 1
PLAN_NAME = "project-plan.md"
STATE_RELATIVE_PATH = Path(".hve") / "brief-state.json"

STORY_FIELDS = (
    "mode",
    "product_surface",
    "duration",
    "theme",
    "aspect_ratio",
    "identity_strategy",
    "identity_choice",
    "visual_ceiling",
    "voice",
    "transition_style",
    "transition_speed",
    "music_strategy",
)
ALL_FIELDS = (*STORY_FIELDS, "final_music_track")
PHASES = tuple(f"phase-{number}" for number in range(1, 6))
BRIEF_PLACEHOLDERS = {
    "mode": "{promo, showcase, or tutorial}",
    "product_surface": "{ui or none}",
    "duration": "{positive seconds, for example 60s}",
    "theme": "{light or dark}",
    "aspect_ratio": (
        "{16:9 1920x1080, 9:16 1080x1920, 1:1 1080x1080, "
        "or 4:5 1080x1350}"
    ),
    "identity_strategy": (
        "{design-system, hyperframes-style, screenshots, or custom}"
    ),
    "identity_choice": (
        "{design-system slug, HyperFrames style name, captured-screenshots, "
        "or custom identity name}"
    ),
    "visual_ceiling": "{derived or flat}",
    "voice": "{elevenlabs:<name>:<voice-id> or kokoro:<voice-id>}",
    "transition_style": (
        "{metallic-swoosh, zoom-through, crossfade, or slide-from-bottom}"
    ),
    "transition_speed": "{quick, medium, or slow}",
    "music_strategy": "{freesound, delegated, user-provided, or none}",
    "final_music_track": (
        "{none or compact JSON with title, path, source, and license}"
    ),
}
VISUAL_CEILINGS = {"derived", "flat"}
DESIGN_SYSTEMS = {
    "stripe",
    "linear-app",
    "apple",
    "notion",
    "vercel",
    "airbnb",
    "github",
    "cal",
    "arc",
    "bento",
}
DESIGN_SYSTEM_THEMES = {
    "stripe": {"light", "dark"},
    "linear-app": {"dark"},
    "apple": {"light", "dark"},
    "notion": {"light", "dark"},
    "vercel": {"light"},
    "airbnb": {"light"},
    "github": {"light", "dark"},
    "cal": {"light"},
    "arc": {"light", "dark"},
    "bento": {"light"},
}
HYPERFRAMES_STYLES = {
    "Swiss Pulse",
    "Velvet Standard",
    "Deconstructed",
    "Maximalist Type",
    "Data Drift",
    "Soft Signal",
    "Folk Frequency",
    "Shadow Cut",
}
ASPECT_RATIOS = {
    "16:9 1920x1080",
    "9:16 1080x1920",
    "1:1 1080x1080",
    "4:5 1080x1350",
}
TRANSITION_STYLES = {
    "metallic-swoosh",
    "zoom-through",
    "crossfade",
    "slide-from-bottom",
}
MUSIC_STRATEGIES = {"freesound", "delegated", "user-provided", "none"}
# A delegated provenance URI: `<skill-name>:<capability>?mode=…&query=…#sha256=…`.
DELEGATED_TOKEN = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
DELEGATED_DIGEST = re.compile(r"sha256=[0-9a-f]{64}")
DELEGATED_MODES = {"retrieve", "generate"}
PLACEHOLDER_WORDS = {
    "choose",
    "missing",
    "n/a",
    "na",
    "pending",
    "placeholder",
    "tbd",
    "todo",
    "unknown",
    "unset",
}


class BriefFormatError(ValueError):
    """The Markdown brief cannot be parsed safely."""


class LegacyBriefRequired(BriefFormatError):
    """A pre-Creative-Brief project plan requires explicit migration."""


class StateFormatError(ValueError):
    """The state file cannot be parsed safely."""


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fingerprint(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def is_placeholder(value: str) -> bool:
    stripped = value.strip()
    lowered = stripped.lower()
    if not stripped:
        return False
    if "{" in stripped or "}" in stripped or re.search(r"<[^>]+>", stripped):
        return True
    if lowered in PLACEHOLDER_WORDS or lowered == "...":
        return True
    if any(lowered.startswith(f"{word}:") for word in PLACEHOLDER_WORDS):
        return True
    return bool(
        re.fullmatch(
            r"(?:choose|missing|n/?a|pending|placeholder|tbd|todo|unknown|unset)"
            r"[\s_-]+(?:choice|here|later|license|path|source|track|value)",
            lowered,
        )
    )


def is_track_field_placeholder(field: str, value: str) -> bool:
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    if normalized == "none" or is_placeholder(value):
        return True
    patterns = {
        "title": (
            r"(?:track|song|music)(?: (?:name|title))?"
            r"|(?:name|title)(?: (?:here|later))?"
            r"|example(?: (?:music|song|track))?"
        ),
        "path": (
            r"(?:file )?path(?: (?:here|later))?"
            r"|(?:/?path/)?to/(?:audio|file)(?:\.[a-z0-9]+)?"
            r"|/?path/to/(?:audio|file)(?:\.[a-z0-9]+)?"
        ),
        "source": (
            r"(?:track )?source(?: url)?"
            r"|url(?: (?:here|later))?"
            r"|https?://example\.com/?"
        ),
        "license": r"(?:track )?license(?: (?:here|later|name))?",
    }
    return bool(re.fullmatch(patterns[field], normalized))


def parse_brief(plan_path: Path) -> dict[str, str]:
    try:
        text = plan_path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise BriefFormatError(f"{PLAN_NAME} was not found at {plan_path}") from error
    except OSError as error:
        raise BriefFormatError(f"cannot read {plan_path}: {error}") from error

    lines = text.splitlines()
    heading_indexes = [
        index
        for index, line in enumerate(lines)
        if line.strip().lower() == "## creative brief"
    ]
    if not heading_indexes:
        raise LegacyBriefRequired(
            "legacy project-plan.md has no ## Creative Brief table; "
            "ask for migration consent, run migrate, then collect every "
            "user-owned choice in Phase 1"
        )
    if len(heading_indexes) > 1:
        raise BriefFormatError("duplicate heading: ## Creative Brief")
    heading_index = heading_indexes[0]

    index = heading_index + 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines) or lines[index].strip().lower() != "| field | value |":
        raise BriefFormatError(
            "Creative Brief must begin with the exact table header: | Field | Value |"
        )
    index += 1
    if index >= len(lines) or not re.fullmatch(
        r"\|\s*:?-{3,}:?\s*\|\s*:?-{3,}:?\s*\|",
        lines[index].strip(),
    ):
        raise BriefFormatError("Creative Brief table separator is malformed")

    values: dict[str, str] = {}
    index += 1
    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("## "):
            break
        index += 1
        if not line:
            if values:
                break
            continue
        if not line.startswith("|") or not line.endswith("|"):
            raise BriefFormatError(f"malformed Creative Brief row: {line}")
        cells = [cell.strip() for cell in line[1:-1].split("|")]
        if len(cells) != 2 or not cells[0]:
            raise BriefFormatError(f"malformed Creative Brief row: {line}")
        field, value = cells
        if field not in ALL_FIELDS:
            raise BriefFormatError(f"unknown Creative Brief field: {field}")
        if field in values:
            raise BriefFormatError(f"duplicate Creative Brief field: {field}")
        values[field] = value
    return values


def validate_story(values: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for field in STORY_FIELDS:
        if field not in values or not values[field].strip():
            errors.append(f"{field}: value is missing")
        elif is_placeholder(values[field]):
            errors.append(f"{field}: placeholder values are not allowed")
    if errors:
        return errors

    if values["mode"] not in {"promo", "showcase", "tutorial"}:
        errors.append("mode: expected promo, showcase, or tutorial")
    if values["product_surface"] not in {"ui", "none"}:
        errors.append("product_surface: expected ui or none")

    duration_match = re.fullmatch(r"(\d+(?:\.\d+)?)s", values["duration"])
    if duration_match is None or float(duration_match.group(1)) <= 0:
        errors.append("duration: expected a positive number followed by s (for example 60s)")
    normalized_aspect = values["aspect_ratio"].replace("\u00d7", "x")
    if normalized_aspect not in ASPECT_RATIOS:
        errors.append(
            "aspect_ratio: expected one of 16:9 1920x1080, 9:16 1080x1920, "
            "1:1 1080x1080, or 4:5 1080x1350"
        )
    if values["theme"] not in {"light", "dark"}:
        errors.append("theme: expected light or dark")

    strategy = values["identity_strategy"]
    choice = values["identity_choice"]
    if strategy not in {"design-system", "hyperframes-style", "screenshots", "custom"}:
        errors.append(
            "identity_strategy: expected design-system, hyperframes-style, screenshots, or custom"
        )
    elif strategy == "design-system" and choice not in DESIGN_SYSTEMS:
        errors.append(
            "identity_choice: expected a documented design-system slug for design-system"
        )
    elif (
        strategy == "design-system"
        and values["theme"] in {"light", "dark"}
        and values["theme"] not in DESIGN_SYSTEM_THEMES[choice]
    ):
        supported = " or ".join(sorted(DESIGN_SYSTEM_THEMES[choice]))
        errors.append(
            f"identity_choice: {choice} supports {supported} theme only; "
            "change theme or identity before confirmation"
        )
    elif strategy == "hyperframes-style" and choice not in HYPERFRAMES_STYLES:
        errors.append("identity_choice: expected a documented HyperFrames style name")
    elif strategy == "screenshots" and choice != "captured-screenshots":
        errors.append(
            "identity_choice: use captured-screenshots when identity_strategy is screenshots"
        )
    elif strategy == "custom" and choice.lower() == "none":
        errors.append("identity_choice: custom identity must name a real direction or source")

    # A ceiling on which runtimes the film may reach, never a request for one.
    # `flat` bars WebGL and canvas heroes; `derived` imposes no ceiling and
    # grants no permission — capability derivation still decides alone.
    if values["visual_ceiling"] not in VISUAL_CEILINGS:
        errors.append("visual_ceiling: expected derived or flat")

    voice = values["voice"]
    if not (
        re.fullmatch(r"elevenlabs:[^:]+:[A-Za-z0-9_-]+", voice)
        or re.fullmatch(r"kokoro:[a-z]{2}_[a-z0-9_-]+", voice)
    ):
        errors.append(
            "voice: expected elevenlabs:<name>:<voice-id> or kokoro:<voice-id>"
        )
    if values["transition_style"] not in TRANSITION_STYLES:
        errors.append(
            "transition_style: expected metallic-swoosh, zoom-through, crossfade, "
            "or slide-from-bottom"
        )
    if values["transition_speed"] not in {"quick", "medium", "slow"}:
        errors.append("transition_speed: expected quick, medium, or slow")
    if values["music_strategy"] not in MUSIC_STRATEGIES:
        errors.append(
            "music_strategy: expected freesound, delegated, user-provided, or none"
        )
    return errors


def delegated_source_is_valid(source: str) -> bool:
    """A delegated track's provenance URI.

    A bed another skill retrieved from a provider catalog or generated locally
    has no public page to cite and no durable download URL. What identifies it
    later is who produced it, by which route, from which request, and which
    bytes came out — so all four are required, in one line:

        <skill-name>:<capability>?mode=<retrieve|generate>&query=<request>#sha256=<64 hex>

    ``mode`` records the route actually taken (the two carry different
    licensing), never the route requested — ``auto`` is a request, not
    provenance. Either ``query`` or ``prompt`` carries the request text.
    Unknown parameters are tolerated: this pins provenance, it does not mirror
    another skill's request schema. The digest is of the file at ``path``, so
    the claim stays checkable offline for as long as the project exists.
    """
    try:
        parsed = urlparse(source)
    except ValueError:
        return False
    if parsed.scheme in {"http", "https", "file", "data"}:
        return False
    if not DELEGATED_TOKEN.fullmatch(parsed.scheme):
        return False
    if parsed.netloc or not DELEGATED_TOKEN.fullmatch(parsed.path):
        return False
    if not DELEGATED_DIGEST.fullmatch(parsed.fragment):
        return False
    try:
        query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        return False
    if query.get("mode", []) == [] or len(query["mode"]) != 1:
        return False
    if query["mode"][0] not in DELEGATED_MODES:
        return False
    requests = [
        value.strip()
        for key in ("query", "prompt")
        for value in query.get(key, [])
    ]
    return len(requests) == 1 and bool(requests[0])


def parse_final_track(
    values: dict[str, str],
) -> tuple[str | dict[str, str] | None, list[str]]:
    field = "final_music_track"
    if field not in values or not values[field].strip():
        return None, [f"{field}: value is missing"]
    raw = values[field].strip()
    if (
        raw.lower() in PLACEHOLDER_WORDS
        or re.fullmatch(r"<[^>]+>", raw)
        or (raw.startswith("{") and raw.endswith("}") and '"' not in raw)
    ):
        return None, [f"{field}: placeholder values are not allowed"]

    strategy = values.get("music_strategy")
    if raw == "none":
        if strategy != "none":
            return None, [
                "final_music_track: none is valid only when music_strategy is none"
            ]
        return "none", []
    if strategy == "none":
        return None, [
            "final_music_track: must be none when music_strategy is none"
        ]

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        return None, [
            "final_music_track: expected none or compact JSON with "
            f"title/path/source/license ({error.msg})"
        ]
    if not isinstance(parsed, dict):
        return None, ["final_music_track: JSON value must be an object"]
    required = {"title", "path", "source", "license"}
    actual = set(parsed)
    if actual != required:
        missing = sorted(required - actual)
        extra = sorted(actual - required)
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unknown " + ", ".join(extra))
        return None, ["final_music_track: " + "; ".join(details)]
    normalized: dict[str, str] = {}
    errors = []
    for key in sorted(required):
        value = parsed[key]
        if not isinstance(value, str) or not value.strip():
            errors.append(f"final_music_track.{key}: value is missing")
        elif is_track_field_placeholder(key, value):
            errors.append(
                f"final_music_track.{key}: placeholder values are not allowed"
            )
        else:
            normalized[key] = value.strip()
    if not errors and strategy == "freesound":
        try:
            source = urlparse(normalized["source"])
            source_hostname = source.hostname
        except ValueError:
            source = None
            source_hostname = None
        if source is None or (
            source.scheme not in {"http", "https"}
            or source_hostname not in {"freesound.org", "www.freesound.org"}
            or not re.fullmatch(
                r"(?:/s/\d+|/people/[^/]+/sounds/\d+)/?",
                source.path,
            )
        ):
            errors.append(
                "final_music_track.source: freesound strategy requires an exact "
                "freesound.org track URL containing its numeric sound ID"
            )
    elif not errors and strategy == "user-provided":
        if parsed["source"] != "user-provided":
            errors.append(
                "final_music_track.source: user-provided strategy requires "
                "the exact value user-provided"
            )
    elif not errors and strategy == "delegated":
        if not delegated_source_is_valid(normalized["source"]):
            errors.append(
                "final_music_track.source: delegated strategy requires a "
                "provenance URI <skill>:<capability>?mode=retrieve|generate"
                "&query=<request>#sha256=<64 hex digest of the file at path>"
            )
    return (normalized if not errors else None), errors


def story_value(values: dict[str, str]) -> dict[str, str]:
    result = {field: values[field].strip() for field in STORY_FIELDS}
    result["aspect_ratio"] = result["aspect_ratio"].replace("\u00d7", "x")
    return result


def default_state() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "story": None,
        "audio": None,
        "phases": {},
    }


def load_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return default_state()
    try:
        with state_path.open(encoding="utf-8") as handle:
            state = json.load(handle)
    except json.JSONDecodeError as error:
        raise StateFormatError(
            f"{STATE_RELATIVE_PATH} is malformed JSON; repair or move it, "
            "then rerun the command"
        ) from error
    except OSError as error:
        raise StateFormatError(f"cannot read {state_path}: {error}") from error

    if not isinstance(state, dict):
        raise StateFormatError(f"{STATE_RELATIVE_PATH} must contain a JSON object")
    if state.get("schema_version") != SCHEMA_VERSION:
        raise StateFormatError(
            f"{STATE_RELATIVE_PATH} has unsupported schema_version "
            f"{state.get('schema_version')!r}; expected {SCHEMA_VERSION}"
        )
    if state.get("story") is not None and not isinstance(state["story"], dict):
        raise StateFormatError(f"{STATE_RELATIVE_PATH} story must be an object or null")
    if state.get("audio") is not None and not isinstance(state["audio"], dict):
        raise StateFormatError(f"{STATE_RELATIVE_PATH} audio must be an object or null")
    if not isinstance(state.get("phases"), dict):
        raise StateFormatError(f"{STATE_RELATIVE_PATH} phases must be an object")

    def require_record(
        label: str,
        record: dict[str, Any],
        required: dict[str, type],
    ) -> None:
        for key, expected_type in required.items():
            invalid = key not in record
            if not invalid:
                value = record[key]
                # Present and of the declared type, and never a bool wearing an
                # int's clothes. Only then is the value comparable: the revision
                # check below is an ordering test, so it must not be reached by
                # a missing key or a value of some other type.
                invalid = not isinstance(value, expected_type) or isinstance(
                    value, bool
                )
                if not invalid and expected_type is str:
                    invalid = not value
                if not invalid and expected_type is int:
                    invalid = value < 1
            if invalid:
                raise StateFormatError(
                    f"{STATE_RELATIVE_PATH} {label}.{key} is invalid"
                )

    if state["story"] is not None:
        require_record(
            "story",
            state["story"],
            {"fingerprint": str, "revision": int, "confirmed_at": str},
        )
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", state["story"]["fingerprint"]):
            raise StateFormatError(
                f"{STATE_RELATIVE_PATH} story.fingerprint is invalid"
            )
    if state["audio"] is not None:
        require_record(
            "audio",
            state["audio"],
            {
                "fingerprint": str,
                "story_fingerprint": str,
                "story_revision": int,
                "revision": int,
                "confirmed_at": str,
            },
        )
        for key in ("fingerprint", "story_fingerprint"):
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", state["audio"][key]):
                raise StateFormatError(
                    f"{STATE_RELATIVE_PATH} audio.{key} is invalid"
                )
    for phase, stamp in state["phases"].items():
        if phase not in PHASES or not isinstance(stamp, dict):
            raise StateFormatError(
                f"{STATE_RELATIVE_PATH} contains an invalid phase stamp: {phase}"
            )
        require_record(
            f"phases.{phase}",
            stamp,
            {
                "stage": str,
                "fingerprint": str,
                "revision": int,
                "stamped_at": str,
            },
        )
        expected_stage = "audio" if phase == "phase-5" else "story"
        if stamp["stage"] != expected_stage:
            raise StateFormatError(
                f"{STATE_RELATIVE_PATH} phases.{phase}.stage must be {expected_stage}"
            )
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", stamp["fingerprint"]):
            raise StateFormatError(
                f"{STATE_RELATIVE_PATH} phases.{phase}.fingerprint is invalid"
            )
    return state


def write_text_atomic(
    path: Path,
    content: str,
    error_type: type[BriefFormatError] | type[StateFormatError],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / (
        f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    )
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    except OSError as error:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise error_type(f"cannot atomically write {path}: {error}") from error


def write_state_atomic(state_path: Path, state: dict[str, Any]) -> None:
    content = json.dumps(
        state,
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    ) + "\n"
    write_text_atomic(state_path, content, StateFormatError)


def placeholder_brief_table() -> str:
    rows = "\n".join(
        f"| {field} | {BRIEF_PLACEHOLDERS[field]} |" for field in ALL_FIELDS
    )
    return "\n".join(
        (
            "## Creative Brief",
            "",
            "| Field | Value |",
            "|---|---|",
            rows,
        )
    )


# --- Storyboard -------------------------------------------------------------
#
# The storyboard follows the official HyperFrames shape: YAML frontmatter, one
# `## Frame N — Title` section per frame, `- key: value` metadata bullets, free
# prose below them. Unknown bullets are preserved verbatim under a frame's
# ``extra`` — that is what carries this skill's director keys and capture
# bindings through the official format, so nothing here may drop a key it does
# not recognize.
#
# Two hard boundaries, both deliberate:
#
# * **Nothing here feeds a fingerprint.** The storyboard is a description of the
#   film, not a consent record; the Creative Brief remains the only fingerprinted
#   artifact. Mixing storyboard content into the story fingerprint would stale
#   every project that already exists.
# * **The parser is lenient**, mirroring the official one: it never raises on
#   surprising content, it records a warning. A storyboard in the older bespoke
#   shape parses too, so an in-flight project keeps resuming with no migration.

STORYBOARD_NAMES = ("storyboard.md", "STORYBOARD.md")
STORYBOARD_BACKUP_NAME = "storyboard.legacy.md"

OFFICIAL_GLOBAL_KEYS = ("format", "duration", "message", "arc", "audience")
FRAME_FIELDS = (
    "status",
    "src",
    "duration",
    "transition_in",
    "scene",
    "voiceover",
    "poster",
)
FRAME_FIELD_ALIASES = {
    "transition": "transition_in",
    "vo": "voiceover",
    "voice_over": "voiceover",
    "narration": "voiceover",
    "description": "scene",
    "summary": "scene",
    "caption": "scene",
}
FRAME_STATUSES = ("outline", "built", "animated")
DEFAULT_FRAME_STATUS = FRAME_STATUSES[0]

FRAME_HEADING = re.compile(
    r"^(#{2,3})[ \t]+(?:Frame|Beat|Scene)\b[ \t]*(\d+)?[ \t]*(?:[—–:-][ \t]*)?(.*)$",
    re.IGNORECASE,
)
METADATA_BULLET = re.compile(r"^[-*][ \t]+([A-Za-z][A-Za-z0-9_-]*)[ \t]*:[ \t]*(.*)$")
LEGACY_FIELD = re.compile(r"\*\*([^*:]+):\*\*")
ITALIC_NOTE = re.compile(r"\*\(([^)]*)\)\*\s*$")
HORIZONTAL_RULE = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})$")
LEGACY_MARKER = re.compile(
    r"^\*\*(?:Window|Scene file|Voiceover[^:]*|Transition to next):\*\*",
    re.MULTILINE,
)

# ── Prose that reads as metadata ────────────────────────────────────────────
#
# `- key: value` is how a frame states metadata in this format, so a prose line
# in the same shape is ambiguous: the identical bytes mean "metadata" to a
# reader and "prose" to the author, and the file cannot say which. This parser
# reads the metadata as the contiguous block under the heading, the rule
# `templates/storyboard.md` states — but a converted file is read by whoever
# opens it next, and nothing obliges another reader to stop looking for bullets
# where this one stops. Bullet preservation is the contract `compat/ecosystem.md`
# registers as `STORYBOARD_EXTRA_KEYS`, and it cuts both ways: the same
# mechanism that carries a director key would carry a line of prose.
#
# Serializing therefore escapes the list marker (`\- key: value`) and parsing
# unescapes it: the document model keeps the author's prose exactly, and the
# file on disk says "prose" to any reader. Escape rather than swap the marker —
# `+ key: value` also reads as prose today, but `+` is a valid list marker a
# reader may come to accept, while an escaped marker can never be one. The shape
# below is the union of the key shapes a reader may recognise, so it errs toward
# escaping a line nobody would have misread rather than leaving one somebody
# would.
BULLET_SHAPE = r"[-*][ \t]+[A-Za-z_][A-Za-z0-9_-]*[ \t]*:"
PROSE_BULLET = re.compile(rf"^([ \t]*)({BULLET_SHAPE})")
ESCAPED_PROSE_BULLET = re.compile(rf"^([ \t]*)\\({BULLET_SHAPE})")

NUMBER = re.compile(r"\d+(?:\.\d+)?")
CANVAS = re.compile(r"(\d+)\s*[×x]\s*(\d+)")
PARENTHETICAL = re.compile(r"\(([^)]*)\)\s*$")
RANGE_SPLIT = re.compile(r"\s*[–—-]\s*")

LEGACY_GLOBAL_MAP = {
    "duration": "duration",
    "canvas": "format",
    "renderer": "renderer",
    "mode": "content_mode",
    "theme": "theme",
    "product surface": "product_surface",
    "capture plan": "capture_plan",
    "web capture source": "web_capture_source",
    "emotional journey": "emotional_journey",
}
LEGACY_FRAME_MAP = {
    "scene file": "src",
    "screenshot": "screenshot",
    "capture": "capture",
    "capture duration": "capture_duration",
    "capture region": "capture_region",
    "command": "command",
    "record timeout": "record_timeout",
    "clip": "clip",
    "speed": "speed",
    "clip audio": "clip_audio",
    "captions": "captions",
    "chapter": "chapter",
    "step label": "step_label",
    # NOT `camera`: the legacy field is free prose ("slow motivated push-in on
    # the wrapper…") while the director key `camera` takes one literal from a
    # closed vocabulary. Folding the two would corrupt that vocabulary silently.
    "camera": "legacy_camera",
}
DIRECTOR_KEYS_LABEL = "director keys"


def snake_case(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.strip().lower()).strip("_")


def escape_prose_bullets(text: str) -> tuple[str, int]:
    """Make every metadata-shaped prose line unreadable as metadata.

    Line by line, fenced code included: a reader scanning for bullets does not
    know about fences either, so a `- key: value` line inside one is ambiguous
    in exactly the same way. The escape is visible in that one case, which is
    the lesser harm — the alternative is losing the line to metadata silently.
    """
    escaped: list[str] = []
    count = 0
    for line in text.split("\n"):
        replaced, hits = PROSE_BULLET.subn(r"\1\\\2", line, count=1)
        count += hits
        escaped.append(replaced)
    return "\n".join(escaped), count


def unescape_prose_bullets(text: str) -> str:
    """Undo :func:`escape_prose_bullets`, so the model holds the prose itself."""
    return "\n".join(
        ESCAPED_PROSE_BULLET.sub(r"\1\2", line, count=1) for line in text.split("\n")
    )


def written_lines(text: str) -> int:
    """Lines that carry something — what a reader counts, blanks excluded."""
    return len([line for line in text.splitlines() if line.strip()])


def document_text(lines: list[str]) -> str:
    """Text above the first frame: joined, edge-trimmed, otherwise untouched.

    No reader can mistake it for a frame's metadata — there is no frame open
    yet — so it is never escaped on the way out and never unescaped on the way
    in. Byte-for-byte is the whole contract.
    """
    return "\n".join(lines).strip()


def section_text(lines: list[str]) -> str:
    """Text below the last frame, which a reader may still read as part of it.

    A heading that opens no frame ends the frame *here*; a reader that scans a
    whole section for bullets keeps going. So this text is escaped on the way
    out, and restored on the way in.
    """
    return unescape_prose_bullets(document_text(lines))


def unquote_scalar(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in "\"'":
        return stripped[1:-1]
    return stripped


def duration_seconds(value: str | None) -> float | None:
    if not value:
        return None
    match = NUMBER.search(value)
    return float(match.group()) if match else None


def new_frame(number: int | None, title: str) -> dict[str, Any]:
    frame: dict[str, Any] = {field: None for field in FRAME_FIELDS}
    frame.update(
        {
            "index": 0,
            "number": number,
            "title": title.strip() or None,
            "narrative": "",
            "extra": {},
        }
    )
    return frame


def finish_frames(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    finished = []
    for index, frame in enumerate(frames, 1):
        frame["index"] = index
        frame["status"] = frame["status"] or DEFAULT_FRAME_STATUS
        frame["duration_seconds"] = duration_seconds(frame["duration"])
        frame["narrative"] = unescape_prose_bullets(frame["narrative"].strip())
        finished.append(frame)
    return finished


def warn(warnings: list[dict[str, Any]], message: str, line: int | None = None) -> None:
    warnings.append({"message": message, "line": line})


def split_globals(
    values: dict[str, str],
    warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {key: values.get(key) for key in OFFICIAL_GLOBAL_KEYS}
    result["extra"] = {
        key: value for key, value in values.items() if key not in OFFICIAL_GLOBAL_KEYS
    }
    if "mode" in result["extra"]:
        warn(
            warnings,
            "frontmatter `mode` is the ecosystem's interaction mode "
            "(collaborative/autonomous), a run-shape contract this skill does not "
            "adopt (ADR-001). Write the content mode as `content_mode` instead",
        )
    return result


def assign_frame_key(
    frame: dict[str, Any],
    key: str,
    value: str,
    line: int,
    warnings: list[dict[str, Any]],
) -> None:
    normalized = FRAME_FIELD_ALIASES.get(key.lower(), key.lower())
    if normalized in FRAME_FIELDS:
        if frame[normalized] is not None:
            warn(warnings, f"duplicate `{normalized}` bullet; the last one wins", line)
        frame[normalized] = value
        if normalized == "status" and value not in FRAME_STATUSES:
            warn(
                warnings,
                f"unknown status {value!r}; expected one of "
                + ", ".join(FRAME_STATUSES),
                line,
            )
        return
    if key in frame["extra"]:
        warn(warnings, f"duplicate `{key}` bullet; the last one wins", line)
    frame["extra"][key] = value


def parse_frontmatter(
    lines: list[str],
    warnings: list[dict[str, Any]],
) -> tuple[dict[str, str], int]:
    if not lines or lines[0].strip() != "---":
        return {}, 0
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() in {"---", "..."}:
            end = index
            break
    if end is None:
        warn(warnings, "frontmatter block is never closed by ---", 1)
        return {}, 0
    values: dict[str, str] = {}
    for index in range(1, end):
        raw = lines[index]
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        key, separator, value = raw.partition(":")
        if not separator or not key.strip():
            warn(
                warnings,
                f"frontmatter line is not `key: value`: {raw.strip()}",
                index + 1,
            )
            continue
        values[key.strip()] = unquote_scalar(value)
    return values, end + 1


def parse_official_storyboard(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    warnings: list[dict[str, Any]] = []
    frontmatter, start = parse_frontmatter(lines, warnings)

    frames: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    narrative: list[str] = []
    # Lines no frame owns: the document's own text. Before the first frame it is
    # the title and any film-level prose; after the last one it is whatever a
    # heading that opens no frame introduced. Neither belongs to a frame, and
    # neither may be dropped on the way through.
    preamble: list[str] = []
    trailing: list[str] = []
    in_metadata = False
    bullet_counts: list[int] = []

    def close() -> None:
        if current is not None:
            current["narrative"] = "\n".join(narrative)

    def unowned(line: str) -> None:
        (trailing if frames else preamble).append(line)

    for offset in range(start, len(lines)):
        line = lines[offset]
        if line.startswith("#"):
            close()
            heading = FRAME_HEADING.match(line.strip())
            if heading is None:
                current = None
                unowned(line)
                continue
            number = int(heading.group(2)) if heading.group(2) else None
            current = new_frame(number, heading.group(3))
            frames.append(current)
            bullet_counts.append(0)
            narrative = []
            in_metadata = True
            continue
        if current is None:
            unowned(line)
            continue
        if in_metadata:
            if not line.strip():
                continue
            bullet = METADATA_BULLET.match(line.strip())
            if bullet is not None:
                assign_frame_key(
                    current,
                    bullet.group(1),
                    bullet.group(2).strip(),
                    offset + 1,
                    warnings,
                )
                bullet_counts[-1] += 1
                continue
            in_metadata = False
        narrative.append(line)
    close()

    for position, count in enumerate(bullet_counts, 1):
        if count == 0:
            warn(
                warnings,
                f"frame {position} carries no metadata bullets; every "
                "`- key: value` bullet must sit directly under the heading, "
                "above the narrative",
            )
    return {
        "format": "official",
        "globals": split_globals(frontmatter, warnings),
        "preamble": document_text(preamble),
        "trailing": section_text(trailing),
        "frames": finish_frames(frames),
        "relocated": [],
        "not_carried": [],
        "warnings": warnings,
        # How many `- key: value` bullets were actually read. Shape detection
        # needs the raw count: `status` defaults to `outline`, so "this frame
        # has a field" is true even for a frame that carried nothing.
        "bullet_count": sum(bullet_counts),
    }


def clean_legacy_value(value: str) -> tuple[str, str | None]:
    """Strip markdown decoration from a legacy value, keeping what it said.

    De-formatting only: a trailing ``*(editorial note)*`` comes back as a
    separate note instead of being glued into a path, and a wholly backticked
    value is unwrapped. Neither changes what the author wrote.
    """
    note = None
    match = ITALIC_NOTE.search(value)
    if match is not None:
        note = match.group(1).strip() or None
        value = value[: match.start()].strip()
    if len(value) > 1 and value.startswith("`") and value.endswith("`"):
        if value.count("`") == 2:
            value = value[1:-1].strip()
    return value, note


def legacy_fields(stripped: str) -> list[tuple[str, str]] | None:
    """Split a legacy `**Label:** value` line, which may carry several fields.

    The film header packs them onto one line (``**Duration:** 53s |
    **Canvas:** 1920x1080 | **Renderer:** HyperFrames``), so reading only the
    first would swallow the rest into its value.
    """
    matches = list(LEGACY_FIELD.finditer(stripped))
    if not matches or matches[0].start() != 0:
        return None
    fields = []
    for position, match in enumerate(matches):
        end = (
            matches[position + 1].start()
            if position + 1 < len(matches)
            else len(stripped)
        )
        value = stripped[match.end() : end].strip().rstrip("|").strip()
        fields.append((match.group(1).strip(), value))
    return fields


def parse_legacy_storyboard(text: str) -> dict[str, Any]:
    """Read the pre-adoption shape and present it in the official structure.

    Mechanical only. A value the legacy file states is re-encoded; a value it
    never stated stays absent. Anything without an official home is carried
    verbatim as an extra key, prose no frame owns travels with the document,
    and whatever is left over is named in ``not_carried`` / ``relocated`` so the
    caller can report it. Nothing is invented, and nothing goes missing quietly.
    """
    lines = text.splitlines()
    warnings: list[dict[str, Any]] = []
    film: dict[str, str] = {}
    frames: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    narrative: list[str] = []
    preamble: list[str] = []
    trailing: list[str] = []
    quote_target: str | None = None
    lifting_bullets = False
    transitions: dict[int, str] = {}
    hoisted: list[str] = []
    separators = 0

    def close() -> None:
        if current is not None:
            current["narrative"] = "\n".join(narrative)

    def unowned(line: str) -> None:
        # The document's own text — the title, the film-level prose above the
        # first scene, anything a later non-scene heading introduced. No frame
        # owns it, so it travels with the document rather than being dropped.
        (trailing if frames else preamble).append(line)

    def replaced(key: str, previous: str, value: str) -> None:
        # The official shape states a key once, so a legacy label written twice
        # loses its earlier value here. Cheap to lose, expensive to notice: say
        # it rather than let a conversion quietly pick one.
        if previous != value:
            warn(
                warnings,
                f"`{key}` is stated more than once with different values; the "
                f"last one wins, so {previous!r} is not carried",
                offset + 1,
            )

    def record(target: dict[str, Any], key: str, value: str, note: str | None) -> None:
        if key in target:
            replaced(key, target[key], value)
        target[key] = value
        if note:
            target[f"{key}_note"] = note

    def record_frame(
        frame: dict[str, Any],
        key: str,
        value: str,
        note: str | None,
    ) -> None:
        if key in FRAME_FIELDS:
            if frame[key] is not None:
                replaced(key, frame[key], value)
            frame[key] = value
            if note:
                frame["extra"][f"{key}_note"] = note
            return
        record(frame["extra"], key, value, note)

    for offset, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            close()
            quote_target, lifting_bullets = None, False
            heading = FRAME_HEADING.match(stripped)
            if heading is None:
                current = None
                unowned(line)
                continue
            current = new_frame(len(frames) + 1, heading.group(3))
            if heading.group(2) is not None:
                current["extra"]["legacy_scene"] = heading.group(2)
            frames.append(current)
            narrative = []
            continue

        if quote_target is not None:
            if stripped.startswith(">"):
                spoken = unquote_scalar(stripped.lstrip("> ").strip())
                if current is not None and spoken:
                    existing = current[quote_target]
                    current[quote_target] = (
                        f"{existing} {spoken}".strip() if existing else spoken
                    )
                continue
            if stripped:
                quote_target = None

        if lifting_bullets and current is not None:
            bullet = METADATA_BULLET.match(stripped)
            if bullet is not None:
                # Verbatim: a bullet is already in the shape the official
                # parser reads, so its decoration is the author's — unwrapping
                # a backticked ``motion`` rule name here would rewrite a
                # citation the storyboard deliberately spelled that way.
                record_frame(current, bullet.group(1), bullet.group(2).strip(), None)
                continue
            if stripped:
                lifting_bullets = False

        fields = legacy_fields(stripped)
        if fields is None:
            if HORIZONTAL_RULE.fullmatch(stripped):
                # A scene separator: layout the converted file expresses with
                # headings instead. Counted so the migration can say it went.
                separators += 1
            elif current is not None:
                narrative.append(line)
            else:
                unowned(line)
            continue

        # A bold label with no value opens a prose block rather than stating a
        # field, so the line is prose. Decided per line, not per field: a line
        # carrying two such labels is still one line of prose.
        prose = False
        for label, raw_value in fields:
            base = label
            timing = None
            parenthetical = PARENTHETICAL.search(label)
            if parenthetical is not None:
                base = label[: parenthetical.start()].strip()
                timing = parenthetical.group(1).strip()
            key = base.lower()
            value, note = clean_legacy_value(raw_value)

            if current is None:
                if not value:
                    prose = True
                    continue
                if frames:
                    hoisted.append(label)
                if key == "canvas":
                    canvas = CANVAS.search(value)
                    record(
                        film,
                        "format",
                        f"{canvas.group(1)}x{canvas.group(2)}" if canvas else value,
                        note or (value if canvas and canvas.group(0) != value else None),
                    )
                    continue
                record(film, LEGACY_GLOBAL_MAP.get(key, snake_case(base)), value, note)
                continue

            if key == DIRECTOR_KEYS_LABEL:
                # The old template kept the director keys as `- key: value`
                # bullets under this label. They are the whole point of the
                # `extra` mechanism, so lift them into the frame's metadata
                # instead of leaving them stranded in prose.
                lifting_bullets = True
                if value:
                    current["extra"]["legacy_director_keys_note"] = value
                elif note:
                    current["extra"]["legacy_director_keys_note"] = note
                continue
            if key.startswith("voiceover"):
                if timing:
                    current["extra"]["legacy_voiceover_timing"] = timing
                if value:
                    current["voiceover"] = unquote_scalar(value)
                else:
                    quote_target = "voiceover"
                continue
            if not value:
                # `**Visual:**` / `**Animation (GSAP):**` open a prose block,
                # not a field. They belong to the narrative, verbatim.
                prose = True
                continue
            if key == "window":
                current["extra"]["window"] = value
                numbers = NUMBER.findall(value)
                explicit = PARENTHETICAL.search(value)
                if explicit is not None and NUMBER.fullmatch(
                    explicit.group(1).strip().rstrip("s")
                ):
                    current["duration"] = explicit.group(1).strip()
                elif len(numbers) >= 2:
                    current["duration"] = (
                        f"{round(float(numbers[1]) - float(numbers[0]), 3):g}s"
                    )
                else:
                    warn(
                        warnings,
                        f"window {value!r} states no readable duration; the "
                        "frame keeps no `duration` rather than a guessed one",
                        offset + 1,
                    )
                continue
            if key == "clip in/out":
                bounds = [part for part in RANGE_SPLIT.split(value) if part]
                if len(bounds) == 2:
                    current["extra"]["clip_in"] = bounds[0]
                    current["extra"]["clip_out"] = bounds[1]
                else:
                    current["extra"]["clip_in_out"] = value
                continue
            if key == "transition to next":
                transitions[len(frames) - 1] = value
                continue
            record_frame(
                current,
                LEGACY_FRAME_MAP.get(key, snake_case(base)),
                value,
                note,
            )

        if prose:
            if current is not None:
                narrative.append(line)
            else:
                unowned(line)
    close()

    for index, raw in transitions.items():
        target = index + 1
        if target >= len(frames):
            # A closing scene's "Transition to next" has no frame to land on.
            # Keep it where it was written rather than dropping it.
            frames[index]["extra"]["legacy_transition_out"] = raw
            continue
        frame = frames[target]
        lowered = raw.lower()
        style = next(
            (
                name
                for name in (*sorted(TRANSITION_STYLES), "cut", "none")
                if re.search(rf"\b{re.escape(name)}\b", lowered)
            ),
            None,
        )
        speed = next(
            (name for name in ("quick", "medium", "slow") if name in lowered),
            None,
        )
        if style is not None:
            frame["transition_in"] = style
        if speed is not None:
            frame["extra"]["transition_speed"] = speed
        frame["extra"]["legacy_transition"] = raw

    return {
        "format": "legacy",
        "globals": split_globals(film, warnings),
        "preamble": document_text(preamble),
        "trailing": section_text(trailing),
        "frames": finish_frames(frames),
        "relocated": (
            [
                "field(s) written after the last scene are recorded as "
                "film-level frontmatter: "
                + ", ".join(f"`{label}`" for label in dict.fromkeys(hoisted))
            ]
            if hoisted
            else []
        ),
        "not_carried": (
            # Counted, not interpreted: the legacy template used these to
            # separate scenes, but an author may have meant a thematic break
            # inside one. Either way the converted file expresses structure
            # with headings, so the line goes — and gets named for going.
            [f"{separators} horizontal rule(s) (`---`)"] if separators else []
        ),
        "warnings": warnings,
    }


def detect_storyboard_shape(text: str) -> str:
    document = parse_official_storyboard(text)
    has_frontmatter = text.lstrip("\ufeff").startswith("---")
    if has_frontmatter or document["bullet_count"]:
        return "official"
    if LEGACY_MARKER.search(text):
        return "legacy"
    return "official" if document["frames"] else "unknown"


def parse_storyboard(text: str) -> dict[str, Any]:
    shape = detect_storyboard_shape(text)
    if shape == "legacy":
        document = parse_legacy_storyboard(text)
        if LEGACY_MARKER.search(text) and document["frames"]:
            warn(
                document["warnings"],
                "read in the pre-adoption storyboard shape; nothing is gated on "
                "it. Convert with `migrate-storyboard` after the user agrees — "
                "the original is preserved as " + STORYBOARD_BACKUP_NAME,
            )
        return document
    document = parse_official_storyboard(text)
    if shape == "unknown":
        document["format"] = "unknown"
        warn(
            document["warnings"],
            "no frames found: the file has neither `## Frame N — Title` headings "
            "nor the older `### Scene N:` headings",
        )
    elif LEGACY_MARKER.search(text):
        warn(
            document["warnings"],
            "mixed shapes: this storyboard has official frames and pre-adoption "
            "`**Field:**` lines. The bold lines are read as narrative",
        )
    return document


def render_storyboard(
    document: dict[str, Any],
    notes: list[str] | None = None,
) -> str:
    """Serialize a parsed document back into the official shape.

    ``notes`` collects what the emitter had to adjust to keep the file
    unambiguous, so a caller that rewrites a user's storyboard can say so
    instead of reporting a clean pass it did not make.
    """
    escaped = 0

    def prose(text: str) -> str:
        nonlocal escaped
        rendered, count = escape_prose_bullets(text)
        escaped += count
        return rendered

    lines = ["---"]
    globals_ = document["globals"]
    for key in OFFICIAL_GLOBAL_KEYS:
        if globals_.get(key):
            lines.append(f"{key}: {globals_[key]}")
    for key, value in globals_.get("extra", {}).items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    # Film-level prose sits below the frontmatter — the format allows nothing
    # above it — and above the first frame, where no frame can claim it.
    if document.get("preamble"):
        lines += ["", document["preamble"]]
    for frame in document["frames"]:
        title = frame.get("title")
        heading = f"## Frame {frame['number'] or frame['index']}"
        lines += ["", f"{heading} — {title}" if title else heading, ""]
        for field in FRAME_FIELDS:
            if frame.get(field):
                lines.append(f"- {field}: {frame[field]}")
        for key, value in frame["extra"].items():
            lines.append(f"- {key}: {value}")
        if frame["narrative"]:
            lines += ["", prose(frame["narrative"])]
    if document.get("trailing"):
        lines += ["", prose(document["trailing"])]
    if notes is not None and escaped:
        notes.append(
            f"{escaped} prose line(s) written as `- key: value` carry an "
            "escaped list marker (`\\- key: value`) so the next read keeps "
            "them as prose; they render as text rather than as list items"
        )
    return "\n".join(lines).rstrip("\n") + "\n"


def find_storyboard(project_dir: Path) -> Path | None:
    for name in STORYBOARD_NAMES:
        candidate = project_dir / name
        if candidate.is_file():
            return candidate
    return None


def read_storyboard(project_dir: Path) -> tuple[Path, str]:
    path = find_storyboard(project_dir)
    if path is None:
        raise FileNotFoundError(
            "no storyboard.md in "
            f"{project_dir}; Phase 1 writes it from templates/storyboard.md"
        )
    try:
        return path, path.read_text(encoding="utf-8")
    except OSError as error:
        raise BriefFormatError(f"cannot read {path}: {error}") from error


def storyboard_payload(project_dir: Path, path: Path, text: str) -> dict[str, Any]:
    document = parse_storyboard(text)
    return {
        "complete": bool(document["frames"]),
        "storyboard": str(path),
        "format": document["format"],
        "migration_available": document["format"] == "legacy",
        "globals": document["globals"],
        "preamble": document["preamble"],
        "trailing": document["trailing"],
        "frames": document["frames"],
        "frame_count": len(document["frames"]),
        "warnings": document["warnings"],
        "errors": [],
    }


def current_status(
    project_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    values = parse_brief(project_dir / PLAN_NAME)
    story_errors = validate_story(values)
    track, track_errors = parse_final_track(values)
    errors = [*story_errors, *track_errors]

    state = load_state(project_dir / STATE_RELATIVE_PATH)
    story = None
    story_fingerprint = None
    if not story_errors:
        story = story_value(values)
        story_fingerprint = fingerprint(story)

    story_state = state["story"]
    story_confirmed = bool(
        story_fingerprint
        and story_state
        and story_state.get("fingerprint") == story_fingerprint
    )

    audio_fingerprint = None
    if story_fingerprint and track is not None:
        audio_fingerprint = fingerprint(
            {
                "story_fingerprint": story_fingerprint,
                "final_music_track": track,
            }
        )
    audio_state = state["audio"]
    audio_confirmed = bool(
        story_confirmed
        and audio_fingerprint
        and audio_state
        and audio_state.get("story_fingerprint") == story_fingerprint
        and audio_state.get("story_revision") == story_state.get("revision")
        and audio_state.get("fingerprint") == audio_fingerprint
    )

    phase_status: dict[str, dict[str, Any]] = {}
    stale_phases = []
    for phase in PHASES:
        stamp = state["phases"].get(phase)
        if phase == "phase-5":
            expected_stage = "audio"
            expected_fingerprint = audio_fingerprint if audio_confirmed else None
            expected_revision = (
                audio_state.get("revision") if audio_confirmed else None
            )
        else:
            expected_stage = "story"
            expected_fingerprint = story_fingerprint if story_confirmed else None
            expected_revision = (
                story_state.get("revision") if story_confirmed else None
            )
        fresh = bool(
            stamp
            and expected_fingerprint
            and expected_revision
            and stamp.get("stage") == expected_stage
            and stamp.get("fingerprint") == expected_fingerprint
            and stamp.get("revision") == expected_revision
        )
        phase_status[phase] = {
            "status": "fresh" if fresh else "stale",
            "stage": expected_stage,
            "stamped_fingerprint": stamp.get("fingerprint") if stamp else None,
            "expected_fingerprint": expected_fingerprint,
            "stamped_revision": stamp.get("revision") if stamp else None,
            "expected_revision": expected_revision,
        }
        if not fresh:
            stale_phases.append(phase)

    payload = {
        "complete": not errors,
        "project_dir": str(project_dir),
        "state_file": str(project_dir / STATE_RELATIVE_PATH),
        "errors": errors,
        "story": {
            "complete": not story_errors,
            "fingerprint": story_fingerprint,
            "confirmed": story_confirmed,
            "revision": story_state.get("revision", 0) if story_state else 0,
        },
        "audio": {
            "complete": track is not None and not track_errors,
            "fingerprint": audio_fingerprint,
            "confirmed": audio_confirmed,
            "revision": audio_state.get("revision", 0) if audio_state else 0,
        },
        "phases": phase_status,
        "stale_phases": stale_phases,
        "earliest_stale_phase": stale_phases[0] if stale_phases else None,
    }
    context = {
        "story_fingerprint": story_fingerprint or "",
        "audio_fingerprint": audio_fingerprint or "",
    }
    return payload, state, context


def emit(payload: dict[str, Any], as_json: bool, *, stream: Any = sys.stdout) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True), file=stream)
        return
    if "message" in payload:
        print(payload["message"], file=stream)
        return
    print(
        "Creative Brief: " + ("complete" if payload.get("complete") else "incomplete"),
        file=stream,
    )
    for error in payload.get("errors", []):
        print(f"- {error}", file=stream)
    if payload.get("earliest_stale_phase"):
        print(
            "Earliest stale phase: " + payload["earliest_stale_phase"],
            file=stream,
        )
    else:
        print("All phase stamps are fresh.", file=stream)


def error_payload(message: str) -> dict[str, Any]:
    return {
        "complete": False,
        "errors": [message],
        "message": message,
    }


def migration_required_payload(
    project_dir: Path,
    message: str,
) -> dict[str, Any]:
    return {
        "complete": False,
        "migration_required": True,
        "project_dir": str(project_dir),
        "state_file": str(project_dir / STATE_RELATIVE_PATH),
        "errors": [message],
        "story": {
            "complete": False,
            "fingerprint": None,
            "confirmed": False,
            "revision": 0,
        },
        "audio": {
            "complete": False,
            "fingerprint": None,
            "confirmed": False,
            "revision": 0,
        },
        "phases": {
            phase: {
                "status": "stale",
                "stage": "audio" if phase == "phase-5" else "story",
                "stamped_fingerprint": None,
                "expected_fingerprint": None,
                "stamped_revision": None,
                "expected_revision": None,
            }
            for phase in PHASES
        },
        "stale_phases": list(PHASES),
        "earliest_stale_phase": "phase-1",
        "message": message,
    }


def command_status(project_dir: Path, as_json: bool) -> int:
    try:
        payload, _, _ = current_status(project_dir)
    except LegacyBriefRequired as error:
        payload = migration_required_payload(project_dir, str(error))
        emit(payload, as_json, stream=sys.stdout if as_json else sys.stderr)
        return 1
    except (BriefFormatError, StateFormatError) as error:
        emit(error_payload(str(error)), as_json, stream=sys.stdout if as_json else sys.stderr)
        return 2
    emit(payload, as_json)
    return 0 if payload["complete"] else 1


def command_migrate(project_dir: Path, as_json: bool) -> int:
    plan_path = project_dir / PLAN_NAME
    try:
        text = plan_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        emit(
            error_payload(f"{PLAN_NAME} was not found at {plan_path}"),
            as_json,
            stream=sys.stdout if as_json else sys.stderr,
        )
        return 2
    except OSError as error:
        emit(
            error_payload(f"cannot read {plan_path}: {error}"),
            as_json,
            stream=sys.stdout if as_json else sys.stderr,
        )
        return 2

    headings = [
        line
        for line in text.splitlines()
        if line.strip().lower() == "## creative brief"
    ]
    if headings:
        emit(
            error_payload(
                f"{PLAN_NAME} already contains a ## Creative Brief heading; "
                "run status instead of migrate"
            ),
            as_json,
            stream=sys.stdout if as_json else sys.stderr,
        )
        return 2

    first_line_end = text.find("\n")
    table = placeholder_brief_table()
    if text.startswith("# ") and first_line_end >= 0:
        insertion = first_line_end + 1
        migrated = text[:insertion] + "\n" + table + "\n\n" + text[insertion:]
    elif text.startswith("# "):
        migrated = text + "\n\n" + table + "\n"
    else:
        migrated = table + "\n\n" + text

    try:
        write_text_atomic(plan_path, migrated, BriefFormatError)
    except BriefFormatError as error:
        emit(error_payload(str(error)), as_json, stream=sys.stdout if as_json else sys.stderr)
        return 2

    payload = {
        "complete": True,
        "migration_required": False,
        "project_plan": str(plan_path),
        "message": (
            "Inserted an empty Creative Brief table without inferring legacy "
            "values. Collect and confirm every user-owned choice in Phase 1."
        ),
    }
    emit(payload, as_json)
    return 0


def command_storyboard(project_dir: Path, as_json: bool) -> int:
    try:
        path, text = read_storyboard(project_dir)
    except FileNotFoundError as error:
        emit(
            error_payload(str(error)),
            as_json,
            stream=sys.stdout if as_json else sys.stderr,
        )
        return 1
    except BriefFormatError as error:
        emit(
            error_payload(str(error)),
            as_json,
            stream=sys.stdout if as_json else sys.stderr,
        )
        return 2

    payload = storyboard_payload(project_dir, path, text)
    summary = [
        f"Storyboard: {payload['format']} shape, "
        f"{payload['frame_count']} frame(s) at {payload['storyboard']}."
    ]
    if payload["migration_available"]:
        summary.append(
            "Pre-adoption shape — it resumes as-is. Ask the user before running "
            "migrate-storyboard."
        )
    summary += [f"- warning: {item['message']}" for item in payload["warnings"]]
    payload["message"] = "\n".join(summary)
    emit(payload, as_json, stream=sys.stdout if payload["complete"] or as_json else sys.stderr)
    return 0 if payload["complete"] else 1


def command_migrate_storyboard(project_dir: Path, as_json: bool) -> int:
    """Convert a pre-adoption storyboard, additively and only when asked.

    The same posture as ``migrate``: the script is the mechanism, the workflow
    owns the consent prompt. Nothing is inferred, and the user's original file
    is never deleted — it is copied to ``storyboard.legacy.md`` *before* the
    converted file is written, and an existing backup stops the command rather
    than being overwritten.

    What the conversion could not carry through untouched it *names*: the report
    separates what was carried verbatim from what was adjusted, relocated, or
    left behind. A rewrite the user consented to still owes them an accurate
    account of it — a conversion that loses content while reporting a clean pass
    leaves them with no signal at all.
    """
    def fail(message: str) -> int:
        emit(
            error_payload(message),
            as_json,
            stream=sys.stdout if as_json else sys.stderr,
        )
        return 2

    try:
        path, text = read_storyboard(project_dir)
    except FileNotFoundError as error:
        return fail(str(error))
    except BriefFormatError as error:
        return fail(str(error))

    shape = detect_storyboard_shape(text)
    if shape != "legacy":
        return fail(
            f"{path.name} is not in the pre-adoption shape (detected: {shape}); "
            "run storyboard instead of migrate-storyboard"
        )
    document = parse_legacy_storyboard(text)
    if not document["frames"]:
        return fail(f"{path.name} contains no scenes to convert")

    backup = path.parent / STORYBOARD_BACKUP_NAME
    if backup.exists():
        return fail(
            f"{STORYBOARD_BACKUP_NAME} already exists; move it aside first — "
            "this command never overwrites a storyboard it did not write"
        )

    # What the conversion had to do beyond re-encoding a field, and what it
    # could not carry at all. Collected before anything is written: a report
    # that claims more than the conversion delivered leaves the user with no
    # signal at exactly the moment they have to trust it.
    adjusted: list[str] = []
    converted = render_storyboard(document, adjusted)
    if document["preamble"]:
        adjusted.append(
            f"{written_lines(document['preamble'])} line(s) of film-level prose "
            "(the document title and anything above the first scene) now sit "
            "below the frontmatter, which the format requires to come first"
        )
    if document["trailing"]:
        adjusted.append(
            f"{written_lines(document['trailing'])} line(s) written under a "
            "heading that opens no scene are kept after the last frame"
        )
    # One note per distinct fact: several fields written after the last scene
    # land in the same place for the same reason, and a report that says it
    # three times is padding, not detail.
    adjusted = list(dict.fromkeys([*adjusted, *document["relocated"]]))
    not_carried = list(dict.fromkeys(document["not_carried"]))

    try:
        write_text_atomic(backup, text, BriefFormatError)
        write_text_atomic(path, converted, BriefFormatError)
    except BriefFormatError as error:
        return fail(str(error))

    carried = sorted(
        {key for frame in document["frames"] for key in frame["extra"]}
        | set(document["globals"]["extra"])
    )
    summary = [
        f"Converted {len(document['frames'])} scene(s) to the official "
        f"storyboard shape. The original is preserved at {backup}. No user-owned "
        "value was inferred: a value the legacy file stated was re-encoded, a "
        "value it never stated stays absent, and anything without an official "
        "home rides as an extra bullet. The one value the migration supplies is "
        "each frame's `status`, which the legacy shape has no field for and "
        "which records build progress, not a user choice."
    ]
    if adjusted:
        summary.append("Carried with an adjustment:")
        summary += [f"- {note}" for note in adjusted]
    if not_carried:
        summary.append("Not carried:")
        summary += [f"- {item}" for item in not_carried]
    if not adjusted and not not_carried:
        summary.append("Nothing needed adjusting and nothing was left behind.")
    summary += [f"- warning: {item['message']}" for item in document["warnings"]]
    payload = {
        "complete": True,
        "migration_required": False,
        "storyboard": str(path),
        "backup": str(backup),
        "format": "official",
        "frame_count": len(document["frames"]),
        "carried_keys": carried,
        "adjusted": adjusted,
        "not_carried": not_carried,
        "warnings": document["warnings"],
        "message": "\n".join(summary),
    }
    emit(payload, as_json)
    return 0


def command_confirm_story(project_dir: Path, as_json: bool) -> int:
    try:
        values = parse_brief(project_dir / PLAN_NAME)
        errors = validate_story(values)
        if errors:
            payload = {
                "complete": False,
                "errors": errors,
                "message": "Story brief is incomplete: " + "; ".join(errors),
            }
            emit(payload, as_json, stream=sys.stdout if as_json else sys.stderr)
            return 1
        current_story_fingerprint = fingerprint(story_value(values))
        state_path = project_dir / STATE_RELATIVE_PATH
        state = load_state(state_path)
        prior = state["story"]
        changed = not prior or prior.get("fingerprint") != current_story_fingerprint
        revision = (
            int(prior.get("revision", 0)) + 1
            if changed and prior
            else (1 if changed else int(prior["revision"]))
        )
        confirmed_at = now_utc() if changed else prior["confirmed_at"]
        state["story"] = {
            "fingerprint": current_story_fingerprint,
            "revision": revision,
            "confirmed_at": confirmed_at,
        }
        write_state_atomic(state_path, state)
    except (BriefFormatError, StateFormatError) as error:
        emit(error_payload(str(error)), as_json, stream=sys.stdout if as_json else sys.stderr)
        return 2

    payload = {
        "complete": True,
        "changed": changed,
        "story_fingerprint": current_story_fingerprint,
        "story_revision": revision,
        "stale_phases": list(PHASES) if changed else [],
        "message": (
            f"Story brief confirmed at revision {revision}. "
            + (
                "Phase 1 through Phase 5 stamps are stale until rerun."
                if changed
                else "The confirmed story fingerprint is unchanged."
            )
        ),
    }
    emit(payload, as_json)
    return 0


def command_confirm_audio(project_dir: Path, as_json: bool) -> int:
    try:
        values = parse_brief(project_dir / PLAN_NAME)
        story_errors = validate_story(values)
        track, track_errors = parse_final_track(values)
        errors = [*story_errors, *track_errors]
        if errors:
            payload = {
                "complete": False,
                "errors": errors,
                "message": "Audio brief is incomplete: " + "; ".join(errors),
            }
            emit(payload, as_json, stream=sys.stdout if as_json else sys.stderr)
            return 1

        current_story_fingerprint = fingerprint(story_value(values))
        state_path = project_dir / STATE_RELATIVE_PATH
        state = load_state(state_path)
        story_state = state["story"]
        if not story_state or story_state.get("fingerprint") != current_story_fingerprint:
            payload = error_payload(
                "story brief is not confirmed at the current fingerprint; "
                "run confirm-story first"
            )
            emit(payload, as_json, stream=sys.stdout if as_json else sys.stderr)
            return 1

        current_audio_fingerprint = fingerprint(
            {
                "story_fingerprint": current_story_fingerprint,
                "final_music_track": track,
            }
        )
        prior = state["audio"]
        changed = bool(
            not prior
            or prior.get("fingerprint") != current_audio_fingerprint
            or prior.get("story_revision") != story_state["revision"]
        )
        revision = (
            int(prior.get("revision", 0)) + 1
            if changed and prior
            else (1 if changed else int(prior["revision"]))
        )
        confirmed_at = now_utc() if changed else prior["confirmed_at"]
        state["audio"] = {
            "fingerprint": current_audio_fingerprint,
            "story_fingerprint": current_story_fingerprint,
            "story_revision": story_state["revision"],
            "revision": revision,
            "confirmed_at": confirmed_at,
        }
        write_state_atomic(state_path, state)
    except (BriefFormatError, StateFormatError) as error:
        emit(error_payload(str(error)), as_json, stream=sys.stdout if as_json else sys.stderr)
        return 2

    payload = {
        "complete": True,
        "changed": changed,
        "audio_fingerprint": current_audio_fingerprint,
        "audio_revision": revision,
        "stale_phases": ["phase-5"] if changed else [],
        "message": (
            f"Exact music choice confirmed at audio revision {revision}. "
            + (
                "Phase 5 is stale until rerun."
                if changed
                else "The confirmed audio fingerprint is unchanged."
            )
        ),
    }
    emit(payload, as_json)
    return 0


def command_require(project_dir: Path, target: str, as_json: bool) -> int:
    try:
        payload, _, _ = current_status(project_dir)
    except (BriefFormatError, StateFormatError) as error:
        emit(error_payload(str(error)), as_json, stream=sys.stdout if as_json else sys.stderr)
        return 2

    if target == "story":
        fresh = payload["story"]["confirmed"]
        message = (
            "Story brief confirmation is current."
            if fresh
            else "story brief is not confirmed at the current fingerprint"
        )
    elif target == "audio":
        fresh = payload["audio"]["confirmed"]
        message = (
            "Exact music choice confirmation is current."
            if fresh
            else "exact music choice is not confirmed at the current fingerprint"
        )
    else:
        fresh = payload["phases"][target]["status"] == "fresh"
        message = f"{target} is fresh" if fresh else f"{target} is stale"

    result = {
        "complete": fresh,
        "target": target,
        "fresh": fresh,
        "message": message,
    }
    emit(result, as_json, stream=sys.stdout if fresh or as_json else sys.stderr)
    return 0 if fresh else 1


def command_stamp(project_dir: Path, phase: str, as_json: bool) -> int:
    try:
        payload, state, context = current_status(project_dir)
        if not payload["story"]["confirmed"]:
            message = (
                "story brief is not confirmed at the current fingerprint; "
                "run confirm-story first"
            )
            emit(
                error_payload(message),
                as_json,
                stream=sys.stdout if as_json else sys.stderr,
            )
            return 1

        phase_number = int(phase.split("-")[1])
        if phase_number > 1:
            previous = f"phase-{phase_number - 1}"
            if payload["phases"][previous]["status"] != "fresh":
                message = f"{previous} must be fresh before stamping {phase}"
                emit(
                    error_payload(message),
                    as_json,
                    stream=sys.stdout if as_json else sys.stderr,
                )
                return 1

        if phase == "phase-5":
            if not payload["audio"]["confirmed"]:
                message = (
                    "exact music choice is not confirmed at the current fingerprint; "
                    "run confirm-audio first"
                )
                emit(
                    error_payload(message),
                    as_json,
                    stream=sys.stdout if as_json else sys.stderr,
                )
                return 1
            stage = "audio"
            current_fingerprint = context["audio_fingerprint"]
            revision = payload["audio"]["revision"]
        else:
            stage = "story"
            current_fingerprint = context["story_fingerprint"]
            revision = payload["story"]["revision"]

        state["phases"][phase] = {
            "stage": stage,
            "fingerprint": current_fingerprint,
            "revision": revision,
            "stamped_at": now_utc(),
        }
        write_state_atomic(project_dir / STATE_RELATIVE_PATH, state)
    except (BriefFormatError, StateFormatError) as error:
        emit(error_payload(str(error)), as_json, stream=sys.stdout if as_json else sys.stderr)
        return 2

    result = {
        "complete": True,
        "phase": phase,
        "fingerprint": current_fingerprint,
        "message": f"Stamped {phase} at the current {stage} fingerprint.",
    }
    emit(result, as_json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and fingerprint an hve-video-director Creative Brief."
    )
    parser.add_argument(
        "--project-dir",
        required=True,
        type=Path,
        help="Generated video project containing project-plan.md.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Validate the brief and report freshness.")
    status.add_argument("--json", action="store_true", help="Emit one JSON object.")

    migrate = subparsers.add_parser(
        "migrate",
        help=(
            "Insert an empty Creative Brief table into a legacy plan after "
            "the user consents; no legacy value is inferred."
        ),
    )
    migrate.add_argument("--json", action="store_true", help="Emit one JSON object.")

    storyboard = subparsers.add_parser(
        "storyboard",
        help=(
            "Parse storyboard.md in the official shape (the pre-adoption shape "
            "is read too) and report its frames."
        ),
    )
    storyboard.add_argument("--json", action="store_true", help="Emit one JSON object.")

    migrate_storyboard = subparsers.add_parser(
        "migrate-storyboard",
        help=(
            "Convert a pre-adoption storyboard to the official shape after the "
            "user consents; the original is preserved alongside it."
        ),
    )
    migrate_storyboard.add_argument(
        "--json", action="store_true", help="Emit one JSON object."
    )

    confirm_story = subparsers.add_parser(
        "confirm-story",
        help="Confirm the current story fields and invalidate downstream stamps on change.",
    )
    confirm_story.add_argument("--json", action="store_true", help="Emit one JSON object.")

    confirm_audio = subparsers.add_parser(
        "confirm-audio",
        help="Confirm the exact final music choice for the current story fingerprint.",
    )
    confirm_audio.add_argument("--json", action="store_true", help="Emit one JSON object.")

    stamp = subparsers.add_parser("stamp", help="Stamp a completed phase as fresh.")
    stamp.add_argument("phase", choices=PHASES)
    stamp.add_argument("--json", action="store_true", help="Emit one JSON object.")

    require = subparsers.add_parser(
        "require",
        help="Require a current confirmation or fresh completed phase.",
    )
    require.add_argument("target", choices=("story", "audio", *PHASES))
    require.add_argument("--json", action="store_true", help="Emit one JSON object.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_dir = args.project_dir.expanduser().resolve()
    if args.command == "status":
        return command_status(project_dir, args.json)
    if args.command == "migrate":
        return command_migrate(project_dir, args.json)
    if args.command == "storyboard":
        return command_storyboard(project_dir, args.json)
    if args.command == "migrate-storyboard":
        return command_migrate_storyboard(project_dir, args.json)
    if args.command == "confirm-story":
        return command_confirm_story(project_dir, args.json)
    if args.command == "confirm-audio":
        return command_confirm_audio(project_dir, args.json)
    if args.command == "stamp":
        return command_stamp(project_dir, args.phase, args.json)
    if args.command == "require":
        return command_require(project_dir, args.target, args.json)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
