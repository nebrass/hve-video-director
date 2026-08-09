#!/usr/bin/env python3
"""Report the motion register of a scene: how many distinct emotions its tweens express.

Measured on a real 60-second film: 56 tweens, every one a decelerate-only curve, zero
`CustomEase`, zero `cubic-bezier`. One scene set `var EASE = "expo.out"` and used it for
nine entrances at durations 0.8/0.9/0.8/0.8/0.9/0.8/0.9/0.8/0.95 -- nine events, one
emotion. `patterns/anti-slop.md` names that exact tell ("same ease + same duration = same
emotion every time, which is no emotion") and nothing caught it: `lint`, `check`, the seam
gate and `ANIMATION_MAP` all passed green, because none of them is looking for it.

**This is a semantic report, not a second validator.** ADR-003 forbids building a parallel
gate when one exists; `ANIMATION_MAP` already owns pacing (`paced-fast`, `paced-slow`,
`collision`, dead zones) and this deliberately reports none of that. What it reports is
whether the *character* of a scene's motion varies with the kind of event -- a question that
needs the frame's intent to answer, which is why it lives here (ADR-006 test 4) rather than
upstream.

It reports and never gates. A scene legitimately built from one repeated element -- a list
revealing in stagger -- will look monotonous by this measure and be right. Exit 1 marks a
finding for a human to read, never a blocked phase.

Pure standard library. Reads; writes nothing.

    python3 scripts/motion_register.py                 # every scenes/*.html
    python3 scripts/motion_register.py scenes/03-x.html --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# A GSAP tween call. Matching `tl.to(` alone was wrong in the most common way there is:
# `tl.to(...).to(...).to(...)` is idiomatic GSAP and only the head has a receiver, so six
# identical entrances reported as one tween and the scene passed clean. Match the METHOD,
# not the receiver, and drop the ones that are not tweens.
TWEEN_CALL = re.compile(r"\.\s*(to|from|fromTo|set)\s*\(")

# Vars-object duration/ease. GSAP also accepts a positional duration in its legacy
# signature -- tl.to(target, 0.8, {...}) -- which carries no `duration:` key at all.
DURATION = re.compile(r"\bduration\s*:\s*([0-9]*\.?[0-9]+)")
POSITIONAL_DURATION = re.compile(r"^\s*[^,]+,\s*([0-9]*\.?[0-9]+)\s*,\s*\{")
EASE = re.compile(r"\bease\s*:\s*(?:\"([^\"]+)\"|'([^']+)'|`([^`]+)`|([A-Za-z_$][\w$.]*))")

# A scene that assigns one ease to a variable and reuses it. The measured failure.
EASE_CONST = re.compile(r"\b(?:var|let|const)\s+([A-Z_][A-Z0-9_]*)\s*=\s*[\"']([\w.]+)[\"']")

# `gsap.timeline({ defaults: { duration: 0.8, ease: "expo.out" } })` — every tween inherits
# these, so a scene can be maximally monotonous while no individual call names either.
DEFAULTS = re.compile(r"\bdefaults\s*:\s*\{([^{}]*)\}")

# Thresholds. Both are reporting sensitivities, not law: no budget number lives here.
SHARE_THRESHOLD = 0.60          # of a scene's tweens sharing one ease
DURATION_BAND = 0.20            # seconds; "near-identical" length
MIN_TWEENS = 4                  # below this a scene is too small to have a register


def _blank(out: list[str], start: int, stop: int) -> None:
    for index in range(start, stop):
        if out[index] != "\n":
            out[index] = " "


def strip_comments(text: str) -> str:
    """Blank comment bodies, preserving length.

    A commented-out `duration:`/`ease:` pair inside a call body was being read as the
    tween's own values -- and, when it sat beside a live pair, it also diluted a real
    finding below the reporting threshold.
    """
    out = list(text)
    index, end = 0, len(text)
    while index < end:
        char = text[index]
        if char in "\"'`":                      # skip strings; a // inside one is not a comment
            quote, index = char, index + 1
            while index < end and text[index] != quote:
                index += 2 if text[index] == "\\" else 1
            index += 1
            continue
        if char == "/" and index + 1 < end and text[index + 1] == "/":
            stop = text.find("\n", index)
            stop = end if stop == -1 else stop
            _blank(out, index, stop)
            index = stop
            continue
        if char == "/" and index + 1 < end and text[index + 1] == "*":
            stop = text.find("*/", index + 2)
            stop = end if stop == -1 else stop + 2
            _blank(out, index, stop)
            index = stop
            continue
        index += 1
    return "".join(out)


def blank_strings(text: str) -> str:
    """Blank string bodies, preserving length.

    Only for finding call boundaries: a `)` inside a string literal truncated the call
    slice, so the tween vanished entirely, and a `(` in one invented a phantom.
    """
    out = list(text)
    index, end = 0, len(text)
    while index < end:
        char = text[index]
        if char in "\"'`":
            quote, index = char, index + 1
            while index < end and text[index] != quote:
                step = 2 if text[index] == "\\" else 1
                _blank(out, index, min(index + step, end))
                index += step
            index += 1
            continue
        index += 1
    return "".join(out)


def slice_call(text: str, start: int) -> str:
    """The argument text of one call, to its matching paren."""
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[start:index]
    return text[start:]


def resolve_ease(raw: str, constants: dict[str, str]) -> str:
    return constants.get(raw, raw)


def timeline_defaults(text: str) -> dict[str, str]:
    """duration/ease inherited by every tween on the timeline."""
    found = DEFAULTS.search(text)
    if not found:
        return {}
    body = found.group(1)
    defaults: dict[str, str] = {}
    duration = DURATION.search(body)
    if duration:
        defaults["duration"] = duration.group(1)
    ease = EASE.search(body)
    if ease:
        defaults["ease"] = next((g for g in ease.groups() if g), "")
    return defaults


def tweens_in(raw_text: str) -> list[dict[str, Any]]:
    # Two passes, because they serve opposite needs. Comments must never be read as
    # values; string bodies must not break paren balance, but the ease VALUE lives
    # inside one -- so extraction reads comment-free text with its strings intact,
    # while call boundaries are found with strings blanked as well.
    source = strip_comments(raw_text)
    spans = blank_strings(source)

    constants = {name: value for name, value in EASE_CONST.findall(source)}
    defaults = timeline_defaults(source)

    found = []
    for match in TWEEN_CALL.finditer(spans):
        if match.group(1) == "set":       # a set has no duration and no character
            continue
        start = match.end() - 1
        span = slice_call(spans, start)
        body = source[start:start + len(span)]

        duration = DURATION.search(span)
        positional = POSITIONAL_DURATION.search(span[1:]) if not duration else None
        seconds = (
            duration.group(1) if duration
            else positional.group(1) if positional
            else defaults.get("duration")
        )
        if seconds is None:
            continue

        ease = EASE.search(body)
        raw = next((g for g in ease.groups() if g), "") if ease else defaults.get("ease", "")
        found.append(
            {
                "duration": float(seconds),
                "ease": resolve_ease(raw, constants) or "(default)",
            }
        )
    return found


def analyse(path: Path) -> dict[str, Any]:
    # A scene is authored HTML and may carry anything; a decode error must not read as
    # a crash-shaped exit 1, which is also the "findings exist" code.
    tweens = tweens_in(path.read_text(encoding="utf-8", errors="replace"))
    report: dict[str, Any] = {
        "scene": path.name,
        "tween_count": len(tweens),
        "eases": {},
        "findings": [],
    }
    if len(tweens) < MIN_TWEENS:
        report["note"] = "too few tweens to have a register"
        return report

    counts: dict[str, list[float]] = {}
    for tween in tweens:
        counts.setdefault(tween["ease"], []).append(tween["duration"])
    report["eases"] = {ease: len(d) for ease, d in sorted(counts.items())}

    for ease, durations in sorted(counts.items()):
        share = len(durations) / len(tweens)
        spread = max(durations) - min(durations)
        if share >= SHARE_THRESHOLD and spread <= DURATION_BAND and len(durations) >= MIN_TWEENS:
            report["findings"].append(
                f"{len(durations)}/{len(tweens)} tweens share ease `{ease}` within a "
                f"{spread:.2f}s duration band — one emotion for {len(durations)} events. "
                "An arrival, an emphasis and a settle are different events; vary the "
                "register with the event, not with the element."
            )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenes", nargs="*", help="scene files (default: scenes/*.html)")
    parser.add_argument("--json", action="store_true", help="Emit one JSON object.")
    args = parser.parse_args(argv)

    paths = [Path(p) for p in args.scenes] or sorted(Path("scenes").glob("*.html"))
    missing = [p for p in paths if not p.is_file()]
    if missing or not paths:
        message = (
            f"no such scene file: {', '.join(str(p) for p in missing)}"
            if missing else "no scenes found (looked for scenes/*.html)"
        )
        if args.json:
            print(json.dumps({"errors": [message], "scenes": []}))
        else:
            print(message, file=sys.stderr)
        return 2

    reports = [analyse(path) for path in paths]
    total = sum(len(r["findings"]) for r in reports)
    payload = {"scenes": reports, "finding_count": total, "errors": []}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for report in reports:
            head = f"{report['scene']}: {report['tween_count']} tween(s)"
            if report.get("note"):
                print(f"{head} — {report['note']}")
                continue
            print(f"{head}; eases {report['eases']}")
            for finding in report["findings"]:
                print(f"  {finding}")
        print(
            f"\n{total} finding(s). This is a report — a scene built from one repeated "
            "element can look monotonous by this measure and be right. Nothing here "
            "blocks a phase."
        )
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
