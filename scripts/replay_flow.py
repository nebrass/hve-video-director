#!/usr/bin/env python3
"""
hve-video-director — Recorded browse-flow planner / cutter / verifier

A user records a browsing session with the Chrome/Edge DevTools Recorder and
drops the JSON export (Puppeteer Replay user-flow schema) into the project's
`recordings/`. The agent replays it through the browser tooling while filming
one continuous master screencast take and writing a step→timecode ledger.
This helper owns everything around that take that must be mechanical rather
than judged (ADR-011):

    plan   read the recording; validate what this pipeline consumes; warn on
           secret-like values; list the origins the flow touches; emit the
           humanized pacing schedule and a sanitized step brief for the
           whole-flow consent. Side-effect-free.
    arm    write `<clip>.replay.pending` for every clip frame bound to the
           recording, so an interrupted take is *incomplete*, never silently
           absent (ADR-009's freshness family). Prior valid clips untouched.
    cut    cut per-frame clips from the master take via the canonical
           stitcher's `path::START::DURATION` segments, then publish each
           atomically with a fingerprinted `<clip>.replay.json` sidecar
           carrying the clip-local pointer track. A failed cut leaves the
           previous clip byte-identical and the pending marker in place.
    check  the resume predicate: pending absent, sidecar present and matching
           the request, clip bytes matching the sidecar fingerprint, and the
           recording hash unchanged — a re-recorded flow stales every clip
           cut from it.

The recording is consumed verbatim: unknown JSON keys are ignored (a plain
Chrome export and an extension-enriched one both replay), and the optional
per-step `hve` namespace (`t`, `dwellAfterMs`, `note`, `marker`) is the only
enrichment this file reads. Recordings are plaintext — a recorded login puts
the password in a `change` step's value — so `plan` flags secret-like values
and the step brief never prints a typed value.

Pure Python standard library. `ffmpeg`/`ffprobe` are invoked with argv (the
same dependency Phase 5 already needs) and only by `cut`; `plan`, `arm` and
`check` run without them. Copied into generated projects beside
`stitch_clip.py` and `capture_screen.py`; it learns nothing about the
storyboard beyond the replay bullets it consumes.

Usage (from inside a generated project):
    python3 scripts/replay_flow.py plan --recording recordings/drill.json \\
        --storyboard storyboard.md --json
    python3 scripts/replay_flow.py arm --recording recordings/drill.json \\
        --storyboard storyboard.md
    python3 scripts/replay_flow.py cut --recording recordings/drill.json \\
        --raw public/clips/.drill.replay-raw.mp4 \\
        --ledger .hve/replay/drill.json --storyboard storyboard.md \\
        --canvas 1920x1080
    python3 scripts/replay_flow.py check --recording recordings/drill.json \\
        --steps 4-9 -o public/clips/scene-02-drill.mp4
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

SCHEMA_VERSION = 1

# ── Human pacing profile ────────────────────────────────────────────────────
#
# These numbers ARE the feel of the replay: they are the difference between a
# demo that reads as a person driving and a script teleporting through state.
# This block is the single owner of every pacing number (the stitch_clip GOP
# precedent): `patterns/recorded-flow-capture.md` states the law in prose and
# names this file as the authority; nothing else may restate a value.
# `test_replay_flow.py` holds the emitted schedule to these bounds.
#
# (lo, hi) pairs are milliseconds. The schedule emitted by `plan` picks a
# deterministic value inside each range (varied per step, reproducible per
# recording) — the agent may stretch toward `hi` for long pointer travel and
# shave toward `lo` for nearby targets, but never outside the range.
POINTER_TRAVEL_MS = (500, 900)      # eased travel to the target before a click
HOVER_SETTLE_MS = 150               # rest on the target before pressing
READ_DWELL_MS = (600, 1200)         # absorb the result after an action
NAV_DWELL_MS = (1500, 2500)         # orientation after a page navigation
TYPE_CHUNK_CHARS = (3, 6)           # characters typed per burst
TYPE_CHUNK_PAUSE_MS = (80, 200)     # pause between typing bursts
SCROLL_MS = (700, 1200)             # duration of one eased scroll
POINTER_EASING = "cubic-in-out"     # easing family for travel + scroll
HVE_T_CLAMP_MS = (120, 8000)        # recorded `hve.t` deltas clamp into this
# ── end pacing profile ──────────────────────────────────────────────────────

# Cut boundaries: both pads are deliberately smaller than the guaranteed dwell
# floors above, so a cut always lands on dwell footage, never mid-action.
LEAD_PAD_S = 0.4
TAIL_PAD_S = 0.8
# Ledger-vs-master drift: proceed inside the soft bound, apply a uniform
# end-anchored offset (with a warning) up to the hard bound, refuse beyond it.
DRIFT_SOFT_S = 1.0
DRIFT_SOFT_FRACTION = 0.05
DRIFT_HARD_S = 3.0

# Step types this pipeline consumes. The recorder may export more; `plan`
# reports anything outside this table so the user learns *before* consent
# rather than mid-take. `close` is ignored by design (the take ends instead);
# `emulateNetworkConditions` is ignored with a warning (capture wants the
# real network).
HANDLED_STEP_TYPES = (
    "setViewport",
    "navigate",
    "click",
    "doubleClick",
    "change",
    "keyDown",
    "keyUp",
    "hover",
    "scroll",
    "waitForElement",
    "waitForExpression",
)
IGNORED_STEP_TYPES = ("close", "emulateNetworkConditions")

# Bullet spellings mirror `templates/storyboard.md` § Capture and clip keys.
# The regexes mirror validate_brief.py's lenient official-shape reader; this
# copy exists because this file is copied into projects and must stand alone.
FRAME_HEADING = re.compile(
    r"^(#{2,3})[ \t]+(?:Frame|Beat|Scene)\b[ \t]*(\d+)?[ \t]*(?:[—–:-][ \t]*)?(.*)$",
    re.IGNORECASE,
)
METADATA_BULLET = re.compile(r"^[-*][ \t]+([A-Za-z][A-Za-z0-9_-]*)[ \t]*:[ \t]*(.*)$")

SECRET_SELECTOR = re.compile(r"(?i)password|passcode|api[_-]?key|secret|token|otp|mfa")
SECRET_VALUE_PATTERNS = (
    re.compile(r"^eyJ[A-Za-z0-9_-]{10,}"),          # JWT-shaped
    re.compile(r"^(?:sk|pk|ghp|gho|xox[a-z])[-_][A-Za-z0-9]{12,}"),  # API-key-shaped
    re.compile(r"^AKIA[0-9A-Z]{16}$"),               # AWS access key id
)


class ReplayError(Exception):
    """Raised for every refused operation; main() prints it and exits 1."""


# ── small shared helpers ────────────────────────────────────────────────────

def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path, what):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise ReplayError(f"{what} not found: {path}")
    except json.JSONDecodeError as exc:
        raise ReplayError(f"{what} is not valid JSON ({path}): {exc}")


def _write_json_atomic(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp, path)


def _norm(path_text):
    """Display/storage form: forward slashes, no leading `./`."""
    text = str(Path(path_text)).replace("\\", "/")
    return text[2:] if text.startswith("./") else text


def _same_file(a, b, base=None):
    """Path equality across relative/absolute spellings.

    Storyboard-bound paths are project-relative; `base` (the storyboard's
    directory) anchors them. Everything else resolves against the cwd, which
    the workflow guarantees is the project root.
    """
    first = Path(a)
    if base is not None and not first.is_absolute():
        first = Path(base) / first
    second = Path(b)
    return first.resolve() == second.resolve()


def pending_path_for(output):
    return Path(f"{output}.replay.pending")


def sidecar_path_for(output):
    return Path(f"{output}.replay.json")


def parse_steps_range(text, step_count):
    """`A-B` (1-based, inclusive) or `A`; None/empty means the whole flow."""
    if text is None or str(text).strip() == "":
        return (1, step_count)
    raw = str(text).strip()
    match = re.fullmatch(r"(\d+)(?:\s*-\s*(\d+))?", raw)
    if not match:
        raise ReplayError(
            f"recording_steps must be `A-B` or `A` (1-based, inclusive); got: {raw!r}")
    first = int(match.group(1))
    last = int(match.group(2)) if match.group(2) else first
    if first < 1 or last < first:
        raise ReplayError(f"recording_steps range is not ascending from 1: {raw!r}")
    if last > step_count:
        raise ReplayError(
            f"recording_steps {raw!r} exceeds the recording's {step_count} step(s)")
    return (first, last)


# ── recording ───────────────────────────────────────────────────────────────

def load_recording(path):
    payload = _read_json(path, "Recording")
    if not isinstance(payload, dict) or not isinstance(payload.get("steps"), list):
        raise ReplayError(
            f"Recording has no `steps` list ({path}); expected a DevTools "
            "Recorder JSON export.")
    steps = payload["steps"]
    if not steps:
        raise ReplayError(f"Recording has zero steps: {path}")
    for i, step in enumerate(steps, start=1):
        if not isinstance(step, dict) or not isinstance(step.get("type"), str):
            raise ReplayError(f"Recording step {i} has no string `type` ({path})")
    return payload


def _sanitized_url(url):
    """scheme://host/path only — query and fragment may carry bearer tokens."""
    try:
        parts = urlsplit(url)
    except ValueError:
        return "«unparseable URL»"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _origin(url):
    try:
        parts = urlsplit(url)
    except ValueError:
        return None
    if not parts.scheme or not parts.netloc:
        return None
    return f"{parts.scheme}://{parts.netloc}"


