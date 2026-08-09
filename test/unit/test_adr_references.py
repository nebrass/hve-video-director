"""ADR citations are load-bearing, so they have to resolve.

Ten records govern this repo and citations point at them from every layer. `ADR-001`
alone is named dozens of times, in prose that tells an agent it may not preselect an
answer. (No count is written here on purpose: this file was briefly wrong about its own
numbers, because four later commits on the same branch changed them.) A citation is the
only thing standing between "this rule has a reason" and "someone asserted it once":
`(ADR-005)` at the end of a sentence is where a reader goes to check whether the rule
still applies, and a number that resolves to nothing is worse than no citation at all --
it looks checked.

Two ways that rots, both silent:

- A record is renumbered or removed and the citations keep pointing at the old number.
- A citation is written for a record that was planned and never landed. This is live: the
  next number in the series is queued for the premium-motion program, and until that record
  exists no file may cite it.

`docs/` is a frozen M1 snapshot everywhere except `adr.md`, which is amended in place --
so the ADR file is the one thing in there this suite may treat as current.

Scanned via `git ls-files --cached --others --exclude-standard`: the repo is what git would
let you commit — tracked files plus untracked ones that are not ignored. A file citing a record
has to resolve before it is staged, not after; tracked-only made a brand-new workflow file
invisible until someone remembered to `git add`. Ignored tool output (graphify-out/, installed
ecosystem skills) is not this repo's prose and must not be able to fail its checks, and
--exclude-standard honours the same .gitignore rules `git status` does, including nested ones.
"""

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADR_FILE = next(ROOT.glob("docs/superpowers/specs/*/adr.md"), None)

CITATION = re.compile(r"\bADR-(\d+)\b")
HEADING = re.compile(r"^## ADR-(\d+)\b", re.M)

SCAN_SUFFIXES = {".md", ".py", ".sh", ".json", ".html"}


def scanned_files():
    # An exported source copy is not a worktree. That is a reason to skip, not to error:
    # this would otherwise be the only test in the tree that cannot run outside git.
    try:
        done = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files",
             "--cached", "--others", "--exclude-standard", "-z"],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, OSError) as error:
        raise unittest.SkipTest(f"not a git worktree, so the file list is unavailable: {error}")
    # dict.fromkeys dedupes: --cached emits one entry per stage during a merge conflict.
    listed = dict.fromkeys(done.stdout.split("\0"))
    for name in listed:
        if not name:
            continue
        path = ROOT / name
        if path.suffix in SCAN_SUFFIXES and path.is_file():
            yield path


class AdrGovernanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert ADR_FILE is not None, "no adr.md under docs/superpowers/specs/*/"
        cls.text = ADR_FILE.read_text(encoding="utf-8")
        cls.defined = {int(n) for n in HEADING.findall(cls.text)}

    def test_the_records_parse(self):
        """Guard on the guard: a heading style change would empty `defined` and turn
        the resolution check below into an assertion that nothing is cited."""
        self.assertGreaterEqual(len(self.defined), 9, f"parsed only {self.defined}")

    def test_the_numbering_has_no_gaps_or_duplicates(self):
        """ADRs are a numbered series. A gap means a record was removed rather than
        superseded in place, which is how a decision loses its history."""
        numbers = [int(n) for n in HEADING.findall(self.text)]
        self.assertEqual(sorted(numbers), numbers, "ADR headings are out of order")
        self.assertEqual(len(numbers), len(set(numbers)), f"duplicate ADR number in {numbers}")
        self.assertEqual(
            list(range(1, max(numbers) + 1)), numbers,
            f"ADR numbering has a gap: {numbers}",
        )

    def test_every_citation_in_the_repo_resolves(self):
        dangling = []
        for path in scanned_files():
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for number, line in enumerate(text.splitlines(), 1):
                for cited in sorted({int(n) for n in CITATION.findall(line)}):
                    if cited not in self.defined:
                        dangling.append(
                            f"{path.relative_to(ROOT)}:{number}: cites ADR-{cited:03d}, "
                            "which has no record"
                        )
        self.assertEqual(
            [], dangling,
            "a citation points at a record that does not exist -- it reads as checked "
            "and is not:\n  " + "\n  ".join(dangling),
        )

    def test_the_status_is_declared_once_and_explicitly(self):
        """Whatever the status is, it is stated -- and stating it is a deliberate act.

        It said PROPOSED for the whole of M0-M6 while the tree treated the records as
        binding law. The check is not that it says ACCEPTED; it is that the file cannot
        go silent on the question.
        """
        statuses = re.findall(r"^\*\*Status of all ADRs:\*\*\s*(\w+)", self.text, re.M)
        self.assertEqual(1, len(statuses), f"expected exactly one status line, found {statuses}")
        self.assertIn(statuses[0], {"ACCEPTED", "PROPOSED", "SUPERSEDED"}, statuses[0])


if __name__ == "__main__":
    unittest.main()
