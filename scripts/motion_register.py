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

# A GSAP call carrying a duration and (usually) an ease. Matches tl.to / tl.from /
# tl.fromTo / gsap.to and friends; the vars object is scanned, not parsed, because a
# scene's script is JavaScript and this is a report rather than an interpreter.
TWEEN_CALL = re.compile(r"\b(?:tl|gsap|timeline)\s*\.\s*(to|from|fromTo|set)\s*\(", re.I)
DURATION = re.compile(r"\bduration\s*:\s*([0-9]*\.?[0-9]+)")
EASE = re.compile(r"\bease\s*:\s*(?:\"([^\"]+)\"|'([^']+)'|([A-Za-z_$][\w$.]*))")

# A scene that assigns one ease to a variable and reuses it. The measured failure.
EASE_CONST = re.compile(r"\b(?:var|let|const)\s+([A-Z_][A-Z0-9_]*)\s*=\s*[\"']([\w.]+)[\"']")

# Thresholds. Both are reporting sensitivities, not law: no budget number lives here.
SHARE_THRESHOLD = 0.60          # of a scene's tweens sharing one ease
DURATION_BAND = 0.20            # seconds; "near-identical" length
MIN_TWEENS = 4                  # below this a scene is too small to have a register


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


def tweens_in(text: str) -> list[dict[str, Any]]:
    constants = {name: value for name, value in EASE_CONST.findall(text)}
    found = []
    for match in TWEEN_CALL.finditer(text):
        if match.group(1) == "set":       # a set has no duration and no character
            continue
        body = slice_call(text, match.end() - 1)
        duration = DURATION.search(body)
        ease = EASE.search(body)
        if not duration:
            continue
        raw = next((g for g in ease.groups() if g), "") if ease else ""
        found.append(
            {
                "duration": float(duration.group(1)),
                "ease": resolve_ease(raw, constants) or "(default)",
            }
        )
    return found


def analyse(path: Path) -> dict[str, Any]:
    tweens = tweens_in(path.read_text(encoding="utf-8"))
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
