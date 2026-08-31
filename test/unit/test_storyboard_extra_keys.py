#!/usr/bin/env python3
"""The `STORYBOARD_EXTRA_KEYS` behavior probe (ADR-007).

M4 adopted the official HyperFrames storyboard shape. Everything this skill
needs that the official key set has no home for — the fourteen director keys
above all — rides along as ordinary `- key: value` bullets, and survives *only*
because the upstream parser preserves unknown bullets verbatim under a frame's
`extra` (and unknown frontmatter keys under `globals.extra`).

That makes the behavior load-bearing, and it is the silent kind. If upstream
ever drops unknown keys, or promotes one of our key names into its own official
set, every frame quietly loses its direction while `lint`, `check`, the seam
gate and the pointer suite all stay green. `compat/ecosystem.md` registered the
probe at M0.5 and carried it as MANUAL/DEFERRED; this file is where it becomes
real.

Two halves, deliberately different in strength:

1. **Round trip through an upstream parser** (`RoundTripThroughUpstreamParser`).
   Several installed ecosystem workflow skills vendor a dependency-free plain-JS
   port of the canonical `@hyperframes/core` storyboard parser — upstream
   authored, upstream shipped, and self-declared as kept in lockstep with core.
   The probe writes a frame carrying every director key, runs it through **every**
   copy it finds, and asserts each key *and its value* comes back under `extra`.
   This is a port, not `@hyperframes/core` itself: that package does not resolve
   here (see the probe's status note in `compat/ecosystem.md`).

2. **The documented contract** (`DocumentedContractSurvives`). Reads the
   `STORYBOARD_FORMAT` document — resolved *through* `compat/ecosystem.md`, so
   this file holds no upstream path — and asserts the preservation guarantee is
   still stated, and that no director key has been promoted into the official
   per-frame key set. Needs nothing installed beyond the skill itself, and runs
   on a machine with no `node`.

Both halves skip cleanly when the ecosystem is not installed: it is optional at
test time, exactly as `test_compat_pointers.py` treats it.

Nothing here restates a director key, an upstream path, or an official key name.
The key set comes from `reasoning/scene-analysis.md` (its single source, the
same table `test_director_keys.py` reads); the official key set comes from the
upstream document; the document's location comes from the compatibility map.
"""

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "SKILL.md"
COMPAT = ROOT / "compat" / "ecosystem.md"
SCENE_ANALYSIS = ROOT / "reasoning" / "scene-analysis.md"

# The symbol whose registry row resolves the upstream storyboard document. The
# path itself is deliberately absent from this file (ADR-007): it is read out of
# the map at runtime, so an upstream relayout is one edit there and zero here.
FORMAT_SYMBOL = "STORYBOARD_FORMAT"

# The exported entry point of the upstream parser. Discovery is by capability,
# not by path: any `*.mjs` under a skill home that exports this name is a
# candidate, so a relayout inside an upstream skill does not blind the probe.
PARSER_EXPORT = "parseStoryboard"

# The manifest fields the format defines for preserved-unknown data.
FRAME_EXTRA = "extra"
GLOBALS_EXTRA = "extra"

SECTION = "## Director keys"
KEY_CELL = re.compile(r"^`([a-z][a-z0-9_]*):`$")
BACKTICKED = re.compile(r"`([^`]+)`")


def read(path):
    return path.read_text(encoding="utf-8")


def rel(path):
    return str(Path(path).relative_to(ROOT))


# --------------------------------------------------------------------------
# Resolution: skill homes, the map, the upstream document, the parser copies
# --------------------------------------------------------------------------


def skill_homes():
    """Candidate skill install homes, repo-vendored copy first.

    The canonical `$SKILL_HOMES` list lives in `SKILL.md` § Runtime
    Compatibility and is parsed out of it, so this stays in lock-step with the
    resolver the skill itself ships rather than pinning a second copy.
    """
    homes = [ROOT / ".agents" / "skills"]
    match = re.search(r'SKILL_HOMES="([^"]*)"', read(SKILL))
    if match:
        for entry in match.group(1).split("|"):
            expanded = entry.replace("$SKILL_ROOT", str(ROOT)).replace(
                "$HOME", str(Path.home())
            )
            candidate = Path(expanded)
            homes.append(candidate if candidate.is_absolute() else ROOT / candidate)
    seen, ordered = set(), []
    for home in homes:
        key = str(home)
        if key not in seen:
            seen.add(key)
            ordered.append(home)
    return [home for home in ordered if home.is_dir()]


