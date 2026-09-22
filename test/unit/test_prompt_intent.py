"""Structural prompt contracts and isolated shell probes, not live-agent grading."""

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from test_validate_brief import VB
from shell_helpers import shell_executable, shell_path


ROOT = Path(__file__).resolve().parents[2]


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def prose(relative):
    return " ".join(text(relative).replace("**", "").replace("`", "").split()).lower()


def terminal_recipe(relative):
    return next(
        block for block in re.findall(r"```bash\n(.*?)```", text(relative), re.S)
        if 'CAST_TMP="$WORK_DIR/scene.cast"' in block
    )


class PromptIntentContractTests(unittest.TestCase):
    def test_intake_declares_lossless_request_and_leading_controls(self):
        skill = prose("SKILL.md")
        for phrase in (
            "all trailing text is the request",
            "leading control block",
            "later flag-looking text stays request content",
            "never turn the entire prompt into a folder name",
            "before creating anything",
            "a malformed value is an error to repair",
        ):
            self.assertIn(phrase, skill)
        for control in ("--mode", "--phase", "--source-dir", "--output-dir"):
            self.assertIn(control, skill)
        hint = re.search(r"^argument-hint: (.+)$", text("SKILL.md"), re.M).group(1)
        self.assertIn("[video request]", hint)
        self.assertNotIn("[project-dir]", hint)

    def test_legacy_resume_and_intake_do_not_create_new_prerequisites(self):
        skill = prose("SKILL.md")
        for phrase in (
            "output workspace and phase first",
            "legacy projects without this section",
            "do not create a placeholder context.md",
            "artifact-only resume",
            "leave source_dir unset",
            "never substitute the output directory as the product source",
        ):
            self.assertIn(phrase, skill)
        template = prose("templates/project-plan.md")
        self.assertIn("provenance, not the creative brief or consent", template)
        self.assertIn("ensure_ascii=true", template)
        self.assertIn("older projects without this section remain resumable", template)

    def test_discovery_distinguishes_user_scope_from_proposals(self):
        discovery = prose("workflows/phase-0-discovery.md")
        for phrase in (
            "user-stated",
            "proposed from evidence",
            "not specified",
            "do not broaden it to a whole-product tour",
            "unknown behavior remains unresolved, never invented",
            "mutually exclusive branches",
        ):
            self.assertIn(phrase, discovery)
        self.assertIn('git -C "$SOURCE_DIR"', text("workflows/phase-0-discovery.md"))
        self.assertIn("## Demonstration Scenario", text("templates/context.md"))

    def test_coverage_is_prose_and_missing_requirements_are_not_completion(self):
        story = prose("workflows/phase-1-storytelling.md")
        for phrase in (
            "after the last frame",
            "single requirement-to-frame-to-evidence map",
            "that frame's own narrative",
            "not on-screen copy",
            "never silently drop steps",
            "missing planned coverage are unresolved work, not completion",
            "without a scenario inventory, omit this section",
        ):
            self.assertIn(phrase, story)
        production = prose("workflows/phase-4-production.md")
        self.assertIn("requirement-bearing moments, not just scene midpoints", production)
        self.assertIn("unresolved work, never completed coverage", production)
        audio = prose("workflows/phase-5-audio.md")
        self.assertIn("reopen the affected assembled evidence", audio)
        self.assertIn("scenario coverage backstop", audio)

    def test_storyboard_coverage_adds_no_frame_metadata_or_phantom_frame(self):
        board = """---
format: 1920x1080
---

## Frame 1 - Configure

- status: outline
- src: scenes/00-configure.html
- duration: 5s

Coverage: R1. Show the required control.

## Frame 2 - Result

- status: outline
- src: scenes/01-result.html
- duration: 5s

Coverage: R2. Show the observable result.

## Scenario Coverage

| Requirement ID | Frames | Planned evidence | Captured evidence | Assembled evidence |
|---|---|---|---|---|
| R1 | 1 | public/clips/configure.mp4 | pending | pending |
| R2 | 2 | public/screenshots/result.png | pending | pending |
"""
        parsed = VB.parse_storyboard(board)
        self.assertEqual(len(parsed["frames"]), 2)
        for index, frame in enumerate(parsed["frames"], 1):
            self.assertEqual(frame["extra"], {})
            self.assertIn(f"Coverage: R{index}", frame["narrative"])


@unittest.skipUnless(shutil.which("bash") and shutil.which("timeout"),
                     "bash and timeout are needed for the isolated shell probe")
class TerminalSourceBindingTests(unittest.TestCase):
    """Stub media binaries prove cwd/ownership only, never real media validity."""

    DOCS = ("workflows/phase-2-capture.md", "patterns/cli-terminal-capture.md")
    STUB = """#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys

tool = Path(sys.argv[0]).name
if tool == "asciinema":
    Path(sys.argv[-1]).write_text(str(Path.cwd()), encoding="utf-8")
elif tool == "agg":
    shutil.copyfile(sys.argv[-2], sys.argv[-1])
elif tool == "ffmpeg":
    shutil.copyfile(sys.argv[sys.argv.index("-i") + 1], sys.argv[-1])
elif tool == "ffprobe":
    print("nb_frames=30\\navg_frame_rate=30/1")
"""

    def run_recipe(self, relative, *, missing_source=False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        source = root / "source project"
        output = root / "video output"
        output.mkdir()
        (output / "scratch").mkdir()
        if not missing_source:
            source.mkdir()
        binaries = root / "bin"
        binaries.mkdir()
        for name in ("asciinema", "agg", "ffmpeg", "ffprobe"):
            stub = binaries / name
            stub.write_text(self.STUB, encoding="utf-8", newline="\n")
            stub.chmod(0o755)
        target = output / "public" / "clips" / "scene-00-test.mp4"
        target.parent.mkdir(parents=True)
        if missing_source:
            target.write_bytes(b"previous valid capture")
        script = root / "record.sh"
        script.write_text(
            terminal_recipe(relative).replace("{NN}", "00").replace("{slug}", "test")
            + '\nprintf "\\n__READY__%s__END__" "$clip_ready"\n',
            encoding="utf-8", newline="\n",
        )
        env = dict(
            os.environ,
            SOURCE_DIR=shell_path(source),
            PROJECT_DIR=shell_path(output),
            TMPDIR="scratch",
            PATH=str(binaries) + os.pathsep + os.environ.get("PATH", ""),
        )
        result = subprocess.run(
            [shell_executable(), script.as_posix()], cwd=output, env=env,
            encoding="utf-8", capture_output=True,
        )
        return result, source, output, target

    def test_recording_uses_source_and_publishes_only_under_output(self):
        for relative in self.DOCS:
            with self.subTest(document=relative):
                result, source, output, target = self.run_recipe(relative)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("__READY__1__END__", result.stdout)
                self.assertEqual(target.read_text(encoding="utf-8"), str(source.resolve()))
                self.assertFalse((source / "public").exists())
                self.assertTrue(target.is_relative_to(output))

    def test_missing_source_does_not_quarantine_a_previous_capture(self):
        for relative in self.DOCS:
            with self.subTest(document=relative):
                result, _, output, target = self.run_recipe(relative, missing_source=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn("source directory unavailable", result.stderr)
                self.assertEqual(target.read_bytes(), b"previous valid capture")
                self.assertEqual(list((output / "scratch").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
