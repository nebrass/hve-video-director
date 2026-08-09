"""Execution notes are a second frame vocabulary, and a capped one (ADR-010).

A director key answers "what should the viewer understand". An execution note answers "how is
this already-decided frame realized". The set of keys is closed at fourteen and verified by
arithmetic; notes are open by design, which is exactly why they need a different bound.

The bound is registration. `reasoning/scene-analysis.md` § Execution notes is the whole list,
and this file is what makes the list mean something. Without it the category is a back door:
the next thing that wants to reach a builder writes itself onto a frame, cites the precedent,
and the vocabulary that was closed at fourteen grows sideways where no test is looking.

The category was not invented by ADR-010 — it was *found*. `grammar/three-taxonomy.md` has told
frames to carry a surface reading since M1, correctly and unrecorded, while
`test_director_keys.py` asserted the storyboard template is "the only surface a key is ever
written on". ADR-010 recorded it and capped it; this suite holds the cap.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SCENE_ANALYSIS = ROOT / "reasoning" / "scene-analysis.md"
GRAMMARS = sorted((ROOT / "grammar").glob("*.md"))

REGISTRY_HEADING = "### Execution notes"
KEY_SECTION = "## Director keys — the closed contract"

# A line that tells a frame to carry something. The scan is scoped to these because a
# `key: value` token anywhere else is prose, a CSS property, or a brief field.
INSTRUCTS_FRAME = re.compile(
    r"\bon(?:to)? (?:a |the |an )?[\w`: -]*frame\b|\bthe packet carries\b|\bwrite[s]? .*frame\b",
    re.I,
)
# `foo_bar:` or `foo_bar: value`, inside backticks.
FRAME_KEY_TOKEN = re.compile(r"`([a-z][a-z0-9_]*):(?:\s[^`]*)?`")


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def rel(path):
    return str(path.relative_to(ROOT))


def section(text, heading, stop=("\n## ", "\n### ")):
    start = text.index(heading)
    rest = text[start + len(heading):]
    cut = min(
        [rest.index(marker) for marker in stop if marker in rest] or [len(rest)]
    )
    return rest[:cut]


# Vocabulary cells separate their values with escaped pipes (`a` \| `b`), so a naive
# split on "|" truncates them mid-cell. Same convention test_compat_pointers uses.
ROW_SPLIT = re.compile(r"(?<!\\)\|")


def registry_rows():
    """(note, owner, trigger, vocabulary) from the registry table, backticks stripped."""
    body = section(read(SCENE_ANALYSIS), REGISTRY_HEADING)
    rows = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in ROW_SPLIT.split(stripped.strip("|"))]
        if len(cells) < 4 or set("".join(cells)) <= set("-: "):
            continue
        note = cells[0].strip("` ")
        if not re.fullmatch(r"[a-z][a-z0-9_]*:", note):
            continue
        rows.append((note, cells[1], cells[2], cells[3]))
    return rows


def director_keys():
    """The closed fourteen, from their own table."""
    body = section(read(SCENE_ANALYSIS), KEY_SECTION, stop=("\n### ",))
    keys = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        first = stripped.strip("|").split("|")[0].strip().strip("` ")
        if re.fullmatch(r"[a-z][a-z0-9_]*:", first):
            keys.append(first)
    return keys


class ExecutionNoteRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = registry_rows()
        cls.keys = director_keys()

    def test_the_registry_exists_and_parses(self):
        """Guard on the guard: an emptied registry would make every check below
        pass on nothing, which is the failure this whole file is about."""
        self.assertTrue(self.rows, "the execution-note registry parsed to nothing")

    def test_the_director_keys_still_parse(self):
        self.assertEqual(
            14, len(self.keys),
            f"parsed {len(self.keys)} director keys, expected the closed fourteen: {self.keys}",
        )

    def test_no_note_collides_with_a_director_key(self):
        """ADR-010 constraint 6. A colliding name is reinterpreted by the upstream
        storyboard parser as its own field and silently loses its meaning."""
        collisions = [note for note, *_ in self.rows if note in self.keys]
        self.assertEqual([], collisions, f"execution note collides with a director key: {collisions}")

    def test_every_row_declares_owner_trigger_and_vocabulary(self):
        """ADR-010 constraint 5. A row missing any of the three is a note nobody
        can apply, audit, or retire."""
        incomplete = [
            f"{note} (owner={owner!r} trigger={trigger!r} vocab={vocab!r})"
            for note, owner, trigger, vocab in self.rows
            if not (owner.strip() and trigger.strip() and vocab.strip())
        ]
        self.assertEqual([], incomplete, "incomplete registry row(s):\n  " + "\n  ".join(incomplete))

    def test_every_declared_owner_file_exists(self):
        missing = []
        for note, owner, *_ in self.rows:
            paths = re.findall(r"`((?:grammar|reasoning|patterns)/[A-Za-z0-9_.-]+)`", owner)
            if not paths:
                missing.append(f"{note}: owner names no repo file ({owner!r})")
                continue
            missing.extend(
                f"{note}: owner {path} does not exist" for path in paths if not (ROOT / path).exists()
            )
        self.assertEqual([], missing, "\n  ".join(missing))

    def test_the_surface_reading_precedent_is_registered(self):
        """The note ADR-010 was written for. If a future edit deletes it from
        three-taxonomy.md the registry should go with it — but silently losing the
        registration while the grammar still emits it is the drift to catch."""
        notes = [note for note, *_ in self.rows]
        taxonomy = read(ROOT / "grammar" / "three-taxonomy.md")
        emits = "surface reading" in taxonomy.lower()
        registered = "surface_reading:" in notes
        self.assertEqual(
            emits, registered,
            "three-taxonomy.md emits a surface reading but the registry does not list it "
            f"(emits={emits}, registered={registered})",
        )

    def test_a_registered_vocabulary_matches_the_owning_grammar(self):
        """The registry restates a vocabulary, so it can drift from its owner."""
        problems = []
        for note, owner, _, vocab in self.rows:
            values = re.findall(r"`([a-z][a-z0-9-]*)`", vocab)
            if not values:
                continue
            for path in re.findall(r"`((?:grammar|reasoning|patterns)/[A-Za-z0-9_.-]+)`", owner):
                text = read(ROOT / path)
                problems.extend(
                    f"{note}: `{value}` is not in {path}"
                    for value in values if f"`{value}`" not in text
                )
        self.assertEqual([], problems, "registry vocabulary drifted from its owner:\n  " + "\n  ".join(problems))

    def test_no_grammar_writes_an_unregistered_note_onto_a_frame(self):
        """The failure this file exists to stop, and the first version could not see it.

        Registration was checked registry->world only: every row well-formed, nothing
        looking the other way. So a grammar could add "write `parallax_bed: shallow` onto
        the frame so the builder receives it" and the suite stayed green -- exactly the
        sideways growth ADR-010 caps.

        Scoped to lines that actually instruct a frame to carry something (they name the
        frame or the packet), because a `key: value` token elsewhere is prose or CSS.
        """
        registered = {note for note, *_ in self.rows}
        allowed = registered | set(self.keys)
        offenders = []
        for path in GRAMMARS + sorted((ROOT / "patterns").glob("*.md")):
            for number, line in enumerate(read(path).splitlines(), 1):
                if not INSTRUCTS_FRAME.search(line):
                    continue
                for token in FRAME_KEY_TOKEN.findall(line):
                    if f"{token}:" in allowed or token in {k.rstrip(":") for k in allowed}:
                        continue
                    offenders.append(
                        f"{rel(path)}:{number}: writes `{token}:` onto a frame, and it is "
                        "neither a director key nor a registered execution note"
                    )
        self.assertEqual(
            [], sorted(set(offenders)),
            "an unregistered note reaches a builder:\n  " + "\n  ".join(sorted(set(offenders))),
        )

    def test_the_registered_note_is_written_as_a_literal_by_its_owner(self):
        """A registry row naming `surface_reading:` while its owner only says "state it"
        leaves a builder knowing a value and not the key it goes under."""
        missing = []
        for note, owner, *_ in self.rows:
            for path in re.findall(r"`((?:grammar|reasoning|patterns)/[A-Za-z0-9_.-]+)`", owner):
                if note not in read(ROOT / path):
                    missing.append(f"{note} is registered but {path} never writes the literal")
        self.assertEqual([], missing, "\n  ".join(missing))

    def test_the_registry_states_its_own_rules(self):
        """The constraints are the category's cap. A registry that lists notes but
        drops the rules becomes a place to add things.

        Structural first: ADR-010 states six, so six numbered rules must be present.
        The keyword pass is a weaker secondary signal — it catches a rule deleted
        outright, not a rule reworded, which is the correct sensitivity for prose.
        """
        body = section(read(SCENE_ANALYSIS), REGISTRY_HEADING)
        numbered = [int(n) for n in re.findall(r"^(\d+)\.\s", body, re.M)]
        self.assertEqual(
            [1, 2, 3, 4, 5, 6], numbered,
            f"the registry lists {numbered} rules; ADR-010 states six, and each one is "
            "load-bearing — dropping any turns the cap into a suggestion",
        )
        for phrase, why in (
            ("ADR-010", "the record that authorises the category"),
            ("derivation", "constraint 1 — notes never derive"),
            ("authoring fact", "constraint 2 — no taste triggers"),
            ("budget", "constraint 3 — never counted, never exempted"),
            ("packet", "constraint 4 — a note must reach the builder"),
        ):
            self.assertIn(phrase, body, f"the registry no longer states {why}")


if __name__ == "__main__":
    unittest.main()
