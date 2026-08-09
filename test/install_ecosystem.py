#!/usr/bin/env python3
"""Install the HyperFrames ecosystem the provisioned CI job tests against.

Reads `skills-lock.json` as the list of skills this repo depends on, clones
each GitHub source once, and copies every skill's directory into a probed
skill home (default: `.agents/skills/`, the home the test suite probes
first). Pure stdlib; git is invoked with argv only.

Deliberately NOT pinned to the lock's content hashes: the clone tracks
upstream's default branch, because catching an upstream relayout before a
user does is the point of the provisioned job. A skill whose recorded
`skillPath` no longer exists upstream fails the install by name — that IS
the drift signal, delivered at install time with a message instead of as a
silently skipped test.

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
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# The ecosystem's own repository, and nothing else. This is the trust anchor for
# code CI runs; widening it is a security decision, not a config tweak.
ALLOWED_SOURCES = frozenset({"heygen-com/hyperframes"})


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
    args = parser.parse_args(argv)

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
                subprocess.run(
                    ["git", "clone", "--depth", "1",
                     f"https://github.com/{source}.git", str(src)],
                    check=True,
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