def registry_row(symbol):
    """(owning skill, skill-relative path) for one capability row of the map."""
    for line in read(COMPAT).splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0].strip("`") != symbol:
            continue
        return cells[1].strip("`"), cells[2].strip("`")
    return None, None


def format_document(homes):
    """The upstream storyboard-format document, resolved through the map."""
    skill, path = registry_row(FORMAT_SYMBOL)
    if not skill or not path:
        return None
    for home in homes:
        candidate = home / skill / path
        if candidate.is_file():
            return candidate
    return None


def vendored_parsers(homes):
    """Every installed ESM module exporting the upstream storyboard parser.

    Sorted and returned whole rather than sampled: the copies are meant to be
    identical, and a probe that silently picks one makes its own identity depend
    on install order.
    """
    found = {}
    marker = f"export function {PARSER_EXPORT}"
    for home in homes:
        for candidate in home.glob("*/**/*.mjs"):
            if candidate.name.startswith("."):
                continue
            try:
                text = candidate.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if marker in text:
                found.setdefault(candidate.resolve(), candidate)
    return [found[key] for key in sorted(found)]


# --------------------------------------------------------------------------
# The director keys, from their single source
# --------------------------------------------------------------------------


def director_keys():
    """Key names from `reasoning/scene-analysis.md` § Director keys.

    The first column of the closed-contract table, which writes each key in its
    bullet form (`` `goal:` ``). Derived rather than typed here so the contract
    keeps exactly one source (ADR-008's posture, applied to vocabulary).
    """
    text = read(SCENE_ANALYSIS)
    start = text.find(SECTION)
    if start == -1:
        return []
    body = text[start + len(SECTION) :]
    end = body.find("\n## ")
    if end != -1:
        body = body[:end]
    keys = []
    for line in body.splitlines():
        if not line.startswith("|"):
            continue
        first = line.strip().strip("|").split("|")[0].strip()
        match = KEY_CELL.match(first)
        if match and match.group(1) not in keys:
            keys.append(match.group(1))
    return keys


# A realistic value per key shape. Values matter as much as names: a parser that
# kept the keys and truncated the values would sail through a presence-only
# assertion. `motion` carries the hard case this repo actually emits — a
# backticked, comma-separated list — and `runtime_rejected` carries an embedded
# colon and an em dash.
SHAPED_VALUES = {
    "motion": "`depth-scatter-assemble`, `center-outward-expansion`",
    "runtime_rejected": (
        "three — requested as `camera: exploded-3d`, but the film's hero beats "
        "are already committed elsewhere"
    ),
    "goal": "the viewer understands the product is three cooperating layers, not one box",
    "capabilities": "timeline-choreography, spatial-depth",
    "user_directed": "true",
    "recording": "recordings/probe-flow.json",
    "recording_steps": "2-5",
}

# Capture bindings ride the same `extra` mechanism as the director keys; the
# round-trip exercises the newest pair (ADR-011's recorded-flow bindings) as
# part of its representative sample.
CAPTURE_BINDING_SAMPLE = ("recording", "recording_steps")


def probe_value(key):
    return SHAPED_VALUES.get(key, f"probe-value-for-{key}")


# Frontmatter keys of our own. Representative, not exhaustive: `globals.extra`
# is one mechanism and this exercises it. The generated file's real field list is
# owned by `templates/storyboard.md`; see the residual limits recorded with the
# probe in `compat/ecosystem.md`.
GLOBAL_EXTRAS = {
    "content_mode": "promo",
    "emotional_journey": "curiosity → tension → relief → confidence",
    "replay_pointer": "branded",
}


def probe_storyboard(keys):
    lines = ["---", "format: 1920x1080", "duration: 22s", 'message: "probe"']
    for key, value in GLOBAL_EXTRAS.items():
        lines.append(f"{key}: {value}")
    lines += ["---", "", "## Frame 1 — Probe", "", "- status: outline", "- duration: 6s"]
    for key in keys:
        lines.append(f"- {key}: {probe_value(key)}")
    lines += ["", "Narrative prose below the bullet block.", ""]
    return "\n".join(lines)


