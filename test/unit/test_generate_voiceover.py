import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "generate_voiceover.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_voiceover_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GenerateVoiceoverTest(unittest.TestCase):
    def test_elevenlabs_generation_requires_its_key(self):
        module = load_module()

        with mock.patch.object(module, "API_KEY", None):
            self.assertEqual(module.main([]), 1)

    def test_assemble_only_requires_every_external_section(self):
        module = load_module()
        module.sections = [(0.0, "First"), (2.0, "Second")]

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "vo_section_00.mp3").write_bytes(b"audio")
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                with mock.patch.object(module, "get_audio_duration", return_value=1.0):
                    self.assertEqual(module.main(["--assemble-only"]), 2)
            finally:
                os.chdir(old_cwd)

    def test_assemble_only_uses_external_sections_without_api_key(self):
        module = load_module()
        module.sections = [(0.0, "First"), (2.0, "Second")]

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "vo_section_00.mp3").write_bytes(b"first")
            Path(tmp, "vo_section_01.mp3").write_bytes(b"second")
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                with (
                    mock.patch.object(module, "API_KEY", None),
                    mock.patch.object(module, "get_audio_duration", return_value=2.0),
                    mock.patch.object(module, "assemble_voiceover") as assemble,
                    mock.patch.object(module, "verify_transcript", return_value=[]),
                ):
                    self.assertEqual(module.main(["--assemble-only"]), 0)
                    assemble.assert_called_once_with(
                        [(0.0, "vo_section_00.mp3"), (2.0, "vo_section_01.mp3")]
                    )
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
