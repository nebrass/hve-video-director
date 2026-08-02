#!/usr/bin/env python3
"""Pointer-validity suite for the ecosystem compatibility map (ADR-007).

`compat/ecosystem.md` is the thin waist between this skill and the HyperFrames
ecosystem. Upstream publishes no stability guarantees: it split the monolithic
`hyperframes` skill into a domain family and deprecated the `validate`/`inspect`/
`layout` gates, and both changes rotted this repo with no local signal. ADR-007
answers that with one rule:

- **Skill names are stable.** They are the ecosystem's public API and may be
  named anywhere in the repo.
- **Intra-skill file paths churn.** They live in `compat/ecosystem.md` and
  nowhere else. Everywhere else, prose names the skill plus a capability SYMBOL
  and points at the map for the exact path.

This suite is the `SKILL_SPLIT_TOPOLOGY` probe that file describes. It asserts,
in both directions, that the map is the only path holder and that it holds every
path actually cited:

1. every registered path resolves under an installed skill home;
2. no `skill` -> `path` citation survives outside the map;
3. no registered path string is quoted verbatim outside the map;
4. no distinctive registered *basename* is quoted outside the map;
5. every SYMBOL referenced in repo prose is defined by the map;
6. every registry row is well-formed.

The map grants ONE exception to rule 2: upstream **rules** and **blueprints** are
cited by bare name because a name is a stable identifier while a path is not
(§ Citing upstream vocabulary). `RecipeCitations` is the other half of that
bargain — it resolves every bare citation in `grammar/` and `reasoning/` against
the two upstream index files, so an invented or renamed recipe is a red test
instead of a dead pointer no gate can see.

Everything except `KNOWN_SKILLS` is derived from `compat/ecosystem.md` itself,
so adding a capability needs no edit here. `KNOWN_SKILLS` is hardcoded on
purpose: the stable-name set *is* the contract ADR-007 pins.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPAT = ROOT / "compat" / "ecosystem.md"
SKILL = ROOT / "SKILL.md"

# The ecosystem's public API — ADR-007's stable-name set. A row may only be
# owned by one of these. Upstream renaming a skill is a breaking change we want
# to see as a red test, not absorb silently.
KNOWN_SKILLS = frozenset(
    {
        "hyperframes",
        "hyperframes-core",
        "hyperframes-animation",
        "hyperframes-creative",
        "hyperframes-cli",
        "hyperframes-registry",
        "hyperframes-keyframes",
        "media-use",
        "motion-doctrine",
        "seam-craft",
        "cut-the-curve",
        "oversized-cursor",
        "motion-graphics",
        "figma",
    }
)

# The prose surface ADR-007 governs, exactly as the milestone enumerates it.
# `.github/copilot-instructions.md` and `AGENTS.md` mirror `CLAUDE.md` but sit
# outside that enumeration, so they are checked for symbols (below) and not for
# paths.
GOVERNED_PROSE = (
    [SKILL, ROOT / "CLAUDE.md", ROOT / "README.md"]
    + sorted((ROOT / "workflows").glob("*.md"))
    + sorted((ROOT / "patterns").glob("*.md"))
    + sorted((ROOT / "design-systems").rglob("*.md"))
    + sorted((ROOT / "grammar").glob("*.md"))
    + sorted((ROOT / "reasoning").glob("*.md"))
    # M5: the scene-builder delta ships upstream-facing prose to a sub-agent, so it
    # is governed like any other authored file — otherwise it is ADR-007-clean by
    # discipline alone, with nothing to catch a regression.
    + sorted((ROOT / "sub-agents").glob("*.md"))
)

# Wider surface for symbol collection: everything this repo authors as prompt
# content. `CHANGELOG.md` (history) and `docs/` (the spec bundle) are excluded —
# both are off-limits to edits, and a test may not demand a fix it forbids.
# `example/` is a generated project, not skill source.
AUTHORED_PROSE = sorted(
    {
        *(p for p in ROOT.glob("*.md") if p.name != "CHANGELOG.md"),
        *(ROOT / "workflows").rglob("*.md"),
        *(ROOT / "patterns").rglob("*.md"),
        *(ROOT / "design-systems").rglob("*.md"),
        *(ROOT / "templates").rglob("*.md"),
        *(ROOT / "compat").rglob("*.md"),
        *(ROOT / "grammar").rglob("*.md"),
        *(ROOT / "reasoning").rglob("*.md"),
        *(ROOT / "sub-agents").rglob("*.md"),
        *(ROOT / ".github").rglob("*.md"),
    }
)

# The reasoning layer (ADR-005) — the repo's most citation-dense prose, and the
# only prose that cites upstream *recipes* by bare name. Governed by everything
# above plus the recipe-resolution checks at the bottom of this file.
REASONING_PROSE = sorted(
    {*(ROOT / "grammar").glob("*.md"), *(ROOT / "reasoning").glob("*.md")}
)

# Files scanned for evidence that an identifier is a shell/env variable rather
# than a capability symbol. Deliberately limited to what this repo authors:
# widening it to the whole tree would let an upstream skill's `NAME=` assignment
# silently suppress a real symbol violation here.
VARIABLE_EVIDENCE = sorted(
    {
        *AUTHORED_PROSE,
        *(p for p in (ROOT / "scripts").glob("*") if p.is_file()),
        *(p for p in (ROOT / "templates").glob("*.html") if p.is_file()),
    }
)

FENCE = re.compile(r"^[ \t]*(?:```|~~~)")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
# Two grammars, deliberately different (see `referenced_symbols` for the why).
# A registry row may name a single-word capability (`PALETTES`, `TRANSCRIBE`,
# `BGM`, `SFX`); a prose *reference* must carry an underscore to be
# distinguishable from ordinary shouting.
REGISTRY_SYMBOL = re.compile(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*")
SYMBOL = re.compile(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+")
ARROW = r"(?:→|->)"
# A citation is `<stable skill name>` -> `<something>`. Anchoring the left side
# on KNOWN_SKILLS is what keeps unrelated prose arrows (`draft` -> `approve`,
# `scripts/caption_gen.py` -> ...) out of the match.
CITATION = re.compile(
    r"`(" + "|".join(sorted(map(re.escape, KNOWN_SKILLS), key=len, reverse=True))
    + r")`\s*" + ARROW + r"\s*`([^`\n]+)`"
)
# The banned right-hand side: an intra-skill *file path*. A bare SYMBOL or a CLI
# command name on the right is the intended replacement and stays legal.
PATH_LIKE = re.compile(r"/|\.(?:md|mjs|js|mts|cjs|json|html|css|py|sh|txt)$")

FIX = (
    "move the path into compat/ecosystem.md and cite the capability SYMBOL here "
    "(ADR-007: intra-skill paths live in exactly one file)"
)

# Narrow, per-line exemption: (repo-relative file, registered path) pairs whose
# literal path may appear INSIDE a fenced code block only. A shell command
# cannot indirect through a symbol, so a runnable invocation has to spell the
# path out. Prose in the same file is still checked.
#
#   phase-4 Step 4.7 runs `node "$ANIM_SKILL_DIR/scripts/animation-map.mjs"`.
#   phase-4 Steps 4.5/4.6 run `node "$DOCTRINE_SKILL_DIR/scripts/seam-stamp.mjs"`
#     and `.../scripts/seam-gate.mjs` — same shape, same reason: both are
#     skill-resident scripts with no `hyperframes <subcommand>` equivalent, so a
#     runnable invocation cannot indirect through SEAM_STAMP / SEAM_VERIFIER.
#
# Keep this list at the handful of genuinely runnable call sites. An allowlist
# that grows to silence prose defeats the test it belongs to.
RUNNABLE_PATH_ALLOWLIST = frozenset(
    {
        ("workflows/phase-4-production.md", "scripts/animation-map.mjs"),
        ("workflows/phase-4-production.md", "scripts/seam-stamp.mjs"),
        ("workflows/phase-4-production.md", "scripts/seam-gate.mjs"),
    }
)

# Files permitted to hold paths/citations because they *are* the map, or because
# they document the rule by quoting the banned form. Each entry needs a reason.
#
#   compat/ecosystem.md — the map itself; the single blast radius by design.
RULE_DOC_ALLOWLIST = frozenset({"compat/ecosystem.md"})

# --- Bare recipe citations (compat/ecosystem.md § Citing upstream vocabulary) ---
#
# Two of the three legal citation forms name an upstream *recipe* by bare
# identifier: a RULE by name and a BLUEPRINT by id, both backticked, both without
# directory and without extension. The bare form is not a style preference — it
# is what keeps the citation legal under the distinctive-basename test above,
# which bans the registered `css-marker-patterns.md` but not the bare string
# `css-marker-patterns`.
#
# Both index files are machine-parseable, which is what lets this suite resolve a
# citation instead of guessing at it:
#
#   rules-index.md       <name path="rules/name.md">summary … Tags: …</name>
#   blueprints-index.md  <blueprint id="id" roles="…" duration="…">…</blueprint>
CATALOG = ROOT / "reasoning" / "capability-catalog.md"
SCENE_ANALYSIS = ROOT / "reasoning" / "scene-analysis.md"
CAMERA_GRAMMAR = ROOT / "grammar" / "camera.md"

RULE_ELEMENT = re.compile(r'<([A-Za-z0-9][A-Za-z0-9._-]*)\s+path="rules/[^"]*"')
BLUEPRINT_ELEMENT = re.compile(r'<blueprint\s+id="([^"]+)"')
# The counts compat/ecosystem.md publishes for each namespace. Parsed, never
# retyped: an early draft of that file said 47 rules, and a hand-copied count is
# exactly the kind of drift this suite exists to catch.
DECLARED_RULE_COUNT = re.compile(r"Upstream \*\*rule\*\* — (\d+) under")
DECLARED_BLUEPRINT_COUNT = re.compile(r"Upstream \*\*blueprint\*\* — (\d+) under")

# The citation shape: lowercase, at least one hyphen, no directory, no extension.
RECIPE_TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)+")
# A path-shaped span that is trying to be a recipe citation. `rules/x`,
# `blueprints/x.md` and a bare `x.md` are all illegal: an upstream citation
# carries neither directory nor extension, and a skill-LOCAL path is always
# written with its directory (`grammar/camera.md`, `patterns/anti-slop.md`).
# A bare hyphenated basename is therefore an upstream leak — unless it names a
# file this repo owns, which `owned_basenames()` subtracts so a future mention
# of `project-plan.md` is not mistaken for one.
PATHY_RECIPE = re.compile(
    r"^(?:(?:rules|blueprints)/[A-Za-z0-9._-]+|[a-z0-9]+(?:-[a-z0-9]+)+\.md)$"
)
BARE_BASENAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)+\.md$")

# Structural prefixes: an identifier carrying one of these is never a recipe
# name, by construction rather than by enumeration. Guarded by
# `test_exclusions_never_shadow_an_upstream_name`.
#
#   data- / aria- — HTML attributes (`data-duration`, `data-start`).
#   hf-           — the HyperFrames runtime's own hooks (`hf-seek`).
#   vfx-          — hyperframes-registry catalog blocks (`vfx-portal`); they
#                   resolve through REGISTRY_CATALOG, not the recipe indexes.
NON_RECIPE_PREFIXES = ("data-", "aria-", "hf-", "vfx-")

# Hyphenated lowercase identifiers that share a citation's shape, are not
# citations, and are not derivable from any vocabulary table this repo owns.
# Every entry needs a reason. A list that grows means the grammar in
# `recipe_citation_candidates` is wrong, not that the list needs another line.
#
#   preserve-3d — the CSS `transform-style` keyword, quoted verbatim in the
#                 perspective-hygiene rule of grammar/camera.md.
NON_RECIPE_TOKENS = frozenset({"preserve-3d"})

CITE_BARE = (
    "cite it bare and backticked — no directory, no `.md` (compat/ecosystem.md "
    "§ Citing upstream vocabulary)"
)

# The column of grammar/camera.md that closes the `camera:` vocabulary: the exact
# literal a storyboard writes. Matched on the concept rather than one spelling —
# a `Key`, a `Slug` and a `` `camera:` value `` column are the same contract.
# Header text is backtick-stripped before matching, so `camera:` is written bare.
CAMERA_KEY_COLUMN = re.compile(r"\bslugs?\b|\bkeys?\b|camera:")
# A Key cell holds one literal, or a Tier-A/Tier-B pair separated by `·` or `/`.
CAMERA_KEY_SPLIT = re.compile(r"[·/,;]")
CAMERA_KEY_LITERAL = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
# Markdown escapes a literal pipe in a cell as `\|`; splitting on a bare pipe
# would shred such a row.
ROW_SPLIT = re.compile(r"(?<!\\)\|")
TABLE_SEPARATOR = re.compile(r":?-{3,}:?")


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


def registry_rows():
    """Parse the capability registry into (symbol, skill, path_cell, what, used_by, line).

    Scoped to the `## Capability registry` section so the CLI-surface table and
    the feature-detection table below it are never mistaken for rows.
    """
    rows = []
    inside_section = False
    for number, line, in_fence in iter_lines(COMPAT):
        if line.startswith("## "):
            inside_section = line.startswith("## Capability registry")
            continue
        if in_fence or not inside_section or not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            continue
        symbol = cells[0].strip("`").strip()
        if len(symbol) < 2 or not REGISTRY_SYMBOL.fullmatch(symbol):
            continue  # header row ("Symbol"), separator row ("---")
        rows.append(
            (symbol, cells[1].strip("`").strip(), cells[2], cells[3], cells[4], number)
        )
    return rows


def expand_paths(path_cell):
    """Expand a registry path cell into concrete skill-relative paths.

    Two shapes occur:

    * a single backticked path, optionally followed by a parenthetical —
      ``` `references/data-attributes.md` ```, ``` `SKILL.md` (gateway) ```;
    * a templated family — ``` `transitions/css-<family>.md`, 13 files:
      `css-3d`, ... ``` — where the enumerated tokens are *file stems*, not
      placeholder substitutions (`css-3d` already carries the `css-` prefix).
      They join as directory + stem + extension, never by replacing `<...>`.

    Returns (paths, declared_count_or_None).
    """
    tokens = INLINE_CODE.findall(path_cell)
    if not tokens:
        return [], None
    template = tokens[0]
    declared = re.search(r"(\d+)\s+files\s*:", path_cell)
    count = int(declared.group(1)) if declared else None
    if "<" in template and ">" in template:
        directory, _, tail = template.rpartition("/")
        suffix = tail[tail.rindex(">") + 1 :] if ">" in tail else ""
        prefix = f"{directory}/" if directory else ""
        return [f"{prefix}{stem}{suffix}" for stem in tokens[1:]], count
    return [template], count


def skill_homes():
    """Resolve candidate skill homes, repo-vendored install first.

    The canonical `$SKILL_HOMES` list is parsed out of `SKILL.md` so this stays
    in lock-step with the resolver the skill itself ships. `ROOT/.agents/skills`
    is probed first: when the ecosystem is vendored into the repo, that copy is
    the one the lock file pins, and preferring it keeps the test deterministic
    on a machine that also has a global install.
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


