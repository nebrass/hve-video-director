#!/usr/bin/env python3
"""Install the HyperFrames ecosystem the provisioned CI job tests against.

Reads `skills-lock.json` as the list of skills this repo depends on, clones
each GitHub source once, and copies every skill's directory into a probed
skill home (default: `.agents/skills/`, the home the test suite probes
first). Pure stdlib; git is invoked with argv only.

Deliberately NOT pinned to the lock's content hashes: by default the clone
tracks upstream's default branch, because catching an upstream relayout before
a user does is the point of the drift job. A skill whose recorded `skillPath`
no longer exists upstream fails the install by name — that IS the drift
signal, delivered at install time with a message instead of as a silently
skipped test.

Two ways to install something other than the tip, because the tip can be
unusable for weeks: `--pinned` installs the commit recorded in
`compat/ecosystem-pin.json` (the last one this registry was verified against —
what pull-request CI gates on, so an unrelated upstream change cannot turn
every PR red), and `--ref` installs any commit, tag or branch by name. Tracking
the tip stays the default and stays in CI, on a schedule: a pin without a drift
job is how a relayout goes unnoticed, and a drift job without a pin is how it
blocks everything else.

Whatever this installs, CI **executes**: the `STORYBOARD_EXTRA_KEYS` round-trip
probe imports an upstream ESM module and drives it under node. Since the list of
what to fetch comes from `skills-lock.json`, a file any PR can edit, the source is
checked against an allowlist here and a `skillPath` may not escape its checkout.

That guard stops the accident — a lock edit or a copy-paste quietly redirecting CI
at an unrelated repo — and not a determined hostile PR, which could edit the guard
out in the same commit. What bounds *that* is GitHub's own posture, and it is the
job's real safety property: fork runs get no secrets and a read-only token. Never
give the provisioned job secrets, a write token, or `pull_request_target`.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIN_FILE = ROOT / "compat" / "ecosystem-pin.json"

# The ecosystem's own repository, and nothing else. This is the trust anchor for
# code CI runs; widening it is a security decision, not a config tweak.
ALLOWED_SOURCES = frozenset({"heygen-com/hyperframes"})

# A ref is handed to git as an argument. It must start with a letter or digit so
# it can never be read as an option, and it carries no `..` so it stays one name.
REF_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}")
# The pin is a full commit id on purpose: a branch or tag name moves, and a pin
# that moves is the default-branch behaviour with a misleading label.
FULL_COMMIT = re.compile(r"[0-9a-f]{40}")


def valid_ref(ref):
    return bool(REF_NAME.fullmatch(ref)) and ".." not in ref


def read_pin(pin_file=None):
    """Return (source, commit) from the pin file, or raise ValueError saying why not."""
    pin_file = pin_file or PIN_FILE
    try:
        pin = json.loads(pin_file.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"cannot read {pin_file}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"{pin_file} is not valid JSON: {error}") from error
    if not isinstance(pin, dict):
        raise ValueError(f"{pin_file} must hold a JSON object")
    source, ref = pin.get("source"), pin.get("ref")
    if not isinstance(source, str) or source not in ALLOWED_SOURCES:
        raise ValueError(
            f"{pin_file} pins source {source!r}, which is not an allowed source "
            f"({', '.join(sorted(ALLOWED_SOURCES))})"
        )
    if not isinstance(ref, str) or not FULL_COMMIT.fullmatch(ref):
        raise ValueError(
            f"{pin_file} must pin a full 40-character commit id, not {ref!r} — "
            "a branch or tag name moves, so it would not be a pin"
        )
    return source, ref


def checkout(url, dest, ref=None):
    """Fetch `url` into `dest`: the default branch's tip, or exactly `ref`."""
    if ref is None:
        subprocess.run(
            ["git", "clone", "--quiet", "--depth", "1", url, str(dest)], check=True
        )
        return
    subprocess.run(["git", "init", "--quiet", str(dest)], check=True)
    subprocess.run(
        ["git", "-C", str(dest), "fetch", "--quiet", "--depth", "1", url, ref],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(dest), "checkout", "--quiet", "FETCH_HEAD"], check=True
    )


