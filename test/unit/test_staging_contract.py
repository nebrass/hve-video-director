"""The staging contract: a frame has to be lit, and it has to keep moving.

This exists because of a measurement, not a preference. Across the committed reference
build -- eight scenes, 60 seconds -- every scene grounded on a **centred** radial gradient
while every card shadow carried a **zero x-offset**. A centred ground plus a straight-down
shadow is the visual signature of no light at all: the object has a drop shadow instead of
a direction. `transformOrigin` appeared in a camera move exactly **zero** times, so every
camera scaled about `50% 50%`, which enlarges the picture without changing what is in front
of what.

The knowledge was already here. `templates/scene-screenshot.html` shipped the correct
`transformOrigin: "32% 28%"` pattern *in a comment*, and it was used nowhere. `grain-overlay`
is recommended in Phase 4 and used nowhere. That is the finding this suite protects: advice
a builder does not receive in its packet is not a rule, and a demonstration commented out is
not a demonstration.

So the contract lives in the two channels that reach a builder -- `sub-agents/scene-builder-delta.md`
(the role, packet item 4) and the scene skeletons (the starting point) -- and this file holds
both to it. Nothing here is a taste judgement: every assertion is a checkable authoring fact,
which is what ADR-010 constraint 2 requires of anything that directs execution.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = sorted((ROOT / "templates").glob("scene-*.html"))
DELTA = ROOT / "sub-agents" / "scene-builder-delta.md"

# A ground gradient positioned dead-centre horizontally. `at 50% <y>` is the tell.
CENTRED_GROUND = re.compile(r"radial-gradient\([^)]*\bat\s+50%\s", re.I)

# A shadow layer: <x> <y> <blur> [spread] rgba(...). Inset layers and hairline rings
# (0 0 0 1px) are not elevation and are excluded before the offset check.
#
# The unit is optional on purpose. A zero offset is almost always written bare -- `0 2px 6px`
# is the idiomatic form, and it is exactly how the defect appears. Requiring `px` on all three
# made this regex match only the *fixed* shadows, so the check passed on a reverted tree.
# Caught by mutation, not by review.
SHADOW_BLOCK = re.compile(r"box-shadow\s*:\s*([^;}]+)", re.I)
LAYER = re.compile(r"(-?[\d.]+)(?:px)?\s+(-?[\d.]+)(?:px)?\s+(-?[\d.]+)(?:px)?")


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def rel(path):
    return str(path.relative_to(ROOT))


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def elevation_layers(block):
    """Layers that actually cast: not inset, and with a non-zero blur."""
    layers = []
    for piece in block.split(","):
        if "inset" in piece:
            continue
        found = LAYER.search(piece)
        if not found:
            continue
        x, y, blur = (float(v) for v in found.groups())
        if blur == 0:  # a hairline ring, not elevation
            continue
        layers.append((x, y, blur))
    return layers


class StagingContractTests(unittest.TestCase):
    def test_there_are_templates_to_check(self):
        """Guard on the guard: a rename would empty this and pass everything."""
        self.assertGreaterEqual(len(TEMPLATES), 7, f"only found {len(TEMPLATES)} scene skeletons")

    def test_no_skeleton_ships_a_horizontally_centred_ground(self):
        """`at 50% <y>` says the light is nowhere. Every skeleton that paints a ground
        declares an off-axis origin instead, so a builder copies a lit frame."""
        centred = []
        for path in TEMPLATES:
            body = strip_comments(read(path))
            for match in CENTRED_GROUND.findall(body) or []:
                centred.append(f"{rel(path)}: {match.strip()[:60]}…")
            if CENTRED_GROUND.search(body):
                centred.append(f"{rel(path)}: ground gradient is centred at 50%")
        self.assertEqual(
            [], sorted(set(centred)),
            "a skeleton grounds on a centred radial — combined with a straight-down shadow "
            "that is the signature of an unlit frame:\n  " + "\n  ".join(sorted(set(centred))),
        )

    def test_every_elevation_shadow_declares_a_direction(self):
        """At least one casting layer per raised surface carries a non-zero x-offset.

        Zero-x on every layer means the light is directly overhead in a frame whose
        ground says otherwise. Hairline rings (0 0 0 1px) and inset grazes are excluded
        -- neither is elevation.
        """
        flat = []
        for path in TEMPLATES:
            body = strip_comments(read(path))
            for block in SHADOW_BLOCK.findall(body):
                layers = elevation_layers(block)
                if not layers:
                    continue
                if all(x == 0 for x, _, _ in layers):
                    flat.append(f"{rel(path)}: {' '.join(block.split())[:70]}…")
        self.assertEqual(
            [], flat,
            "a raised surface casts straight down, so it reads as a sticker rather than "
            "a lit object:\n  " + "\n  ".join(flat),
        )

    def test_a_camera_move_example_names_its_origin(self):
        """Every `scale:` example in a skeleton -- commented or live -- carries a
        `transformOrigin`. The reference build used none, and the reason is visible
        here: the only place the pattern appeared was a comment beside examples that
        did not use it."""
        missing = []
        for path in TEMPLATES:
            for number, line in enumerate(read(path).splitlines(), 1):
                if not re.search(r"\bscale:\s*[\d.]", line):
                    continue
                if "transformOrigin" in line:
                    continue
                missing.append(f"{rel(path)}:{number}: {line.strip()[:70]}…")
        self.assertEqual(
            [], missing,
            "a camera-move example scales about the default 50% 50%, which enlarges the "
            "picture without changing what is in front of what:\n  " + "\n  ".join(missing),
        )

    def test_the_builder_role_carries_the_staging_rules(self):
        """The skeletons demonstrate; the delta is what makes it binding. A builder
        that starts from a registry block instead of a skeleton still reads this."""
        body = read(DELTA)
        for phrase, why in (
            ("light direction", "declare one light and make ground, shadows and edges obey it"),
            ("x-offset", "a shadow without one has no direction"),
            ("transformOrigin", "a camera move points at something"),
            ("seam owns it", "the exit is the seam's, which is why a frozen tail is invisible"),
            ("grain", "static atmosphere is not motion and costs nothing"),
            ("preserve-3d", "a filter there collapses translateZ"),
        ):
            self.assertIn(phrase, body, f"the builder delta no longer says: {why}")

    def test_the_staging_rules_do_not_license_decoration(self):
        """The one way this becomes slop. `grammar/motion.md` bans idle wobble and
        `patterns/anti-slop.md` bans motion that fills silence; the delta has to carry
        that ban next to the permission, or a builder reads 'atmosphere' as 'shimmer'."""
        body = read(DELTA)
        self.assertRegex(
            body, r"stays banned|is banned|banned outright",
            "the staging section no longer refuses ambient decoration — without that "
            "sentence 'add atmosphere' reads as 'add a pulse'",
        )


if __name__ == "__main__":
    unittest.main()