def resolve_skill(name, homes):
    for home in homes:
        candidate = home / name
        if candidate.is_dir():
            return candidate
    return None


def defined_symbols():
    """Symbols the map defines: registry rows plus behavior-probe headings.

    Probe headings (`### \\`CHECK_DEPRECATION_SIGNAL\\` — …`) are matched
    anywhere in the file rather than inside a named section, so renaming the
    `## Behavior probes` heading cannot silently empty the set. The registry's
    own sub-headings name skills in lowercase and never match.
    """
    symbols = {row[0] for row in registry_rows()}
    for line in read(COMPAT).splitlines():
        heading = re.match(r"^###\s+`([A-Z][A-Z0-9_]*)`", line)
        if heading:
            symbols.add(heading.group(1))
    return symbols


def shell_variable_names():
    """Identifiers used as shell/env variables somewhere in this repo's sources.

    Evidence is any of `$NAME`, `${NAME}`, `NAME=` across the authored surface,
    or a quoted `"NAME"` inside `scripts/` (the `os.environ[...]` form). The
    quoted form is restricted to scripts so a JSON option label in a workflow
    can never mask a real capability symbol.
    """
    prose_blob = "\n".join(
        read(p) for p in VARIABLE_EVIDENCE if p.is_file() and p.suffix != ".py"
    )
    script_blob = "\n".join(
        read(p)
        for p in VARIABLE_EVIDENCE
        if p.is_file() and p.parent.name == "scripts"
    )
    blob = prose_blob + "\n" + script_blob
    names = set()
    for name in set(SYMBOL.findall(blob)):
        pattern = re.escape(name)
        if re.search(r"\$\{?" + pattern + r"\b", blob):
            names.add(name)
        elif re.search(r"\b" + pattern + r"[ \t]*=", blob):
            names.add(name)
        elif re.search(r"[\"']" + pattern + r"[\"']", script_blob):
            names.add(name)
    return names


