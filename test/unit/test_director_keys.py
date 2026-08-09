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

And two vocabulary contracts:

4. **Capability tags** (ADR-005). Every tag declared by a `grammar/` entry must
   be defined in `reasoning/capability-catalog.md`, which owns and versions that
   vocabulary. Q11's derivation is the *union of the tags declared by every
   grammar entry a frame cites*; an undefined tag therefore enters a frame's
   capability set, matches no runtime row, and stops the derivation being
   mechanical — silently, because no gate reads these tables.
5. **Closed value vocabularies.** Two keys take their value from a grammar
   column instead of an inline enum: `camera:` from the Key column of
   `grammar/camera.md` (D1) and `metaphor:` from the Concept column of
   `grammar/metaphors.md` (D2). Every value the template demonstrates, and every
   value Phase 1 names, must resolve against the owning column. This is the check
   that catches a *derived* literal — the template once told authors to lowercase
   the Title-Case Move name, which yields `exploded-view` for a file that defines
   `exploded` / `exploded-3d`.

Everything is derived from the six files themselves. Nothing here restates a key
name, a tag name, a camera literal, a concept, or a budget number.
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
CAMERA_GRAMMAR = ROOT / "grammar" / "camera.md"
METAPHOR_GRAMMAR = ROOT / "grammar" / "metaphors.md"

# The two section headings that own the key contract. Matched by prefix so the
# em-dash subtitle of the second one can be reworded without breaking the parse.
QUESTIONS_SECTION = "## The thirteen questions"
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

# --- Closed value vocabularies (D1 `camera:`, D2 `metaphor:`) ---------------
#
# Two keys take their value from a column of a grammar file rather than from an
# inline enum in the contract table:
#
#   `camera:`   — the slug column of grammar/camera.md, which spells the exact
#                 literal a storyboard writes. Before that column existed the
#                 template *guessed* the literal by lowercasing the Move name,
#                 which silently disagreed with the file ("exploded-view" vs the
#                 "exploded" / "exploded-3d" pair camera.md actually defines).
#   `metaphor:` — the Concept column of grammar/metaphors.md. The Concept is the
#                 row identifier; the Metaphor cell is the picture it maps to,
#                 and "one concept → one metaphor" only parses if the key names
#                 the concept.
#
# Nothing about either vocabulary is restated here: both are read out of the
# column that owns them, so adding a move or a concept needs no edit in this
# file, and a renamed one turns red on the next run.
CAMERA_KEY = "camera:"
METAPHOR_KEY = "metaphor:"

# A `- key: value` bullet as a frame actually writes it. The optional `>`
# prefixes matter: the template's *filled example* — the only place a real value
# is ever demonstrated — sits inside a blockquote, and an extractor that misses
# it would check the placeholder rows and nothing else.
VALUE_BULLET = re.compile(
    r"^[ \t]*(?:>[ \t]*)*[-*][ \t]+([a-z][a-z0-9_]*):[ \t]*(\S.*?)[ \t]*$"
)
# The same pair written inline as prose — `` `camera: push-in` ``. This is the
# form the template's own guidance uses, and the form the guessed-slug bug lived
# in, so it is not optional to collect.
VALUE_SPAN = re.compile(r"^([a-z][a-z0-9_]*):[ \t]+(\S.*)$")
# A trailing `*(editorial note)*` on a template bullet is annotation, not value.
BULLET_ANNOTATION = re.compile(r"[ \t]*\*\([^)]*\)\*[ \t]*$")
# A placeholder value — `{a move name from …}` — is the shape of the template,
# not a demonstrated value, and resolves against nothing.
PLACEHOLDER = "{"

# The column headers that carry each vocabulary. Matched on the concept rather
# than one spelling, the same posture as TAG_COLUMN above: a `Slug` column, a
# `Key` column and a `` `camera:` value `` column are the same contract. Header
# text is backtick-stripped before matching, so `camera:` is written bare here.
SLUG_COLUMN = re.compile(r"\bslugs?\b|\bkeys?\b|camera:")
CONCEPT_COLUMN = re.compile(r"\bconcepts?\b")
# A camera literal: lowercase, hyphen-joined, no spaces. `exploded`, `push-in`,
# `exploded-3d`.
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
# A Key cell spells one literal or a Tier-A/Tier-B pair; both separators are in
# use across this repo's tables.
KEY_SPLIT = re.compile(r"[·/,;]")


