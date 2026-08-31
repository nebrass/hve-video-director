"""replay_flow.py is where a recorded flow's trust is made mechanical.

Four drifts this suite pins, each one a way the recorded-browse-flow feature
(ADR-011) would quietly rot:

- **Pacing bounds.** The pacing profile in `replay_flow.py` is the single
  owner of every humanization number (the stitch_clip GOP precedent). If the
  schedule can emit a dwell outside the profile's ranges, the "law in prose,
  numbers in the script" split is broken and the pattern file starts lying.
- **Freshness.** A re-recorded flow must stale every clip cut from it, and a
  half-finished take must read as *incomplete*, never as absent (ADR-009's
  family — the delegated-audio scar: exit-0-plus-file-exists proved nothing).
  `check` therefore refuses on a pending marker, a hash mismatch, a steps
  mismatch, and a tampered clip.
- **Consent-brief privacy.** Recordings are plaintext; a recorded login puts
  the password in a `change` step's value. The brief exists to be shown to a
  human for whole-flow consent, so it must never print a typed value — and
  the secret heuristics must actually fire (guard on the guard below).
- **Cut atomicity.** `cut` publishes clip+sidecar as a pair; a failed cut
  leaves the previous clip byte-identical and the pending marker in place,
  mirroring capture_screen.py's publish discipline.

Hermetic: no ffmpeg/ffprobe runs. `cut` is exercised by patching the module's
`subprocess.run` and `_probe_duration`, then inspecting the argv it built for
`stitch_clip.py` — the same argv-inspection idiom as test_stitch_clip.py.
"""

import importlib.util
import io
import json
import shutil
import unittest
import uuid
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "replay_flow.py"
WORK = ROOT / "test" / ".work"