def referenced_symbols():
    """Collect capability-symbol references from authored prose.

    Grammar, stated precisely:

    * a **candidate** is a token matching ``[A-Z][A-Z0-9]*(_[A-Z0-9]+)+`` — all
      caps, digits allowed, at least one underscore. Requiring an underscore
      drops single-word shouting (`WCAG`, `GROUPS`, `MANUAL`, `HTML`); requiring
      all caps drops camelCase upstream type names (`StoryboardManifest`). The
      cost is that the registry's four single-word symbols (`PALETTES`,
      `TRANSCRIBE`, `BGM`, `SFX`) are never collected from prose — a deliberate
      false negative, preferred over the false positives an underscore-free
      grammar produces. Those rows are still fully covered by the path and
      row-shape tests.
    * it counts as a reference only when it is either the **entire** contents of
      an inline code span (`` `VISUAL_STYLES` ``, optionally `$`/`${}` wrapped)
      or a **bare token in prose** — outside fenced code blocks and outside
      inline code. Both citation styles are in use today. Fenced blocks are
      skipped because their all-caps tokens are shell variables and diagram
      labels, not citations.
    * candidates with shell/env-variable evidence anywhere in this repo's
      sources are dropped (see `shell_variable_names`). That removes
      `ELEVENLABS_API_KEY`, `SKILL_HOMES`, `SKILL_DIR`, `PROJECT_DIR`,
      `ANIM_SKILL_DIR`, `VOICE_ID`, `RECORD_TIMEOUT`, … without an enumerated
      denylist that would rot on the next new variable.

    Returns {symbol: [(file, line), ...]}.
    """
    variables = shell_variable_names()
    hits = {}
    for path in AUTHORED_PROSE:
        for number, line, inside in iter_lines(path):
            if inside:
                continue
            found = set()
            for span in INLINE_CODE.findall(line):
                token = span.strip().lstrip("$").strip("{}")
                if SYMBOL.fullmatch(token):
                    found.add(token)
            for token in SYMBOL.findall(INLINE_CODE.sub("", line)):
                found.add(token)
            for token in found - variables:
                hits.setdefault(token, []).append((rel(path), number))
    return hits