def rel(path):
    return str(Path(path).resolve().relative_to(ROOT))


def normalize(value):
    """Fold a value for comparison: collapse whitespace, ignore case.

    Capitalization of a concept drifts between a heading, a table cell and a
    frame; the row identity does not. Dashes and punctuation are left exactly as
    written — a swapped em dash is real drift, not a spelling variant.
    """
    return " ".join(value.split()).casefold()


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


def column_cells(path, predicate):
    """Yield (cell, lineno) for every table column of `path` whose header matches.

    Structural, not positional: it walks the parsed tables of the whole file, so
    a reordered column, a renamed section heading, an added table and reflowed
    prose around any of them all leave it working. That is not hypothetical —
    the one parse bug this suite has already shipped was a line-scoped read of a
    sentence that later wrapped, which silently collected half a vocabulary.
    """
    for headers, rows in tables(iter_lines(path)):
        for index, header in enumerate(headers):
            if not predicate(header):
                continue
            for cells, number in rows:
                if index < len(cells):
                    yield cells[index], number


def camera_slugs():
    """The closed `camera:` vocabulary — the Key column of grammar/camera.md.

    D1: the literal a storyboard writes is stated explicitly and never derived
    from the Move display name. Lowercasing "Exploded View" yields
    `exploded-view`, which the file does not define — it defines the `exploded` /
    `exploded-3d` pair. That mismatch is the bug this vocabulary closes, and the
    reason nothing here reconstructs a literal from anything else.

    A Key cell holds one slug, or a Tier-A/Tier-B pair separated by `·` or `/`.
    Segments are matched whole: a segment that is not a bare slug is dropped
    rather than mined for tokens, so a Key cell that grows prose narrows the
    accepted vocabulary (a loud failure downstream) instead of widening it.
    Backticked or bare is immaterial — the strip covers both.

    Returns {slug: lineno}; first occurrence wins, so the reported line is
    stable when a slug legitimately appears twice.
    """
    values = {}
    for cell, number in column_cells(CAMERA_GRAMMAR, SLUG_COLUMN.search):
        for segment in KEY_SPLIT.split(cell):
            token = segment.strip().strip("*_` ").strip()
            if SLUG.fullmatch(token):
                values.setdefault(token, number)
    return values


def metaphor_concepts():
    """The closed `metaphor:` vocabulary — the Concept column of metaphors.md.

    D2: the value is the **Concept**, not the Metaphor. The Concept is the row
    identifier; the Metaphor cell is the picture that explains it. The budget
    rule reads "one concept → one metaphor" and counts distinct `metaphor:`
    values, which only parses if the key on the frame names the concept.

    A concept is the whole cell — it is a phrase, not a token list, so nothing
    here splits on `/` or `,` (that would shred "Before / after", "CI/CD" and
    "3D structure (molecule, mesh, model)" into fragments no frame can write).
    """
    values = {}
    for cell, number in column_cells(METAPHOR_GRAMMAR, CONCEPT_COLUMN.search):
        concept = cell.strip().strip("*_` ").strip()
        if concept and concept != "—":
            values.setdefault(concept, number)
    return values


def sentinel_values(key):
    """The non-grammar literals the contract table allows for `key`.

    `camera:` allows `static` and `metaphor:` allows `none — real product` — a
    frame that answers no viewer question, and a beat that binds a real capture.
    Both are read out of the Allowed-values cell of the closed-contract table
    rather than typed here, so scene-analysis.md stays the single source and a
    reworded sentinel is caught instead of being quietly accepted.

    Three kinds of backticked span in that cell are not values: a file pointer
    (`grammar/camera.md`), another key (`motion:`), and a suffix marker (`-3d`)
    — a marker describes how a literal is formed, it is not a literal a frame
    may write on its own.
    """
    for headers, rows in tables(section(SCENE_ANALYSIS, CONTRACT_SECTION)):
        if headers[:2] != ["key", "required"]:
            continue
        for cells, _number in rows:
            if cells[0].strip("` ") != key or len(cells) < 3:
                continue
            return {
                token.strip()
                for token in INLINE_CODE.findall(cells[2])
                if "/" not in token
                and not token.endswith(":")
                and not token.startswith("-")
            }
    return set()