DRIVER = """\
import { parseStoryboard } from %(module)s;
import { readFileSync } from "node:fs";
const manifest = parseStoryboard(readFileSync(process.argv[2], "utf8"));
process.stdout.write(JSON.stringify(manifest));
"""


class RoundTripThroughUpstreamParser(unittest.TestCase):
    """Write every director key, parse, assert every key and value survives."""

    def test_director_keys_survive_the_official_format(self):
        homes = skill_homes()
        if not homes:
            self.skipTest(
                "no skill home resolved from $SKILL_HOMES — the ecosystem is "
                "optional at test time"
            )
        parsers = vendored_parsers(homes)
        if not parsers:
            self.skipTest(
                f"no installed module exports `{PARSER_EXPORT}` under any of "
                f"{len(homes)} skill home(s); run `npx hyperframes skills update` "
                "to restore the round-trip half of this probe"
            )
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not on PATH — the round-trip half needs it")

        keys = director_keys()
        self.assertTrue(
            keys,
            f"{rel(SCENE_ANALYSIS)}: no director keys parsed out of "
            f"'{SECTION}' — the probe has nothing to prove, which is a broken "
            f"probe, not a passing one",
        )
        keys = keys + list(CAPTURE_BINDING_SAMPLE)
        source = probe_storyboard(keys)

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            storyboard = tmp / "STORYBOARD.md"
            storyboard.write_text(source, encoding="utf-8")
            for index, parser in enumerate(parsers):
                # `as_uri()` percent-encodes: skill homes may contain spaces,
                # which is why $SKILL_HOMES is pipe-delimited in the first place.
                driver = tmp / f"driver-{index}.mjs"
                driver.write_text(
                    DRIVER % {"module": json.dumps(parser.resolve().as_uri())},
                    encoding="utf-8",
                )
                manifest = self._parse(node, driver, storyboard, parser)
                self._assert_survives(manifest, keys, parser)

    def _parse(self, node, driver, storyboard, parser):
        result = subprocess.run(
            [node, str(driver), str(storyboard)],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"the upstream parser at {parser} could not be driven "
            f"(exit {result.returncode}). This is a probe failure, not "
            f"necessarily a contract break — read stderr first:\n"
            f"{result.stderr.strip()}",
        )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            self.fail(
                f"the upstream parser at {parser} returned no JSON manifest "
                f"({exc}); stdout was:\n{result.stdout[:2000]}"
            )

    def _assert_survives(self, manifest, keys, parser):
        frames = manifest.get("frames") or []
        self.assertEqual(
            len(frames),
            1,
            f"{parser}: expected the probe storyboard to yield exactly one "
            f"frame, got {len(frames)} — the frame-heading shape this skill "
            f"writes is no longer recognised",
        )
        frame = frames[0]
        extra = frame.get(FRAME_EXTRA)
        self.assertIsInstance(
            extra,
            dict,
            f"{parser}: the parsed frame has no `{FRAME_EXTRA}` mapping. "
            f"STORYBOARD_EXTRA_KEYS is broken: every director key this skill "
            f"writes is now discarded, and no gate would say so",
        )

        dropped = [key for key in keys if key not in extra]
        promoted = [key for key in dropped if key in frame]
        self.assertFalse(
            dropped,
            f"{parser}: {len(dropped)} of {len(keys)} director key(s) did not "
            f"survive parsing: {', '.join(dropped)}. "
            + (
                f"{', '.join(promoted)} now land in named manifest field(s) "
                f"instead — upstream promoted our key name(s) into its official "
                f"set, so the value is reinterpreted rather than preserved. "
                if promoted
                else "They were dropped outright. "
            )
            + "Frames silently lose their direction while every gate stays "
            "green; see the STORYBOARD_EXTRA_KEYS probe in compat/ecosystem.md",
        )

        mangled = {
            key: (probe_value(key), extra[key])
            for key in keys
            if extra[key] != probe_value(key)
        }
        self.assertFalse(
            mangled,
            f"{parser}: {len(mangled)} director key(s) survived by name but not "
            f"by value — preservation is no longer verbatim: "
            + "; ".join(
                f"{key}: wrote {wrote!r}, read {got!r}"
                for key, (wrote, got) in sorted(mangled.items())
            ),
        )

        globals_extra = (manifest.get("globals") or {}).get(GLOBALS_EXTRA)
        self.assertIsInstance(
            globals_extra,
            dict,
            f"{parser}: the parsed globals have no `{GLOBALS_EXTRA}` mapping — "
            f"this skill's own frontmatter fields are discarded",
        )
        lost = {
            key: value
            for key, value in GLOBAL_EXTRAS.items()
            if globals_extra.get(key) != value
        }
        self.assertFalse(
            lost,
            f"{parser}: frontmatter field(s) did not survive under "
            f"`globals.{GLOBALS_EXTRA}`: {', '.join(sorted(lost))}",
        )