def upstream_recipe_names(homes=None):
    """Parse the two upstream indexes into (rule_names, blueprint_ids).

    Returns (None, None) when `hyperframes-animation` is not installed, so the
    callers can skip the way `test_every_registered_path_exists` does. The index
    paths themselves are read out of the registry rows for `RULES_INDEX` and
    `BLUEPRINT_INDEX` rather than typed here — ADR-007 applies to this file's own
    knowledge of upstream layout just as much as to the prose it polices.
    """
    homes = skill_homes() if homes is None else homes
    index_paths = {}
    for symbol, skill, path_cell, _what, _used, _line in registry_rows():
        if symbol in ("RULES_INDEX", "BLUEPRINT_INDEX"):
            paths = expand_paths(path_cell)[0]
            if paths:
                index_paths[symbol] = (skill, paths[0])
    if set(index_paths) != {"RULES_INDEX", "BLUEPRINT_INDEX"}:
        return None, None
    resolved = {}
    for symbol, (skill, value) in index_paths.items():
        root = resolve_skill(skill, homes)
        if root is None or not (root / value).is_file():
            return None, None
        resolved[symbol] = read(root / value)
    return (
        set(RULE_ELEMENT.findall(resolved["RULES_INDEX"])),
        set(BLUEPRINT_ELEMENT.findall(resolved["BLUEPRINT_INDEX"])),
    )


def owned_basenames():
    """Filenames this repo owns, so an upstream rule can never be confused with one."""
    return {
        p.name
        for directory in ("workflows", "patterns", "templates", "design-systems",
                          "scripts", "test", "compat", "grammar", "reasoning")
        for p in (ROOT / directory).rglob("*")
        if p.is_file()
    }


