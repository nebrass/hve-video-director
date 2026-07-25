# Agent Skills

This repo ships the **hve-spielberg** agent skill via [vercel-labs/skills](https://github.com/vercel-labs/skills). `SKILL.md` lives at the repository **root** (a single-skill layout), so the skills CLI discovers it directly — there is no `skills/` wrapper.

## Install

```bash
# Project install — auto-detects your agent and writes to its project skills home
npx skills add nebrass/hve-spielberg

# Global install (Claude Code is the default agent)
npx skills add nebrass/hve-spielberg --global

# Global install for GitHub Copilot CLI (~/.copilot/skills/)
npx skills add nebrass/hve-spielberg --agent github-copilot --global
```

The CLI auto-detects which coding agents you have installed and resolves the correct scanned skills home for each — you never hand-pick a path.

## Plugin manifest

Only **Claude Code** reads a plugin manifest; it ships at the repo root and points its skills source at `./` (the repo root holds `SKILL.md`), not `./skills/`:

- `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` — Claude Code (verified)

MIT-licensed, matching this repository.

## Native skill discovery (no manifest)

**GitHub Copilot CLI**, **OpenCode**, **Pi**, **Codex**, and **Cursor** need no manifest — they discover skills by directory convention and read the same Agent Skills `SKILL.md` format. They scan overlapping homes, all of which `npx skills add nebrass/hve-spielberg` writes into (`.agents/skills/` for a project install, `~/.claude/skills/` etc. for global):

- **OpenCode** — `.claude/skills/`, `~/.claude/skills/`, `.agents/skills/`, `~/.agents/skills/`, `.opencode/skills/`, `~/.config/opencode/skills/`
- **Pi** — `~/.pi/agent/skills/`, `~/.agents/skills/`, `.pi/skills/`, project `.agents/skills/` (once trusted)
- **Codex** — `$CWD/.agents/skills/`, `$REPO_ROOT/.agents/skills/`, `$HOME/.agents/skills/`, `/etc/codex/skills/`
- **Cursor** — `.agents/skills/`, `.cursor/skills/`, `~/.agents/skills/`, `~/.cursor/skills/`, plus `.claude/skills/` and `.codex/skills/`

`npx skills add nebrass/hve-spielberg` installs a `<name>/SKILL.md` subdir into a scanned home,
so these agents can discover it natively (see [`README.md`](README.md)). **Discovery is not
end-to-end compatibility:** Phase 0→5 is verified on Claude Code and GitHub Copilot CLI only.
OpenCode, Pi, Codex, and Cursor remain pipeline-unverified; their question and MCP tool identifiers
are resolved at runtime rather than assumed to match Claude Code.

## Using the skill

Invocation differs by host:

| Agent | Invocation |
|---|---|
| Claude Code | `/hve-spielberg` |
| GitHub Copilot CLI | `/hve-spielberg` or intent; inspect with `/skills info hve-spielberg` |
| OpenCode | Intent/native skill loader |
| Pi | `/skill:hve-spielberg` |
| Codex | `/skills` or `$hve-spielberg` |
| Cursor | `/hve-spielberg` |

See [`SKILL.md`](SKILL.md) and [`README.md`](README.md) for the six-phase pipeline.
