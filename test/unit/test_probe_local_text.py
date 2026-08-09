"""Behaviour probes: the registry says where its local text lives, and that text exists.

`compat/ecosystem.md` § Behavior probes registers upstream behaviours this skill depends on
that **no upstream file documents** — the case ADR-002 § Precedence governs. The clause says
the dependency must be registered, and registration was enforced in one direction only:
`test_compat_pointers.py` proves a registered *path* resolves upstream, and nothing looked
the other way.

A reverse scan of the repo for "an imperative about undocumented upstream behaviour" was
designed and then rejected on measurement, not taste. Built as a keyword/proximity lint it
scored **0% recall line-scoped** (it missed all three real instances, because "hf-seek carries
the ROOT clock" contains no imperative keyword) and **~9% precision paragraph-scoped**, against
776 imperative-bearing lines and 8 probes. `test_motion_register.py` already set this repo's
written noise standard at one finding in eight scenes; a prose lint fails it thirtyfold, and a
guard that fires on correct work gets deleted.

What is checkable is *structure*, and it turns out five of the eight probes already declared
their local text in prose without being asked. This makes that house practice a field:

    - **Local text.** `path/to/file.md`, `scripts/thing.py`
    - **Local text.** none — a clearance, not an imperative.

Then two deterministic assertions: every probe declares the field, and every path it names
exists. Zero heuristics, zero false positives.

What this does NOT do, stated plainly because the gap is easy to think closed: it cannot find
an *unregistered* dependency. That is unbuildable at acceptable noise. The mechanism for it is
procedural — § Pin and update policy step 5 walks every probe at each lock bump — and the one
unregistered instance in the tree was found by a human reading, not by a scan. It is now
registered as `CLIP_KEYFRAME_DENSITY`.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPAT = ROOT / "compat" / "ecosystem.md"

PROBE_HEADING = re.compile(r"^### `([A-Z][A-Z0-9_]+)`", re.M)
LOCAL_TEXT = re.compile(r"^- \*\*Local text\.\*\*\s*(.+?)(?=\n- \*\*|\n\n|\Z)", re.M | re.S)
REPO_PATH = re.compile(r"`((?:scripts|workflows|patterns|templates|sub-agents|reasoning|grammar)/[A-Za-z0-9_*./-]+)`")


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def probes():
    """{symbol: entry text} for every § Behavior probes entry."""
    text = read(COMPAT)
    section = text[text.index("## Behavior probes"):]
    section = section.split("\n## ", 1)[0]
    found = {}
    marks = [(m.group(1), m.start()) for m in PROBE_HEADING.finditer(section)]
    for index, (symbol, start) in enumerate(marks):
        end = marks[index + 1][1] if index + 1 < len(marks) else len(section)
        found[symbol] = section[start:end]
    return found


class ProbeLocalTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probes = probes()

    def test_the_probe_section_parses(self):
        """Guard on the guard: a heading style change would empty this and make every
        assertion below true of nothing."""
        self.assertGreaterEqual(
            len(self.probes), 8, f"parsed only {sorted(self.probes)}"
        )

    def test_every_probe_declares_where_its_local_text_lives(self):
        """ADR-002 § Precedence permits a narrowing imperative *because* the dependency
        is registered. A row that does not say which file holds the imperative leaves an
        auditor reading that file with no way back to the clause that permits it."""
        missing = sorted(s for s, body in self.probes.items() if not LOCAL_TEXT.search(body))
        self.assertEqual(
            [], missing,
            "probe(s) with no `- **Local text.**` field — write the paths, or write "
            f"`none` and say why: {missing}",
        )

    def test_every_declared_path_exists(self):
        """The half that rots. A probe outlives the file that held its imperative, or
        the imperative moves, and the row keeps pointing at nothing."""
        gone = []
        for symbol, body in sorted(self.probes.items()):
            field = LOCAL_TEXT.search(body)
            if not field:
                continue
            for path in REPO_PATH.findall(field.group(1)):
                if "*" in path:
                    matches = list(ROOT.glob(path))
                    if not matches:
                        gone.append(f"{symbol}: `{path}` matches nothing")
                elif not (ROOT / path).exists():
                    gone.append(f"{symbol}: `{path}` does not exist")
        self.assertEqual([], gone, "probe local text points at missing files:\n  " + "\n  ".join(gone))

    def test_a_probe_claiming_no_local_text_says_why(self):
        """`none` alone reads as "not filled in yet". The distinction that matters is
        between a clearance (upstream says do this) and an imperative (we narrow it),
        and only the second is what ADR-002 § Precedence is about."""
        bare = []
        for symbol, body in sorted(self.probes.items()):
            field = LOCAL_TEXT.search(body)
            if not field:
                continue
            value = " ".join(field.group(1).split())
            if value.lower().startswith("none") and len(value) < 25:
                bare.append(f"{symbol}: `{value}`")
        self.assertEqual([], bare, "a probe says `none` without a reason:\n  " + "\n  ".join(bare))

    def test_the_pin_bump_procedure_walks_the_probes(self):
        """The procedural half, and the one that actually closes ADR-002's loop.

        Six of the eight probes are manual, and each stated its own re-read duty inside
        its own entry — where an auditor reads the map, not where a maintainer takes a
        lock bump. The update procedure had five steps and none of them was "walk the
        probes", so every one of those duties was reachable by nobody.
        """
        text = read(COMPAT)
        policy = text[text.index("## Pin and update policy"):]
        policy = policy.split("\n## ", 1)[0]
        self.assertRegex(
            policy, r"Behavior probes",
            "the update procedure no longer walks § Behavior probes — the manual probes' "
            "re-read duties become unreachable again",
        )


if __name__ == "__main__":
    unittest.main()
