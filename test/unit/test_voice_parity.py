"""The four ElevenLabs voices are a user-facing contract stated in three places.

`SKILL.md` and `README.md` each carry a name -> id table; `workflows/phase-1-storytelling.md`
carries the picker the user actually answers. A voice added to one table and not the other two
gives the user a choice the brief cannot record, or records an id the picker never offers.

CLAUDE.md's "Add a voice" entry names all three sites. This test is what makes that instruction
enforceable instead of advisory.
"""

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

SKILL_MD = REPO / "SKILL.md"
README_MD = REPO / "README.md"
PHASE_1 = REPO / "workflows" / "phase-1-storytelling.md"

PICKER_QUESTION = "Which ElevenLabs voice for the voiceover?"


def read_table_after(path, heading):
    """Return the first markdown table below `heading` as a list of dicts.

    Keys come from the header row, so a table may reorder its columns freely --
    SKILL.md and README.md genuinely do.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        raise AssertionError(f"{path.name} has no heading {heading!r}")

    rows = []
    header = None
    for line in lines[start + 1:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        rows.append(dict(zip(header, cells)))
    if not rows:
        raise AssertionError(f"{path.name}: no table rows under {heading!r}")
    return rows


def voice_map(path, heading):
    out = {}
    for row in read_table_after(path, heading):
        name = row["Voice"].strip("` ")
        out[name] = row["Voice ID"].strip("` ")
    return out


def picker_labels(path):
    """Labels offered by the phase-1 voice picker, read from its JSON block."""
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```json\n(.*?)\n```", text, re.DOTALL)
    for block in blocks:
        if PICKER_QUESTION not in block:
            continue
        payload = json.loads(block)
        for question in payload["questions"]:
            if question.get("question") == PICKER_QUESTION:
                return [option["label"] for option in question["options"]]
    raise AssertionError(f"{path.name}: no picker asking {PICKER_QUESTION!r}")


class VoiceParityTests(unittest.TestCase):
    def test_skill_and_readme_tables_agree_on_every_name_and_id(self):
        skill = voice_map(SKILL_MD, "## ElevenLabs Voice IDs")
        readme = voice_map(README_MD, "## Voices")
        self.assertEqual(
            skill,
            readme,
            "SKILL.md and README.md voice tables diverged -- both are the user-facing contract",
        )

    def test_the_phase_1_picker_offers_exactly_the_documented_voices(self):
        skill = voice_map(SKILL_MD, "## ElevenLabs Voice IDs")
        labels = picker_labels(PHASE_1)
        self.assertEqual(
            sorted(labels),
            sorted(skill),
            "the phase-1 picker and the voice tables offer different voices",
        )

    def test_no_voice_is_offered_twice_in_the_picker(self):
        labels = picker_labels(PHASE_1)
        self.assertEqual(sorted(labels), sorted(set(labels)), "duplicate label in the picker")

    def test_the_worked_voice_example_uses_a_real_name_and_id_pair(self):
        """`elevenlabs:<name>:<id>` is the literal string that lands in the brief.

        A worked example carrying an id that no table lists teaches the format with a
        value the pipeline would then have to honour.
        """
        skill = voice_map(SKILL_MD, "## ElevenLabs Voice IDs")
        text = PHASE_1.read_text(encoding="utf-8")
        pairs = re.findall(r"elevenlabs:([A-Za-z][A-Za-z0-9 _-]*):([A-Za-z0-9]{16,})", text)
        self.assertTrue(pairs, "phase-1 shows no worked `elevenlabs:<name>:<id>` example")
        for name, voice_id in pairs:
            self.assertIn(name, skill, f"worked example names unlisted voice {name!r}")
            self.assertEqual(
                skill[name], voice_id, f"worked example gives {name} the wrong voice id"
            )


if __name__ == "__main__":
    unittest.main()
