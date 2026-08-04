#!/usr/bin/env python3
"""Unit suite for `scripts/stitch_clip.py` (Phase 2 clip normalization).

The defect this suite pins:

(a) the encode's keyframe interval (GOP) must follow the ACTUAL output fps.
    `agg` emits change-only frames, so on mostly-static terminal output x264's
    scene-change heuristic can leave keyframes many seconds apart — a real
    capture produced an 8.33s interval, and the HyperFrames renderer then
    reports "sparse keyframes … causes seek failures and frame freezing" and
    renders the clip black or frozen while `lint`, `check` and the seam gate
    all pass green.

    Pinning `-g`/`-keyint_min` to the module-level constant is not enough:
    `--fps` is a real CLI argument, and a hard-coded GOP silently desyncs from
    it (`--fps 24` with a 30-frame GOP = 1.25s between keyframes, straight back
    into the failure). The GOP must be derived from the fps actually used.

No encoding runs: only the argv `build_command` produces is inspected, so the
suite is hermetic and passes on a machine without ffmpeg.
"""

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "stitch_clip.py"


def load_module():
    spec = importlib.util.spec_from_file_location("stitch_clip", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def flag_value(cmd, flag):
    """Return the argv value following `flag`, or None when absent."""
    if flag not in cmd:
        return None
    return cmd[cmd.index(flag) + 1]


class GopFollowsOutputFps(unittest.TestCase):
    """(a) keyframe interval must track the fps the encode actually uses."""

    def setUp(self):
        self.mod = load_module()

    def _cmd(self, fps):
        return self.mod.build_command(
            [("in.mp4", None, None)], "out.mp4", fps, 1920, 1080
        )

    def test_gop_flags_are_emitted_at_all(self):
        cmd = self._cmd(30)
        self.assertIn("-g", cmd, "encode must pin a GOP or the renderer reports sparse keyframes")
        self.assertIn("-keyint_min", cmd, "-keyint_min stops x264 inserting shorter GOPs")

    def test_gop_matches_default_fps(self):
        cmd = self._cmd(30)
        self.assertEqual(flag_value(cmd, "-g"), "30")
        self.assertEqual(flag_value(cmd, "-keyint_min"), "30")

    def test_gop_follows_a_non_default_fps(self):
        """The regression: --fps 24 must not keep a 30-frame GOP."""
        for fps in (24, 25, 50, 60):
            with self.subTest(fps=fps):
                cmd = self._cmd(fps)
                self.assertEqual(
                    flag_value(cmd, "-g"), str(fps),
                    f"--fps {fps} must produce a {fps}-frame GOP, not a hard-coded one",
                )
                self.assertEqual(flag_value(cmd, "-keyint_min"), str(fps))

    def test_gop_yields_one_keyframe_per_second(self):
        """Whatever the fps, the interval stays 1.00s — the renderer's requirement."""
        for fps in (24, 30, 60):
            with self.subTest(fps=fps):
                cmd = self._cmd(fps)
                interval = int(flag_value(cmd, "-g")) / fps
                self.assertAlmostEqual(interval, 1.0, places=6)

    def test_filter_graph_fps_and_gop_agree(self):
        """The two places fps appears must never disagree."""
        for fps in (24, 30, 60):
            with self.subTest(fps=fps):
                cmd = self._cmd(fps)
                graph = cmd[cmd.index("-filter_complex") + 1]
                self.assertIn(f"fps={fps}", graph)
                self.assertEqual(flag_value(cmd, "-g"), str(fps))


class EncodeContractUnchanged(unittest.TestCase):
    """The rest of the canonical encode contract must survive the GOP change."""

    def setUp(self):
        self.mod = load_module()

    def test_core_encode_flags_still_present(self):
        cmd = self.mod.build_command(
            [("in.mp4", None, None)], "out.mp4", 30, 1920, 1080
        )
        self.assertEqual(flag_value(cmd, "-c:v"), "libx264")
        self.assertEqual(flag_value(cmd, "-profile:v"), "high")
        self.assertEqual(flag_value(cmd, "-pix_fmt"), "yuv420p")
        self.assertEqual(flag_value(cmd, "-movflags"), "+faststart")
        self.assertIn("-an", cmd, "clips carry no audio track")
        self.assertEqual(cmd[-1], "out.mp4")


if __name__ == "__main__":
    unittest.main()
