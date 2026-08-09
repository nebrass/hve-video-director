"""The frame-packet contract, which is the reason builder context stays bounded.

A scene builder sees a packet and nothing else. The packet is exactly five items, and it
carries no `reasoning/` or `grammar/` file — those produced the director keys, and the keys
*are* the conclusion, so shipping the derivation beside them is what makes builder context
unbounded (ADR-004).

Until now this was the only major invariant in the repo with no test. The closed key set has
one. The tag vocabulary has three. The GSAP pin, SKILL_HOMES, the voice tables, storyboard
extra keys, instruction parity, compat pointers -- all guarded. "A packet carries exactly five
things" was stated at five sites and enforced by nobody.

It will not be breached in one visible line. It gets breached as a sixth item that seemed
useful, or as a count that says six in one file and five in the others, or as a "just for
context" grammar reference in the builder role -- each diff hunk reasonable on its own, CI
green throughout, and the property discovered gone later as "why are scene builds timing out
on a nine-frame film". CLAUDE.md names the failure in advance: *adding "just a little" grammar
context is the regression this rule exists to stop.*

The canonical definition is the numbered table in `workflows/phase-3-design.md` Step 3.3.
Everything else restates it, so everything else has to agree with it.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CANONICAL = ROOT / "workflows" / "phase-3-design.md"
RESTATEMENTS = [
    ROOT / "CLAUDE.md",
    ROOT / "SKILL.md",
    ROOT / "workflows" / "phase-4-production.md",
]

EXPECTED_ITEMS = 5

# Written-out numbers only: "exactly five things". A bare digit would match version
# numbers, step numbers and durations all over these files.
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}
COUNT_CLAIM = re.compile(
    r"(?:contains|carries|is)\s+(?:exactly\s+)?(" + "|".join(NUMBER_WORDS) + r")\s+(?:things|items)",
    re.I,
)

# The five items, by a keyword that identifies each without pinning the wording.
ITEM_KEYWORDS = (
    ("the frame's own storyboard block", ("storyboard block",)),
    ("the design spec", ("DESIGN.md",)),
    ("inlined recipe bodies", ("bodies",)),
    ("the builder role", ("FRAME_WORKER_CORE", "scene-builder-delta")),
    ("canvas / captions / capture paths", ("captions",)),
)


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def rel(path):
    return str(path.relative_to(ROOT))


def step_33():
    """The Step 3.3 section: canonical definition of a packet."""
    text = read(CANONICAL)
    start = text.index("## Step 3.3")
    end = text.index("## Step 3.4", start)
    return text[start:end]


class PacketContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.section = step_33()

    def test_the_canonical_table_enumerates_exactly_five_items(self):
        """Rows numbered 1..N in the Step 3.3 table. This is the definition; the
        count claims elsewhere are checked against it, not the other way round."""
        numbers = [int(n) for n in re.findall(r"^\|\s*(\d+)\s*\|", self.section, re.M)]
        self.assertTrue(numbers, "Step 3.3 has no numbered packet table — parse broke")
        self.assertEqual(
            list(range(1, EXPECTED_ITEMS + 1)), numbers,
            f"the packet table enumerates {numbers}, not 1..{EXPECTED_ITEMS}. Adding an "
            "item to a packet is an architecture change (ADR-004): it is paid on every "
            "frame, including the frames it does not apply to.",
        )

    def test_the_canonical_section_states_the_count_and_states_five(self):
        claims = COUNT_CLAIM.findall(self.section)
        self.assertTrue(
            claims,
            "Step 3.3 no longer states how many things a packet contains. The count is "
            "what makes a sixth item visible in review.",
        )
        for claim in claims:
            self.assertEqual(
                EXPECTED_ITEMS, NUMBER_WORDS[claim.lower()],
                f"Step 3.3 says a packet contains {claim!r}",
            )

    def test_every_restatement_agrees_on_the_count(self):
        """Scanned by paragraph, not by line.

        Found by mutating this suite: a line-scoped check that also required the word
        "packet" on the same line missed CLAUDE.md entirely, because it introduces the
        packet in one sentence and states the count in the next.
        """
        wrong = []
        for path in RESTATEMENTS:
            for paragraph in re.split(r"\n\s*\n", read(path)):
                if "packet" not in paragraph.lower():
                    continue
                for claim in COUNT_CLAIM.findall(paragraph):
                    if NUMBER_WORDS[claim.lower()] != EXPECTED_ITEMS:
                        first = paragraph.strip().splitlines()[0][:70]
                        wrong.append(f"{rel(path)}: says a packet has {claim!r} — {first}…")
        self.assertEqual(
            [], wrong,
            "a restatement disagrees with the canonical table:\n  " + "\n  ".join(wrong),
        )

    def test_the_canonical_table_names_all_five_items(self):
        """Guard against the count staying five while an item is swapped out."""
        missing = [
            label for label, keywords in ITEM_KEYWORDS
            if not any(keyword in self.section for keyword in keywords)
        ]
        self.assertEqual(
            [], missing,
            f"the packet table no longer names: {missing}. The count can stay at five "
            "while an item is quietly replaced.",
        )

    def test_the_exclusion_is_stated_where_the_packet_is_defined(self):
        """`reasoning/` and `grammar/` are named as excluded, at the definition."""
        for directory in ("reasoning/", "grammar/"):
            self.assertIn(
                directory, self.section,
                f"Step 3.3 no longer mentions {directory} — the exclusion that keeps "
                "builder context bounded has to be stated where a packet is assembled",
            )
        self.assertRegex(
            self.section, r"must\s+NOT\s+carry|never carries|carries no",
            "Step 3.3 states no exclusion at all",
        )

    def test_claude_md_carries_the_exclusion_and_cites_the_record(self):
        """The rule is only followable if a reader can find the decision behind it."""
        text = read(ROOT / "CLAUDE.md")
        window = [
            line for line in text.splitlines()
            if "reasoning/" in line and "grammar/" in line and "packet" in line.lower()
        ]
        self.assertTrue(
            window,
            "CLAUDE.md no longer states that a packet carries no reasoning/ or grammar/ file",
        )
        self.assertRegex(
            text, r"packet[^.]*ADR-004|ADR-004[^.]*packet",
            "the packet exclusion in CLAUDE.md no longer cites ADR-004",
        )

    def test_a_builder_is_told_it_opens_nothing_outside_the_packet(self):
        """The exclusion is only enforceable if the builder role says so too --
        otherwise a builder helpfully reads a grammar file nobody sent it.

        Two assertions, not one alternation. Found by mutating this suite: a single
        regex OR-ing three phrasings still passed after the prohibition was rewritten
        into a permission, because a different phrasing elsewhere in the file matched.
        Both the framing and the prohibition have to survive.
        """
        delta = read(ROOT / "sub-agents" / "scene-builder-delta.md")
        self.assertRegex(
            delta, r"your whole world|packet is your whole",
            "the builder delta no longer frames the packet as the builder's whole world",
        )
        self.assertRegex(
            delta, r"opens? nothing outside",
            "the builder delta no longer prohibits opening files outside the packet — "
            "framing alone is not a rule",
        )


if __name__ == "__main__":
    unittest.main()