def _selector_text(step):
    selectors = step.get("selectors")
    if not isinstance(selectors, list):
        return ""
    flat = []
    for group in selectors:
        if isinstance(group, list):
            flat.extend(str(s) for s in group)
        else:
            flat.append(str(group))
    return " ".join(flat)


def _describe_target(step):
    for group in step.get("selectors", []) or []:
        candidates = group if isinstance(group, list) else [group]
        for selector in candidates:
            selector = str(selector)
            if selector.startswith("aria/"):
                return selector[len("aria/"):]
    text = _selector_text(step)
    return text[:80] if text else "«no selector»"


def _secret_findings(index, step):
    findings = []
    if step.get("type") != "change":
        return findings
    if SECRET_SELECTOR.search(_selector_text(step)):
        findings.append(
            f"step {index}: types into a secret-looking field "
            f"({_describe_target(step)!r})")
    value = step.get("value")
    if isinstance(value, str) and any(p.match(value) for p in SECRET_VALUE_PATTERNS):
        findings.append(f"step {index}: typed value looks like a credential/token")
    return findings


def _pick(lo_hi, index, salt):
    """Deterministic, per-step-varied point inside a (lo, hi) range.

    No randomness: the schedule must reproduce byte-for-byte for the same
    recording, but a flat constant would read as a metronome. Knuth's
    multiplicative hash spreads step indexes across the range.
    """
    lo, hi = lo_hi
    fraction = ((index + salt) * 2654435761 % 997) / 996.0
    return int(round(lo + fraction * (hi - lo)))


