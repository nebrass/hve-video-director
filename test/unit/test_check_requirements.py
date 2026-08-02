#!/usr/bin/env python3

import json
import shutil
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_requirements.sh"
WORK_ROOT = ROOT / "test" / ".work"


class RequirementsCheckerTestCase(unittest.TestCase):
    def setUp(self):
        self.work = WORK_ROOT / uuid.uuid4().hex
        self.bin = self.work / "bin"
        self.home = self.work / "home"
        self.log = self.work / "commands.log"
        self.bin.mkdir(parents=True)
        self.home.mkdir()
        self.sandbox = Path(tempfile.mkdtemp(prefix="hve-checker-cwd-"))
        self.addCleanup(shutil.rmtree, self.sandbox, ignore_errors=True)
        self.write_executable("uname", "printf 'Darwin\\n'")

    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)

    def write_executable(self, name, body):
        path = self.bin / name
        path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
        path.chmod(0o755)
        return path

    def environment(self):
        return {
            "PATH": str(self.bin),
            "HOME": str(self.home),
            "CHECKER_TEST_LOG": str(self.log),
            "PYTHONDONTWRITEBYTECODE": "1",
        }

    def install_required_shims(self, include_hyperframes=True, include_chrome=True):
        self.write_executable("node", "printf 'v22.12.0\\n'")
        self.write_executable(
            "npx",
            'printf "npx %s\\n" "$*" >> "$CHECKER_TEST_LOG"\nexit 0',
        )
        self.write_executable("python3", "printf 'Python 3.11.9\\n'")
        self.write_executable("ffmpeg", "printf 'ffmpeg version 7.0\\n'")
        self.write_executable("ffprobe", "printf 'ffprobe version 7.0\\n'")
        if include_hyperframes:
            self.write_executable(
                "hyperframes",
                'if [ "$1" = "--version" ]; then printf "1.2.3\\n"; exit 0; fi\n'
                'if [ "$1" = "transcribe" ]; then exit 0; fi\nexit 0',
            )
        if include_chrome:
            self.write_executable("chrome-headless-shell", "exit 0")

    def install_optional_shims(self, include_whisper=True):
        self.write_executable(
            "pip3",
            'printf "pip3 %s\\n" "$*" >> "$CHECKER_TEST_LOG"\nexit 0',
        )
        names = ["espeak-ng", "asciinema", "agg", "timeout"]
        if include_whisper:
            names.append("whisper")
        for name in names:
            self.write_executable(name, "exit 0")

    def install_skills(self, *names):
        # Defaults to the pair every pre-existing test assumed. Companion skills
        # under test are passed explicitly so their absent case stays absent.
        for name in names or ("hyperframes", "gsap"):
            skill = self.home / ".claude" / "skills" / name / "SKILL.md"
            skill.parent.mkdir(parents=True, exist_ok=True)
            skill.write_text(f"# {name}\n", encoding="utf-8")
        return self.home / ".claude" / "skills"

    def json_checks(self, *args, env=None):
        result = self.run_checker("--json", *args, env=env)
        report = json.loads(result.stdout)
        return result, {check["id"]: check for check in report["checks"]}

    def run_checker(self, *args, env=None, cwd=None):
        # The default cwd MUST stay outside this repository: $SKILL_HOMES holds
        # cwd-relative homes (.claude/skills, .agents/skills, …) and
        # $SKILL_ROOT-relative ones, and $SKILL_ROOT falls back to $PWD. Running
        # from ROOT would let the repo's own installed skills — and any repo
        # .npmrc or node_modules/ — decide what the checker reports.
        return subprocess.run(
            ["/bin/bash", str(SCRIPT), *args],
            cwd=cwd or self.sandbox,
            env=env or self.environment(),
            text=True,
            capture_output=True,
            check=False,
        )

    def test_help_and_unknown_argument(self):
        help_result = self.run_checker("--help")
        self.assertEqual(help_result.returncode, 0)
        for flag in ("--json", "--plan", "--fix=<id,id>"):
            self.assertIn(flag, help_result.stdout)

        unknown = self.run_checker("--wat")
        self.assertEqual(unknown.returncode, 2)
        self.assertIn("unknown arg: --wat", unknown.stderr)

    def test_human_output_preserves_essentials_and_required_exit_codes(self):
        self.install_required_shims()
        self.install_optional_shims()
        self.install_skills()
        env = self.environment()
        env.update({
            "ELEVENLABS_API_KEY": "test",
            "FREESOUND_API_KEY": "test",
        })
        ready = self.run_checker(env=env)
        self.assertEqual(ready.returncode, 0, ready.stdout + ready.stderr)
        self.assertIn("hve-video-director requirements check", ready.stdout)
        self.assertIn("Required", ready.stdout)
        self.assertIn("Node.js 22.12.0", ready.stdout)
        self.assertIn("All required dependencies satisfied.", ready.stdout)

        blocked_bin = self.work / "blocked-bin"
        blocked_bin.mkdir()
        blocked_uname = blocked_bin / "uname"
        blocked_uname.write_text("#!/bin/sh\nprintf 'Darwin\\n'\n", encoding="utf-8")
        blocked_uname.chmod(0o755)
        blocked_env = self.environment()
        blocked_env["PATH"] = str(blocked_bin)
        blocked = self.run_checker(env=blocked_env)
        self.assertEqual(blocked.returncode, 1)
        self.assertIn("Node.js — not found", blocked.stdout)
        self.assertIn("Python 3 — not found", blocked.stdout)
        self.assertIn("Missing required dependencies", blocked.stdout)

    def test_recommended_and_optional_gaps_do_not_fail(self):
        self.install_required_shims()
        self.install_skills()
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("All required dependencies satisfied.", result.stdout)
        self.assertIn("○", result.stdout)

    def assert_companion_skill_degrades(self, name, check_id, phases):
        """A recommended companion skill: present -> ready, absent -> degraded.

        Both directions run the side-effect-free JSON report, so the assertions
        double as proof that discovery never reaches for an installer: the `npx`
        shim appends to $CHECKER_TEST_LOG, and that file must never appear.

        Returns the absent-case check so the caller can assert on the wording
        that is specific to its skill.
        """
        self.install_required_shims()
        home = self.install_skills("hyperframes", "gsap", name)

        present, checks = self.json_checks()
        check = checks[check_id]
        self.assertEqual(present.returncode, 0, present.stdout + present.stderr)
        self.assertEqual(check["state"], "ready")
        self.assertEqual(check["tier"], "recommended")
        self.assertEqual(check["phases"], phases)
        self.assertIn(str(home), check["detail"])
        # No new safe fix ID: these are bundle installs, and the one safe ID
        # that installs the bundle gates on `hyperframes` being absent, so
        # reusing it here would report "already ready" while this skill is
        # still missing.
        self.assertEqual(check["fixability"]["kind"], "manual-online")
        self.assertIsNone(check["fixability"]["id"])
        self.assertEqual(
            check["fixability"]["command"],
            "npx --yes skills add heygen-com/hyperframes --global --yes",
        )
        self.assertFalse(self.log.exists())

        shutil.rmtree(home / name)
        absent, checks = self.json_checks()
        check = checks[check_id]
        # Degraded, never blocked: a missing recommended companion costs a
        # capability, it does not stop the pipeline.
        self.assertEqual(absent.returncode, 0, absent.stdout + absent.stderr)
        self.assertEqual(check["state"], "degraded")
        self.assertEqual(check["tier"], "recommended")
        self.assertEqual(check["phases"], phases)
        self.assertFalse(self.log.exists())
        return check

    def test_motion_doctrine_skill_degrades_without_blocking_phase_4(self):
        check = self.assert_companion_skill_degrades(
            "motion-doctrine", "motion-doctrine-skill", [4]
        )
        # The seam gate is a quality gate. Losing it changes what Phase 4 may
        # claim, which is what the degraded detail has to say.
        self.assertIn("unverified", check["detail"])

    def test_media_use_skill_degrades_to_the_local_audio_scripts(self):
        check = self.assert_companion_skill_degrades(
            "media-use", "media-use-skill", [5]
        )
        self.assertIn("generate_voiceover.py", check["detail"])

    def test_heygen_credential_reports_presence_without_running_the_cli(self):
        self.install_required_shims()
        self.install_skills()
        # Installed throughout: if a presence branch broke, the check would fall
        # through to the CLI-found-but-no-credential degrade instead of silently
        # passing on some other signal.
        self.write_executable(
            "heygen",
            'printf "heygen %s\\n" "$*" >> "$CHECKER_TEST_LOG"\nexit 0',
        )

        for variable in ("HEYGEN_API_KEY", "HYPERFRAMES_API_KEY"):
            with self.subTest(signal=variable):
                env = self.environment()
                env[variable] = "test-token"
                _, checks = self.json_checks(env=env)
                check = checks["heygen-credential"]
                self.assertEqual(check["state"], "ready")
                self.assertIn(f"{variable} is set", check["detail"])
                self.assertFalse(self.log.exists(), "the heygen CLI was run")

        with self.subTest(signal="default credential file"):
            credential = self.home / ".heygen" / "credentials"
            credential.parent.mkdir(parents=True)
            credential.write_text("token\n", encoding="utf-8")
            _, checks = self.json_checks()
            check = checks["heygen-credential"]
            self.assertEqual(check["state"], "ready")
            self.assertIn(str(credential), check["detail"])
            self.assertFalse(self.log.exists(), "the heygen CLI was run")
            shutil.rmtree(credential.parent)

        with self.subTest(signal="HEYGEN_CONFIG_DIR"):
            custom = self.work / "heygen config dir"
            custom.mkdir()
            (custom / "credentials").write_text("token\n", encoding="utf-8")
            env = self.environment()
            env["HEYGEN_CONFIG_DIR"] = str(custom)
            _, checks = self.json_checks(env=env)
            check = checks["heygen-credential"]
            self.assertEqual(check["state"], "ready")
            self.assertIn(str(custom / "credentials"), check["detail"])
            self.assertFalse(self.log.exists(), "the heygen CLI was run")

    def test_heygen_credential_degrades_with_and_without_the_cli(self):
        self.install_required_shims()
        self.install_skills()

        nothing, checks = self.json_checks()
        check = checks["heygen-credential"]
        self.assertEqual(nothing.returncode, 0, nothing.stdout + nothing.stderr)
        self.assertEqual(check["state"], "degraded")
        self.assertEqual(check["tier"], "recommended")
        self.assertEqual(check["phases"], [5])
        self.assertIn("no heygen CLI", check["detail"])

        cli = self.write_executable(
            "heygen",
            'printf "heygen %s\\n" "$*" >> "$CHECKER_TEST_LOG"\nexit 0',
        )
        installed, checks = self.json_checks()
        check = checks["heygen-credential"]
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        self.assertEqual(check["state"], "degraded")
        self.assertIn(str(cli), check["detail"])
        self.assertFalse(
            self.log.exists(),
            "presence detection executed the heygen CLI — it must resolve the "
            "binary without running it",
        )

    def test_json_is_parseable_and_complete_without_node_or_python(self):
        result = self.run_checker("--json")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("\x1b", result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["summary"]["state"], "blocked")

        checks = {check["id"]: check for check in report["checks"]}
        expected_ids = {
            "node", "npx", "python", "ffmpeg", "ffprobe", "chrome-shell",
            "hyperframes-cli", "hyperframes-skill", "gsap-skill",
            "motion-doctrine-skill", "media-use-skill", "heygen-credential",
            "elevenlabs-key", "whisper", "freesound-key", "espeak-ng",
            "terminal-capture",
        }
        # Exact equality, not issubset: `docker-wsl` is the only conditional
        # check and this run is pinned to Darwin, so the id set is fully
        # determined here. An added check that no test names is exactly how
        # `media-use-skill` and `heygen-credential` shipped uncovered.
        self.assertEqual(set(checks), expected_ids)
        self.assertEqual(checks["node"]["state"], "blocked")
        self.assertEqual(checks["python"]["state"], "blocked")

        required_fields = {
            "id", "label", "tier", "state", "phases", "detail", "version",
            "fixability",
        }
        for check in checks.values():
            self.assertTrue(required_fields.issubset(check))
            self.assertIn(check["tier"], {"required", "recommended", "optional"})
            self.assertIn(check["state"], {"ready", "degraded", "blocked"})
            self.assertIsInstance(check["phases"], list)
            self.assertEqual(
                set(check["fixability"]),
                {"kind", "id", "command"},
            )

    def test_json_escapes_control_characters_and_discovered_paths(self):
        self.write_executable("uname", "printf 'Odd\\033OS\\n'")
        chrome = self.work / 'chrome"\n\x1bheadless-shell'
        chrome.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        chrome.chmod(0o755)
        env = self.environment()
        env["PUPPETEER_EXECUTABLE_PATH"] = str(chrome)
        result = self.run_checker("--json", env=env)
        report = json.loads(result.stdout)
        self.assertEqual(report["platform"], "Odd\x1bOS")
        check = next(item for item in report["checks"]
                     if item["id"] == "chrome-shell")
        self.assertIn(str(chrome), check["detail"])

    def test_report_json_and_plan_never_invoke_install_or_network_stubs(self):
        self.install_required_shims(include_hyperframes=False, include_chrome=False)
        self.install_optional_shims(include_whisper=False)
        env = self.environment()

        for mode in ((), ("--json",), ("--plan",)):
            with self.subTest(mode=mode):
                if self.log.exists():
                    self.log.unlink()
                self.run_checker(*mode, env=env)
                self.assertFalse(
                    self.log.exists(),
                    f"{mode or ('default',)} invoked: "
                    f"{self.log.read_text(encoding='utf-8') if self.log.exists() else ''}",
                )

    def test_cached_hyperframes_is_ready_without_invoking_npx(self):
        self.install_required_shims(include_hyperframes=False)
        self.install_skills()
        cached = (
            self.home / ".npm" / "_npx" / "cache-id"
            / "node_modules" / ".bin" / "hyperframes"
        )
        cached.parent.mkdir(parents=True)
        cached.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = \"--version\" ]; then printf '1.2.3\\n'; exit 0; fi\n"
            "if [ \"$1\" = \"transcribe\" ]; then exit 0; fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        cached.chmod(0o755)

        result = self.run_checker("--json")
        report = json.loads(result.stdout)
        checks = {check["id"]: check for check in report["checks"]}

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(checks["hyperframes-cli"]["state"], "ready")
        self.assertEqual(checks["hyperframes-cli"]["version"], "1.2.3")
        self.assertIn(str(cached), checks["hyperframes-cli"]["detail"])
        self.assertEqual(checks["whisper"]["state"], "ready")
        self.assertFalse(self.log.exists())

    def test_hyperframes_uses_custom_npmrc_cache_without_invoking_npm(self):
        self.install_required_shims(include_hyperframes=False)
        self.install_skills()
        cache = self.work / "custom npm cache"
        cached = (
            cache / "_npx" / "cache-id"
            / "node_modules" / ".bin" / "hyperframes"
        )
        cached.parent.mkdir(parents=True)
        cached.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = \"--version\" ]; then printf '2.0.0\\n'; exit 0; fi\n"
            "if [ \"$1\" = \"transcribe\" ]; then exit 0; fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        cached.chmod(0o755)
        (self.home / ".npmrc").write_text(
            f'cache = "{cache}"\n',
            encoding="utf-8",
        )

        result = self.run_checker("--json")
        report = json.loads(result.stdout)
        check = next(
            item for item in report["checks"]
            if item["id"] == "hyperframes-cli"
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(check["state"], "ready")
        self.assertEqual(check["version"], "2.0.0")
        self.assertIn(str(cached), check["detail"])
        self.assertFalse(self.log.exists())

    def test_hyperframes_cache_path_preserves_trailing_newline(self):
        self.install_required_shims(include_hyperframes=False)
        self.install_skills()
        cache = self.work / "npm cache\n"
        cached = (
            cache / "_npx" / "cache-id"
            / "node_modules" / ".bin" / "hyperframes"
        )
        cached.parent.mkdir(parents=True)
        cached.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = \"--version\" ]; then printf '4.0.0\\n'; exit 0; fi\n"
            "if [ \"$1\" = \"transcribe\" ]; then exit 0; fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        cached.chmod(0o755)
        env = self.environment()
        env["npm_config_cache"] = str(cache)

        result = self.run_checker("--json", env=env)
        report = json.loads(result.stdout)
        check = next(
            item for item in report["checks"]
            if item["id"] == "hyperframes-cli"
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(check["version"], "4.0.0")
        self.assertIn(str(cached), check["detail"])

    def test_hyperframes_uses_expanded_global_npmrc_cache(self):
        self.install_required_shims(include_hyperframes=False)
        self.install_skills()
        cache_root = self.work / "xdg cache"
        cache = cache_root / "npm"
        cached = (
            cache / "_npx" / "cache-id"
            / "node_modules" / ".bin" / "hyperframes"
        )
        cached.parent.mkdir(parents=True)
        cached.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = \"--version\" ]; then printf '3.0.0\\n'; exit 0; fi\n"
            "if [ \"$1\" = \"transcribe\" ]; then exit 0; fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        cached.chmod(0o755)
        global_npmrc = self.work / "etc" / "npmrc"
        global_npmrc.parent.mkdir()
        global_npmrc.write_text(
            "cache = ${CUSTOM_CACHE_ROOT}/npm\n",
            encoding="utf-8",
        )
        env = self.environment()
        env["CUSTOM_CACHE_ROOT"] = str(cache_root)

        result = self.run_checker("--json", env=env)
        report = json.loads(result.stdout)
        check = next(
            item for item in report["checks"]
            if item["id"] == "hyperframes-cli"
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(check["state"], "ready")
        self.assertEqual(check["version"], "3.0.0")
        self.assertIn(str(cached), check["detail"])
        self.assertFalse(self.log.exists())

    def test_plan_is_side_effect_free_and_prints_exact_actions(self):
        self.install_required_shims(include_hyperframes=False, include_chrome=False)
        self.install_optional_shims()
        result = self.run_checker("--plan")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Setup plan", result.stdout)
        self.assertIn("No changes will be made.", result.stdout)
        self.assertIn(
            "npx --yes puppeteer browsers install chrome-headless-shell",
            result.stdout,
        )
        self.assertIn("npm install --global hyperframes", result.stdout)
        self.assertFalse(self.log.exists())

    def test_scoped_fix_runs_only_selected_safe_action(self):
        self.install_required_shims(include_hyperframes=False, include_chrome=False)
        self.install_optional_shims(include_whisper=False)
        result = self.run_checker("--fix=whisper")
        self.assertEqual(result.returncode, 1)
        calls = self.log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(calls, ["pip3 install --user openai-whisper"])
        self.assertNotIn("sudo", "\n".join(calls))

    def test_hyperframes_skill_fix_is_global_and_noninteractive(self):
        self.install_required_shims()
        self.install_optional_shims()
        result = self.run_checker("--fix=hyperframes-skill")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            self.log.read_text(encoding="utf-8").splitlines(),
            [
                "npx --yes skills add heygen-com/hyperframes "
                "--global --yes"
            ],
        )

    def test_wsl_reports_never_contact_docker_daemon(self):
        self.install_required_shims()
        self.install_skills()
        self.write_executable("uname", "printf 'Linux\\n'")
        self.write_executable("grep", "exit 0")
        self.write_executable(
            "docker",
            'printf "docker %s\\n" "$*" >> "$CHECKER_TEST_LOG"\nexit 0',
        )
        env = self.environment()
        env["DOCKER_HOST"] = "ssh://example.invalid"

        result = self.run_checker("--json", env=env)
        report = json.loads(result.stdout)
        check = next(
            item for item in report["checks"]
            if item["id"] == "docker-wsl"
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(check["state"], "ready")
        self.assertIn("do not contact the daemon", check["detail"])
        self.assertFalse(self.log.exists())

    def test_unknown_fix_fails_before_any_action(self):
        self.install_required_shims(include_hyperframes=False, include_chrome=False)
        self.install_optional_shims()
        result = self.run_checker("--fix=unknown")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown fix ID: unknown", result.stderr)
        self.assertFalse(self.log.exists())

    def test_wildcard_fix_id_is_rejected_without_expansion(self):
        self.install_required_shims(include_hyperframes=False)
        (self.work / "chrome-shell").write_text("", encoding="utf-8")

        result = self.run_checker("--fix=chrome-*", cwd=self.work)

        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown fix ID: chrome-*", result.stderr)
        self.assertFalse(self.log.exists())

    def test_unselected_safe_fixes_and_sudo_are_never_run(self):
        self.install_required_shims(include_hyperframes=False, include_chrome=False)
        self.install_optional_shims()
        self.write_executable(
            "sudo",
            'printf "sudo %s\\n" "$*" >> "$CHECKER_TEST_LOG"\nexit 99',
        )
        result = self.run_checker("--fix=chrome-shell")
        self.assertEqual(result.returncode, 1)
        calls = self.log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            calls,
            ["npx --yes puppeteer browsers install chrome-headless-shell"],
        )

    def test_repeated_scoped_fix_form_runs_each_selected_action(self):
        self.install_required_shims(include_hyperframes=False, include_chrome=False)
        self.install_optional_shims(include_whisper=False)
        result = self.run_checker("--fix=chrome-shell", "--fix=whisper")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            self.log.read_text(encoding="utf-8").splitlines(),
            [
                "npx --yes puppeteer browsers install chrome-headless-shell",
                "pip3 install --user openai-whisper",
            ],
        )


if __name__ == "__main__":
    unittest.main()
