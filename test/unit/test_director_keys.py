#!/usr/bin/env python3
"""Docs-as-contract suite for the director keys and the capability vocabulary.

Phase 1 answers twelve questions per storyboard frame and writes the answers as
`- key: value` bullets. Three files have to agree about what those keys are:

* `reasoning/scene-analysis.md` **defines** them (the closed contract table);
* `templates/storyboard.md` **shows** them — it is the only surface on which a
  key is ever actually written;
* `workflows/phase-1-storytelling.md` **drives** the work that fills them in.

Drift between the three is how a key silently stops being written: renamed in
the definition, still shown in the template, and nobody notices until a builder
reads a frame that no longer carries its runtime rationale. Nothing else in the
repo can see that — the keys are prose, and upstream's storyboard parser
deliberately preserves unknown bullets under `extra` (`STORYBOARD_EXTRA_KEYS`),
so a misspelled key parses fine and means nothing.

Two contracts, plus a bound:

1. **Definition ↔ template is an equality.** Every defined key appears in the
   template and the template shows no key the contract does not define.
2. **Phase 1 is a subset, not a copy.** The workflow delegates the key list to
   the two files that own it and restates none of it — the repo's single-source
   rule (ADR-008/C6 for budgets, the same posture for vocabulary). So the
   workflow is checked for *staleness*, not coverage: every key it names must
   still exist, and it must still point at both owners. Demanding all fourteen
   here would force exactly the duplication the architecture forbids.
3. **The key set stays bounded.** Key sprawl is this milestone's named risk. The
   bound is derived, not chosen — see `KeySetIsClosed.test_key_set_is_bounded`.

And one vocabulary contract, from ADR-005: every capability tag declared by a
`grammar/` entry must be defined in `reasoning/capability-catalog.md`, which owns
and versions that vocabulary. Q11's derivation is the *union of the tags declared
by every grammar entry a frame cites*; an undefined tag therefore enters a
frame's capability set, matches no runtime row, and stops the derivation being
mechanical — silently, because no gate reads these tables.

Everything is derived from the four files themselves. Nothing here restates a
key name, a tag name, or a budget number.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCENE_ANALYSIS = ROOT / "reasoning" / "scene-analysis.md"
CATALOG = ROOT / "reasoning" / "capability-catalog.md"
TEMPLATE = ROOT / "templates" / "storyboard.md"
PHASE_1 = ROOT / "workflows" / "phase-1-storytelling.md"
GRAMMAR = sorted((ROOT / "grammar").glob("*.md"))

# The two section headings that own the key contract. Matched by prefix so the
# em-dash subtitle of the second one can be reworded without breaking the parse.
QUESTIONS_SECTION = "## The twelve questions"
CONTRACT_SECTION = "## Director keys"

FENCE = re.compile(r"^[ \t]*(?:```|~~~)")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
SEPARATOR = re.compile(r":?-{3,}:?")
# Markdown escapes a literal pipe inside a cell as `\|`; the `runtime:` row uses
# that form to list its alternatives, so a naive split would shred it.
ROW_SPLIT = re.compile(r"(?<!\\)\|")

# A director key: lowercase snake_case followed by the colon that is part of the
# name (`runtime_rejected:`). The trailing colon is deliberate — it is what makes
# a key distinguishable from an ordinary word in prose.
KEY_TOKEN = re.compile(r"[a-z][a-z0-9_]*:")
# A director-key bullet as scene-analysis.md mandates it: `- key: value`.
KEY_BULLET = re.compile(r"^[ \t]*[-*][ \t]+([a-z][a-z0-9_]*):")
# A capability tag: lowercase, hyphenated, no directory and no extension.
TAG_TOKEN = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)+")

# Column headers that declare capability tags. Grammar files use four different
# spellings for the same column — `capabilities` (camera), `Tags` (motion),
# `Requires` (metaphors), `Capability tags` / `Three-only tag` (three-taxonomy) —
# and the catalog re-uses the vocabulary under `Serves` and `Derived`. Matching
# the concept rather than one spelling is what lets a fifth table be added
# without editing this file. `\btags?\b` is word-anchored so a `Stage` column
# never matches.
TAG_COLUMN = re.compile(r"\btags?\b|capabilit|\bserves\b|\bderived\b|\brequires\b")

# Spelled-out counts the closed-set sentence could plausibly carry. The set is
# one key per question plus one ADR-001 override; a set outside this band has
# stopped being "closed" in any useful sense and needs an architecture review,
# not a wider map here.
NUMBER_WORDS = {
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20,
}
CLOSED_SET_COUNT = re.compile(r"\b([A-Za-z]+) key names\b")

# The one key the contract table carries that no question emits. ADR-001 puts it
# there: it records a user's explicit creative instruction overriding a derived
# verdict, which is a consent fact, not an answer to a question.
OVERRIDE_KEY = "user_directed:"


def rel(path):
    return str(Path(path).resolve().relative_to(ROOT))


def read(path):
    return Path(path).read_text(encoding="utf-8")


def iter_lines(path):
    """Yield (lineno, line, inside_fence) for a markdown file."""
    inside = False
    for number, line in enumerate(read(path).splitlines(), 1):
        if FENCE.match(line):
            inside = not inside
            continue
        yield number, line, inside


def section(path, heading_prefix):
    """Yield the lines under a `##` heading, sub-headings included.

    Only a sibling `## ` closes the section, so a `###` subsection (the ADR-001
    override note, the judgment-vs-derivation note) stays inside its parent.
    """
    inside = False
    for number, line, in_fence in iter_lines(path):
        if line.startswith("## "):
            inside = line.startswith(heading_prefix)
            continue
        if inside:
            yield number, line, in_fence


def split_row(line):
    body = line.strip()
    body = body[1:] if body.startswith("|") else body
    body = body[:-1] if body.endswith("|") else body
    return [cell.strip() for cell in ROW_SPLIT.split(body)]


def tables(lines):
    """Parse markdown tables out of an (lineno, line, in_fence) stream.

    Returns [(headers, [(cells, lineno), ...]), ...]. Headers are normalized —
    backticks, bold markers and case stripped — because the same column is
    spelled `` `capabilities` `` in one file and `Capability tags` in another.
    """
    out, headers, rows = [], None, []
    for number, line, in_fence in lines:
        stripped = line.strip()
        if in_fence or not stripped.startswith("|"):
            if headers is not None:
                out.append((headers, rows))
            headers, rows = None, []
            continue
        cells = split_row(stripped)
        if cells and all(SEPARATOR.fullmatch(c) for c in cells if c):
            continue  # the `|---|---|` separator row
        if headers is None:
            headers = [c.strip("*` ").lower() for c in cells]
        else:
            rows.append((cells, number))
    if headers is not None:
        out.append((headers, rows))
    return out


def column(headers, rows, predicate):
    """Yield (cell, lineno) for every column whose header satisfies `predicate`."""
    for index, header in enumerate(headers):
        if not predicate(header):
            continue
        for cells, number in rows:
            if index < len(cells):
                yield cells[index], number


def keys_in(text):
    """Backticked director keys inside a blob of markdown."""
    return {t for t in INLINE_CODE.findall(text) if KEY_TOKEN.fullmatch(t)}


def question_keys():
    """Keys emitted by the twelve questions (§ The twelve questions, Key column).

    Question 7 answers "*no key of its own*" — it feeds Q11 as an asset reality
    rather than landing on the frame — and contributes nothing, which falls out
    of the parse rather than needing a special case: the cell holds no backticked
    key. Rows 10 and 12 each name two alternatives in one cell; both are keys.
    """
    keys = {}
    for headers, rows in tables(section(SCENE_ANALYSIS, QUESTIONS_SECTION)):
        if "key" not in headers:
            continue
        for cell, number in column(headers, rows, lambda h: h == "key"):
            for key in keys_in(cell):
                keys.setdefault(key, number)
    return keys


def contract_rows():
    """(key, required, lineno) from § Director keys — the closed contract."""
    rows_out = []
    for headers, rows in tables(section(SCENE_ANALYSIS, CONTRACT_SECTION)):
        if headers[:2] != ["key", "required"]:
            continue
        for cells, number in rows:
            key = cells[0].strip("` ")
            if KEY_TOKEN.fullmatch(key):
                rows_out.append((key, cells[1].strip().lower(), number))
    return rows_out


def key_mentions(path):
    """Director keys a file emits or names, as {key: [lineno, ...]}.

    Two accepted forms, and only two:

    * a frame bullet — ``- goal: …`` — the form scene-analysis.md mandates for
      the storyboard itself;
    * a backticked mention — ``` `goal:` ``` — how prose refers to a key.

    Prose that merely happens to contain the word "goal:" is not a mention.
    Requiring one of the two forms is what stops a presence assertion from being
    satisfied by an accident, and what stops an absence assertion from firing on
    an ordinary sentence.
    """
    hits = {}
    for number, line, inside in iter_lines(path):
        if inside:
            continue
        bullet = KEY_BULLET.match(line)
        if bullet:
            hits.setdefault(f"{bullet.group(1)}:", []).append(number)
        for key in keys_in(line):
            hits.setdefault(key, []).append(number)
    return hits


def catalog_tags():
    """The tag vocabulary owned by capability-catalog.md (§ The tags)."""
    tags = {}
    inside = False
    for number, line, in_fence in iter_lines(CATALOG):
        if line.startswith("#"):
            inside = line.strip("# ").strip().lower() == "the tags"
            continue
        if in_fence or not inside or not line.lstrip().startswith("|"):
            continue
        cells = split_row(line)
        if len(cells) == 2 and cells[0].startswith("`"):
            tags.setdefault(cells[0].strip("` "), number)
    return tags


def declared_tags(path):
    """Capability tags declared by a file's tag columns, as [(tag, lineno)].

    A column declares its tags in one style, and the style is whichever the
    column itself uses: `grammar/metaphors.md` writes them bare (`spatial-depth,
    volumetric-count`), every other file backticks them. So the mode is decided
    per column, not per token — bare extraction inside a backticked column would
    read prose like "data-generated keyframes" as a tag, and backtick-only
    extraction would read the bare column as empty.
    """
    found = []
    for headers, rows in tables(iter_lines(path)):
        for index, header in enumerate(headers):
            if not TAG_COLUMN.search(header):
                continue
            cells = [(c[index], n) for c, n in rows if index < len(c)]
            backticked = any(INLINE_CODE.search(cell) for cell, _ in cells)
            for cell, number in cells:
                if backticked:
                    tokens = [
                        t for t in INLINE_CODE.findall(cell) if TAG_TOKEN.fullmatch(t)
                    ]
                else:
                    tokens = TAG_TOKEN.findall(cell)
                found.extend((token, number) for token in tokens)
    return found


class KeySetIsClosed(unittest.TestCase):
    def test_the_contract_table_parses(self):
        """A silently-empty parse would make every assertion below vacuous."""
        self.assertTrue(
            contract_rows(),
            f"{rel(SCENE_ANALYSIS)}: `{CONTRACT_SECTION}` produced no rows — the "
            f"closed-contract table moved or changed shape, and every director-key "
            f"assertion in this suite just stopped checking anything",
        )
        self.assertTrue(
            question_keys(),
            f"{rel(SCENE_ANALYSIS)}: `{QUESTIONS_SECTION}` produced no keys",
        )

    def test_every_question_key_is_declared_in_the_contract_table(self):
        contract = {key for key, _required, _line in contract_rows()}
        orphans = sorted(
            f"{rel(SCENE_ANALYSIS)}:{line}: `{key}`"
            for key, line in question_keys().items()
            if key not in contract
        )
        self.assertFalse(
            orphans,
            "a question emits a key the closed-contract table does not declare, "
            "so nothing downstream knows the key exists:\n  " + "\n  ".join(orphans),
        )

    def test_key_set_is_bounded(self):
        """Key sprawl is the named risk; the bound is derived, not chosen.

        scene-analysis.md states the bound itself: the keys are "emitted by the
        twelve questions plus the ADR-001 override". So the size of the set is
        not a number anyone picks — it is *one key per question answer, plus
        exactly one override key*. Adding a fifteenth key therefore requires
        adding a question, which the file calls an architecture change. Checked
        three ways: the extra key is exactly the override, the arithmetic holds,
        and the prose count agrees with the table it introduces.
        """
        contract = {key for key, _required, _line in contract_rows()}
        questions = set(question_keys())
        extra = contract - questions
        self.assertEqual(
            extra,
            {OVERRIDE_KEY},
            f"{rel(SCENE_ANALYSIS)}: the closed set may hold exactly one key no "
            f"question emits — `{OVERRIDE_KEY}` (ADR-001). Found "
            f"{sorted(extra) or 'none'}. A new key means a new question, which is "
            f"an architecture change reviewed as such, not a convenience",
        )
        self.assertEqual(
            len(contract),
            len(questions) + 1,
            f"{rel(SCENE_ANALYSIS)}: {len(contract)} keys for {len(questions)} "
            f"question keys plus one override",
        )

        match = CLOSED_SET_COUNT.search(read(SCENE_ANALYSIS))
        self.assertIsNotNone(
            match,
            f"{rel(SCENE_ANALYSIS)}: the closed-set sentence no longer states how "
            f"many key names there are, so the prose can drift from the table "
            f"unnoticed",
        )
        word = match.group(1).lower()
        self.assertIn(
            word,
            NUMBER_WORDS,
            f"{rel(SCENE_ANALYSIS)}: closed-set count {match.group(1)!r} is not a "
            f"number word in the plausible band {min(NUMBER_WORDS.values())}–"
            f"{max(NUMBER_WORDS.values())}",
        )
        self.assertEqual(
            NUMBER_WORDS[word],
            len(contract),
            f"{rel(SCENE_ANALYSIS)}: the prose says {word} key names, the table "
            f"declares {len(contract)} — the same class of drift as a hand-copied "
            f"upstream count",
        )


class TheThreeFilesAgree(unittest.TestCase):
    def test_template_shows_every_declared_key(self):
        """The template is the only surface a key is ever written on.

        A key defined but absent here is a key that silently stops being written:
        Phase 1 fills in the template, upstream's parser accepts whatever bullets
        it finds, and the missing rationale surfaces only when a builder needs it.
        """
        contract = [key for key, _required, _line in contract_rows()]
        shown = key_mentions(TEMPLATE)
        missing = [key for key in contract if key not in shown]
        if not missing:
            return
        unlanded = len(missing) == len(contract)
        self.fail(
            f"{rel(TEMPLATE)} shows {len(contract) - len(missing)} of "
            f"{len(contract)} director keys; missing: {', '.join(missing)}.\n"
            + (
                "  The template carries NO director keys at all — the Phase-1 "
                "wiring has not landed yet. Land it; do not narrow this test."
                if unlanded
                else "  This is drift: the contract table and the template "
                "disagree. Add the missing key(s) to the template, or remove "
                "the question that emits them."
            ),
        )

    def test_template_shows_no_undeclared_key(self):
        contract = {key for key, _required, _line in contract_rows()}
        strays = sorted(
            f"{rel(TEMPLATE)}:{lines[0]}: `{key}`"
            for key, lines in key_mentions(TEMPLATE).items()
            if key not in contract
        )
        self.assertFalse(
            strays,
            "the storyboard template writes a key the closed contract does not "
            "declare. Upstream's parser preserves it under `extra`, so it will "
            "look fine and mean nothing:\n  " + "\n  ".join(strays),
        )

    def test_phase_1_names_no_stale_key(self):
        """Phase 1 delegates the list; what it *does* name must still exist.

        The workflow deliberately restates none of the vocabulary — it points at
        the two files that own it. So coverage is not the contract here and
        asserting it would force the duplication the architecture forbids.
        Staleness is: a key renamed in scene-analysis.md while the workflow still
        drives the old name.
        """
        contract = {key for key, _required, _line in contract_rows()}
        named = key_mentions(PHASE_1)
        stale = sorted(
            f"{rel(PHASE_1)}:{lines[0]}: `{key}`"
            for key, lines in named.items()
            if key not in contract
        )
        self.assertFalse(
            stale,
            "Phase 1 drives a director key the closed contract does not declare "
            "— it was renamed or removed and the workflow was not followed "
            "through:\n  " + "\n  ".join(stale),
        )

    def test_phase_1_points_at_both_owners(self):
        """What makes Phase 1's subset legitimate instead of an omission.

        The workflow is exempt from listing all fourteen keys only because it
        sends the reader to the files that do. If it stops citing either owner,
        the delegation is broken and the exemption above is unearned.
        """
        blob = read(PHASE_1)
        for owner in (SCENE_ANALYSIS, TEMPLATE):
            self.assertIn(
                rel(owner),
                blob,
                f"{rel(PHASE_1)} no longer cites {rel(owner)}. Phase 1 is held to "
                f"a subset of the director keys precisely because it delegates to "
                f"that file; without the pointer the reader has no way to reach "
                f"the full list",
            )


class CapabilityVocabulary(unittest.TestCase):
    def test_the_tag_table_parses(self):
        self.assertGreater(
            len(catalog_tags()),
            1,
            f"{rel(CATALOG)}: the `### The tags` table produced no vocabulary, so "
            f"every tag check below is vacuous",
        )

    def test_grammar_declares_only_catalog_tags(self):
        """ADR-005: the catalog owns and versions the tag vocabulary.

        Q11 is a mechanical derivation — the union of the tags declared by every
        grammar entry a frame cites. A tag the catalog does not define enters
        that union, matches no runtime row in the selection procedure, and turns
        the derivation back into a judgment call. Nothing else catches it: these
        are markdown table cells.
        """
        defined = set(catalog_tags())
        violations = []
        for path in GRAMMAR:
            for tag, number in declared_tags(path):
                if tag not in defined:
                    violations.append(
                        f"{rel(path)}:{number}: `{tag}` is not defined in "
                        f"{rel(CATALOG)}"
                    )
        self.assertFalse(
            violations,
            "grammar entries declare capability tags outside the owned "
            "vocabulary — fix the spelling, or add the tag to the catalog and "
            "bump its vocabulary version:\n  " + "\n  ".join(sorted(set(violations))),
        )

    def test_catalog_uses_only_its_own_vocabulary(self):
        """The owner has to obey itself.

        Its runtime table's `Serves` column and its worked examples both spell
        tags out; a typo there is worse than a typo in a grammar file, because
        this is the table runtime selection reads.
        """
        defined = set(catalog_tags())
        violations = [
            f"{rel(CATALOG)}:{number}: `{tag}`"
            for tag, number in declared_tags(CATALOG)
            if tag not in defined
        ]
        self.assertFalse(
            violations,
            "capability-catalog.md names tags it does not define:\n  "
            + "\n  ".join(sorted(set(violations))),
        )

    def test_grammar_files_actually_declare_tags(self):
        """Guard: a renamed column header would empty the check silently."""
        silent = [rel(p) for p in GRAMMAR if not declared_tags(p)]
        self.assertFalse(
            silent,
            "these grammar files declare no capability tags at all — either the "
            "tag column was renamed to something TAG_COLUMN does not recognize, "
            "or the entries stopped declaring tags and Q11's union is now "
            "incomplete: " + ", ".join(silent),
        )


if __name__ == "__main__":
    unittest.main()
