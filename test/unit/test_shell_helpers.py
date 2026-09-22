from pathlib import Path
import tempfile
import unittest
from unittest import mock

import shell_helpers


class ShellPathTests(unittest.TestCase):
    def test_shell_paths_round_trip_through_native_python(self):
        with tempfile.TemporaryDirectory(prefix="shell paths ") as temporary:
            path = Path(temporary).resolve() / "nested directory"
            path.mkdir()
            for shell in ("bash", "sh"):
                with self.subTest(shell=shell):
                    value = shell_helpers.shell_path(path, shell)
                    converted = shell_helpers.native_path(value, shell)
                    self.assertTrue(converted.is_absolute())
                    self.assertEqual(converted.resolve(), path)

    def test_missing_shell_is_an_explicit_error(self):
        with mock.patch.object(shell_helpers.shutil, "which", return_value=None):
            with self.assertRaisesRegex(FileNotFoundError, "bash is required"):
                shell_helpers.shell_executable()

    def test_empty_shell_output_is_not_the_working_directory(self):
        with self.assertRaisesRegex(ValueError, "empty shell path"):
            shell_helpers.native_path("")


if __name__ == "__main__":
    unittest.main()
