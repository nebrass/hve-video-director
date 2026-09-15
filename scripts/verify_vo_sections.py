#!/usr/bin/env python3
"""Prove every narration section belongs to THIS script and synthesis identity.

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

Preparation and schema-2 seals bind the complete request, each exact line and all
non-BGM/SFX settings to the checked language profile's speech fingerprint. Changing
only the text locale leaves speech identity intact; changing synthesis settings does
not. A local/user-supplied origin attestation cannot waive language-aware preparation.

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
import math
import os
import re
import sys
import uuid
from pathlib import Path

# A section id is a zero-padded index and nothing else. It is interpolated into a
# path, so an id like "/tmp/take" or "../../secret" would make `prepare` unlink a file
# outside the project — pathlib lets an absolute component replace the whole path.
SECTION_ID = re.compile(r"^[0-9]{2,}$")

PENDING_NAME = "vo-sections.pending.json"
MANIFEST_NAME = "vo-sections.json"
PROFILE_NAME = "language-profile.json"
SCHEMA_VERSION = 2

# Attestations for the paths that produce no engine metadata: a confirmed local Kokoro
# voice via the HyperFrames CLI, or narration the user supplied. Language-aware
# attestations name the origin; they do not waive request/profile/preparation proof.
ATTESTATIONS = ("engine", "local-tts", "user-supplied")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(value: object) -> str:
    """Hash exact JSON data independently of whitespace or object key order."""
    return sha256_text(json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    ))


def state_dir(project_dir: Path) -> Path:
    return project_dir / ".hve"


def wav_for(project_dir: Path, section_id: str) -> Path:
    return project_dir / "assets" / "voice" / f"{section_id}.wav"


def mp3_for(project_dir: Path, section_id: str) -> Path:
    return project_dir / f"vo_section_{section_id}.mp3"


def read_json_object(path: Path) -> dict:
    """Read a proof/request object without treating malformed data as missing."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"{path.name} is not valid JSON: {error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    try:
        sha256_json(data)  # Reject NaN/Infinity before a request can clear any audio.
    except ValueError as error:
        raise ValueError(f"{path.name} is not finite, UTF-8 JSON: {error}") from error
    return data


def load_request(project_dir: Path) -> dict:
    """Read exact lines and all settings except independent BGM/SFX requests."""
    path = project_dir / "audio_request.json"
    if not path.is_file():
        # read_json_object only translates malformed JSON, so without this the
        # operator sees a bare ENOENT instead of the file that is missing.
        raise FileNotFoundError(f"no audio_request.json in {project_dir}")
    data = read_json_object(path)
    lines = data.get("lines")
    if not isinstance(lines, list) or not lines:
        raise ValueError("audio_request.json carries no lines[]")
    seen = set()
    for line in lines:
        if not isinstance(line, dict) or "id" not in line:
            raise ValueError("every audio_request.json line needs an id")
        section_id = line["id"]
        if not isinstance(section_id, str) or not SECTION_ID.fullmatch(section_id):
            raise ValueError(
                f"invalid section id {section_id!r} — ids are zero-padded indices "
                "(00, 01, …). They are used as path components, so anything else is "
                "refused rather than resolved."
            )
        if section_id in seen:
            raise ValueError(f"duplicate section id {section_id} in audio_request.json")
        seen.add(section_id)
        if not isinstance(line.get("text"), str) or not line["text"].strip():
            raise ValueError(f"section {section_id} needs nonempty exact text")
    for field in ("provider", "voice", "model", "lang", "narration_language"):
        if field in data and (not isinstance(data[field], str) or not data[field].strip()):
            raise ValueError(f"audio_request.json {field} must be a nonempty string")
    if "speed" in data and (
        isinstance(data["speed"], bool) or not isinstance(data["speed"], (int, float))
        or not math.isfinite(data["speed"]) or data["speed"] <= 0
    ):
        raise ValueError("audio_request.json speed must be a positive finite number")
    return data


def read_proof(path: Path) -> dict:
    """Read legacy proofs for inspection/replacement, never for new subset reuse."""
    if not path.exists():
        return {}
    data = read_json_object(path)
    if type(data.get("schema_version")) is not int or data["schema_version"] not in (1, 2):
        raise ValueError(f"{path.name} has an unsupported schema_version")
    return data


def request_identity(project_dir: Path, data: dict | None = None) -> dict:
    """Bind settings, each complete line and the repo-owned speech identity."""
    data = load_request(project_dir) if data is None else data
    profile_path = state_dir(project_dir) / PROFILE_NAME
    speech_fingerprint = None
    if profile_path.exists():
        profile = read_json_object(profile_path)
        speech = profile.get("speech")
        speech_fields = {"provider", "model", "voice", "narration_language",
                         "tts_language", "asr_language"}
        if (type(profile.get("schema_version")) is not int or profile["schema_version"] != 1
                or not isinstance(speech, dict) or set(speech) != speech_fields
                or not all(isinstance(value, str) and value for value in speech.values())
                or not isinstance(profile.get("narration"), dict)
                or profile["narration"].get("tag") != speech["narration_language"]):
            raise ValueError("language-profile.json is invalid; recheck language-profile")
        speech_fingerprint = f"sha256:{sha256_json(speech)}"
        if profile.get("speech_fingerprint") != speech_fingerprint:
            raise ValueError("language-profile.json speech fingerprint is stale")
        for field, speech_field in (
            ("provider", "provider"), ("voice", "voice"), ("model", "model"),
            ("lang", "tts_language"), ("narration_language", "narration_language"),
        ):
            if data.get(field) != speech[speech_field]:
                raise ValueError(
                    f"audio_request.json {field} does not match the checked language profile"
                )
    elif "narration_language" in data:
        raise ValueError("language-profile.json is missing for a language-aware request")
    settings = {key: value for key, value in data.items() if key not in {"lines", "bgm", "sfx"}}
    synthesis_sha256 = sha256_json({
        "settings": settings, "speech_fingerprint": speech_fingerprint,
    })
    return {
        "data": data,
        "lines": {line["id"]: line for line in data["lines"]},
        "speech_fingerprint": speech_fingerprint,
        "synthesis_sha256": synthesis_sha256,
        "request_fingerprint": sha256_json({
            "synthesis_sha256": synthesis_sha256, "lines": data["lines"],
        }),
        "request_sha256": {
            line["id"]: sha256_json({"synthesis_sha256": synthesis_sha256, "line": line})
            for line in data["lines"]
        },
    }


def require_profile_binding(identity: dict, *proofs: dict) -> None:
    """Refuse to erase an existing language binding by removing its profile."""
    if identity["speech_fingerprint"] is None and any(
        proof.get("speech_fingerprint") is not None for proof in proofs
    ):
        raise ValueError("language profile was removed; restore it before preparing or sealing")


def pending_ids(pending: dict) -> list[str]:
    """Validate the absence proof before consulting any of its paths."""
    if pending.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("legacy preparation proof; run full `prepare` and synthesize again")
    ids = pending.get("ids")
    hashes = pending.get("request_sha256")
    if (not isinstance(ids, list) or not ids
            or not all(isinstance(i, str) and SECTION_ID.fullmatch(i) for i in ids)
            or len(ids) != len(set(ids)) or not isinstance(hashes, dict)
            or set(hashes) != set(ids)
            or not all(isinstance(h, str) and re.fullmatch(r"[0-9a-f]{64}", h)
                       for h in hashes.values())):
        raise ValueError("invalid pending preparation proof; run full `prepare`")
    return ids


def require_prepared_request(identity: dict, pending: dict) -> list[str]:
    """Reject any request edit after prepare, including edits to prepared lines."""
    ids = pending_ids(pending)
    if any(pending.get(key) != identity[key] for key in (
        "synthesis_sha256", "speech_fingerprint", "request_fingerprint",
    )) or any(
        pending["request_sha256"][i] != identity["request_sha256"].get(i) for i in ids
    ):
        raise ValueError(
            "request or speech profile changed after prepare; prepare the changed "
            "sections again (all sections for synthesis-setting changes)"
        )
    return ids


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
    voices = meta.get("voices") if isinstance(meta, dict) else None
    if not isinstance(voices, list):
        return []
    return [str(v.get("id")) for v in voices if isinstance(v, dict) and "id" in v]


def cmd_prepare(project_dir: Path, ids: list[str], as_json: bool) -> int:
    """Delete the sections about to be regenerated, so a failure leaves absence."""
    identity = request_identity(project_dir)
    requested = identity["lines"]
    malformed = [i for i in ids if not SECTION_ID.fullmatch(i)]
    if malformed:
        emit({"errors": [f"invalid section id(s): {', '.join(malformed)}"]},
             as_json, stream=sys.stderr)
        return 2
    unknown = [i for i in ids if i not in requested]
    if unknown:
        emit({"errors": [f"ids not in audio_request.json: {', '.join(unknown)}"]},
             as_json, stream=sys.stderr)
        return 2
    target = sorted(set(ids)) if ids else sorted(requested)
    pending_path = state_dir(project_dir) / PENDING_NAME
    existing = read_proof(pending_path)
    prior = read_proof(state_dir(project_dir) / MANIFEST_NAME)
    require_profile_binding(identity, existing, prior)
    retained = {}
    if set(target) != set(requested):
        existing_ids = set(pending_ids(existing)) if existing else set()
        proofs = [existing]
        if set(requested) - existing_ids - set(target):
            proofs.append(prior)
        for proof in proofs:
            if not proof:
                continue
            if proof["schema_version"] != SCHEMA_VERSION:
                raise ValueError(
                    "legacy text-only proof cannot support a subset retry; run full `prepare`"
                )
            if (proof.get("synthesis_sha256") != identity["synthesis_sha256"]
                    or proof.get("speech_fingerprint") != identity["speech_fingerprint"]):
                raise ValueError(
                    "synthesis settings or speech profile changed; run full `prepare` "
                    "before synthesizing, not a subset retry"
                )
        if existing:
            for section_id in sorted(existing_ids):
                if section_id in target:
                    continue
                if existing["request_sha256"][section_id] != identity["request_sha256"].get(section_id):
                    raise ValueError(
                        f"prepared section {section_id} changed; include it in `prepare` "
                        "before reusing the rest of this retry round"
                    )
                retained[section_id] = existing["request_sha256"][section_id]
    pending = {
        "schema_version": SCHEMA_VERSION,
        "ids": sorted(set(retained) | set(target)),
        "speech_fingerprint": identity["speech_fingerprint"],
        "synthesis_sha256": identity["synthesis_sha256"],
        "request_fingerprint": identity["request_fingerprint"],
        "request_sha256": {
            **retained, **{i: identity["request_sha256"][i] for i in target},
        },
    }
    # Validate the whole request and every retained proof before clearing either layer.
    removed = []
    for section_id in target:
        for path in (wav_for(project_dir, section_id), mp3_for(project_dir, section_id)):
            # Both layers: a stale wav laundered through a fresh transcode is
            # indistinguishable downstream, so clearing only one proves nothing.
            if path.exists():
                path.unlink()
                removed.append(str(path.relative_to(project_dir)))
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
    identity = request_identity(project_dir)
    pending_path = state_dir(project_dir) / PENDING_NAME
    pending = read_proof(pending_path)
    if not pending:
        raise ValueError("no pending marker — run `prepare` before synthesizing")
    require_profile_binding(identity, pending)
    ids = require_prepared_request(identity, pending)
    missing = [
        i for i in ids if not any(
            path.is_file() and path.stat().st_size > 0
            for path in (mp3_for(project_dir, i), wav_for(project_dir, i))
        )
    ]
    returned = read_anomalies(project_dir)
    payload = {
        "expected": ids,
        "missing": missing,
        "returned_by_engine": returned,
        "errors": [],
    }
    if missing:
        # Emit the retry input so the next engine call is a paste, not hand-assembly.
        base = {**identity["data"], "lines": [identity["lines"][i] for i in missing]}
        out = project_dir / "audio_request.retry.json"
        write_text_atomic(out, json.dumps(base, indent=1) + "\n")
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
    pending = read_proof(pending_path)
    prior = read_proof(state_dir(project_dir) / MANIFEST_NAME)
    data = load_request(project_dir) if (project_dir / "audio_request.json").exists() else None
    needs_request = (
        attest == "engine" or (state_dir(project_dir) / PROFILE_NAME).exists()
        or bool(pending) or prior.get("speech_fingerprint") is not None
        or (data is not None and "narration_language" in data)
    )
    if needs_request and not pending:
        emit(
            {"errors": [
                "no pending marker — run `prepare` before synthesizing. Sealing "
                "files that were never cleared would certify stale bytes as fresh."
            ]},
            as_json,
            stream=sys.stderr,
        )
        return 2

    identity = None
    if needs_request:
        identity = request_identity(project_dir, data)
        require_profile_binding(identity, pending, prior)
        requested = identity["lines"]
        ids = sorted(requested)
        # `prepare` deliberately supports a subset, so presence of the marker is not
        # enough: an id that was never cleared has no absence-proof behind it, and
        # sealing it would certify exactly the leftover this gate exists to catch.
        # Such an id may be carried forward only when the previous manifest still
        # proves its bytes, exact line, synthesis settings and speech identity.
        prepared = set(require_prepared_request(identity, pending))
        prior_sections = prior.get("sections", {})
        if not isinstance(prior_sections, dict):
            raise ValueError("vo-sections.json sections must be an object")
        unproven = []
        for section_id in ids:
            if section_id in prepared:
                continue
            entry = prior_sections.get(section_id)
            mp3 = mp3_for(project_dir, section_id)
            if (
                prior.get("schema_version") != SCHEMA_VERSION
                or prior.get("synthesis_sha256") != identity["synthesis_sha256"]
                or prior.get("speech_fingerprint") != identity["speech_fingerprint"]
                or not isinstance(entry, dict)
                or not mp3.is_file()
                or entry.get("audio_sha256") != sha256_file(mp3)
                or entry.get("request_sha256") != identity["request_sha256"][section_id]
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
        # Historical standalone recordings can still be attested without a profile.
        # Once language-aware, removing a request/profile never reopens this path.
        requested = {}
        ids = sorted(
            p.name[len("vo_section_"):-len(".mp3")]
            for p in project_dir.glob("vo_section_*.mp3")
        )
        if not ids:
            emit({"errors": ["no vo_section_NN.mp3 files to seal"]}, as_json,
                 stream=sys.stderr)
            return 2
        if not all(SECTION_ID.fullmatch(i) for i in ids):
            raise ValueError("attested filenames must use zero-padded section indices")

    sections = {}
    missing = []
    for section_id in ids:
        mp3 = mp3_for(project_dir, section_id)
        if not mp3.is_file() or mp3.stat().st_size == 0:
            missing.append(section_id)
            continue
        entry = {"audio_sha256": sha256_file(mp3)}
        if identity is not None:
            entry["request_sha256"] = identity["request_sha256"][section_id]
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
        "speech_fingerprint": identity["speech_fingerprint"] if identity else None,
    }
    if identity is not None:
        manifest.update({
            "synthesis_sha256": identity["synthesis_sha256"],
            "request_fingerprint": identity["request_fingerprint"],
            "script_sha256": {i: sha256_text(line["text"]) for i, line in requested.items()},
        })
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
