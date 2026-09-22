#!/usr/bin/env python3
"""Native Bash smoke checks; real runtimes, isolated homes, no real installers."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_requirements.sh"


class NativeShellChecks(unittest.TestCase):
    bash = ""
    expected_platform = ""
    expected_bash = ""

    @classmethod
    def setUpClass(cls):
        if sys.platform != cls.expected_platform:
            raise RuntimeError(
                f"Expected native Python on {cls.expected_platform}, got {sys.platform}"
            )
        result = subprocess.run(
            [cls.bash, "--noprofile", "--norc", "-c",
             'printf "%s\\n" "$BASH_VERSION"; uname -s'],
            capture_output=True, text=True, check=True, timeout=30,
        )
        version, system = result.stdout.strip().splitlines()
        if cls.expected_bash and not version.startswith(cls.expected_bash + "."):
            raise RuntimeError(f"Expected Bash {cls.expected_bash}, got {version}")
        if sys.platform == "win32" and not system.startswith(("MINGW", "MSYS")):
            raise RuntimeError(f"Expected native Windows Git Bash, got {system}")
        if sys.platform == "darwin" and system != "Darwin":
            raise RuntimeError(f"Expected native macOS Bash, got {system}")
        node = shutil.which("node")
        if not node:
            raise RuntimeError("A real Node runtime is required")
        node_platform = subprocess.run(
            [node, "-p", "process.platform"], capture_output=True, text=True,
            check=True, timeout=30,
        ).stdout.strip()
        if node_platform != cls.expected_platform:
            raise RuntimeError(f"Expected native Node, got {node_platform}")
        print(f"Native host: Python={sys.platform}, Node={node_platform}, "
              f"Bash={version}, uname={system}", flush=True)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="hve native shell ")
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        (self.work / "home").mkdir()
        bin_dir = self.work / "bin"
        bin_dir.mkdir()
        self.log = self.work / "install-commands.log"
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        for name in ("BASH_ENV", "ENV"):
            self.env.pop(name, None)
        # Convert with the chosen shell, not an assumed Windows mount prefix.
        result = subprocess.run(
            [self.bash, "--noprofile", "--norc", "-c",
             'cd "$1" && pwd -P', "native-path", self.work.as_posix()],
            env=self.env, capture_output=True, text=True, check=True, timeout=30,
        )
        self.shell_work = result.stdout.strip()
        self.env["HOME"] = self.shell_work + "/home"
        self.env["CHECKER_TEST_LOG"] = "install-commands.log"
        for command in ("npx", "npm", "pip3", "curl"):
            path = bin_dir / command
            path.write_bytes(
                (f'#!/bin/sh\nprintf "%s %s\\n" "{command}" "$*" '
                 '>> "$CHECKER_TEST_LOG"\n'
                 '[ "${PORTABILITY_ALLOW_FIX:-0}" = 1 ]\n').encode("utf-8")
            )
            path.chmod(0o755)

    def run_bash(self, *args, input_bytes=None, env=None):
        return subprocess.run(
            [self.bash, "--noprofile", "--norc", "-c",
             'PATH="$1:$PATH"; export PATH; shift; '
             'exec "$BASH" --noprofile --norc "$@"',
             "native-check", self.shell_work + "/bin", *args],
            input=input_bytes, cwd=self.work, env=env or self.env,
            capture_output=True, timeout=60,
        )

    def assert_exit(self, result, codes):
        self.assertIn(
            result.returncode, codes,
            result.stdout.decode("utf-8", errors="replace")
            + result.stderr.decode("utf-8", errors="replace"),
        )

    def test_both_scripts_parse(self):
        for script in (SCRIPT, ROOT / "test" / "run.sh"):
            with self.subTest(script=script.name):
                self.assert_exit(self.run_bash("-n", script.as_posix()), (0,))

    def test_report_modes_from_file_stdin_and_standalone_copy(self):
        standalone = self.work / "standalone checker.sh"
        shutil.copyfile(SCRIPT, standalone)
        for invocation in ("file", "stdin", "standalone"):
            for flags in ((), ("--json",), ("--plan",)):
                with self.subTest(invocation=invocation, flags=flags):
                    if invocation == "stdin":
                        result = self.run_bash(
                            "-s", "--", *flags, input_bytes=SCRIPT.read_bytes()
                        )
                    else:
                        path = SCRIPT if invocation == "file" else standalone
                        result = self.run_bash(path.as_posix(), *flags)
                    self.assert_exit(result, (0, 1))
                    self.assertFalse(self.log.exists(), "report mode invoked an installer")
                    if flags == ("--json",):
                        report = json.loads(result.stdout)
                        self.assertEqual(report["schema_version"], 1)
                        checks = {item["id"]: item for item in report["checks"]}
                        for name in ("node", "python"):
                            self.assertEqual(checks[name]["state"], "ready", checks[name])
                        blocked = any(item["tier"] == "required"
                                      and item["state"] == "blocked"
                                      for item in checks.values())
                        self.assertEqual(result.returncode, int(blocked))
                    elif flags == ("--plan",):
                        self.assertIn(b"No changes will be made.", result.stdout)
                    else:
                        self.assertIn(b"requirements check", result.stdout)

    def test_help_and_invalid_arguments(self):
        result = self.run_bash(SCRIPT.as_posix(), "--help")
        self.assert_exit(result, (0,))
        for flags in (("--unknown",), ("--fix=unknown",), ("--json", "--fix"),
                      ("--plan", "--fix"), ("--json", "--plan")):
            with self.subTest(flags=flags):
                result = self.run_bash(SCRIPT.as_posix(), *flags)
                self.assert_exit(result, (2,))
                self.assertTrue(result.stderr)
                self.assertFalse(self.log.exists())

    def test_installed_skill_requires_its_language_helper(self):
        root = self.work / "installed skill"
        scripts = root / "scripts"
        scripts.mkdir(parents=True)
        (root / "SKILL.md").write_bytes(b"---\nname: hve-video-director\n---\n")
        checker = scripts / SCRIPT.name
        helper = scripts / "language_tools.mjs"
        shutil.copyfile(SCRIPT, checker)

        result = self.run_bash(checker.as_posix(), "--json")
        self.assert_exit(result, (1,))
        node = next(item for item in json.loads(result.stdout)["checks"] if item["id"] == "node")
        self.assertEqual(node["state"], "blocked")
        self.assertIn("language_tools.mjs is missing", node["detail"])
        self.assertIn("Reinstall hve-video-director", node["fixability"]["command"])

        shutil.copyfile(SCRIPT.with_name("language_tools.mjs"), helper)
        result = self.run_bash(checker.as_posix(), "--json")
        self.assert_exit(result, (0, 1))
        node = next(item for item in json.loads(result.stdout)["checks"] if item["id"] == "node")
        self.assertEqual(node["state"], "ready", node)
        self.assertFalse(self.log.exists(), "checking installation health must remain offline")

    def test_stdin_fixes_never_reach_real_installers(self):
        allowed = {
            "npx --yes puppeteer browsers install chrome-headless-shell",
            "npx --yes skills add heygen-com/hyperframes --global --yes",
            "pip3 install --user openai-whisper",
        }
        for flag in ("--fix=chrome-shell", "--fix"):
            with self.subTest(flag=flag):
                self.log.unlink(missing_ok=True)
                result = self.run_bash(
                    "-s", "--", flag, input_bytes=SCRIPT.read_bytes(),
                    env=dict(self.env, PORTABILITY_ALLOW_FIX="1"),
                )
                self.assert_exit(result, (0, 1))
                self.assertIn(b"--fix: applying", result.stdout)
                calls = self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []
                permitted = allowed if flag == "--fix" else {
                    "npx --yes puppeteer browsers install chrome-headless-shell"
                }
                self.assertTrue(set(calls).issubset(permitted), calls)
                print(f"{flag}: intercepted installer calls: {calls}", flush=True)

    @unittest.skipUnless(sys.platform == "win32", "native Windows checkout regression")
    def test_windows_autocrlf_checkout_executes_both_scripts(self):
        checkout = self.work / "autocrlf checkout"
        checkout.mkdir()
        git = shutil.which("git")
        self.assertIsNotNone(git, "Git is required to verify Windows checkout behavior")
        subprocess.run(
            [git, "-c", "core.autocrlf=true", "checkout-index",
             f"--prefix={checkout.as_posix()}/", "--",
             "scripts/check_requirements.sh", "test/run.sh"],
            cwd=ROOT, capture_output=True, check=True, timeout=30,
        )
        unit = checkout / "test" / "unit"
        unit.mkdir()
        (unit / "test_smoke.py").write_bytes(
            b"import unittest\n\nclass Smoke(unittest.TestCase):\n"
            b"    def test_runner(self):\n        self.assertTrue(True)\n"
        )
        for name, flags in (("scripts/check_requirements.sh", ("--help",)),
                            ("test/run.sh", ())):
            with self.subTest(script=name):
                path = checkout / name
                result = self.run_bash(path.as_posix(), *flags)
                self.assert_exit(result, (0,))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bash", required=True, help="Exact native Bash executable")
    parser.add_argument("--expected-platform", required=True, choices=("darwin", "win32", "linux"))
    parser.add_argument("--expected-bash", default="", help="Required major.minor, e.g. 3.2")
    args = parser.parse_args()
    executable = shutil.which(args.bash)
    if not executable:
        parser.error(f"Bash executable not found: {args.bash}")
    NativeShellChecks.bash = executable
    NativeShellChecks.expected_platform = args.expected_platform
    NativeShellChecks.expected_bash = args.expected_bash
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeShellChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
