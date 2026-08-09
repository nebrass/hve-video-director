#!/usr/bin/env python3
"""Prove every narration section was synthesized for THIS script, not a previous one.

Phase 5 delegates TTS to the `media-use` audio engine, which reports a failed line as
a non-fatal anomaly and exits 0. Two properties of that engine make a failure both
silent and durable:

  * It never deletes a destination file before writing. A failed line leaves the
    PREVIOUS run's audio at the exact expected path — same name, plausible duration,
    valid header. Assembling then ships superseded narration under a current
    storyboard.
  * Its success predicate is `exit == 0 and the file exists`. A provider that exits 0
    without writing therefore reports success against the leftover, and the engine
    goes on to measure and transcribe it. So "voices[] holds one entry per section"
    cannot prove freshness — a laundered stale file satisfies it.

A third property rules out the obvious repair: `--only tts` replaces `voices[]`
wholesale, so retrying 2 lines of 40 leaves the metadata describing 2. Any check that
counts entries is wrong on exactly the recovery path it exists to enable.

So freshness is established by absence, not by self-report. `prepare` deletes the
requested sections; a line that fails to regenerate is then MISSING rather than stale,
and missing already fails loudly. `seal` records what survived, so assembly — a
separate process, often a separate session, which cannot observe the deletion — can
still prove it.

The split is deliberate. This script is skill-resident and reads upstream's
`audio_request.json`, so it absorbs that schema's churn. `generate_voiceover.py` is
copied into every project and hand-edited there; it therefore learns nothing about the
engine and checks only a hash against a manifest this repo defines.

`audio_meta.json` and the anomalies it echoes are ADVISORY DIAGNOSTICS ONLY. An
upstream schema change degrades this to "no explanation printed" — never to a false
green.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from pathlib import Path

# A section id is a zero-padded index and nothing else. It is interpolated into a
# path, so an id like "/tmp/take" or "../../secret" would make `prepare` unlink a file
# outside the project — pathlib lets an absolute component replace the whole path.
SECTION_ID = re.compile(r"^\d{2,}$")

PENDING_NAME = "vo-sections.pending.json"
MANIFEST_NAME = "vo-sections.json"
SCHEMA_VERSION = 1

# Attestations for the paths that produce no engine metadata: a confirmed local Kokoro
# voice via the HyperFrames CLI, or narration the user supplied. Both are legitimate
# and neither can be machine-verified against a request, so the operator states it.
ATTESTATIONS = ("engine", "local-tts", "user-supplied")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def state_dir(project_dir: Path) -> Path:
    return project_dir / ".hve"


def wav_for(project_dir: Path, section_id: str) -> Path:
    return project_dir / "assets" / "voice" / f"{section_id}.wav"


def mp3_for(project_dir: Path, section_id: str) -> Path:
    return project_dir / f"vo_section_{section_id}.mp3"


def load_request(project_dir: Path) -> dict:
    """Read audio_request.json. Only `lines[].id` and `lines[].text` are consumed."""
    path = project_dir / "audio_request.json"
    if not path.is_file():
        raise FileNotFoundError(f"no audio_request.json in {project_dir}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"audio_request.json is not valid JSON: {error}") from error
    lines = data.get("lines")
    if not isinstance(lines, list) or not lines:
        raise ValueError("audio_request.json carries no lines[]")
    out = {}
    for line in lines:
        if not isinstance(line, dict) or "id" not in line:
            raise ValueError("every audio_request.json line needs an id")
        section_id = str(line["id"])
        if not SECTION_ID.match(section_id):
            raise ValueError(
                f"invalid section id {section_id!r} — ids are zero-padded indices "
                "(00, 01, …). They are used as path components, so anything else is "
                "refused rather than resolved."
            )
        out[section_id] = str(line.get("text", ""))
    return out


def write_text_atomic(path: Path, content: str) -> None:
    """Publish state via tmp-write + fsync + rename.

    Both files this writes are proofs (the pending marker's absence-proof, the
    sealed manifest's byte record); truncating one mid-write destroys the seal
    and the only remedy is re-synthesis. Duplicated from validate_brief.py by
    design — every script here is standalone stdlib with no shared module.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    try:
        with tmp.open("x", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        try:
            dir_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            dir_fd = None
        if dir_fd is not None:
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
    except OSError:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def read_anomalies(project_dir: Path) -> list[str]:
    """Best-effort diagnostic. Never load-bearing — see the module docstring."""
    path = project_dir / "audio_meta.json"
    if not path.is_file():
        return []
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    voices = meta.get("voices")
    if not isinstance(voices, list):
        return []
    return [str(v.get("id")) for v in voices if isinstance(v, dict) and "id" in v]


def cmd_prepare(project_dir: Path, ids: list[str], as_json: bool) -> int:
    """Delete the sections about to be regenerated, so a failure leaves absence."""
    requested = load_request(project_dir)
    malformed = [i for i in ids if not SECTION_ID.match(i)]
    if malformed:
        emit({"errors": [f"invalid section id(s): {', '.join(malformed)}"]},
             as_json, stream=sys.stderr)
        return 2
    unknown = [i for i in ids if i not in requested]
    if unknown:
        emit({"errors": [f"ids not in audio_request.json: {', '.join(unknown)}"]},
             as_json, stream=sys.stderr)
        return 2
    target = ids or sorted(requested)
    removed = []
    for section_id in target:
        for path in (wav_for(project_dir, section_id), mp3_for(project_dir, section_id)):
            # Both layers: a stale wav laundered through a fresh transcode is
            # indistinguishable downstream, so clearing only one proves nothing.
            if path.exists():
                path.unlink()
                removed.append(str(path.relative_to(project_dir)))
    state_dir(project_dir).mkdir(parents=True, exist_ok=True)
    pending_path = state_dir(project_dir) / PENDING_NAME
    # A subset prepare during a retry round must EXTEND the round, not restart
    # it: dropping a previously-cleared id from the marker erases the
    # absence-proof behind its already-good take, and on a first round (no
    # prior manifest to carry it forward) seal then refuses exactly the
    # sections that synthesized correctly. `seal` unlinks the marker, which is
    # what ends the round.
    existing = {}
    if pending_path.is_file():
        try:
            existing = json.loads(pending_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}  # corrupt marker: its ids lose their proof; seal refuses them
    pending = {
        "schema_version": SCHEMA_VERSION,
        "ids": sorted(set(existing.get("ids", [])) | set(target)),
        "request_sha256": {
            **existing.get("request_sha256", {}),
            **{i: sha256_text(requested[i]) for i in target},
        },
    }
    write_text_atomic(
        pending_path, json.dumps(pending, indent=2, sort_keys=True) + "\n"
    )
    payload = {
        "prepared": target,
        "removed": removed,
        "message": (
            f"Cleared {len(removed)} file(s) for {len(target)} section(s). "
            "A section that now fails to synthesize is missing, not stale."
        ),
    }
    emit(payload, as_json)
    return 0


def cmd_check(project_dir: Path, as_json: bool) -> int:
    """Report which prepared sections came back, and build the retry request."""
    requested = load_request(project_dir)
    pending_path = state_dir(project_dir) / PENDING_NAME
    if pending_path.is_file():
        ids = json.loads(pending_path.read_text(encoding="utf-8")).get("ids", [])
    else:
        ids = sorted(requested)
    missing = [i for i in ids if not mp3_for(project_dir, i).is_file()
               and not wav_for(project_dir, i).is_file()]
    returned = read_anomalies(project_dir)
    payload = {
        "expected": ids,
        "missing": missing,
        "returned_by_engine": returned,
        "errors": [],
    }
    if missing:
        # Emit the retry input so the next engine call is a paste, not hand-assembly.
        retry = {"lines": [{"id": i, "text": requested[i]} for i in missing]}
        source = project_dir / "audio_request.json"
        base = json.loads(source.read_text(encoding="utf-8"))
        base["lines"] = retry["lines"]
        out = project_dir / "audio_request.retry.json"
        out.write_text(json.dumps(base, indent=1) + "\n", encoding="utf-8")
        payload["retry_request"] = str(out.relative_to(project_dir))
        payload["message"] = (
            f"{len(missing)} of {len(ids)} section(s) did not come back: "
            f"{', '.join(missing)}.\n"
            f"Wrote {out.name} — re-run the engine against it. "
            "Retry the failed ids only; re-clearing a good take re-bills it and "
            "rolls the dice again. Two retries, then stop and report."
        )
        emit(payload, as_json, stream=sys.stderr if not as_json else sys.stdout)
        return 1
    payload["message"] = f"All {len(ids)} prepared section(s) are present."
    emit(payload, as_json)
    return 0


def cmd_seal(project_dir: Path, attest: str, as_json: bool) -> int:
    """Record the bytes that will be assembled, so assembly can prove freshness."""
    pending_path = state_dir(project_dir) / PENDING_NAME
    if attest == "engine" and not pending_path.is_file():
        emit(
            {"errors": [
                "no pending marker — run `prepare` before synthesizing. Sealing "
                "files that were never cleared would certify stale bytes as fresh."
            ]},
            as_json,
            stream=sys.stderr,
        )
        return 2

    if attest == "engine":
        requested = load_request(project_dir)
        ids = sorted(requested)
        # `prepare` deliberately supports a subset, so presence of the marker is not
        # enough: an id that was never cleared has no absence-proof behind it, and
        # sealing it would certify exactly the leftover this gate exists to catch.
        # Such an id may be carried forward only when the previous manifest still
        # proves BOTH its bytes and that its script line has not changed.
        pending = json.loads(pending_path.read_text(encoding="utf-8"))
        prepared = set(pending.get("ids", []))
        prior = {}
        manifest_path = state_dir(project_dir) / MANIFEST_NAME
        if manifest_path.is_file():
            try:
                prior = json.loads(manifest_path.read_text(encoding="utf-8")).get(
                    "sections", {}
                )
            except (json.JSONDecodeError, OSError):
                prior = {}
        unproven = []
        for section_id in ids:
            if section_id in prepared:
                continue
            entry = prior.get(section_id)
            mp3 = mp3_for(project_dir, section_id)
            if (
                not entry
                or not mp3.is_file()
                or entry.get("audio_sha256") != sha256_file(mp3)
                or entry.get("request_sha256") != sha256_text(requested[section_id])
            ):
                unproven.append(section_id)
        if unproven:
            emit(
                {"errors": [
                    f"{len(unproven)} section(s) were neither prepared nor provably "
                    f"unchanged: {', '.join(unproven)}. Re-run `prepare` for them (or "
                    "`prepare` with no ids to clear everything) and synthesize again — "
                    "sealing them now would certify audio nothing cleared."
                ]},
                as_json,
                stream=sys.stderr,
            )
            return 1
    else:
        # No engine ran, so there is no request to bind against. The operator states
        # where the audio came from; the bytes are still recorded.
        requested = {}
        ids = sorted(
            p.name[len("vo_section_"):-len(".mp3")]
            for p in project_dir.glob("vo_section_*.mp3")
        )
        if not ids:
            emit({"errors": ["no vo_section_NN.mp3 files to seal"]}, as_json,
                 stream=sys.stderr)
            return 2

    sections = {}
    missing = []
    for section_id in ids:
        mp3 = mp3_for(project_dir, section_id)
        if not mp3.is_file() or mp3.stat().st_size == 0:
            missing.append(section_id)
            continue
        entry = {"audio_sha256": sha256_file(mp3)}
        if section_id in requested:
            entry["request_sha256"] = sha256_text(requested[section_id])
        sections[section_id] = entry
    if missing:
        emit(
            {"errors": [
                f"cannot seal — {len(missing)} section(s) have no audio: "
                f"{', '.join(missing)}. Transcode them, or re-run the engine."
            ]},
            as_json,
            stream=sys.stderr,
        )
        return 1

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "attest": attest,
        "sections": sections,
    }
    state_dir(project_dir).mkdir(parents=True, exist_ok=True)
    write_text_atomic(
        state_dir(project_dir) / MANIFEST_NAME,
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    )
    pending_path.unlink(missing_ok=True)
    emit(
        {
            "sealed": sorted(sections),
            "attest": attest,
            "message": (
                f"Sealed {len(sections)} section(s) ({attest}). "
                "generate_voiceover.py will verify these bytes before assembling."
            ),
        },
        as_json,
    )
    return 0


def emit(payload: dict, as_json: bool, *, stream=sys.stdout) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True), file=stream)
        return
    if payload.get("errors"):
        for error in payload["errors"]:
            print(f"Error: {error}", file=stream)
        return
    print(payload.get("message", ""), file=stream)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prove narration sections are fresh, not left over from a prior run."
    )
    parser.add_argument("--project-dir", type=Path, default=Path("."),
                        help="Generated video project (default: cwd).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser(
        "prepare",
        help="Delete the sections about to be synthesized so a failure leaves absence.",
    )
    prepare.add_argument("ids", nargs="*", help="Section ids; default every requested id.")
    prepare.add_argument("--json", action="store_true", help="Emit one JSON object.")

    check = subparsers.add_parser(
        "check", help="Report which prepared sections came back; write a retry request."
    )
    check.add_argument("--json", action="store_true", help="Emit one JSON object.")

    seal = subparsers.add_parser(
        "seal", help="Record the section bytes so assembly can verify them."
    )
    seal.add_argument("--attest", choices=ATTESTATIONS, default="engine",
                      help="Where the audio came from (default: engine).")
    seal.add_argument("--json", action="store_true", help="Emit one JSON object.")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    project_dir = args.project_dir.expanduser().resolve()
    try:
        if args.command == "prepare":
            return cmd_prepare(project_dir, args.ids, args.json)
        if args.command == "check":
            return cmd_check(project_dir, args.json)
        if args.command == "seal":
            return cmd_seal(project_dir, args.attest, args.json)
    except (FileNotFoundError, ValueError) as error:
        emit({"errors": [str(error)]}, args.json, stream=sys.stderr)
        return 2
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
