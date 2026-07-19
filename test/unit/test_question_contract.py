#!/usr/bin/env python3

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "SKILL.md"
WORKFLOWS = sorted((ROOT / "workflows").glob("*.md"))
QUESTION_BLOCK = re.compile(
    r"^[ \t]*```json[ \t]*\n(.*?)^[ \t]*```[ \t]*$",
    re.DOTALL | re.MULTILINE,
)

DESIGN_SYSTEMS = {
    "Stripe",
    "Linear",
    "Apple",
    "Notion",
    "Vercel",
    "Airbnb",
    "GitHub",
    "Cal.com",
    "Arc",
    "Bento",
}
HYPERFRAMES_STYLES = {
    "Swiss Pulse",
    "Velvet Standard",
    "Deconstructed",
    "Maximalist Type",
    "Data Drift",
    "Soft Signal",
    "Folk Frequency",
    "Shadow Cut",
}


class QuestionContractTestCase(unittest.TestCase):
    def test_every_question_block_is_json_with_at_most_four_options(self):
        question_count = 0
        for path in (SKILL, *WORKFLOWS):
            text = path.read_text(encoding="utf-8")
            for match in QUESTION_BLOCK.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                try:
                    payload = json.loads(match.group(1))
                except json.JSONDecodeError as error:
                    self.fail(f"{path.relative_to(ROOT)}:{line}: invalid JSON: {error}")
                if "questions" not in payload:
                    continue
                self.assertIsInstance(
                    payload["questions"],
                    list,
                    f"{path.relative_to(ROOT)}:{line}: questions must be a list",
                )
                question_count += len(payload["questions"])
                for question in payload["questions"]:
                    self.assertIsInstance(
                        question.get("question"),
                        str,
                        f"{path.relative_to(ROOT)}:{line}: question text must be a string",
                    )
                    self.assertIsInstance(
                        question.get("header"),
                        str,
                        f"{path.relative_to(ROOT)}:{line}: header must be a string",
                    )
                    self.assertLessEqual(
                        len(question["header"]),
                        12,
                        f"{path.relative_to(ROOT)}:{line}: "
                        f"{question['header']} header exceeds 12 characters",
                    )
                    self.assertIsInstance(
                        question.get("multiSelect"),
                        bool,
                        f"{path.relative_to(ROOT)}:{line}: multiSelect must be boolean",
                    )
                    self.assertIsInstance(
                        question.get("options"),
                        list,
                        f"{path.relative_to(ROOT)}:{line}: options must be a list",
                    )
                    self.assertLessEqual(
                        len(question["options"]),
                        4,
                        f"{path.relative_to(ROOT)}:{line}: "
                        f"{question.get('header', 'question')} has too many options",
                    )
                    for option in question["options"]:
                        self.assertIsInstance(
                            option,
                            dict,
                            f"{path.relative_to(ROOT)}:{line}: "
                            "each option must be an object",
                        )
                        for field in ("label", "description"):
                            self.assertIsInstance(
                                option.get(field),
                                str,
                                f"{path.relative_to(ROOT)}:{line}: "
                                f"option {field} must be a string",
                            )
        self.assertGreater(question_count, 0)

    def test_workflows_never_name_runtime_specific_picker_tools(self):
        for path in WORKFLOWS:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("AskUserQuestion", text, path.name)
            self.assertNotIn("ask_user", text, path.name)

    def test_all_design_systems_and_hyperframes_styles_remain_reachable(self):
        storytelling = (ROOT / "workflows" / "phase-1-storytelling.md").read_text(
            encoding="utf-8"
        )
        for choice in sorted(DESIGN_SYSTEMS | HYPERFRAMES_STYLES):
            self.assertIn(choice, storytelling)
        self.assertRegex(storytelling, r"(?i)custom")
        self.assertRegex(storytelling, r"(?i)derive.+screenshots")
        self.assertRegex(storytelling, r"(?i)(family|category)")

    def test_phase_zero_handoff_preserves_user_ownership(self):
        discovery = (ROOT / "workflows" / "phase-0-discovery.md").read_text(
            encoding="utf-8"
        )
        self.assertRegex(
            discovery,
            r"(?is)Phase 1.+you.+choose.+looks.+sounds",
        )

    def test_story_confirmation_precedes_storyboard_creation(self):
        storytelling = (ROOT / "workflows" / "phase-1-storytelling.md").read_text(
            encoding="utf-8"
        )
        confirm = storytelling.index("confirm-story")
        storyboard = storytelling.index("## Step 1.6: Build Storyboard")
        self.assertLess(confirm, storyboard)
        for label in (
            "Mode",
            "Product surface",
            "Duration",
            "Theme",
            "Aspect",
            "Identity",
            "Voice",
            "Transition style",
            "Transition speed",
            "Music strategy",
        ):
            self.assertIn(label, storytelling[confirm - 1800:confirm])

    def test_exact_music_track_confirmation_precedes_mixing(self):
        audio = (ROOT / "workflows" / "phase-5-audio.md").read_text(encoding="utf-8")
        confirm = audio.index("confirm-audio")
        mixing = audio.index("## Step 5.3: Audio Mixing")
        self.assertLess(confirm, mixing)
        confirmation_section = audio[confirm - 1600:confirm + 500]
        for field in ("title", "path", "source", "license"):
            self.assertIn(field, confirmation_section)
        self.assertRegex(confirmation_section, r"(?i)explicit.+none")

    def test_confirmed_transition_style_and_speed_are_consumed(self):
        production = (
            ROOT / "workflows" / "phase-4-production.md"
        ).read_text(encoding="utf-8")
        storyboard = (
            ROOT / "templates" / "storyboard.md"
        ).read_text(encoding="utf-8")
        design = (
            ROOT / "workflows" / "phase-3-design.md"
        ).read_text(encoding="utf-8")

        for field in ("transition_style", "transition_speed"):
            self.assertIn(field, production)
            self.assertIn(field, storyboard)
            self.assertIn(field, design)
        for style in (
            "crossfade",
            "metallic-swoosh",
            "zoom-through",
            "slide-from-bottom",
        ):
            self.assertIn(style, production)
            self.assertIn(style, storyboard)
        for speed, duration in (
            ("quick", "0.4s"),
            ("medium", "0.7s"),
            ("slow", "1.2s"),
        ):
            self.assertRegex(
                production,
                rf"`?{speed}`?.+`?{re.escape(duration)}`?",
            )
        self.assertNotIn("Default to a quiet crossfade", production)

    def test_confirmed_theme_is_enforced_across_downstream_phases(self):
        storytelling = (ROOT / "workflows" / "phase-1-storytelling.md").read_text(
            encoding="utf-8"
        )
        capture = (ROOT / "workflows" / "phase-2-capture.md").read_text(
            encoding="utf-8"
        )
        design = (ROOT / "workflows" / "phase-3-design.md").read_text(
            encoding="utf-8"
        )
        production = (ROOT / "workflows" / "phase-4-production.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("| Dark only | `linear-app` |", storytelling)
        self.assertIn("confirmed `theme`", capture)
        self.assertIn("### Confirmed Theme", design)
        self.assertIn("Theme backstop", production)
        self.assertIn("Never invert a brand palette", storytelling)
        self.assertIn("never capture the opposite theme", capture)
        self.assertIn("opposite-theme canvas or surface", design)
        self.assertIn("opposite-theme default", production)

    def test_confirmed_voice_provider_controls_generation(self):
        storytelling = (ROOT / "workflows" / "phase-1-storytelling.md").read_text(
            encoding="utf-8"
        )
        audio = (ROOT / "workflows" / "phase-5-audio.md").read_text(
            encoding="utf-8"
        )

        for value in (
            "elevenlabs:<name>:<voice-id>",
            "kokoro:<voice-id>",
        ):
            self.assertIn(value, storytelling)
            self.assertIn(value, audio)
        self.assertIn("Do not choose a provider from environment-variable availability", audio)
        self.assertIn("python3 ./voiceover.py --assemble-only", audio)
        self.assertRegex(audio, r"(?is)kokoro.+even if.+ElevenLabs key")

    def test_resume_and_jump_route_stale_state(self):
        skill = SKILL.read_text(encoding="utf-8")
        self.assertIn("validate_brief.py", skill)
        self.assertIn("status --json", skill)
        self.assertIn("earliest_stale_phase", skill)
        self.assertIn("migration_required", skill)
        self.assertIn("migrate --json", skill)
        self.assertRegex(skill, r"(?is)migration.+never infer")
        self.assertRegex(skill, r"(?is)continue.+stale.+earliest")
        self.assertRegex(skill, r"(?is)jump.+require phase-")

    def test_each_downstream_phase_requires_and_stamps_freshness(self):
        for phase in range(1, 6):
            text = (
                ROOT / "workflows" / (
                    "phase-1-storytelling.md"
                    if phase == 1
                    else {
                        2: "phase-2-capture.md",
                        3: "phase-3-design.md",
                        4: "phase-4-production.md",
                        5: "phase-5-audio.md",
                    }[phase]
                )
            ).read_text(encoding="utf-8")
            self.assertIn(f"stamp phase-{phase}", text)
            if phase > 1:
                self.assertIn(f"require phase-{phase - 1}", text)

    def test_validator_is_registered_in_directly_related_docs(self):
        for relative in (
            "README.md",
            "CLAUDE.md",
            ".github/copilot-instructions.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("validate_brief.py", text, relative)
            self.assertIn(".hve/brief-state.json", text, relative)


if __name__ == "__main__":
    unittest.main()