def registered_path_stems():
    """Extension-less basenames of every registered path.

    A recipe whose file is ALSO registered as a capability has two identities;
    compat/ecosystem.md resolves that by requiring the SYMBOL. `css-marker-
    patterns` is the only such overlap today, but the set is derived so a second
    one is caught the day it appears rather than the day it rots.
    """
    stems = {}
    for symbol, skill, path_cell, _what, _used, _line in registry_rows():
        for value in expand_paths(path_cell)[0]:
            base = value.rsplit("/", 1)[-1]
            stems.setdefault(base.rsplit(".", 1)[0], (symbol, skill))
    return stems


def capability_tags():
    """The tag vocabulary owned by `reasoning/capability-catalog.md` (ADR-005).

    Parsed from the two-column table under `### The tags`. Tags are hyphenated
    and backticked, so without subtracting them every tag reads as a recipe
    citation.
    """
    tags = set()
    inside = False
    for _number, line, in_fence in iter_lines(CATALOG):
        if line.startswith("#"):
            inside = line.strip("# ").strip().lower() == "the tags"
            continue
        if in_fence or not inside or not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 2 and cells[0].startswith("`"):
            tags.add(cells[0].strip("`").strip())
    return tags


def runtime_values():
    """Allowed `runtime:` values, read from the director-keys table.

    `html-in-canvas` is hyphenated and backticked; it is a runtime name, not a
    recipe.
    """
    for _number, line, in_fence in iter_lines(SCENE_ANALYSIS):
        if in_fence or not line.lstrip().startswith("| `runtime:`"):
            continue
        return {t for t in INLINE_CODE.findall(line) if not t.endswith(":")}
    return set()


def table_column_cells(path, header_pattern):
    """Yield the cells of every markdown-table column whose header matches.

    A deliberately small structural parser — a table is a run of `|`-leading
    lines outside a fence, its first row is the header, and the `|---|` rule is
    skipped. Structural rather than positional: a reordered column, an added
    table, a renamed section heading and reflowed prose around any of them all
    leave it working, which is the property a vocabulary reader has to have.
    """
    headers = None
    for _number, line, in_fence in iter_lines(path):
        stripped = line.strip()
        if in_fence or not stripped.startswith("|"):
            headers = None
            continue
        cells = [c.strip() for c in ROW_SPLIT.split(stripped.strip("|"))]
        if cells and all(TABLE_SEPARATOR.fullmatch(c) for c in cells if c):
            continue
        if headers is None:
            headers = [c.strip("*` ").lower() for c in cells]
            continue
        for index, header in enumerate(headers):
            if header_pattern.search(header) and index < len(cells):
                yield cells[index]


def camera_key_values():
    """The `camera:` value vocabulary (`push-in`, `exploded`, `exploded-3d`, …).

    These are director-key values, not recipe names, and they share a citation's
    shape exactly, so the scanner has to subtract them.

    Read from TWO places on purpose, because the vocabulary is stated in two:

    * the **Key column** of the grammar table, which owns it — the exact literal
      a storyboard writes, closed by that column so nothing derives a literal
      from the Title-Case Move name;
    * the **paragraph** stating the `-3d` tier-suffix rule, which spells the
      Tier-A/Tier-B pairs inline.

    The column is a superset today, but a value backticked in only one of the
    two is still a value, and reading both costs nothing. Both reads are
    structural rather than line-scoped: the column is parsed as a table and the
    paragraph as a whole block. Prose reflow is not hypothetical here — an
    earlier line-scoped version of this function silently collected only the
    pairs that happened to precede the first newline.
    """
    values = set()
    for block in re.split(r"\n\s*\n", read(CAMERA_GRAMMAR)):
        if "`camera:` value" not in block:
            continue
        values |= {t for t in INLINE_CODE.findall(block) if not t.endswith(":")}
    for cell in table_column_cells(CAMERA_GRAMMAR, CAMERA_KEY_COLUMN):
        for segment in CAMERA_KEY_SPLIT.split(cell):
            token = segment.strip().strip("*_` ").strip()
            if CAMERA_KEY_LITERAL.fullmatch(token):
                values.add(token)
    return values


def non_recipe_vocabulary():
    """Everything that shares a recipe citation's shape but is not one."""
    return (
        capability_tags()
        | runtime_values()
        | camera_key_values()
        | set(KNOWN_SKILLS)
        | set(NON_RECIPE_TOKENS)
    )