class DocumentedContractSurvives(unittest.TestCase):
    """The upstream document still promises preservation, and still leaves room.

    Runs with no `node` and no npm anything. Structural where phrasing would be
    brittle, exact where the question is precise: a reworded guarantee must not
    fail, and a *collision* must not pass.
    """

    def setUp(self):
        homes = skill_homes()
        document = format_document(homes) if homes else None
        if document is None:
            skill, path = registry_row(FORMAT_SYMBOL)
            self.skipTest(
                f"{FORMAT_SYMBOL} ({skill or '?'}) is not installed under any of "
                f"{len(homes)} skill home(s) — the ecosystem is optional at test "
                f"time"
            )
        self.document = document
        self.text = read(document)

    def frame_key_table(self):
        """The per-frame key table: the one whose rows name `status`.

        Identified by content, not by position or heading text, so a reordered
        or renamed section does not read as a broken contract.
        """
        table, best = [], []
        for line in self.text.splitlines():
            if line.startswith("|"):
                table.append([c.strip() for c in line.strip().strip("|").split("|")])
                continue
            if table:
                if any("`status`" == row[0] for row in table if row):
                    best = table
                table = []
        if table and any("`status`" == row[0] for row in table if row):
            best = table
        return best

    def test_unknown_keys_are_still_promised_to_be_preserved(self):
        rows = self.frame_key_table()
        self.assertTrue(
            rows,
            f"{self.document}: no per-frame key table found. The document that "
            f"defines what a storyboard frame may carry changed shape; re-read "
            f"it before trusting STORYBOARD_EXTRA_KEYS",
        )
        catch_all = [
            row
            for row in rows
            if len(row) > 1 and not BACKTICKED.fullmatch(row[0]) and FRAME_EXTRA in row[1]
        ]
        self.assertTrue(
            catch_all,
            f"{self.document}: the per-frame key table no longer carries a "
            f"catch-all row promising unknown keys are kept under "
            f"`{FRAME_EXTRA}`. This skill's director keys ride entirely on that "
            f"promise",
        )

    def test_globals_still_keep_unknown_frontmatter(self):
        self.assertIn(
            f"globals.{GLOBALS_EXTRA}",
            self.text,
            f"{self.document}: the frontmatter section no longer states that "
            f"unknown keys are kept under `globals.{GLOBALS_EXTRA}` — this "
            f"skill's own film-level fields ride on it",
        )

    def test_manifest_still_declares_the_preserved_mapping(self):
        blocks = re.findall(r"```[^\n]*\n(.*?)```", self.text, re.S)
        manifest = [b for b in blocks if "StoryboardManifest" in b]
        self.assertTrue(
            manifest,
            f"{self.document}: no StoryboardManifest shape published — the "
            f"parsed side of the contract is no longer documented",
        )
        self.assertIn(
            FRAME_EXTRA,
            manifest[0],
            f"{self.document}: the published StoryboardManifest no longer "
            f"declares `{FRAME_EXTRA}`",
        )

    def test_no_director_key_collides_with_an_official_key(self):
        keys = set(director_keys())
        official = {
            match.group(1)
            for row in self.frame_key_table()
            if row and (match := BACKTICKED.fullmatch(row[0]))
        }
        collisions = sorted(keys & official)
        self.assertFalse(
            collisions,
            f"{self.document}: upstream now defines {', '.join(collisions)} as "
            f"an official frame key, and this skill writes the same name as a "
            f"director key. The value stops landing in `{FRAME_EXTRA}` and is "
            f"reinterpreted as upstream's field instead — silently. Rename the "
            f"director key in reasoning/scene-analysis.md (its single source) "
            f"and everywhere it is emitted",
        )


if __name__ == "__main__":
    unittest.main()