def load_module():
    spec = importlib.util.spec_from_file_location("replay_flow", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def recording_payload(step_count=6):
    steps = [
        {"type": "setViewport", "width": 1280, "height": 720},
        {"type": "navigate", "url": "https://app.example.com/reports?token=SECRET#x",
         "assertedEvents": [{"type": "navigation"}]},
        {"type": "click", "selectors": [["aria/Sales by Region"], ["#tile-3"]],
         "offsetX": 10, "offsetY": 12},
        {"type": "change", "value": "north", "selectors": [["aria/Region filter"]]},
        {"type": "scroll", "x": 0, "y": 640},
        {"type": "click", "selectors": [["aria/Drill through"]]},
    ]
    return {"title": "Drill to details", "steps": steps[:step_count]}


STORYBOARD = """---
format: hyperframes/storyboard@1
duration: 30
web_capture_source: navigate
---

## Frame 1 — Overview still
- capture: screenshot
- screenshot: public/screenshots/scene-00-overview.png
- recording: recordings/drill.json
- recording_steps: 2

Prose.

## Frame 2 — The drill
- capture: screencast
- recording: recordings/drill.json
- recording_steps: 3-6
- clip: public/clips/scene-01-drill.mp4
- duration: 6

Prose.

## Frame 3 — Unrelated title card
- capture: none
"""


class ReplayFlowCase(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()
        self.work = WORK / uuid.uuid4().hex
        self.work.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.work, ignore_errors=True)
        (self.work / "recordings").mkdir()
        self.recording = self.work / "recordings" / "drill.json"
        self.write_recording(recording_payload())
        self.storyboard = self.work / "storyboard.md"
        self.storyboard.write_text(STORYBOARD, encoding="utf-8")

    def write_recording(self, payload):
        self.recording.write_text(json.dumps(payload), encoding="utf-8")


class ScheduleStaysInsideHumanBounds(ReplayFlowCase):
    def test_every_emitted_dwell_sits_inside_the_profile_ranges(self):
        schedule = self.mod.build_schedule(recording_payload())
        travel_lo, travel_hi = self.mod.POINTER_TRAVEL_MS
        read_lo, read_hi = self.mod.READ_DWELL_MS
        nav_lo, nav_hi = self.mod.NAV_DWELL_MS
        for entry in schedule:
            if entry["type"] in ("click", "doubleClick", "hover", "change"):
                self.assertGreaterEqual(
                    entry["pre_ms"], travel_lo + self.mod.HOVER_SETTLE_MS)
                self.assertLessEqual(
                    entry["pre_ms"], travel_hi + self.mod.HOVER_SETTLE_MS)
                self.assertTrue(read_lo <= entry["post_ms"] <= read_hi)
            if entry["type"] == "navigate":
                self.assertTrue(nav_lo <= entry["post_ms"] <= nav_hi)

    def test_the_schedule_is_deterministic_but_not_a_metronome(self):
        first = self.mod.build_schedule(recording_payload())
        second = self.mod.build_schedule(recording_payload())
        self.assertEqual(first, second)
        dwells = {e["post_ms"] for e in first if e["type"] == "click"}
        self.assertGreater(len(dwells), 1, "every click dwell identical — a metronome")

    def test_recorded_hve_timing_beats_synthesis_and_is_clamped(self):
        payload = recording_payload()
        payload["steps"][2]["hve"] = {"t": 1000}
        payload["steps"][3]["hve"] = {"t": 61000}  # 60s delta → clamp to max
        payload["steps"][5]["hve"] = {"dwellAfterMs": 10}  # → clamp to min
        schedule = self.mod.build_schedule(payload)
        self.assertEqual(schedule[2]["post_ms"], self.mod.HVE_T_CLAMP_MS[1])
        self.assertEqual(schedule[5]["post_ms"], self.mod.HVE_T_CLAMP_MS[0])

    def test_an_unhandled_step_type_is_marked_so_consent_sees_it(self):
        payload = recording_payload()
        payload["steps"].append({"type": "customStep", "name": "x"})
        schedule = self.mod.build_schedule(payload)
        self.assertIn("UNHANDLED", schedule[-1]["note"])
        self.write_recording(payload)
        plan = self.mod.build_plan(self.recording)
        self.assertTrue(any("customStep" in w for w in plan["unhandled"]))


class SecretLikeValuesAreFlagged(ReplayFlowCase):
    def test_a_password_field_and_a_token_value_both_fire(self):
        payload = recording_payload()
        payload["steps"][3] = {"type": "change", "value": "hunter2",
                               "selectors": [["aria/Password"]]}
        payload["steps"].append({"type": "change",
                                 "value": "eyJhbGciOiJIUzI1NiJ9.payload",
                                 "selectors": [["#q"]]})
        self.write_recording(payload)
        plan = self.mod.build_plan(self.recording)
        self.assertEqual(len(plan["secrets"]), 2)

    def test_the_guard_on_the_guard_an_ordinary_change_is_not_flagged(self):
        plan = self.mod.build_plan(self.recording)
        self.assertEqual(plan["secrets"], [])

    def test_the_consent_brief_never_prints_a_typed_value_or_a_query_string(self):
        plan = self.mod.build_plan(self.recording, self.storyboard)
        out = io.StringIO()
        with redirect_stdout(out):
            self.mod.print_brief(plan)
        brief = out.getvalue()
        self.assertNotIn("north", brief)
        self.assertNotIn("token=SECRET", brief)
        self.assertIn("typed value hidden", brief)
        self.assertIn("https://app.example.com/reports", brief)


class BindingsComeFromTheStoryboard(ReplayFlowCase):
    def test_bound_frames_resolve_with_ranges_and_outputs(self):
        bindings = self.mod.replay_bindings(self.storyboard, self.recording, 6)
        self.assertEqual(
            bindings,
            [{"frame": 1, "capture": "screenshot", "steps": [2, 2],
              "output": "public/screenshots/scene-00-overview.png"},
             {"frame": 2, "capture": "screencast", "steps": [3, 6],
              "output": "public/clips/scene-01-drill.mp4"}])

    def test_a_range_beyond_the_recording_refuses_before_any_take(self):
        with self.assertRaisesRegex(self.mod.ReplayError, "exceeds"):
            self.mod.replay_bindings(self.storyboard, self.recording, 4)

    def test_a_clip_frame_with_no_clip_bullet_refuses(self):
        broken = STORYBOARD.replace("- clip: public/clips/scene-01-drill.mp4\n", "")
        self.storyboard.write_text(broken, encoding="utf-8")
        with self.assertRaisesRegex(self.mod.ReplayError, "names no"):
            self.mod.replay_bindings(self.storyboard, self.recording, 6)

    def test_an_absent_recording_steps_bullet_means_the_whole_flow(self):
        whole = STORYBOARD.replace("- recording_steps: 3-6\n", "")
        self.storyboard.write_text(whole, encoding="utf-8")
        bindings = self.mod.replay_bindings(self.storyboard, self.recording, 6)
        self.assertEqual(bindings[1]["steps"], [1, 6])

    def test_range_grammar_is_strict(self):
        for bad in ("5-3", "0-2", "9-12", "two", "1-2-3"):
            with self.subTest(bad=bad):
                with self.assertRaises(self.mod.ReplayError):
                    self.mod.parse_steps_range(bad, 6)
        self.assertEqual(self.mod.parse_steps_range(None, 6), (1, 6))
        self.assertEqual(self.mod.parse_steps_range("4", 6), (4, 4))


class CutMathBindsFramesToLedger(ReplayFlowCase):
    def ledger_payload(self, sha):
        return {
            "schema_version": 1,
            "recording_sha256": sha,
            "source": "navigate",
            "pointer": "branded",
            "steps": [
                {"index": i, "type": t, "t_start": s, "t_end": e,
                 "bbox": [10 * i, 20, 30, 40]}
                for i, (t, s, e) in enumerate(
                    [("setViewport", 0.0, 0.0), ("navigate", 0.5, 2.4),
                     ("click", 4.0, 5.2), ("change", 7.0, 8.6),
                     ("scroll", 10.0, 11.1), ("click", 13.0, 14.2)],
                    start=1)
            ],
        }

    def write_ledger(self, payload):
        path = self.work / ".hve" / "replay" / "drill.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_segments_are_pad_extended_and_clamped_to_the_take(self):
        ledger = self.ledger_payload(self.mod.sha256_file(self.recording))
        start, duration = self.mod.segment_for(ledger, (3, 6), 15.0)
        self.assertAlmostEqual(start, 4.0 - self.mod.LEAD_PAD_S)
        self.assertAlmostEqual(start + duration, 15.0)  # tail clamped to master
        start, duration = self.mod.segment_for(ledger, (1, 2), 15.0)
        self.assertAlmostEqual(start, 0.0)  # lead clamped at zero

    def test_drift_inside_the_soft_bound_is_zero_beyond_hard_refuses(self):
        ledger = self.ledger_payload("x")
        offset, warning = self.mod.drift_offset(14.9, ledger)  # span 14.2
        self.assertEqual(offset, 0.0)
        self.assertIsNone(warning)
        offset, warning = self.mod.drift_offset(16.2, ledger)
        self.assertAlmostEqual(offset, 2.0, places=6)
        self.assertIn("end-anchored", warning)
        with self.assertRaisesRegex(self.mod.ReplayError, "retake"):
            self.mod.drift_offset(18.0, ledger)

    def test_the_pointer_track_is_rebased_to_clip_local_time(self):
        ledger = self.ledger_payload("x")
        track = self.mod.pointer_track_for(ledger, (3, 6), 3.6, 0.0)
        self.assertEqual([e["step"] for e in track], [3, 4, 5, 6])
        self.assertAlmostEqual(track[0]["t"], 0.4)
        self.assertTrue(all(e["t"] >= 0 for e in track))

    def cut_with_fake_ffmpeg(self, stitch_fails=False):
        sha = self.mod.sha256_file(self.recording)
        ledger_path = self.write_ledger(self.ledger_payload(sha))
        raw = self.work / "public" / "clips" / ".drill.replay-raw.mp4"
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(b"master-take")
        commands = []

        def fake_run(cmd, capture_output=True, text=True, **kwargs):
            commands.append(cmd)
            if not stitch_fails:
                Path(cmd[cmd.index("-o") + 1]).write_bytes(b"cut-bytes")
            return mock.Mock(returncode=1 if stitch_fails else 0,
                             stdout="", stderr="boom" if stitch_fails else "")

        cwd = Path.cwd()
        os_chdir = __import__("os").chdir
        os_chdir(self.work)
        self.addCleanup(os_chdir, cwd)
        with mock.patch.object(self.mod.subprocess, "run", side_effect=fake_run), \
                mock.patch.object(self.mod, "_probe_duration",
                                  return_value=(15.0, {"width": 1920, "height": 1080})):
            self.mod.arm(self.recording, self.storyboard)
            results = self.mod.cut(
                "recordings/drill.json", str(raw), str(ledger_path),
                str(self.storyboard), canvas=(1920, 1080))
        return commands, results

    def test_cut_builds_the_canonical_stitch_argv(self):
        commands, results = self.cut_with_fake_ffmpeg()
        self.assertEqual(len(commands), 1)
        cmd = commands[0]
        self.assertTrue(str(cmd[1]).endswith("stitch_clip.py"))
        segment = cmd[2]
        # steps 3-6: lead 4.0-0.4=3.6; tail 14.2+0.8 clamps to the 15.0s master
        self.assertRegex(segment, r"::3\.600::11\.400$")
        self.assertEqual(cmd[cmd.index("--fps") + 1], "30")
        self.assertEqual(cmd[cmd.index("--width") + 1], "1920")
        self.assertEqual(cmd[cmd.index("--height") + 1], "1080")
        clip = self.work / "public" / "clips" / "scene-01-drill.mp4"
        sidecar = self.work / "public" / "clips" / "scene-01-drill.mp4.replay.json"
        self.assertEqual(clip.read_bytes(), b"cut-bytes")
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual(payload["requested"]["steps"], [3, 6])
        self.assertEqual(payload["requested"]["pointer"], "branded")
        self.assertFalse(
            (self.work / "public" / "clips"
             / "scene-01-drill.mp4.replay.pending").exists())
        self.assertEqual(results[0]["frame"], 2)

    def test_a_failed_cut_preserves_the_previous_clip_and_the_pending_marker(self):
        clip = self.work / "public" / "clips" / "scene-01-drill.mp4"
        clip.parent.mkdir(parents=True, exist_ok=True)
        clip.write_bytes(b"previous-good-take")
        with self.assertRaisesRegex(self.mod.ReplayError, "untouched"):
            self.cut_with_fake_ffmpeg(stitch_fails=True)
        self.assertEqual(clip.read_bytes(), b"previous-good-take")
        self.assertTrue(
            (self.work / "public" / "clips"
             / "scene-01-drill.mp4.replay.pending").exists())
        leftovers = [p for p in clip.parent.iterdir() if "candidate" in p.name]
        self.assertEqual(leftovers, [])

    def test_a_ledger_for_a_different_recording_refuses(self):
        ledger_path = self.write_ledger(self.ledger_payload("not-the-hash"))
        with self.assertRaisesRegex(self.mod.ReplayError, "hash mismatch"):
            self.mod.load_ledger(ledger_path, self.recording)


class CheckRefusesStaleRecordings(ReplayFlowCase):
    def published(self):
        clip = self.work / "public" / "clips" / "scene-01-drill.mp4"
        clip.parent.mkdir(parents=True, exist_ok=True)
        clip.write_bytes(b"cut-bytes")
        sidecar = {
            "schema_version": 1,
            "state": "complete",
            "requested": {
                "recording": "recordings/drill.json",
                "recording_sha256": self.mod.sha256_file(self.recording),
                "steps": [3, 6],
                "output": str(clip),
            },
            "media": {"fingerprint": {
                "algorithm": "sha256",
                "value": self.mod.sha256_file(clip)}},
        }
        (clip.parent / "scene-01-drill.mp4.replay.json").write_text(
            json.dumps(sidecar), encoding="utf-8")
        return clip

    def check(self, clip, steps="3-6"):
        cwd = Path.cwd()
        os_chdir = __import__("os").chdir
        os_chdir(self.work)
        self.addCleanup(os_chdir, cwd)
        return self.mod.check("recordings/drill.json", clip, steps)

    def test_a_published_cut_passes(self):
        clip = self.published()
        self.assertEqual(self.check(clip), 0)

    def test_a_pending_marker_means_incomplete(self):
        clip = self.published()
        (clip.parent / "scene-01-drill.mp4.replay.pending").write_text("{}")
        with self.assertRaisesRegex(self.mod.ReplayError, "incomplete"):
            self.check(clip)

    def test_a_re_recorded_flow_stales_the_cut(self):
        clip = self.published()
        payload = recording_payload()
        payload["steps"][2]["selectors"] = [["aria/Different tile"]]
        self.write_recording(payload)
        with self.assertRaisesRegex(self.mod.ReplayError, "re-recorded"):
            self.check(clip)

    def test_a_steps_mismatch_refuses(self):
        clip = self.published()
        with self.assertRaisesRegex(self.mod.ReplayError, "storyboard"):
            self.check(clip, steps="2-6")

    def test_tampered_clip_bytes_fail_the_fingerprint(self):
        clip = self.published()
        clip.write_bytes(b"tampered")
        with self.assertRaisesRegex(self.mod.ReplayError, "fingerprint"):
            self.check(clip)


class ArmWritesPendingForClipFramesOnly(ReplayFlowCase):
    def test_arm_marks_the_clip_and_leaves_the_still_alone(self):
        cwd = Path.cwd()
        os_chdir = __import__("os").chdir
        os_chdir(self.work)
        self.addCleanup(os_chdir, cwd)
        self.mod.arm(self.recording, self.storyboard)
        pending = (self.work / "public" / "clips"
                   / "scene-01-drill.mp4.replay.pending")
        self.assertTrue(pending.is_file())
        payload = json.loads(pending.read_text(encoding="utf-8"))
        self.assertEqual(payload["state"], "pending")
        self.assertEqual(payload["requested"]["steps"], [3, 6])
        self.assertFalse(
            (self.work / "public" / "screenshots"
             / "scene-00-overview.png.replay.pending").exists())


if __name__ == "__main__":
    unittest.main()
