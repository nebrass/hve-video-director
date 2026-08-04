# Migration: `hve-spielberg` → `hve-video-director`

**Version 0.1.0 renames this skill.** The pipeline, phases, workflows, scripts, and
generated-project layout are unchanged — only the name changed.

> **You must remove the old install.** `npx skills update` does **not** complete the rename —
> it installs the new skill alongside the old one and leaves the stale copy behind. See
> [Why `update` is not enough](#why-update-is-not-enough).

## Why the rename

The previous name referenced a living public figure. Regardless of intent, using a famous
person's name as a product identity carries trademark and right-of-publicity exposure, and
it implied an endorsement that never existed. The new name describes what the skill actually
does, and pairs an explicit domain (`video`) with the role it performs (`director`).

See [`TRADEMARKS.md`](TRADEMARKS.md) for third-party attribution.

## Upgrading

### If you installed with the Skills CLI (recommended)

```bash
# Global install
npx skills remove hve-spielberg --global
npx skills add nebrass/hve-video-director --global

# GitHub Copilot CLI, global
npx skills remove hve-spielberg --agent github-copilot --global
npx skills add nebrass/hve-video-director --agent github-copilot --global

# Project install — run from your project root
npx skills remove hve-spielberg
npx skills add nebrass/hve-video-director
```

### If you installed with `git clone`

Rename the directory so it matches the new skill name:

```bash
cd ~/.claude/skills            # or ~/.copilot/skills
mv hve-spielberg hve-video-director
cd hve-video-director
git remote set-url origin https://github.com/nebrass/hve-video-director.git
git pull
```

If you pull without renaming the directory, the skill still resolves — v0.1.0 falls back to
matching the skill's own layout rather than its directory name — but the invocation name and
your directory will disagree. Rename it.

### If you use the Claude Code plugin marketplace

Remove and re-add the plugin; the plugin name changed from `hve-spielberg` to
`hve-video-director`.

## What changes for you

| | Before | After |
|---|---|---|
| Invocation | `/hve-spielberg` | `/hve-video-director` |
| Repository | `nebrass/hve-spielberg` | `nebrass/hve-video-director` |
| Install dir | `<skills-home>/hve-spielberg/` | `<skills-home>/hve-video-director/` |
| Plugin name | `hve-spielberg` | `hve-video-director` |
| Version | `0.0.4` | `0.1.0` |

## What does *not* change

- **Existing generated video projects keep working.** Project scaffolding never embedded the
  skill name — `templates/` contains no reference to it. Your `project-plan.md`,
  `.hve/brief-state.json`, `storyboard.md`, `scenes/*.html`, and `out/final.mp4` are unaffected.
- **No phase, workflow, script, CLI flag, or file-format change.** `0.1.0` is a breaking
  release only because the install identity changed.
- **Old repository URLs keep resolving.** GitHub redirects the renamed repository, so existing
  clones, links, and `git fetch` continue to work. The old name will never be reused.

## Why `update` is not enough

The Skills CLI keys each install directory and lock entry by the `name` field in `SKILL.md`
frontmatter, not by the repository slug. Because the old repository URL redirects to the new one,
`npx skills update` *does* resolve the renamed skill — it fetches the new `SKILL.md`, reads
`name: hve-video-director`, and installs it under that new key.

What it does **not** do is remove what it replaced. The old `hve-spielberg` directory and its lock
entry both survive, so a single `update` leaves you with two installs:

```
$ npx skills update -g -y
Checking skills from source: nebrass/hve-spielberg
Found 1 global update(s)
Updating hve-spielberg…
  ✓ Updated hve-spielberg
✓ Updated 1 skill(s)

$ ls ~/.claude/skills/
hve-spielberg          # 0.0.4, still declares `name: hve-spielberg`
hve-video-director     # 0.1.0
```

Two consequences:

- **Your agent can load the stale one.** Both directories contain a valid `SKILL.md`, so both are
  discoverable, and the 0.0.4 copy still answers to the old name.
- **It never converges.** The stale lock entry stays pending forever — every subsequent
  `npx skills update` reports the same `✓ Updated 1 skill(s)` again.

Removing the old install explicitly is the only way to reach a clean state.

## Verifying the upgrade

```bash
# Should list hve-video-director at 0.1.0
npx skills list

# Should print the new banner
<skills-home>/hve-video-director/scripts/check_requirements.sh
```

## Trouble?

[Open an issue](https://github.com/nebrass/hve-video-director/issues).