def demonstrated_values(path):
    """Director-key values a file actually writes, as {key: [(value, lineno)]}.

    Two forms, both load-bearing:

    * a frame bullet — ``- camera: exploded`` — including inside a blockquote,
      which is where templates/storyboard.md keeps its *filled example*, the one
      place a real value is ever demonstrated;
    * an inline span — ``` `camera: push-in` ``` — the form the template's own
      guidance uses and the form the guessed-slug bug lived in.

    Placeholder bullets (``- camera: {a move name from …}``) are the shape of the
    template rather than a value and are skipped; so is a trailing
    ``*(editorial note)*``.
    """
    hits = {}
    for number, line, inside in iter_lines(path):
        if inside:
            continue
        bullet = VALUE_BULLET.match(line)
        if bullet:
            value = BULLET_ANNOTATION.sub("", bullet.group(2)).strip()
            if value and not value.startswith(PLACEHOLDER):
                hits.setdefault(f"{bullet.group(1)}:", []).append((value, number))
        for span in INLINE_CODE.findall(line):
            pair = VALUE_SPAN.match(span.strip())
            if not pair:
                continue
            value = pair.group(2).strip()
            if value and not value.startswith(PLACEHOLDER):
                hits.setdefault(f"{pair.group(1)}:", []).append((value, number))
    return hits


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
        # `fail`, not `assertIsNotNone`: the next two lines read `match.group(1)`,
        # so a reworded sentence has to stop here with the actionable message
        # rather than raise AttributeError on None one line later.
        if match is None:
            self.fail(
                f"{rel(SCENE_ANALYSIS)}: the closed-set sentence no longer states "
                f"how many key names there are, so the prose can drift from the "
                f"table unnoticed"
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


class ValueVocabulariesAreClosed(unittest.TestCase):
    """`camera:` and `metaphor:` take their values from a grammar column.

    Every other key in the contract table carries its allowed values inline —
    `calm | build | peak | resolve` — so a wrong value is visible in the one
    file that defines it. These two do not: their vocabularies are tables in
    `grammar/`, and the value written on a frame is a literal copied out of a
    column. Nothing downstream reads either key yet (Phase 3 becomes a reader in
    M5), so a literal that resolves against nothing is invisible until a builder
    asks for a move that does not exist.

    It has already happened once. The template derived the literal by lowercasing
    the Title-Case Move name, which produced `exploded-view` while camera.md
    defined the `exploded` / `exploded-3d` pair — a guess that read as a rule and
    disagreed with the file. D1 closes that by making the Key column explicit;
    this class is the check that would have caught it. D2 does the same for
    `metaphor:`, whose value is the **Concept** column — the row identifier, and
    the unit the metaphor-consistency budget counts.
    """

    def demonstrated(self, key):
        """Every value of `key` the template writes or Phase 1 names.

        Phase 1 deliberately names no values today — it delegates to the two
        owning files, the same posture `test_phase_1_names_no_stale_key` holds it
        to. It is scanned anyway so the day it does name one, the value is
        checked rather than trusted. Its empty contribution is why the vacuity
        guard below is asserted on the template.
        """
        sites = []
        for path in (TEMPLATE, PHASE_1):
            for value, number in demonstrated_values(path).get(key, []):
                sites.append((value, f"{rel(path)}:{number}"))
        return sites

    def test_the_grammar_columns_parse(self):
        """A silently-empty column would make both resolution checks vacuous."""
        self.assertTrue(
            camera_slugs(),
            f"{rel(CAMERA_GRAMMAR)}: no table column names the literal a "
            f"storyboard writes, so the `camera:` vocabulary is not closed and "
            f"every value below resolves against nothing. The Key column is the "
            f"contract (D1) — it was renamed, dropped, or its header no longer "
            f"matches SLUG_COLUMN",
        )
        self.assertTrue(
            metaphor_concepts(),
            f"{rel(METAPHOR_GRAMMAR)}: no table column is headed Concept, so the "
            f"`metaphor:` vocabulary is not closed. The Concept column is the row "
            f"identifier and the value a frame writes (D2)",
        )

    def test_the_template_demonstrates_both_values(self):
        """The extractor has to see the filled example, or it checks nothing.

        The template's real values live in a blockquote (`> - camera: exploded`)
        and in backticked prose (`` `camera: push-in` ``); its top-level bullets
        are placeholders. An extractor that reads only one of those forms passes
        while checking a fraction of the surface, which is the failure mode this
        guard exists for.
        """
        for key in (CAMERA_KEY, METAPHOR_KEY):
            self.assertTrue(
                self.demonstrated(key),
                f"{rel(TEMPLATE)}: no `{key}` value is demonstrated anywhere — "
                f"either the filled example lost the key, or the template was "
                f"reflowed into a shape `demonstrated_values` no longer reads. "
                f"Both leave the closed-vocabulary checks passing vacuously",
            )

    def test_camera_values_resolve_against_the_key_column(self):
        slugs = camera_slugs()
        allowed = {normalize(v) for v in slugs} | {
            normalize(v) for v in sentinel_values(CAMERA_KEY)
        }
        violations = [
            f"{where}: `camera: {value}`"
            for value, where in self.demonstrated(CAMERA_KEY)
            if normalize(value) not in allowed
        ]
        self.assertFalse(
            violations,
            f"these `camera:` values are in neither the Key column of "
            f"{rel(CAMERA_GRAMMAR)} nor the contract table's sentinel set. Copy "
            f"the Key cell verbatim — never lowercase the Title-Case Move name, "
            f"which is a display name and does not match ({len(slugs)} literals "
            f"are defined):\n  " + "\n  ".join(violations),
        )

    def test_metaphor_values_resolve_against_the_concept_column(self):
        concepts = metaphor_concepts()
        # Case-insensitive on purpose: prose capitalization of a concept drifts
        # between a heading, a cell and a frame; the row identity does not.
        # Dashes and spacing are compared as written — a swapped dash is drift.
        allowed = {normalize(v) for v in concepts} | {
            normalize(v) for v in sentinel_values(METAPHOR_KEY)
        }
        violations = [
            f"{where}: `metaphor: {value}`"
            for value, where in self.demonstrated(METAPHOR_KEY)
            if normalize(value) not in allowed
        ]
        self.assertFalse(
            violations,
            f"these `metaphor:` values name no row of {rel(METAPHOR_GRAMMAR)}. "
            f"The value is the **Concept** column — the row identifier — not the "
            f"Metaphor cell that describes the picture ({len(concepts)} concepts "
            f"are defined):\n  " + "\n  ".join(violations),
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



# --- The cap: nothing writes a frame key the contract does not declare -------
#
# Kept from the superseded ADR-010 delivery, which is the one thing that record
# was right about: the growth this stops is sideways, not upward. A new key
# needs a question and trips the arithmetic above; a *bullet* needs nothing, and
# nothing was looking. Repointing it at the closed fifteen is what makes the cap
# absolute -- while an execution-note registry existed, the cap had a legal exit
# (register another note), and the exit was the whole problem.

# A line that tells a frame to carry something.
INSTRUCTS_FRAME = re.compile(
    r"\bon(?:to)? (?:a |the |an )?[\w`: -]*frame\b|\bthe packet carries\b|\bwrite[s]? .*frame\b",
    re.I,
)
FRAME_KEY_TOKEN = re.compile(r"`([a-z][a-z0-9_]*):(?:\s[^`]*)?`")

# Where a frame's OTHER vocabularies are defined. A frame block carries official
# fields and capture bindings as well as director keys; read them from the
# template's own tables so a new binding needs no edit here.
TEMPLATE_KEY_SECTIONS = ("## Official keys", "## Capture and clip keys")


def template_frame_keys():
    text = read(TEMPLATE)
    names = set()
    for heading in TEMPLATE_KEY_SECTIONS:
        if heading not in text:
            continue
        body = text.split(heading, 1)[1].split("\n## ", 1)[0]
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            first = ROW_SPLIT.split(stripped.strip("|"))[0].strip()
            names |= {f"{n}:" for n in re.findall(r"`([a-z][a-z0-9_]*)`", first)}
    return names


class TheFencedSkeletonIsGuardedToo(unittest.TestCase):
    """The most-copied surface in the template, and nothing was looking at it.

    `key_mentions()` skips fenced blocks — correctly, because the skeleton legitimately
    shows official fields and capture bindings the director-key contract does not
    declare. The consequence was that the fence became the one place an undeclared key
    could sit unnoticed: an adversarial pass added an invented `parallax_bed:` inside it
    and the whole suite stayed green. It is also the path of least resistance, which is
    what makes it the one to guard.

    So check it against the union of every vocabulary a frame may legally carry.
    """

    def _skeleton(self):
        """The fenced block itself, not "up to the next `## `".

        The skeleton *contains* a `## Frame {N} — {title}` heading — it is showing what a
        storyboard looks like — so splitting on the next `## ` truncates it after sixteen
        lines and the bullets never get read. Found by mutating this test: an invented
        bullet added below that heading was missed.
        """
        text = read(TEMPLATE)
        body = text.split("## File skeleton", 1)
        self.assertEqual(2, len(body), f"{rel(TEMPLATE)}: no `## File skeleton` section")
        lines, block, inside = body[1].splitlines(), [], False
        for line in lines:
            if line.strip().startswith("```"):
                if inside:
                    break
                inside = True
                continue
            if inside:
                block.append(line)
        self.assertTrue(block, f"{rel(TEMPLATE)}: `## File skeleton` has no fenced block")
        return "\n".join(block)

    def test_the_skeleton_writes_no_undeclared_bullet(self):
        allowed = (
            {key for key, _required, _line in contract_rows()}
            | template_frame_keys()
            | {OVERRIDE_KEY}
        )
        strays = []
        for number, line in enumerate(self._skeleton().splitlines(), 1):
            bullet = KEY_BULLET.match(line)
            if not bullet:
                continue
            name = f"{bullet.group(1)}:"
            if name not in allowed:
                strays.append(f"{rel(TEMPLATE)} § File skeleton:{number}: `{name}`")
        self.assertEqual(
            [], strays,
            "the fenced skeleton — the block authors copy — writes a bullet no vocabulary "
            "declares:\n  " + "\n  ".join(strays),
        )


class NothingWritesAnUndeclaredFrameKey(unittest.TestCase):
    """The reasoning layer may not invent a frame bullet on its way past.

    A grammar or a workflow that says "state `parallax_bed: shallow` on the
    frame" creates a fifteenth-and-a-half key: the upstream parser preserves it
    under `extra`, a packet carries it, a builder may act on it, and no arithmetic
    notices because it was never in the contract table.
    """

    def test_the_other_frame_vocabularies_parse(self):
        """Guard on the guard: an empty allowed-set would flag everything, and
        the repair instinct under a red suite is to widen the filter."""
        self.assertTrue(
            template_frame_keys(),
            f"{rel(TEMPLATE)}: no official/capture key tables parsed — the scan "
            "below would report every legitimate binding as undeclared",
        )

    def test_no_file_writes_an_undeclared_key_onto_a_frame(self):
        allowed = (
            {key for key, _required, _line in contract_rows()}
            | template_frame_keys()
            | {OVERRIDE_KEY}
        )
        sources = (
            sorted((ROOT / "grammar").glob("*.md"))
            + sorted((ROOT / "patterns").glob("*.md"))
            + sorted((ROOT / "workflows").glob("*.md"))
        )
        offenders = []
        for path in sources:
            for number, line in enumerate(read(path).splitlines(), 1):
                if not INSTRUCTS_FRAME.search(line):
                    continue
                for token in FRAME_KEY_TOKEN.findall(line):
                    if f"{token}:" in allowed:
                        continue
                    offenders.append(
                        f"{rel(path)}:{number}: writes `{token}:` onto a frame, and the "
                        "closed contract does not declare it"
                    )
        self.assertEqual(
            [], sorted(set(offenders)),
            "a frame bullet nobody declared reaches a builder — add the question that "
            "emits it, or stop writing it:\n  " + "\n  ".join(sorted(set(offenders))),
        )


if __name__ == "__main__":
    unittest.main()