def _hve_dwell_ms(steps, index):
    """Recorded timing beats synthesized timing, clamped to sane bounds."""
    step = steps[index - 1]
    hve = step.get("hve")
    if isinstance(hve, dict):
        dwell = hve.get("dwellAfterMs")
        if isinstance(dwell, (int, float)):
            return int(min(max(dwell, HVE_T_CLAMP_MS[0]), HVE_T_CLAMP_MS[1]))
    if index < len(steps):
        here, following = steps[index - 1].get("hve"), steps[index].get("hve")
        if (isinstance(here, dict) and isinstance(following, dict)
                and isinstance(here.get("t"), (int, float))
                and isinstance(following.get("t"), (int, float))):
            delta = following["t"] - here["t"]
            if delta > 0:
                return int(min(max(delta, HVE_T_CLAMP_MS[0]), HVE_T_CLAMP_MS[1]))
    return None


def build_schedule(recording):
    """Per-step humanized pacing: what the agent performs, in order."""
    steps = recording["steps"]
    schedule = []
    for index, step in enumerate(steps, start=1):
        step_type = step.get("type")
        entry = {
            "index": index,
            "type": step_type,
            "pre_ms": 0,
            "post_ms": 0,
            "easing": POINTER_EASING,
        }
        recorded = _hve_dwell_ms(steps, index)
        if step_type in ("click", "doubleClick", "hover"):
            entry["pre_ms"] = _pick(POINTER_TRAVEL_MS, index, 1) + HOVER_SETTLE_MS
            entry["post_ms"] = recorded or _pick(READ_DWELL_MS, index, 2)
            entry["target"] = _describe_target(step)
        elif step_type == "change":
            entry["pre_ms"] = _pick(POINTER_TRAVEL_MS, index, 1) + HOVER_SETTLE_MS
            entry["post_ms"] = recorded or _pick(READ_DWELL_MS, index, 2)
            entry["target"] = _describe_target(step)
            entry["typing"] = {
                "chunk_chars": list(TYPE_CHUNK_CHARS),
                "chunk_pause_ms": list(TYPE_CHUNK_PAUSE_MS),
            }
        elif step_type == "navigate":
            entry["post_ms"] = recorded or _pick(NAV_DWELL_MS, index, 3)
            entry["url"] = _sanitized_url(str(step.get("url", "")))
        elif step_type == "scroll":
            entry["pre_ms"] = _pick(SCROLL_MS, index, 4)
            entry["post_ms"] = recorded or _pick(READ_DWELL_MS, index, 5)
        elif step_type == "setViewport":
            entry["note"] = "overridden by the locked Phase-1 canvas"
        elif step_type in ("waitForElement", "waitForExpression"):
            entry["note"] = "poll; no artificial dwell"
        elif step_type in ("keyDown", "keyUp"):
            entry["post_ms"] = recorded or _pick(TYPE_CHUNK_PAUSE_MS, index, 6)
            entry["key"] = str(step.get("key", ""))
        elif step_type in IGNORED_STEP_TYPES:
            entry["note"] = "ignored by design"
        else:
            entry["note"] = "UNHANDLED — replay aborts at this step"
        schedule.append(entry)
    return schedule


