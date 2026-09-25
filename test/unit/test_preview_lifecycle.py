#!/usr/bin/env python3
"""Verify that HyperFrames previews have an explicit managed lifecycle."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class PreviewLifecycleTestCase(unittest.TestCase):
    """Test preview startup, shutdown, and user-facing documentation."""

    def test_phase_four_stops_managed_preview_before_checkpoint(self):
        """Phase 4 stops its managed preview before stamping completion."""
        production = (
            ROOT / "workflows" / "phase-4-production.md"
        ).read_text(encoding="utf-8")

        start = production.index("npx hyperframes preview . --background")
        approval = production.index('"How does the composition look?')
        stop = production.index("npx hyperframes preview . --stop")
        stamp = production.index(
            'stamp phase-4',
            production.index("## Checkpoint"),
        )

        self.assertLess(start, approval)
        self.assertLess(approval, stop)
        self.assertLess(stop, stamp)
        self.assertIn("before leaving Phase 4", production)
        self.assertIn("Closing the Studio browser does not stop", production)

    def test_readme_documents_preview_shutdown(self):
        """The README tells users to stop the preview after review."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("npx hyperframes preview --background", readme)
        self.assertIn("npx hyperframes preview --stop", readme)
        self.assertIn("Closing the Studio browser does not stop", readme)


if __name__ == "__main__":
    unittest.main()
