#!/usr/bin/env python3
"""Every credential the skill's own scripts need must be reported by the checker.

Phase -1 exists so a run fails at setup rather than at Phase 5. That promise
holds only while `scripts/check_requirements.sh` knows about every environment
variable the skill's scripts actually read.

The drift this catches really happened. M6 retired `scripts/search_music.py`
and the checker gained a comment saying nothing read `FREESOUND_API_KEY` any
more. The script was then restored — Freesound is the *recommended* music
strategy — and the comment stayed. The checker went on asserting a code path
was gone while Phase 5 invoked it, so a user could take the recommended option,
complete four phases, and fail on a missing key the setup step had pronounced
irrelevant.

Note the inversion that made it invisible: the checker probed
`ELEVENLABS_API_KEY`, which no script in this repo reads (it serves the
delegated engine's route), and skipped the only variable that any of them do.
Counting probes would have looked healthy. This test reads the scripts.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
CHECKER = SCRIPTS / "check_requirements.sh"

# Read from os.environ in any of the shapes the helpers use — including
# `os.getenv`, the idiomatic spelling nothing in scripts/ uses *yet*.
ENV_READ = re.compile(
    r"environ\.get\(\s*[\"']([A-Z][A-Z0-9_]{3,})[\"']"
    r"|environ\[\s*[\"']([A-Z][A-Z0-9_]{3,})[\"']"
    r"|getenv\(\s*[\"']([A-Z][A-Z0-9_]{3,})[\"']"
)

# Variables a script reads that are NOT the user's to provide, so the checker
# has no business reporting them. Keep this empty unless there is a real case;
# an entry here is an exemption, and an exemption is how the last gap survived.
NOT_USER_SUPPLIED = frozenset()


class CredentialCoverage(unittest.TestCase):
    def env_vars_scripts_read(self):
        found = {}
        for script in sorted(SCRIPTS.glob("*.py")):
            text = script.read_text(encoding="utf-8")
            for groups in ENV_READ.findall(text):
                name = next(g for g in groups if g)
                found.setdefault(name, set()).add(script.name)
        return found

    def test_the_scanner_catches_every_env_read_spelling(self):
        """Guard the guard: `os.getenv` is the idiomatic spelling a future
        credential is most likely to use, and a spelling the scanner misses is
        a credential the checker never probes — the exact drift class this
        module exists to stop (mutation-verified before this test existed)."""
        snippet = (
            'a = os.environ.get("VAR_ALPHA")\n'
            'b = os.environ["VAR_BRAVO"]\n'
            'c = os.getenv("VAR_CHARLIE", "fallback")\n'
        )
        names = set()
        for groups in ENV_READ.findall(snippet):
            names.update(g for g in groups if g)
        self.assertEqual(names, {"VAR_ALPHA", "VAR_BRAVO", "VAR_CHARLIE"})

    def test_every_env_var_a_script_reads_is_probed_by_the_checker(self):
        checker = CHECKER.read_text(encoding="utf-8")
        unprobed = []
        for name, users in sorted(self.env_vars_scripts_read().items()):
            if name in NOT_USER_SUPPLIED:
                continue
            # A probe is a real shell expansion of the variable, not a mention
            # in prose — a comment claiming it is unneeded is exactly the bug.
            if not re.search(r"\$\{?" + re.escape(name) + r"\b", checker):
                unprobed.append(f"{name} (read by {', '.join(sorted(users))})")
        self.assertFalse(
            unprobed,
            "scripts read environment variables that check_requirements.sh never "
            "probes, so Phase -1 reports a clean setup and the run fails later:\n  "
            + "\n  ".join(unprobed),
        )

    def test_the_checker_reports_a_check_for_each_such_variable(self):
        """Probing is not enough — it has to surface as a check the user sees."""
        import json
        import subprocess

        result = subprocess.run(
            ["bash", str(CHECKER), "--json"],
            capture_output=True, text=True, cwd=str(ROOT), check=False,
        )
        payload = json.loads(result.stdout)
        labels = {c.get("label", "") for c in payload["checks"]}
        missing = [
            name for name in sorted(self.env_vars_scripts_read())
            if name not in NOT_USER_SUPPLIED and name not in labels
        ]
        self.assertFalse(
            missing,
            "no check is reported for: " + ", ".join(missing)
            + " — a probe with no check tells the user nothing",
        )


if __name__ == "__main__":
    unittest.main()