def recipe_citation_candidates():
    """Collect bare upstream-recipe citations from `grammar/` and `reasoning/`.

    Grammar, stated precisely. A candidate is a token that

    * is the **entire** contents of an inline code span. compat/ecosystem.md
      makes this normative — "Keep citations backticked — that is what the
      scanner sees" — which is what lets the scanner ignore ordinary hyphenated
      prose ("hub-and-spoke", "code→matter", "front-loading");
    * sits **outside** fenced code blocks, which hold shell commands and the
      selection pseudo-code, not citations;
    * matches ``[a-z0-9]+(-[a-z0-9]+)+`` — lowercase, at least one hyphen, no
      directory and no extension, exactly the form compat mandates. Requiring a
      hyphen drops single-word spans (`three`, `css`, `focal`, `static`);
      requiring lowercase drops the SYMBOL grammar handled above;

    and is **not** a member of a vocabulary that shares that shape:

    * a capability tag — `reasoning/capability-catalog.md` owns them (ADR-005);
    * a skill name — `KNOWN_SKILLS`, the ecosystem's stable API (ADR-007);
    * a `runtime:` value from the director-keys table (`html-in-canvas`);
    * a tier-suffixed `camera:` value (`orbit-3d`, `isometric-3d`, …);
    * an identifier carrying a structural prefix (`data-`, `aria-`, `hf-`,
      `vfx-`) — see NON_RECIPE_PREFIXES;
    * one of the NON_RECIPE_TOKENS.

    Four of those five subtracted sets are derived from the files that own them,
    so adding a tag, a runtime, or a camera tier needs no edit here. The residue
    is asserted to be empty by `test_every_candidate_resolves_upstream`: any
    token the grammar cannot classify is reported rather than silently dropped,
    which is what keeps the false-positive rate verifiable instead of assumed.

    Returns {token: [(file, line), ...]}.
    """
    known = non_recipe_vocabulary()
    hits = {}
    for path in REASONING_PROSE:
        for number, line, inside in iter_lines(path):
            if inside:
                continue
            for span in INLINE_CODE.findall(line):
                token = span.strip()
                if not RECIPE_TOKEN.fullmatch(token):
                    continue
                if token in known or token.startswith(NON_RECIPE_PREFIXES):
                    continue
                hits.setdefault(token, []).append((rel(path), number))
    return hits


class RegistryShape(unittest.TestCase):
    def test_registry_rows_are_wellformed(self):
        rows = registry_rows()
        self.assertGreater(len(rows), 0, f"{rel(COMPAT)}: capability registry parsed as empty")
        seen = {}
        for symbol, skill, path_cell, what, used_by, line in rows:
            where = f"{rel(COMPAT)}:{line}"
            self.assertRegex(symbol, r"^[A-Z][A-Z0-9]{1,}$|^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$",
                             f"{where}: bad symbol")
            self.assertTrue(
                skill in KNOWN_SKILLS,
                f"{where}: {symbol} is owned by unknown skill {skill!r}; "
                f"skill names are the stable API — add it to KNOWN_SKILLS only "
                f"if upstream really published it",
            )
            paths, declared = expand_paths(path_cell)
            self.assertTrue(paths, f"{where}: {symbol} has no skill-relative path")
            for value in paths:
                self.assertTrue(value.strip(), f"{where}: {symbol} has an empty path")
            if declared is not None:
                self.assertEqual(
                    declared,
                    len(paths),
                    f"{where}: {symbol} says {declared} files but enumerates {len(paths)}",
                )
            self.assertTrue(what.strip(), f"{where}: {symbol} has no description")
            self.assertTrue(used_by.strip(), f"{where}: {symbol} has no 'Used by' entry")
            self.assertTrue(
                symbol not in seen,
                f"{where}: {symbol} is already defined at line {seen.get(symbol)} — "
                f"a duplicated symbol with two paths is exactly the silent rot "
                f"this map exists to prevent",
            )
            seen[symbol] = line


class RegisteredPathsResolve(unittest.TestCase):
    def test_every_registered_path_exists(self):
        rows = registry_rows()
        homes = skill_homes()
        owners = sorted({row[1] for row in rows})
        resolved = {name: resolve_skill(name, homes) for name in owners}
        if not any(resolved.values()):
            self.skipTest(
                "no HyperFrames skill install found under any $SKILL_HOMES entry "
                f"(probed {len(homes)} homes) — the ecosystem is optional at test "
                "time; run `npx hyperframes skills update` to verify pointers"
            )

        missing_skills = sorted(name for name, path in resolved.items() if path is None)
        self.assertFalse(
            missing_skills,
            f"{rel(COMPAT)}: the ecosystem is installed but incomplete — "
            f"{', '.join(missing_skills)} not found under any $SKILL_HOMES entry. "
            f"`skills update` with no names never expands a partial install; run "
            f"`npx hyperframes skills update {' '.join(missing_skills)}`",
        )

        broken = []
        for symbol, skill, path_cell, _what, _used, line in rows:
            root = resolved[skill]
            if root is None:
                # Unreachable: the assertion above already failed on any unresolved
                # skill. Kept explicit so the invariant is visible to readers and
                # type checkers instead of being implied by a prior assertion.
                continue
            for value in expand_paths(path_cell)[0]:
                if not (root / value).exists():
                    broken.append(f"{rel(COMPAT)}:{line}: {symbol} -> {skill}/{value}")
        self.assertFalse(
            broken,
            "registered upstream paths no longer resolve — upstream relaid out "
            "the skill and this map is the one place to repair it:\n  "
            + "\n  ".join(broken),
        )


