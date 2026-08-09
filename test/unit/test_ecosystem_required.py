#!/usr/bin/env python3
"""`HVE_REQUIRE_ECOSYSTEM=1` turns "the ecosystem is absent" into a failure.

The pointer-validity suite and the storyboard extra-keys probes skip on a
machine without the HyperFrames ecosystem. Locally that is correct — the
ecosystem is optional at test time. But CI's bare checkout has no ecosystem
either, so the guards ADR-007 calls "the only thing that protects the
registry" skipped on every CI run, and a green badge proved the shape rules
only: the upstream relayout that motivated ADR-007 would have landed green.

CI's provisioned job installs the ecosystem (test/install_ecosystem.py) and
sets `HVE_REQUIRE_ECOSYSTEM=1`. Under that flag, this module asserts the
exact preconditions whose absence makes those suites skip — so a failed or
partial install fails the job loudly instead of silently skipping the tests
the job exists to run. Without the flag, nothing here runs, and the
bare-machine behavior is unchanged.
"""

import os
import shutil
import unittest

import test_compat_pointers as pointers
import test_storyboard_extra_keys as storyboard


REQUIRED = os.environ.get("HVE_REQUIRE_ECOSYSTEM") == "1"


@unittest.skipUnless(
    REQUIRED,
    "HVE_REQUIRE_ECOSYSTEM is not set — the ecosystem stays optional here",
)
class TheProvisionedJobActuallyRunsTheGuards(unittest.TestCase):
    def test_every_registry_owner_resolves(self):
        """The precondition of `test_every_registered_path_exists` and the
        citation checks: every skill the compat map registers paths for must
        be installed, or those tests skip and the map goes unverified."""
        homes = pointers.skill_homes()
        owners = sorted({row[1] for row in pointers.registry_rows()})
        unresolved = sorted(
            owner for owner in owners
            if pointers.resolve_skill(owner, homes) is None
        )
        self.assertFalse(
            unresolved,
            "this run REQUIRES the ecosystem, but these registered skills did "
            f"not resolve under any probed home: {', '.join(unresolved)} — "
            "the pointer-validity suite is skipping instead of verifying. "
            "Did test/install_ecosystem.py run, and into a probed home?",
        )

    def test_the_round_trip_probe_has_its_parser_and_node(self):
        """The preconditions of the STORYBOARD_EXTRA_KEYS behavior probe:
        a resolvable format document, a vendored parser module, and node."""
        homes = storyboard.skill_homes()
        self.assertTrue(
            homes,
            "no skill home resolved at all — the extra-keys probe is skipping",
        )
        self.assertIsNotNone(
            storyboard.format_document(homes),
            "the storyboard format document did not resolve — the extra-keys "
            "probe is skipping instead of guarding the preserved-`extra` "
            "assumption the whole storyboard format rests on",
        )
        self.assertTrue(
            storyboard.vendored_parsers(homes),
            "no installed module exports the storyboard parser — the "
            "round-trip half of the probe is skipping",
        )
        self.assertIsNotNone(
            shutil.which("node"),
            "node is not on PATH — the round-trip half of the probe needs it",
        )


if __name__ == "__main__":
    unittest.main()
