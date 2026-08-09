"""Tilt caps, and the Q7 → tag mapping. Both were gaps that reviewing could not see.

**Tilt.** The mockup tilt limits are stated at five live sites. Until now they covered two
axes -- `rotateY` and `rotateZ` -- while `patterns/visual-patterns.md` sanctioned a worked
example using `rotateX(3deg)`, an axis no cap governed, and two design-system presets said
"Tilt <= 3 deg" naming no axis at all. Nothing was wrong at any single site; the *set* had a
hole, which is what an unguarded five-site duty produces. SKILL_HOMES, the GSAP pin and the
voice tables each drifted the same way before they were guarded.

So: every site that states a cap states all three axes, and states the same number for each.
A brand may narrow a cap further -- that is a legitimate brand decision -- but it must name
the axis it is narrowing, because "tilt <= 3 deg" leaves a builder to pick which rotation it
governs.

**Q7.** Question 7 asks whether a frame needs spatial reasoning and has no key of its own; its
answer becomes a capability tag and nowhere else. The rule said "the spatial tag it names"
without naming the mapping, so the one step that turns a yes/no into a tag was left to be
re-read at each frame -- the taste-shaped hole in a derivation ADR-005 requires to be
mechanical. The table is the fix, and this suite keeps it consistent with the catalog.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Live sites that state the caps. `docs/` is a frozen M1 snapshot and `example/` is a record
# of a render that happened; neither tracks a later decision.
CAP_SITES = [
    ROOT / "grammar" / "camera.md",
    ROOT / "patterns" / "visual-patterns.md",
    ROOT / "CLAUDE.md",
    ROOT / ".github" / "copilot-instructions.md",
]

AXES = ("rotateY", "rotateX", "rotateZ")
EXPECTED_CAPS = {"rotateY": 8, "rotateX": 4, "rotateZ": 4}

# "`rotateY` ≤ 8°" / "≤8° `rotateY`" — both orders appear, both are fine.
CAP_AFTER = re.compile(r"`(rotate[XYZ])`\s*≤\s*(\d+)\s*°")
CAP_BEFORE = re.compile(r"≤\s*(\d+)\s*°\s*`(rotate[XYZ])`")

SCENE_ANALYSIS = ROOT / "reasoning" / "scene-analysis.md"
CATALOG = ROOT / "reasoning" / "capability-catalog.md"


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def rel(path):
    return str(path.relative_to(ROOT))


def caps_in(text):
    """{axis: degrees} for every cap stated in a file."""
    found = {}
    for axis, degrees in CAP_AFTER.findall(text):
        found.setdefault(axis, set()).add(int(degrees))
    for degrees, axis in CAP_BEFORE.findall(text):
        found.setdefault(axis, set()).add(int(degrees))
    return found


class TiltCapTests(unittest.TestCase):
    def test_the_cap_sites_still_state_caps(self):
        """Guard on the guard: a rewording that stopped matching would silently
        turn every assertion below into a check on an empty dict."""
        stating = [path for path in CAP_SITES if caps_in(read(path))]
        self.assertEqual(
            len(CAP_SITES), len(stating),
            f"only {len(stating)} of {len(CAP_SITES)} sites state a tilt cap in a "
            "recognisable form",
        )

    def test_every_site_covers_all_three_axes(self):
        """The original gap: rotateX was used in a sanctioned example and capped nowhere."""
        gaps = []
        for path in CAP_SITES:
            found = caps_in(read(path))
            for axis in AXES:
                if axis not in found:
                    gaps.append(f"{rel(path)}: no cap for `{axis}`")
        self.assertEqual(
            [], gaps,
            "an axis is usable and uncapped — a limit that names two of three rotations "
            "reads as permission for the third:\n  " + "\n  ".join(gaps),
        )

    def test_every_site_states_the_same_number_for_each_axis(self):
        wrong = []
        for path in CAP_SITES:
            for axis, degrees in sorted(caps_in(read(path)).items()):
                if degrees != {EXPECTED_CAPS[axis]}:
                    wrong.append(
                        f"{rel(path)}: `{axis}` capped at {sorted(degrees)}°, "
                        f"expected {EXPECTED_CAPS[axis]}°"
                    )
        self.assertEqual([], wrong, "tilt caps diverged:\n  " + "\n  ".join(wrong))

    def test_a_preset_that_narrows_a_cap_names_the_axis(self):
        """A brand may narrow; it may not leave the axis to the builder's guess."""
        vague = []
        for preset in sorted((ROOT / "design-systems").glob("*/DESIGN.md")):
            for number, line in enumerate(read(preset).splitlines(), 1):
                if not re.search(r"\btilt(?:ed)?\b", line, re.I):
                    continue
                if re.search(r"\bon [XYZ]\b|rotate[XYZ]", line):
                    continue
                vague.append(f"{rel(preset)}:{number}: {line.strip()[:70]}…")
        self.assertEqual(
            [], vague,
            "a preset states a tilt limit without naming the axis it governs:\n  "
            + "\n  ".join(vague),
        )


class Q7MappingTests(unittest.TestCase):
    """Q7's answer becomes a tag here and nowhere else, so the mapping is the derivation."""

    def _mapping_rows(self):
        text = read(SCENE_ANALYSIS)
        start = text.index("**Q7 → the tag it names.**")
        end = text.index("`spatial-depth` is the common answer", start)
        rows = []
        past_header = False
        for line in text[start:end].splitlines():
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) != 2:
                continue
            # The separator line divides the header from the body. Without this the
            # header cell "Tag" is read as a tag and checked against the catalog.
            if set("".join(cells)) <= set("-: "):
                past_header = True
                continue
            if not past_header:
                continue
            rows.append((cells[0], cells[1].strip("`* ")))
        return rows

    def test_the_mapping_exists_and_has_an_escape_row(self):
        rows = self._mapping_rows()
        self.assertGreaterEqual(len(rows), 4, f"Q7 mapping parsed to {rows}")
        self.assertTrue(
            any("no tag" in tag.lower() for _, tag in rows),
            "the mapping has no 'none of the above' row, so every yes is forced to a tag",
        )

    def test_every_mapped_tag_is_in_the_catalog_vocabulary(self):
        """ADR-005: tags come from the catalog. A mapping that invents one would put
        a tag into derivation that no runtime row serves."""
        catalog = read(CATALOG)
        unknown = [
            tag for _, tag in self._mapping_rows()
            if "no tag" not in tag.lower() and f"`{tag}`" not in catalog
        ]
        self.assertEqual([], unknown, f"Q7 maps to tags outside the catalog: {unknown}")

    def test_the_mapping_does_not_restate_the_self_occlusion_discriminator(self):
        """ADR-002 in miniature: `grammar/three-taxonomy.md` owns the spatial-depth vs
        topology-3d rule. The table may point at it; a second copy would drift."""
        text = read(SCENE_ANALYSIS)
        start = text.index("**Q7 → the tag it names.**")
        section = text[start:start + 1800]
        self.assertIn(
            "grammar/three-taxonomy.md", section,
            "the Q7 mapping no longer cites the owner of the self-occlusion discriminator",
        )


if __name__ == "__main__":
    unittest.main()
