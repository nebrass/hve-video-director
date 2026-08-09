"""Every authored GSAP tag agrees with `gsap-pin.json`.

The failure this prevents is quiet in a way that matters: an integrity hash that does not
match its version makes the browser refuse the script, so every scene renders with no
animation at all. Nothing in the authoring loop reports it -- `npx hyperframes check` is
the first thing that notices, at the Phase 4/5 gate, long after the scenes were written.

The previous guard (a CI step) counted *distinct* values across the tree and required the
count to be 1. That proves the tree agrees with itself and nothing more: a version and a
hash copied wrong together, everywhere at once, passed it. This file replaces the
self-consistency check with a directional one -- every copy must equal the declared pin --
and CI adds the half that needs the network, re-fetching the pinned version and recomputing
its hash.

`crossorigin` is checked for the same reason it exists: a cross-origin script carrying
`integrity` without `crossorigin="anonymous"` is not merely unverified, it fails to load.
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIN_FILE = ROOT / "gsap-pin.json"

# Sites whose tags must track the pin. `example/` and `CHANGELOG.md` are records and are
# excluded on purpose -- gsap-pin.json § excluded states why, so the reason survives here.
AUTHORED = sorted(ROOT.glob("templates/*.html")) + [
    ROOT / "workflows" / "phase-3-design.md",
    ROOT / "workflows" / "phase-4-production.md",
]

# Prose docs. These must *defer* to the pin rather than restate it — see the test below.
# CHANGELOG.md and example/ are records and are deliberately absent.
PROSE = [
    ROOT / "CLAUDE.md",
    ROOT / "README.md",
    ROOT / ".github" / "copilot-instructions.md",
    ROOT / "SKILL.md",
    ROOT / "AGENTS.md",
]

GSAP_TAG = re.compile(r"<script\b[^>]*\bgsap@[^>]*>")
TAG_VERSION = re.compile(r"gsap@([0-9][0-9.]*)/dist/gsap\.min\.js")
VERSION_MENTION = re.compile(r"gsap@([0-9][0-9.]*)")


def attr(name, tag):
    match = re.search(rf'{name}="([^"]*)"', tag)
    return match.group(1) if match else None


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def rel(path):
    return str(path.relative_to(ROOT))


def tags():
    """(file, tag) for every authored GSAP script tag."""
    found = []
    for path in AUTHORED:
        for tag in GSAP_TAG.findall(read(path)):
            found.append((path, tag))
    return found


class GsapPinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pin = json.loads(PIN_FILE.read_text(encoding="utf-8"))
        cls.tags = tags()

    def test_the_pin_declares_a_plausible_version_and_hash(self):
        self.assertRegex(self.pin["version"], r"^\d+\.\d+\.\d+$")
        self.assertRegex(self.pin["integrity"], r"^sha384-[A-Za-z0-9+/]{60,}=*$")
        self.assertEqual("anonymous", self.pin["crossorigin"])

    def test_the_authored_sites_are_actually_found(self):
        """Guard on the guard. A template rename or a skeleton rewritten to load GSAP
        differently would empty this list, and every assertion below would pass on
        nothing. Ten tags today: seven templates plus three workflow skeletons."""
        self.assertGreaterEqual(
            len(self.tags), 10,
            f"only {len(self.tags)} GSAP tags found across {len(AUTHORED)} authored files — "
            "the scan lost sites rather than the sites losing GSAP",
        )

    def test_every_tag_carries_the_pinned_version(self):
        wrong = []
        for path, tag in self.tags:
            found = TAG_VERSION.search(tag)
            if not found:
                wrong.append(f"{rel(path)}: tag has no parseable gsap version: {tag[:80]}")
            elif found.group(1) != self.pin["version"]:
                wrong.append(f"{rel(path)}: gsap@{found.group(1)}, pin says {self.pin['version']}")
        self.assertEqual([], wrong, "authored tags disagree with the pin:\n  " + "\n  ".join(wrong))

    def test_every_tag_carries_the_pinned_integrity_hash(self):
        wrong = []
        for path, tag in self.tags:
            got = attr("integrity", tag)
            if got != self.pin["integrity"]:
                wrong.append(f"{rel(path)}: integrity={got!r}")
        self.assertEqual(
            [], wrong,
            "a stale or missing SRI hash makes the browser refuse GSAP and every scene "
            "renders without animation:\n  " + "\n  ".join(wrong),
        )

    def test_every_tag_sets_crossorigin_anonymous(self):
        """Not cosmetic: `integrity` on a cross-origin script requires a CORS request.
        Without `crossorigin`, the script does not load at all."""
        wrong = [
            f"{rel(path)}: crossorigin={attr('crossorigin', tag)!r}"
            for path, tag in self.tags
            if attr("crossorigin", tag) != self.pin["crossorigin"]
        ]
        self.assertEqual([], wrong, "SRI without crossorigin blocks the load:\n  " + "\n  ".join(wrong))

    def test_no_live_doc_restates_the_version(self):
        """Docs point at the pin; they do not copy it.

        This is the single-sourcing rule made checkable. The ten `<script>` tags have
        to carry literals — a template is copied verbatim into a generated project and
        cannot read a variable — but a *doc* has no such excuse, and a doc that names
        `gsap@3.x.y` is one more thing to remember during a bump and the first thing
        to go stale after it. Write `gsap@$V`, or name `gsap-pin.json`.

        Records are exempt and stay out of PROSE: CHANGELOG.md describes the tree at
        release time, and example/ is a record of a render that happened.
        """
        restated = []
        for path in PROSE:
            for version in sorted(set(VERSION_MENTION.findall(read(path)))):
                restated.append(
                    f"{rel(path)}: hard-codes gsap@{version} — defer to gsap-pin.json instead"
                )
        self.assertEqual(
            [], restated,
            "a live doc restates the pin instead of pointing at it:\n  " + "\n  ".join(restated),
        )

    def test_the_recompute_command_targets_the_pinned_url(self):
        """The bump instruction and the pin cannot drift apart: the command a human runs
        has to fetch the artifact the pin describes."""
        url = self.pin["url"].replace("{version}", self.pin["version"])
        self.assertIn(url, self.pin["recompute"].replace("{version}", self.pin["version"]))
        self.assertIn("sha384", self.pin["recompute"])


if __name__ == "__main__":
    unittest.main()
