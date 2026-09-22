"""Checkout conversion must not alter source scripts or the recorded example."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class CheckoutPolicyTests(unittest.TestCase):
    def test_autocrlf_checkout_preserves_committed_bytes(self):
        paths = [
            "scripts/check_requirements.sh", "test/run.sh",
            "example/project-plan.md", "example/.hve/brief-state.json",
        ]
        git = shutil.which("git")
        self.assertIsNotNone(git, "Git is required for checkout policy verification")
        with tempfile.TemporaryDirectory(prefix="checkout policy ") as temporary:
            root = Path(temporary)
            subprocess.run(
                [git, "-c", "core.autocrlf=true", "checkout-index",
                 f"--prefix={root.as_posix()}/", "--", *paths],
                cwd=ROOT, check=True, capture_output=True,
            )
            for relative in paths:
                with self.subTest(path=relative):
                    committed = subprocess.run(
                        [git, "show", f":{relative}"], cwd=ROOT,
                        check=True, capture_output=True,
                    ).stdout
                    self.assertEqual((root / relative).read_bytes(), committed)


if __name__ == "__main__":
    unittest.main()
