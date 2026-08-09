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
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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

    dest_root = Path(args.dest)
    dest_root.mkdir(parents=True, exist_ok=True)
    installed, missing = [], []

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
            for name, meta in sorted(skills.items()):
                skill_dir = (src / meta["skillPath"]).parent
                if not (skill_dir / "SKILL.md").is_file():
                    missing.append(name)
                    continue
                target = dest_root / name
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(skill_dir, target)
                installed.append(name)

    print(f"installed {len(installed)} skill(s) into {dest_root}")
    if missing:
        print(
            "NOT installed — recorded skillPath no longer exists at the "
            "source (upstream relayout?): " + ", ".join(sorted(missing)),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
