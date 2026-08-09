"""`compat/ecosystem.md` is the thin waist: every upstream capability resolves through it.

`test_compat_pointers.py` proves a registered path exists upstream. This file proves the
*other* half of a row -- its "Used by" claim. A row that says "Phase 5" while no file in the
repo cites the symbol is a claim about this repo that stopped being true, and nothing else
catches it: the path still resolves, so the pointer suite stays green.

Rows may opt out by saying so in the same cell (**Not wired**, deliberately NOT adopted, ...).
That is a decision, not drift -- several names are registered precisely so a future need
resolves to them instead of re-deriving a path.

Unlike the pointer suite this needs no installed ecosystem: it reads only this repo.
"""

import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ECOSYSTEM = REPO / "compat" / "ecosystem.md"

REGISTRY_HEADER = "| Symbol | Owning skill | Skill-relative path | What it is | Used by |"

# A row may declare itself unwired. Matched case-insensitively against the Used-by cell.
NOT_WIRED_MARKERS = (
    "not wired",
    "not adopted",
    "reserved name",
)

# compat/ecosystem.md is excluded: a row citing itself would make every claim
# self-fulfilling. `test/` and CHANGELOG.md are excluded for exactly the same reason,
# found by an adversarial pass -- a bogus row plus one line in either passed. `docs/` is
# the frozen M1 snapshot and describes the tree as it was.
SKIP_DIRS = {".git", "node_modules", ".agents", "__pycache__", "docs", "test"}
SKIP_FILES = {"CHANGELOG.md"}


def registry_rows():
    """(symbol, used_by) for every capability-registry row in the file."""
    rows = []
    in_table = False
    for line in ECOSYSTEM.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == REGISTRY_HEADER:
            in_table = True
            continue
        if not in_table:
            continue
        if not stripped.startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 5 or set("".join(cells)) <= set("-: "):
            continue
        symbol = cells[0].strip("` ")
        if not re.fullmatch(r"[A-Z][A-Z0-9_]+", symbol):
            continue
        rows.append((symbol, cells[4]))
    return rows


def repo_citations():
    """Every non-compat file's text, so a symbol can be looked for across the repo.

    Enumerated by git rather than rglob, which is not a tidiness preference. rglob read
    975 files here, 893 of them gitignored — including `agent/` (501 files, an installed
    copy of the upstream skills that DEFINE these symbols) and `graphify-out/` (352 files,
    a knowledge-graph dump of this repo). A row satisfied by either is self-fulfilling in
    exactly the way SKIP_DIRS exists to prevent, and the hand-written blocklist had already
    drifted: it listed `.agents` and not `agent`. Git's ignore rules maintain themselves.
    """
    try:
        done = subprocess.run(
            ["git", "-C", str(REPO), "ls-files",
             "--cached", "--others", "--exclude-standard", "-z"],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, OSError) as error:
        raise unittest.SkipTest(f"not a git worktree, so the file list is unavailable: {error}")
    texts = []
    for name in dict.fromkeys(done.stdout.split("\0")):
        if not name:
            continue
        path = REPO / name
        if path.suffix not in {".md", ".py", ".sh", ".html", ".json"} or not path.is_file():
            continue
        if path == ECOSYSTEM:
            continue
        relative = path.relative_to(REPO)
        if any(part in SKIP_DIRS for part in relative.parts) or relative.name in SKIP_FILES:
            continue
        try:
            texts.append((relative, path.read_text(encoding="utf-8")))
        except (UnicodeDecodeError, OSError):
            continue
    return texts


class RegistryClaimTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = registry_rows()
        cls.texts = repo_citations()

    def test_the_registry_parses_at_all(self):
        """A guard on the guard: a table relayout that silently emptied this would
        make every other assertion below vacuously true."""
        self.assertGreater(len(self.rows), 20, "capability registry parsed to almost nothing")

    # Directional matching -- check the symbol appears where the row CLAIMS it is used --
    # was measured too, and is worse than the three below: strict (every named locator)
    # fails 17 of 67 rows and lenient (>=1) fails 8, of which 7 are correct work. A phase
    # reaches a capability through a file it loads (patterns/INDEX.md, the reasoning
    # layer), through a sibling symbol (Phase 3 gets palette and type via VISUAL_STYLES),
    # or through a stable CLI command name -- and it does not even address the flaw below,
    # because narrowing WHERE a token is sought does not change WHAT a token proves: 8 of
    # the 57 rows it passes still pass only on a negated line.
    #
    # A token match proves the symbol is named, not that the naming is a citation --
    # prose rejecting a symbol would satisfy its own row. Left that way deliberately:
    # 22% of citation lines here carry a negation word ("never push the camera under a
    # fixed overlay (MG_ASSET_FUSION)"), so a negation filter fails 7 of 67 real rows and
    # requiring two citations fails 16. The cheap precision was in the scan, not the match.
    def test_every_used_by_claim_resolves_to_a_real_citer(self):
        unresolved = []
        for symbol, used_by in self.rows:
            if any(marker in used_by.lower() for marker in NOT_WIRED_MARKERS):
                continue
            # Word-boundary, so BGM is not satisfied by BGM_PATH in a shell snippet.
            token = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(symbol) + r"(?![A-Za-z0-9_])")
            if any(token.search(text) for _, text in self.texts):
                continue
            unresolved.append(f"{symbol} claims 'Used by: {used_by[:60]}' but nothing cites it")
        self.assertEqual(
            [],
            unresolved,
            "compat rows claim a caller this repo does not have:\n  " + "\n  ".join(unresolved),
        )

    def test_an_unwired_row_says_so_rather_than_leaving_the_cell_empty(self):
        """An empty Used-by reads as 'not looked at yet'. Silence is the one thing a
        registry row may not say -- the exemption has to be a written decision."""
        empty = [symbol for symbol, used_by in self.rows if not used_by.strip()]
        self.assertEqual([], empty, f"registry rows with an empty Used-by cell: {empty}")


if __name__ == "__main__":
    unittest.main()
