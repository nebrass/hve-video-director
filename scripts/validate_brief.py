#!/usr/bin/env python3
"""Validate and fingerprint an hve-spielberg creative brief.

The generated project's ``project-plan.md`` must contain the exact two-column
``## Creative Brief`` table documented in ``templates/project-plan.md``.
Confirmation state is stored atomically in ``.hve/brief-state.json``.

Examples:
    python3 validate_brief.py --project-dir ./my-video status --json
    python3 validate_brief.py --project-dir ./my-video migrate
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
from urllib.parse import urlparse


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
    "voice": "{elevenlabs:<name>:<voice-id> or kokoro:<voice-id>}",
    "transition_style": (
        "{metallic-swoosh, zoom-through, crossfade, or slide-from-bottom}"
    ),
    "transition_speed": "{quick, medium, or slow}",
    "music_strategy": "{freesound, user-provided, or none}",
    "final_music_track": (
        "{none or compact JSON with title, path, source, and license}"
    ),
}
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
    if values["music_strategy"] not in {"freesound", "user-provided", "none"}:
        errors.append("music_strategy: expected freesound, user-provided, or none")
    return errors


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
            value = record.get(key)
            if (
                not isinstance(value, expected_type)
                or isinstance(value, bool)
                or (expected_type is str and not value)
                or (expected_type is int and value < 1)
            ):
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
        description="Validate and fingerprint an hve-spielberg Creative Brief."
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