def resolved_commit(checkout):
    """The commit actually installed, so a run is attributable after the fact.

    Best effort: a --source-dir checkout need not be a git repo at all.
    """
    try:
        done = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return done.stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest",
        default=str(ROOT / ".agents" / "skills"),
        help="skill home to install into (must be one the suite probes)",
    )
    parser.add_argument(
        "--source-dir",
        default=None,
        help="pre-cloned source checkout to copy from instead of cloning "
        "(single-source locks only)",
    )
    which = parser.add_mutually_exclusive_group()
    which.add_argument(
        "--ref",
        default=None,
        help="commit, tag or branch to install instead of the default branch's "
        "tip (single-source locks only)",
    )
    which.add_argument(
        "--pinned",
        action="store_true",
        help="install the commit recorded in compat/ecosystem-pin.json — the "
        "last one this registry was verified against",
    )
    args = parser.parse_args(argv)

    if args.source_dir and (args.ref or args.pinned):
        print(
            "--source-dir is installed exactly as it is on disk, so it cannot be "
            "combined with --ref or --pinned; check out the commit you want there "
            "first",
            file=sys.stderr,
        )
        return 2
    if args.ref is not None and not valid_ref(args.ref):
        print(
            f"refusing --ref {args.ref!r}: a ref starts with a letter or digit and "
            "contains only letters, digits, '.', '_', '/' and '-'",
            file=sys.stderr,
        )
        return 2
    refs = {}
    if args.pinned:
        try:
            pin_source, pin_ref = read_pin()
        except ValueError as error:
            print(f"cannot install the pinned ecosystem: {error}", file=sys.stderr)
            return 2
        refs[pin_source] = pin_ref

    lock = json.loads((ROOT / "skills-lock.json").read_text(encoding="utf-8"))
    by_source = {}
    for name, meta in lock["skills"].items():
        key = (meta.get("sourceType"), meta.get("source"))
        by_source.setdefault(key, {})[name] = meta

    # Refuse everything before fetching anything: one bad source in the lock must
    # not be reached by way of a successful clone of the others.
    disallowed = sorted(
        {source for _, source in by_source if source not in ALLOWED_SOURCES}
    )
    if disallowed:
        print(
            "refusing to install from unlisted source(s): "
            + ", ".join(repr(s) for s in disallowed)
            + "\nCI EXECUTES what this installs (the storyboard round-trip probe "
            "imports and runs an upstream module under node), so the source is "
            "allowlisted in test/install_ecosystem.py. Allowed: "
            + ", ".join(sorted(ALLOWED_SOURCES)),
            file=sys.stderr,
        )
        return 2

    dest_root = Path(args.dest)
    dest_root.mkdir(parents=True, exist_ok=True)
    installed, missing, escaping = [], [], []

    with tempfile.TemporaryDirectory() as tmp:
        for (source_type, source), skills in sorted(by_source.items()):
            if source_type != "github":
                print(
                    f"cannot install from {source!r}: unsupported sourceType "
                    f"{source_type!r}",
                    file=sys.stderr,
                )
                missing.extend(skills)
                continue
            if args.source_dir:
                src = Path(args.source_dir)
            else:
                src = Path(tmp) / source.replace("/", "__")
                checkout(
                    f"https://github.com/{source}.git",
                    src,
                    ref=args.ref or refs.get(source),
                )
            print(f"{source} @ {resolved_commit(src)}")
            root = src.resolve()
            for name, meta in sorted(skills.items()):
                skill_dir = (src / meta["skillPath"]).parent
                # A recorded path may not reach outside its own checkout: that
                # would copy — and then run — something the source never shipped.
                try:
                    resolved = skill_dir.resolve()
                    inside = resolved == root or root in resolved.parents
                except OSError:
                    inside = False
                if not inside:
                    escaping.append(f"{name} ({meta['skillPath']})")
                    continue
                if not (skill_dir / "SKILL.md").is_file():
                    missing.append(name)
                    continue
                target = dest_root / name
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(skill_dir, target)
                installed.append(name)

    print(f"installed {len(installed)} skill(s) into {dest_root}")
    if escaping:
        print(
            "REFUSED — skillPath escapes its checkout: " + ", ".join(sorted(escaping)),
            file=sys.stderr,
        )
    if missing:
        print(
            "NOT installed — recorded skillPath no longer exists at the "
            "source (upstream relayout?): " + ", ".join(sorted(missing)),
            file=sys.stderr,
        )
    return 1 if (missing or escaping) else 0


if __name__ == "__main__":
    raise SystemExit(main())