class PathsStayInTheMap(unittest.TestCase):
    def test_no_intra_skill_paths_outside_compat_map(self):
        violations = []
        for path in GOVERNED_PROSE:
            if rel(path) in RULE_DOC_ALLOWLIST:
                continue
            for number, line, _inside in iter_lines(path):
                for skill, target in CITATION.findall(line):
                    if PATH_LIKE.search(target.strip()):
                        violations.append(
                            f"{rel(path)}:{number}: `{skill}` -> `{target}` — {FIX}"
                        )
        self.assertFalse(
            violations,
            "intra-skill path citations found outside compat/ecosystem.md:\n  "
            + "\n  ".join(violations),
        )

    def test_no_registered_path_string_outside_compat_map(self):
        """The arrow form is only one way to leak a path; a bare mention leaks too."""
        registered = set()
        for _symbol, _skill, path_cell, _what, _used, _line in registry_rows():
            for value in expand_paths(path_cell)[0]:
                if "/" in value:  # `SKILL.md` alone is not identifying
                    registered.add(value)
        violations = []
        for path in GOVERNED_PROSE:
            name = rel(path)
            if name in RULE_DOC_ALLOWLIST:
                continue
            for number, line, inside in iter_lines(path):
                for value in registered:
                    if value not in line:
                        continue
                    if inside and (name, value) in RUNNABLE_PATH_ALLOWLIST:
                        continue
                    violations.append(f"{name}:{number}: `{value}` — {FIX}")
        self.assertFalse(
            violations,
            "registered upstream paths quoted outside compat/ecosystem.md:\n  "
            + "\n  ".join(violations),
        )

    def test_no_distinctive_basename_outside_compat_map(self):
        """A bare basename leaks a path just as effectively as a full one.

        The check above matches the registered string verbatim, so it never
        sees prose that drops the directory — the real form this rule was
        first violated in: "live in the `hyperframes` skill at
        `visual-styles.md`" (wrong skill *and* an unregistered path, invisible
        to every other assertion here).

        Scope is deliberately narrow to stay false-positive free: only
        hyphenated basenames, which are distinctive enough that a coincidental
        prose match is implausible, and only those that do not collide with a
        file this repo owns.
        """
        owned = owned_basenames()
        distinctive = {}
        for symbol, skill, path_cell, _what, _used, _line in registry_rows():
            for value in expand_paths(path_cell)[0]:
                base = value.rsplit("/", 1)[-1]
                if "-" in base and base not in owned:
                    distinctive.setdefault(base, (symbol, skill))

        violations = []
        for path in GOVERNED_PROSE:
            name = rel(path)
            if name in RULE_DOC_ALLOWLIST:
                continue
            for number, line, inside in iter_lines(path):
                for base, (symbol, skill) in distinctive.items():
                    if base not in line:
                        continue
                    # Reuse the one allowlist rather than keeping a second copy
                    # keyed by basename — two lists would drift, which is the
                    # failure this suite exists to prevent. An entry sanctioning
                    # `scripts/animation-map.mjs` also sanctions the basename.
                    if inside and any(
                        allowed_file == name
                        and base in (allowed_path, allowed_path.rsplit("/", 1)[-1])
                        for allowed_file, allowed_path in RUNNABLE_PATH_ALLOWLIST
                    ):
                        continue
                    violations.append(
                        f"{name}:{number}: `{base}` — name the capability instead: "
                        f"`{skill}` -> `{symbol}`. {FIX}"
                    )
        self.assertFalse(
            violations,
            "upstream filenames quoted outside compat/ecosystem.md:\n  "
            + "\n  ".join(violations),
        )


class SymbolsAreDefined(unittest.TestCase):
    def test_referenced_symbols_are_defined(self):
        defined = defined_symbols()
        self.assertIn("VISUAL_STYLES", defined, "registry parse produced no symbols")
        undefined = {
            symbol: sites
            for symbol, sites in referenced_symbols().items()
            if symbol not in defined
        }
        report = [
            f"{sites[0][0]}:{sites[0][1]}: {symbol} "
            f"({len(sites)} site{'s' if len(sites) > 1 else ''})"
            for symbol, sites in sorted(undefined.items())
        ]
        self.assertFalse(
            report,
            "capability symbols cited in prose but not defined in "
            "compat/ecosystem.md — either the symbol is misspelled or the "
            "capability needs a registry row:\n  " + "\n  ".join(report),
        )