# ── storyboard bindings ─────────────────────────────────────────────────────

def parse_frames(storyboard_text):
    """Official-shape frames with just the bullets replay consumes.

    Lenient like the validator's reader: metadata is the contiguous
    `- key: value` block directly under a `## Frame N` heading; anything
    surprising is skipped, never fatal.
    """
    frames = []
    current = None
    in_block = False
    for line in storyboard_text.splitlines():
        heading = FRAME_HEADING.match(line)
        if heading:
            current = {"number": int(heading.group(2)) if heading.group(2) else None,
                       "title": heading.group(3).strip(), "keys": {}}
            frames.append(current)
            in_block = True
            continue
        if current is None or not in_block:
            continue
        bullet = METADATA_BULLET.match(line)
        if bullet:
            key = bullet.group(1).strip().lower()
            current["keys"].setdefault(key, bullet.group(2).strip())
        elif line.strip():
            in_block = False  # first prose line ends the contiguous block
    return frames


def replay_bindings(storyboard_path, recording_path, step_count):
    """Frames bound to *this* recording → cut/still requests."""
    try:
        text = Path(storyboard_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ReplayError(f"Storyboard not found: {storyboard_path}")
    project_dir = Path(storyboard_path).resolve().parent
    bindings = []
    for frame in parse_frames(text):
        keys = frame["keys"]
        bound = keys.get("recording")
        if not bound or not _same_file(bound, recording_path, base=project_dir):
            continue
        capture = keys.get("capture", "screenshot")
        first, last = parse_steps_range(keys.get("recording_steps"), step_count)
        output = keys.get("clip") if capture == "screencast" else keys.get("screenshot")
        if not output:
            raise ReplayError(
                f"Frame {frame['number']} binds `recording:` with "
                f"`capture: {capture}` but names no "
                f"{'`clip:`' if capture == 'screencast' else '`screenshot:`'} output")
        bindings.append({
            "frame": frame["number"],
            "capture": capture,
            "steps": [first, last],
            "output": output,
        })
    if not bindings:
        raise ReplayError(
            f"No storyboard frame binds `recording: {_norm(str(recording_path))}` "
            "— nothing to do.")
    return bindings


# ── plan ────────────────────────────────────────────────────────────────────

def build_plan(recording_path, storyboard_path=None):
    recording = load_recording(recording_path)
    steps = recording["steps"]
    schedule = build_schedule(recording)

    origins, warnings, secrets, unhandled = [], [], [], []
    for index, step in enumerate(steps, start=1):
        step_type = step.get("type")
        if step_type == "navigate":
            origin = _origin(str(step.get("url", "")))
            if origin and origin not in origins:
                origins.append(origin)
        if step_type == "emulateNetworkConditions":
            warnings.append(
                f"step {index}: emulateNetworkConditions is ignored — capture "
                "films the real network")
        if step_type not in HANDLED_STEP_TYPES and step_type not in IGNORED_STEP_TYPES:
            unhandled.append(f"step {index}: unhandled type {step_type!r}")
        secrets.extend(_secret_findings(index, step))

    plan = {
        "schema_version": SCHEMA_VERSION,
        "recording": str(recording_path),
        "recording_sha256": sha256_file(recording_path),
        "title": recording.get("title", ""),
        "step_count": len(steps),
        "origins": origins,
        "warnings": warnings,
        "secrets": secrets,
        "unhandled": unhandled,
        "schedule": schedule,
    }
    if storyboard_path:
        plan["bindings"] = replay_bindings(storyboard_path, recording_path, len(steps))
    return plan


def print_brief(plan):
    """The sanitized consent brief: hosts and targets, never typed values."""
    title = plan["title"] or Path(plan["recording"]).stem
    print(f"Recorded flow: {title} — {plan['step_count']} step(s), "
          f"sha256 {plan['recording_sha256'][:12]}…")
    if plan["origins"]:
        print("Origins the flow visits (replay aborts on any other):")
        for origin in plan["origins"]:
            print(f"  - {origin}")
    for entry in plan["schedule"]:
        line = f"  {entry['index']:>3}. {entry['type']}"
        if "url" in entry:
            line += f" → {entry['url']}"
        if "target" in entry:
            line += f" — {entry['target']!r}"
        if entry["type"] == "change":
            line += " («typed value hidden»)"
        if "key" in entry and entry["key"]:
            line += f" [{entry['key']}]"
        if "note" in entry:
            line += f" ({entry['note']})"
        print(line)
    for finding in plan["secrets"]:
        print(f"SECRET WARNING: {finding} — record after authenticating instead, "
              "and never commit this recording.")
    for finding in plan["unhandled"] + plan["warnings"]:
        print(f"Warning: {finding}")
    for binding in plan.get("bindings", []):
        first, last = binding["steps"]
        print(f"Frame {binding['frame']}: {binding['capture']} from steps "
              f"{first}-{last} → {binding['output']}")


# ── arm ─────────────────────────────────────────────────────────────────────

def arm(recording_path, storyboard_path):
    recording = load_recording(recording_path)
    recording_sha = sha256_file(recording_path)
    bindings = replay_bindings(storyboard_path, recording_path,
                               len(recording["steps"]))
    armed = []
    for binding in bindings:
        if binding["capture"] != "screencast":
            continue  # stills are presence-only; no sidecar family (ADR-011)
        pending = pending_path_for(binding["output"])
        _write_json_atomic(pending, {
            "schema_version": SCHEMA_VERSION,
            "state": "pending",
            "requested": {
                "recording": _norm(str(recording_path)),
                "recording_sha256": recording_sha,
                "steps": binding["steps"],
                "output": binding["output"],
            },
        })
        armed.append(str(pending))
    if not armed:
        print("No clip frames bound to this recording; nothing to arm "
              "(stills need no pending marker).")
    for path in armed:
        print(f"Armed: {path}")
    return 0


# ── cut ─────────────────────────────────────────────────────────────────────

def _probe_duration(path):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "format=duration:stream=width,height,nb_frames",
             "-of", "json", str(path)],
            capture_output=True, text=True, check=True).stdout
    except FileNotFoundError:
        raise ReplayError("`ffprobe` not found on PATH — install ffmpeg (bundles ffprobe).")
    except subprocess.CalledProcessError as exc:
        raise ReplayError(f"ffprobe failed on {path}: {exc.stderr.strip()}")
    payload = json.loads(out)
    try:
        duration = float(payload["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        raise ReplayError(f"ffprobe reported no duration for {path}")
    stream = (payload.get("streams") or [{}])[0]
    return duration, stream


def load_ledger(path, recording_path):
    ledger = _read_json(path, "Replay ledger")
    if ledger.get("schema_version") != SCHEMA_VERSION:
        raise ReplayError(
            f"Ledger schema_version {ledger.get('schema_version')!r} is not "
            f"{SCHEMA_VERSION} ({path})")
    recorded_sha = ledger.get("recording_sha256")
    actual_sha = sha256_file(recording_path)
    if recorded_sha != actual_sha:
        raise ReplayError(
            "Ledger was written for a different recording (hash mismatch) — "
            "re-run the take against the current recording.")
    steps = ledger.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ReplayError(f"Ledger has no `steps` entries ({path})")
    previous_start = -1.0
    for entry in steps:
        try:
            index = int(entry["index"])
            t_start = float(entry["t_start"])
            t_end = float(entry["t_end"])
        except (KeyError, TypeError, ValueError):
            raise ReplayError(f"Ledger step entry is malformed: {entry!r}")
        if index < 1 or t_end < t_start or t_start < previous_start:
            raise ReplayError(
                f"Ledger times are not monotonic at step {entry.get('index')!r}")
        previous_start = t_start
    return ledger, actual_sha


def _ledger_index(ledger):
    return {int(entry["index"]): entry for entry in ledger["steps"]}


def segment_for(ledger, steps_range, master_duration):
    """Dwell-aligned cut window for one frame's step range, clamped to the take."""
    by_index = _ledger_index(ledger)
    first, last = steps_range
    if first not in by_index or last not in by_index:
        raise ReplayError(
            f"Ledger covers no timing for steps {first}-{last} — the take "
            "ended before the range completed; retake or narrow the range.")
    start = max(0.0, float(by_index[first]["t_start"]) - LEAD_PAD_S)
    end = min(master_duration, float(by_index[last]["t_end"]) + TAIL_PAD_S)
    if end <= start:
        raise ReplayError(
            f"Cut for steps {first}-{last} is empty after clamping to the "
            f"{master_duration:.2f}s master — the ledger and take disagree.")
    return start, end - start


def drift_offset(master_duration, ledger):
    """End-anchored correction when the take and the ledger disagree."""
    span = max(float(e["t_end"]) for e in ledger["steps"])
    drift = master_duration - span
    allowed = max(DRIFT_SOFT_S, DRIFT_SOFT_FRACTION * span)
    if abs(drift) <= allowed:
        return 0.0, None
    if abs(drift) > DRIFT_HARD_S:
        raise ReplayError(
            f"Ledger span {span:.2f}s vs master {master_duration:.2f}s drifts "
            f"{drift:+.2f}s (> {DRIFT_HARD_S}s hard bound) — the take is not "
            "trustworthy; retake the flow.")
    return drift, (f"Warning: ledger drifts {drift:+.2f}s from the master; "
                   "applying a uniform end-anchored offset.")


def pointer_track_for(ledger, steps_range, clip_start, offset):
    first, last = steps_range
    track = []
    for entry in ledger["steps"]:
        index = int(entry["index"])
        if index < first or index > last:
            continue
        t_clip = float(entry["t_start"]) + offset - clip_start
        track.append({
            "step": index,
            "t": round(max(0.0, t_clip), 3),
            "action": str(entry.get("action", entry.get("type", ""))),
            "bbox": entry.get("bbox"),
            "easing": POINTER_EASING,
        })
    return track


def cut(recording_path, raw_path, ledger_path, storyboard_path,
        canvas=None, stitch_path=None, fps=30):
    recording = load_recording(recording_path)
    ledger, recording_sha = load_ledger(ledger_path, recording_path)
    bindings = replay_bindings(storyboard_path, recording_path,
                               len(recording["steps"]))
    clip_bindings = [b for b in bindings if b["capture"] == "screencast"]
    if not clip_bindings:
        raise ReplayError("No clip frames bound to this recording; `cut` cuts clips only.")
    if not Path(raw_path).is_file():
        raise ReplayError(f"Master take not found: {raw_path}")

    master_duration, _ = _probe_duration(raw_path)
    offset, drift_warning = drift_offset(master_duration, ledger)
    if drift_warning:
        print(drift_warning, file=sys.stderr)

    stitch = Path(stitch_path) if stitch_path else Path(__file__).with_name("stitch_clip.py")
    if not stitch.is_file():
        raise ReplayError(f"stitch_clip.py not found at {stitch}")

    results = []
    for binding in clip_bindings:
        output = Path(binding["output"])
        start, duration = segment_for(
            ledger, tuple(binding["steps"]), master_duration)
        start = max(0.0, start + offset)
        candidate = output.with_name(f".{output.name}.replay-candidate-{uuid.uuid4().hex}.mp4")
        command = [sys.executable, str(stitch),
                   f"{raw_path}::{start:.3f}::{duration:.3f}",
                   "-o", str(candidate), "--fps", str(fps)]
        if canvas:
            command += ["--width", str(canvas[0]), "--height", str(canvas[1])]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0 or not candidate.is_file() or candidate.stat().st_size == 0:
            candidate.unlink(missing_ok=True)
            raise ReplayError(
                f"Cut failed for frame {binding['frame']} ({output}): "
                f"{result.stderr.strip() or 'no output produced'}. Previous "
                "clip and pending marker are untouched.")

        clip_duration, stream = _probe_duration(candidate)
        sidecar_payload = {
            "schema_version": SCHEMA_VERSION,
            "state": "complete",
            "requested": {
                "recording": _norm(str(recording_path)),
                "recording_sha256": recording_sha,
                "steps": binding["steps"],
                "output": str(output),
                "canvas": list(canvas) if canvas else None,
                "source": ledger.get("source"),
                "pointer": ledger.get("pointer"),
            },
            "take": {
                "ledger": _norm(str(ledger_path)),
                "master_duration_seconds": round(master_duration, 3),
                "drift_offset_seconds": round(offset, 3),
                "cut_start_seconds": round(start, 3),
            },
            "media": {
                "duration_seconds": round(clip_duration, 3),
                "width": stream.get("width"),
                "height": stream.get("height"),
                "file_size_bytes": candidate.stat().st_size,
                "fingerprint": {"algorithm": "sha256",
                                "value": sha256_file(candidate)},
            },
            "pointer_track": pointer_track_for(
                ledger, tuple(binding["steps"]), start, offset),
        }
        _publish(candidate, output, sidecar_payload)
        results.append({"frame": binding["frame"], "output": str(output),
                        "start": round(start, 3),
                        "duration": round(clip_duration, 3)})
        print(f"Cut frame {binding['frame']}: {output} "
              f"({start:.2f}s +{clip_duration:.2f}s of the master)")
    return results


def _publish(candidate, output, sidecar_payload):
    """Atomic clip+sidecar publish; any failure restores the previous pair."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sidecar = sidecar_path_for(output)
    backup_clip = backup_sidecar = None
    try:
        if output.is_file():
            backup_clip = output.with_name(f".{output.name}.replay-prev-{uuid.uuid4().hex}")
            os.replace(output, backup_clip)
        if sidecar.is_file():
            backup_sidecar = sidecar.with_name(f".{sidecar.name}.prev-{uuid.uuid4().hex}")
            os.replace(sidecar, backup_sidecar)
        os.replace(candidate, output)
        _write_json_atomic(sidecar, sidecar_payload)
        pending_path_for(output).unlink(missing_ok=True)
    except Exception:
        if backup_clip is not None and backup_clip.is_file():
            os.replace(backup_clip, output)
        if backup_sidecar is not None and backup_sidecar.is_file():
            os.replace(backup_sidecar, sidecar)
        candidate.unlink(missing_ok=True)
        raise
    for leftover in (backup_clip, backup_sidecar):
        if leftover is not None:
            Path(leftover).unlink(missing_ok=True)


# ── check ───────────────────────────────────────────────────────────────────

def check(recording_path, output, steps_text=None):
    recording = load_recording(recording_path)
    step_count = len(recording["steps"])
    steps_range = list(parse_steps_range(steps_text, step_count))

    output = Path(output)
    pending = pending_path_for(output)
    if pending.is_file():
        raise ReplayError(
            f"Replay capture is incomplete because the pending marker exists: {pending}")
    sidecar = sidecar_path_for(output)
    if not sidecar.is_file():
        raise ReplayError(f"Replay sidecar is missing: {sidecar}")
    payload = _read_json(sidecar, "Replay sidecar")
    if payload.get("schema_version") != SCHEMA_VERSION or payload.get("state") != "complete":
        raise ReplayError(f"Replay sidecar is not a complete v{SCHEMA_VERSION} record: {sidecar}")

    requested = payload.get("requested") or {}
    if not requested.get("recording") or not _same_file(
            requested["recording"], recording_path):
        raise ReplayError(
            "Sidecar was cut from a different recording path than requested.")
    if requested.get("recording_sha256") != sha256_file(recording_path):
        raise ReplayError(
            "Recording changed since this clip was cut (hash mismatch) — "
            "the flow was re-recorded; re-run the take and cut again.")
    if list(requested.get("steps") or []) != steps_range:
        raise ReplayError(
            f"Sidecar covers steps {requested.get('steps')} but the storyboard "
            f"requests {steps_range} — re-cut from the master (or retake).")

    if not output.is_file() or output.stat().st_size == 0:
        raise ReplayError(f"Bound clip is missing or empty: {output}")
    fingerprint = ((payload.get("media") or {}).get("fingerprint") or {})
    if fingerprint.get("algorithm") != "sha256" or \
            fingerprint.get("value") != sha256_file(output):
        raise ReplayError(
            "Clip bytes do not match the sidecar fingerprint — the file was "
            "modified after publish; retake or re-cut.")
    print(f"Replay capture is complete and fresh: {output}")
    return 0


# ── CLI ─────────────────────────────────────────────────────────────────────

def _parse_canvas(text):
    match = re.fullmatch(r"(\d+)x(\d+)", text.strip())
    if not match:
        raise argparse.ArgumentTypeError("canvas must be WIDTHxHEIGHT, e.g. 1920x1080")
    return (int(match.group(1)), int(match.group(2)))


def _parser():
    parser = argparse.ArgumentParser(
        description="Plan, arm, cut, and verify recorded browse-flow captures.")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_cmd = sub.add_parser("plan", help="Validate a recording; emit schedule + consent brief.")
    plan_cmd.add_argument("--recording", required=True)
    plan_cmd.add_argument("--storyboard")
    plan_cmd.add_argument("--json", action="store_true")

    arm_cmd = sub.add_parser("arm", help="Write pending markers for the bound clip frames.")
    arm_cmd.add_argument("--recording", required=True)
    arm_cmd.add_argument("--storyboard", required=True)

    cut_cmd = sub.add_parser("cut", help="Cut per-frame clips from the master take.")
    cut_cmd.add_argument("--recording", required=True)
    cut_cmd.add_argument("--raw", required=True)
    cut_cmd.add_argument("--ledger", required=True)
    cut_cmd.add_argument("--storyboard", required=True)
    cut_cmd.add_argument("--canvas", type=_parse_canvas)
    cut_cmd.add_argument("--stitch", help="Path to stitch_clip.py (default: sibling).")
    cut_cmd.add_argument("--fps", type=int, default=30)

    check_cmd = sub.add_parser("check", help="Verify one bound clip is complete and fresh.")
    check_cmd.add_argument("--recording", required=True)
    check_cmd.add_argument("--steps", help="A-B (1-based); omit for the whole flow.")
    check_cmd.add_argument("-o", "--output", required=True)
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        if args.command == "plan":
            plan = build_plan(args.recording, args.storyboard)
            if args.json:
                print(json.dumps(plan, indent=2, sort_keys=True))
            else:
                print_brief(plan)
            return 0
        if args.command == "arm":
            return arm(args.recording, args.storyboard)
        if args.command == "cut":
            cut(args.recording, args.raw, args.ledger, args.storyboard,
                canvas=args.canvas, stitch_path=args.stitch, fps=args.fps)
            return 0
        if args.command == "check":
            return check(args.recording, args.output, args.steps)
    except ReplayError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
