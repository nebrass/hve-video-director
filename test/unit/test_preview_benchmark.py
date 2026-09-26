#!/usr/bin/env python3
"""Offline tests for the preview-lifecycle benchmark (test/bench/preview_lifecycle.py).

The live benchmark needs the real HyperFrames CLI and network; these tests drive the same
harness against a small fake CLI that mimics the ``preview`` lifecycle flags, so the
orchestration, accounting and teardown are checked without either.
"""

import importlib.util
import io
import json
import os
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "preview_lifecycle", ROOT / "test" / "bench" / "preview_lifecycle.py"
)
bench = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bench)

FAKE_CLI = textwrap.dedent(r'''
    import http.server, json, os, signal, subprocess, sys, time
    from pathlib import Path

    STATE = Path(os.environ["FAKE_HF_STATE"])

    def load():
        return json.loads(STATE.read_text()) if STATE.exists() else {}

    def alive(pid):
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def serve(announce):
        server = http.server.HTTPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler)
        announce(server.server_port)
        server.serve_forever()

    args = sys.argv[1:]
    if args == ["--version"]:
        print("fake-0.0.1")
        sys.exit(0)
    if args[:1] == ["serve"]:
        port_file = Path(args[1])
        serve(lambda port: port_file.write_text(str(port)))
    project = os.path.realpath(os.getcwd())
    state = load()
    if "--list" in args:
        sessions = [dict(v, projectDir=k) for k, v in state.items() if alive(v["pid"])]
        print(json.dumps({"result": {"sessions": sessions}}))
    elif "--stop" in args:
        entry = state.pop(project, None)
        if entry and alive(entry["pid"]):
            os.kill(entry["pid"], signal.SIGTERM)
        STATE.write_text(json.dumps(state))
    elif "--foreground" in args:
        serve(lambda port: print(f"Server    http://127.0.0.1:{port}", flush=True))
    else:  # --background, or the non-interactive default of current CLIs
        entry = state.get(project)
        if not entry or not alive(entry["pid"]):
            port_file = Path(project).parent / "fake-port"
            port_file.unlink(missing_ok=True)
            child = subprocess.Popen(
                [sys.executable, __file__, "serve", str(port_file)],
                start_new_session=True, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            while not port_file.exists() or not port_file.read_text():
                time.sleep(0.02)
            entry = {"pid": child.pid, "port": int(port_file.read_text())}
            state[project] = entry
            STATE.write_text(json.dumps(state))
        print(f"Server    http://127.0.0.1:{entry['port']}")
''')


class HelperTestCase(unittest.TestCase):
    def test_parse_cputime_handles_ps_formats(self):
        self.assertAlmostEqual(bench.parse_cputime("0:00.12"), 0.12)
        self.assertAlmostEqual(bench.parse_cputime("00:01:05"), 65)
        self.assertAlmostEqual(bench.parse_cputime("1-02:00:00"), 93600)

    def test_parse_server_url_prefers_server_line(self):
        text = "Studio    http://localhost:3101/#project/bp\nServer    http://localhost:3101\n"
        self.assertEqual(bench.parse_server_url(text), "http://localhost:3101")
        self.assertEqual(bench.parse_server_url("at http://127.0.0.1:9/x"), "http://127.0.0.1:9")
        self.assertIsNone(bench.parse_server_url("no url here"))

    def test_process_tree_and_cpu_delta(self):
        table = {1: (0, 10, 1.0), 2: (1, 20, 2.0), 3: (2, 30, 3.0), 4: (0, 40, 4.0)}
        self.assertEqual(bench.process_tree({1}, table), {1, 2, 3})
        self.assertEqual(bench.process_tree({99}, table), set())
        after = {1: (0, 10, 1.5), 2: (1, 20, 2.0), 5: (1, 5, 0.25)}
        self.assertAlmostEqual(bench.cpu_delta({1, 2, 3, 5}, table, after), 0.75)

    def test_summary_reports_gain_of_fixed(self):
        runs = [
            {"strategy": "legacy-default", "lifecycle_s": 4.0, "residual_processes": 2},
            {"strategy": "legacy-default", "lifecycle_s": 6.0, "residual_processes": 2},
            {"strategy": "fixed", "lifecycle_s": 3.0, "residual_processes": 0},
            {"strategy": "fixed", "error": "boom"},
        ]
        summary = bench.summarize(runs)
        self.assertEqual(summary["strategies"]["legacy-default"]["lifecycle_s"]["median"], 5.0)
        self.assertEqual(summary["strategies"]["fixed"]["lifecycle_s"]["n"], 1)
        gain = summary["gains_of_fixed_over"]["legacy-default"]
        self.assertEqual(gain["lifecycle_s"]["saved"], 2.0)
        self.assertEqual(gain["residual_processes"]["percent"], 100)
        self.assertNotIn("legacy-attached", summary["gains_of_fixed_over"])