class RecipeCitations(unittest.TestCase):
    """Bare rule/blueprint citations in `grammar/` and `reasoning/` resolve.

    ADR-007 keeps upstream *paths* in the map; these two namespaces are the
    exception it grants, because a rule NAME is a stable identifier while its
    path is not. The exception only holds if the names are checked — an invented
    or renamed recipe is otherwise a dead pointer no gate can see.
    """

    def setUp(self):
        self.rules, self.blueprints = upstream_recipe_names()

    def require_ecosystem(self):
        """Return (rules, blueprints), or skip when the ecosystem is absent.

        The guard *returns* the two sets rather than narrowing `self.rules` in
        place, so a caller cannot reach them without passing through it. Both
        halves are checked: `upstream_recipe_names` returns the pair or
        `(None, None)`, and binding them here makes that invariant visible to a
        reader instead of leaving `None | None` one forgotten call away.
        """
        rules, blueprints = self.rules, self.blueprints
        if rules is None or blueprints is None:
            self.skipTest(
                "hyperframes-animation is not installed under any $SKILL_HOMES "
                "entry, so the rule/blueprint indexes cannot be read — the "
                "ecosystem is optional at test time; run "
                "`npx hyperframes skills update hyperframes-animation` to verify "
                "citations"
            )
        return rules, blueprints

    def test_scanner_has_a_vocabulary_to_subtract(self):
        """A silently-empty exclusion set would turn every tag into a citation."""
        self.assertTrue(
            REASONING_PROSE,
            "grammar/ and reasoning/ parsed as empty — the reasoning layer moved "
            "and this suite is now checking nothing",
        )
        self.assertIn(
            "timeline-choreography",
            capability_tags(),
            f"{rel(CATALOG)}: the `### The tags` table did not parse; every "
            f"capability tag would be misread as an upstream recipe citation",
        )
        self.assertIn(
            "html-in-canvas",
            runtime_values(),
            f"{rel(SCENE_ANALYSIS)}: the `runtime:` row of the director-keys "
            f"table did not parse",
        )
        self.assertTrue(
            camera_key_values(),
            f"{rel(CAMERA_GRAMMAR)}: neither the Key column of the grammar table "
            f"nor the paragraph stating the `-3d` tier-suffix rule yielded any "
            f"`camera:` value, so every director-key literal in that file "
            f"(`push-in`, `exploded-3d`, …) now reads as an upstream recipe name",
        )

    def test_exclusions_never_shadow_an_upstream_name(self):
        """An exclusion that swallows a real name would hide a dead pointer."""
        rules, blueprints = self.require_ecosystem()
        names = rules | blueprints
        shadowed = sorted(names & (set(NON_RECIPE_TOKENS) | non_recipe_vocabulary()))
        self.assertFalse(
            shadowed,
            "these local vocabulary terms collide with an upstream rule/blueprint "
            "name, so citing them would silently skip resolution: "
            + ", ".join(shadowed),
        )
        swallowed = sorted(n for n in names if n.startswith(NON_RECIPE_PREFIXES))
        self.assertFalse(
            swallowed,
            "these upstream names carry a structural non-recipe prefix, so "
            f"NON_RECIPE_PREFIXES {NON_RECIPE_PREFIXES} now hides real citations: "
            + ", ".join(swallowed),
        )

    def test_every_candidate_resolves_upstream(self):
        """The closed-world check: no unclassifiable token survives.

        A candidate is either a real rule, a real blueprint, or a bug — an
        invented name, a typo, or a vocabulary term the grammar in
        `recipe_citation_candidates` does not yet know about. All three need a
        human, so all three are reported the same way.
        """
        rules, blueprints = self.require_ecosystem()
        names = rules | blueprints
        stems = registered_path_stems()
        candidates = recipe_citation_candidates()
        self.assertTrue(
            candidates, "no recipe citations found at all — the scanner is broken"
        )
        violations = []
        for token, sites in sorted(candidates.items()):
            where = f"{sites[0][0]}:{sites[0][1]}"
            if token in stems:
                symbol, skill = stems[token]
                violations.append(
                    f"{where}: `{token}` is both a recipe and a registered "
                    f"capability — cite `{skill}` -> `{symbol}` instead "
                    f"(compat/ecosystem.md pins the SYMBOL for this overlap)"
                )
            elif token not in names:
                violations.append(
                    f"{where}: `{token}` is not a rule in RULES_INDEX nor a "
                    f"blueprint id in BLUEPRINT_INDEX ({len(sites)} site"
                    f"{'s' if len(sites) > 1 else ''}) — fix the name, or, if it "
                    f"is local vocabulary rather than a citation, teach "
                    f"recipe_citation_candidates() where it is defined"
                )
        self.assertFalse(
            violations,
            "unresolvable upstream recipe citations:\n  " + "\n  ".join(violations),
        )

    def test_citations_carry_no_directory_or_extension(self):
        """`rules/x.md` reads as a path and violates ADR-007's one rule.

        Runs without the ecosystem installed: this is a syntax rule, not a
        resolution one.
        """
        owned = owned_basenames()
        violations = []
        for path in REASONING_PROSE:
            for number, line, inside in iter_lines(path):
                if inside:
                    continue
                for span in INLINE_CODE.findall(line):
                    token = span.strip()
                    if not PATHY_RECIPE.match(token):
                        continue
                    if BARE_BASENAME.match(token) and token in owned:
                        continue  # a repo-owned file, cited without its directory
                    violations.append(f"{rel(path)}:{number}: `{token}` — {CITE_BARE}")
        self.assertFalse(
            violations,
            "path-shaped recipe citations:\n  " + "\n  ".join(violations),
        )

    def test_declared_namespace_counts_match_the_indexes(self):
        """compat/ecosystem.md publishes both counts; drift is the 47-vs-48 bug."""
        rules, blueprints = self.require_ecosystem()
        blob = read(COMPAT)
        for label, pattern, actual in (
            ("rule", DECLARED_RULE_COUNT, rules),
            ("blueprint", DECLARED_BLUEPRINT_COUNT, blueprints),
        ):
            match = pattern.search(blob)
            # `fail`, not `assertIsNotNone`: the very next line reads
            # `match.group(1)`, and a missing sentence must stop here with the
            # actionable message rather than raise AttributeError on None.
            if match is None:
                self.fail(
                    f"{rel(COMPAT)}: § Citing upstream vocabulary no longer states "
                    f"how many {label}s upstream publishes"
                )
            self.assertEqual(
                int(match.group(1)),
                len(actual),
                f"{rel(COMPAT)}: § Citing upstream vocabulary says "
                f"{match.group(1)} {label}s, the installed index publishes "
                f"{len(actual)} — update the map, never the index",
            )


if __name__ == "__main__":
    unittest.main()
