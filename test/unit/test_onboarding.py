#!/usr/bin/env python3

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "SKILL.md"


class FirstRunOnboardingTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = SKILL.read_text(encoding="utf-8")
        start = cls.skill.index("### Phase -1:")
        end = cls.skill.index("**First, select video type:**", start)
        cls.phase_minus_one = cls.skill[start:end]

    def test_phase_minus_one_is_first_run_only_and_skips_resume_modes(self):
        text = self.phase_minus_one
        self.assertIn("no `project-plan.md`", text)
        self.assertRegex(text, r"(?i)new.+only")
        self.assertRegex(text, r"(?i)(skip|never run).+`continue`.+`jump`")
        self.assertIn("check_requirements.sh\" --json", text)

    def test_phase_minus_one_uses_neutral_consent_and_only_safe_fix_ids(self):
        text = self.phase_minus_one
        self.assertIn('"questions"', text)
        self.assertIn('"multiSelect": true', text)
        for fix_id in ("chrome-shell", "hyperframes-skill", "whisper"):
            self.assertIn(fix_id, text)
        self.assertIn("--fix=", text)
        self.assertNotIn("AskUserQuestion", text)
        self.assertNotIn("ask_user", text)
        self.assertRegex(text, r"(?i)manual.+(sudo|system|environment)")
        self.assertRegex(text, r"(?i)never run")

    def test_phase_minus_one_reruns_and_blocks_only_required_failures(self):
        text = self.phase_minus_one
        self.assertGreaterEqual(text.count("--json"), 2)
        self.assertRegex(text, r"(?i)block.+required")
        self.assertRegex(text, r"(?i)(recommended|optional).+degraded.+continue")

    def test_phase_minus_one_shows_all_six_approval_checkpoints(self):
        text = self.phase_minus_one
        for phase in range(6):
            self.assertIn(f"Phase {phase}", text)
        self.assertRegex(text, r"(?i)(approval|checkpoint)")

    def test_phase_minus_one_describes_native_screen_recording_support(self):
        text = self.phase_minus_one
        for term in ("screen-recording", "macOS", "Windows", "X11", "Wayland",
                     "wf-recorder", "WSL"):
            self.assertIn(term, text)

    def test_skill_homes_lines_remain_byte_identical(self):
        paths = [
            ROOT / "SKILL.md",
            ROOT / "workflows" / "phase-3-design.md",
            ROOT / "workflows" / "phase-5-audio.md",
            ROOT / "scripts" / "check_requirements.sh",
        ]
        lines = set()
        for path in paths:
            lines.update(re.findall(
                r'SKILL_HOMES="[^"]*"',
                path.read_text(encoding="utf-8"),
            ))
        self.assertEqual(len(lines), 1, sorted(lines))


if __name__ == "__main__":
    unittest.main()