@unittest.skipIf(os.name == "nt", "the benchmark supports Linux and macOS only")
class FakeCliBenchmarkTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        tmp = Path(self.tmp.name)
        self.project = tmp / "project"
        (self.project / "out").mkdir(parents=True)
        (self.project / "index.html").write_text("<html></html>\n", encoding="utf-8")
        self.cli = tmp / "fake_hyperframes.py"
        self.cli.write_text(FAKE_CLI, encoding="utf-8")
        self.env_backup = os.environ.get("FAKE_HF_STATE")
        os.environ["FAKE_HF_STATE"] = str(tmp / "state.json")

    def tearDown(self):
        if self.env_backup is None:
            os.environ.pop("FAKE_HF_STATE", None)
        else:
            os.environ["FAKE_HF_STATE"] = self.env_backup
        self.tmp.cleanup()

    def run_bench(self, *extra):
        out_json = Path(self.tmp.name) / "result.json"
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = bench.main([
                "--project", str(self.project),
                "--cli", f"{sys.executable} {self.cli}",
                "--passes", "2", "--repeats", "1", "--idle", "0.2",
                "--edits", "1", "--edit-interval", "0.05", "--settle", "0.05",
                "--attach-grace", "0.5", "--start-timeout", "20",
                "--json", str(out_json), *extra,
            ])
        return code, json.loads(out_json.read_text()), stdout.getvalue(), stderr.getvalue()

    def test_measures_each_lifecycle_and_leaks_nothing(self):
        code, result, report, errors = self.run_bench()
        self.assertEqual(code, 0, errors)
        runs = {r["strategy"]: r for r in result["runs"]}
        self.assertEqual(set(runs), set(bench.STRATEGIES))
        for record in runs.values():
            self.assertNotIn("error", record)
            self.assertEqual(record["leaked_pids"], [])

        attached = runs["legacy-attached"]
        self.assertEqual(attached["servers_started"], 2)
        self.assertEqual(attached["blocking_calls"], 2)
        self.assertEqual(attached["call_return_s"], [None, None])
        self.assertGreaterEqual(attached["residual_processes"], 2)
        self.assertEqual(len(attached["listening_after_phase"]), 2)

        default = runs["legacy-default"]
        self.assertEqual(default["servers_started"], 1)
        self.assertEqual(default["blocking_calls"], 0)
        self.assertGreaterEqual(default["residual_processes"], 1)

        fixed = runs["fixed"]
        self.assertEqual(fixed["servers_started"], 1)
        self.assertEqual(len(fixed["reuse_s"]), 1)
        self.assertIsNotNone(fixed["stop_s"])
        self.assertEqual(fixed["residual_processes"], 0)
        self.assertEqual(fixed["residual_rss_mb"], 0)
        self.assertEqual(fixed["listening_after_phase"], [])

        self.assertIn("Gain of `fixed` over `legacy-attached`", report)
        # The source project is copied, never edited; the ignored output dir is not copied.
        self.assertEqual((self.project / "index.html").read_text(), "<html></html>\n")

    def test_rejects_unknown_strategy_and_missing_project(self):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(bench.main(["--strategies", "bogus"]), 2)
            self.assertEqual(bench.main(["--project", self.tmp.name]), 2)


if __name__ == "__main__":
    unittest.main()
