# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) — and GitHub Copilot CLI, which also reads `CLAUDE.md` — when working with code in this repository.

## What this repo is

This repo **is an agent skill** (`hve-spielberg`) that runs on both **Claude Code** and **GitHub Copilot CLI**, not a typical application. The "source" is prompt content (markdown) plus two Python helper scripts. There is no build system, no test suite, no lint config — the skill is consumed by future agent sessions that invoke `/hve-spielberg <project-dir>` (a slash command on Claude Code; invoked by name/intent on Copilot CLI). The `SKILL.md` frontmatter uses the Claude Code skill schema; Copilot CLI loads the skill from `name`/`description` and harmlessly ignores the Claude-only fields.

The renderer is **HyperFrames** (HTML + GSAP, rendered via headless Chromium). React/Remotion are no longer used.

Two things to keep distinct:

- **This repo** — the skill definition (`SKILL.md`, `workflows/`, `templates/`, `patterns/`, `scripts/`, `design-systems/`) plus the canonical demo (`example/`). Edits here change behavior for *all* users.
- **Generated video projects** — created by the skill at runtime in `{project-dir}/`. They contain `project-plan.md`, `context.md`, `storyboard.md`, `DESIGN.md`, `public/screenshots/`, `scenes/*.html`, `index.html` (root HyperFrames composition), `voiceover.mp3`, `out/final.mp4`. These do not live in this repo (except `example/`, which is *this skill's own* generated project, committed as the reference build).

## Architecture

`SKILL.md` is the orchestrator prompt. It loads first, decides the entry mode (`new` / `continue` / `jump`), and dispatches to one of six phase workflows. Each phase has a user-approval checkpoint before advancing.

```
SKILL.md (orchestrator)
  ├─ workflows/phase-0-discovery.md     → produces context.md
  ├─ workflows/phase-1-storytelling.md  → produces storyboard.md
  ├─ workflows/phase-2-capture.md       → produces public/screenshots/ (via Chrome DevTools MCP)
  ├─ workflows/phase-3-design.md        → produces DESIGN.md + scenes/*.html (via hyperframes skill)
  ├─ workflows/phase-4-production.md    → produces root index.html composition (via hyperframes skill)
  └─ workflows/phase-5-audio.md         → produces voiceover.mp3 + background-music.mp3 + out/final.mp4 (npx hyperframes render)
```

**Phase prerequisites are enforced in `jump` mode** — see `SKILL.md`. When editing workflows, preserve the file-presence contract:
- Phase 1 needs `context.md`
- Phase 2 needs `context.md` + `storyboard.md`
- Phase 3 needs capture artifacts (`public/screenshots/` and/or `public/clips/`)
- Phase 4 needs context + storyboard + `DESIGN.md` + `scenes/*.html`
- Phase 5 needs `index.html` (root composition) and passing `npx hyperframes lint|inspect|validate`
- Tutorial content mode prefers `public/clips/` but degrades to stills with a warning when clips are absent (warn-don't-block, spec §7.3); only missing captions is a hard check in tutorial mode

**External dependencies the skill calls out to:**
- `mcp__chrome-devtools__*` for app capture (Phase 2)
- The `hyperframes` skill for HTML/GSAP authoring rules (Phases 3 + 4)
- The `gsap` skill (optional companion) for choreography reference
- `npx hyperframes` CLI for `init`, `add` (pull catalog blocks, Phase 4), `lint`, `preview`, `inspect`, `validate`, `render`, `doctor` (render-environment diagnostics, Phase 5), `transcribe` (preferred voiceover-timing verifier in Phase 5; falls back to standalone Whisper if unavailable), and `tts` (used in Phase 5 as the no-API-key fallback when `ELEVENLABS_API_KEY` is unset)
- `mcp__chrome-devtools__screencast_*` + `resize_page` for Phase-2 web-clip capture (experimental, feature-detected — needs `--experimentalScreencast=true`; falls back to screenshots), and optional `asciinema`+`agg` for CLI clip recording (otherwise the authored-terminal path)
- `scripts/generate_voiceover.py` → ElevenLabs API + optional Whisper transcription (Phase 5)
- `scripts/caption_gen.py` → converts `transcript.json`/`voiceover.json` into `voiceover.srt` + `voiceover.vtt` caption sidecars (Phase 5, all modes; pure stdlib). ASR draft subtitles, not WCAG closed captions
- `scripts/stitch_clip.py` → normalizes/stitches raw captures into the Phase-2 clip contract (CFR30, H.264 high/yuv420p, `+faststart`) via the ffmpeg concat filter (pure stdlib). Native `capture-screen` is intentionally not shipped (no portable backend)
- `scripts/search_music.py` → Freesound API for CC music (Phase 5)
- `scripts/check_requirements.sh` → verifies the toolchain (node/python/ffmpeg/chrome-headless-shell/hyperframes CLI + companion skills + env vars); `--fix` auto-installs user-scoped deps and prints (never runs) sudo/system commands. Its `SKILL_HOMES` line must stay in lock-step with the canonical list in `SKILL.md` (same parity rule as the Phase 3/5 resolvers).

`templates/` files are copied into generated projects. `patterns/` files are referenced for visual techniques — `metallic-swoosh.md` documents *why* clipPath transitions are banned (black-sliver artifacts), and `cli-terminal-capture.md` documents the `asciinema` + `agg` workflow for the optional real-terminal-clip path (the dependency-free authored-terminal path uses `templates/scene-terminal.html`; the asciinema clip path uses `templates/scene-terminal-clip.html`).

## Working with the skill scripts

The Python scripts run inside generated video projects, not from this repo. `generate_voiceover.py` and `search_music.py` self-install `requests` via pip on first run; `caption_gen.py` and `stitch_clip.py` are pure standard library (the latter shells out to `ffmpeg`/`ffprobe`).

```bash
# Voiceover generation (from inside a generated project)
ELEVENLABS_API_KEY=... python3 scripts/generate_voiceover.py

# Caption sidecars (from inside a generated project, after a transcript exists)
python3 scripts/caption_gen.py                 # writes voiceover.srt + voiceover.vtt

# Normalize / stitch a capture into the Phase-2 clip contract
python3 scripts/stitch_clip.py raw.mp4 -o public/clips/scene-02-dashboard.mp4

# Music search (from inside a generated project) — query is a required argument
FREESOUND_API_KEY=... python3 scripts/search_music.py "cinematic corporate uplifting"
```

Both `ELEVENLABS_API_KEY` and `ELEVEN_LABS_API_KEY` are accepted (back-compat).

## Editing rules — DON'Ts that are easy to violate

These are enforced verbally in the `## DON'Ts` section of `SKILL.md`. If you modify workflows or patterns, do not reintroduce them:

- **No jitter** (shaking, vibrating motion).
- **No 360° scene spins.** Subtle `rotateY` ≤ 8° / `rotateZ` ≤ 4° on mockups only.
- **No 3D transforms in transitions.** 2D only (opacity, position, scale, gradient masks).
- **No clipPath transitions.** They cause anti-aliased black slivers; use crossfade + shine overlay (see `patterns/metallic-swoosh.md`).
- **No exit animations except on the closing scene.** The inter-scene transition owns the exit.
- **Never animate `display`, `visibility`, or call `.play()` inside a timeline.** Breaks HyperFrames' deterministic seek; use `opacity` + `pointer-events`.
- **Never animate `<img>` dimensions directly.** Wrap the `<img>` in a non-timed `<div>` and animate the wrapper's `transform`. Direct dimension tweens trigger layout recompute that breaks deterministic seek.
- **Never use `tl.from()` for opacity tweens.** GSAP records the end-state at registration; if the CSS rest is `opacity:0` the recorded end is `opacity:0` (the tween goes nowhere), and under stagger later instances re-hide elements earlier ones revealed. Always use `tl.fromTo(target, {opacity:0,...}, {opacity:1,...}, pos)`.
- **Never ship a bare `<video>` in a clip scene.** The runtime only frame-syncs videos carrying `data-start`; with 2+ clip scenes bare videos cross-route (wrong footage / black) while every gate passes green. The explicit contract is `id` + `data-start="0"` + `data-duration` (loader's crossfade-extended window, not the bare clip length) + `data-media-start` (storyboard `Clip in`) + `data-track-index="0"` — see `workflows/phase-3-design.md` § Clip scene.

## Common edits

- **Add a voice** → update both the `## ElevenLabs Voice IDs` table in `SKILL.md` and the `## Voices` table in `README.md` (the two tables must stay in sync).
- **Change phase logic** → edit the relevant `workflows/phase-N-*.md`; update the prerequisite list in `SKILL.md` if a new required file is introduced.
- **Adjust prerequisite checks** → the `## Prerequisites` block in `SKILL.md` (runs at skill entry).
- **Add a user-interaction prompt in a workflow** → write it as a neutral `{"questions":[...]}` block (the runtime-agnostic schema), introduced by plain prose ("ask the user…", "present selectable options…"). **Never name a picker tool** (`AskUserQuestion`, `ask_user`) or write a literal tool call inside a workflow — the per-runtime binding for the question schema, `Skill(<name>)`, and `multiSelect` lives in **one place**: `SKILL.md` § Runtime Compatibility. This is the "name actions, not tools" rule that keeps the phase content portable; a tool name hard-coded in a phase body is a portability regression. (Qualified MCP names like `mcp__chrome-devtools__*` are *not* a violation — they're identical across runtimes; the rule targets names that *differ* per runtime.)
- **Change where the skill can be installed** (`$SKILL_HOMES`) → `SKILL.md` § Runtime Compatibility holds the canonical search list. The same `SKILL_ROOT=…` bootstrap and pipe-delimited `SKILL_HOMES="…"` line are repeated in the `SKILL.md` prereq probe, the `SKILL_DIR` resolver of `workflows/phase-3-design.md` + `workflows/phase-5-audio.md`, and `scripts/check_requirements.sh` (shell state can't cross the agent's separate bash calls, so the list is re-stated at each bootstrap point rather than sourced). The `|` delimiter plus `IFS='|'` preserves skill paths containing spaces. Keep all `SKILL_HOMES` lines byte-identical; verify with:
  ```bash
  grep -rho 'SKILL_HOMES="[^"]*"' SKILL.md workflows/phase-3-design.md workflows/phase-5-audio.md scripts/check_requirements.sh | sort -u | wc -l   # must print 1
  ```
- **Bump skill metadata** → frontmatter at top of `SKILL.md` (especially `allowed-tools` if a new MCP tool is needed).
- **Bump the GSAP version** → the CDN `<script>` tags carry a Subresource Integrity hash (`integrity="sha384-…" crossorigin="anonymous"`), pinned to `gsap@3.14.2`. Changing the version *requires* recomputing the hash, or the script is blocked and every scene renders without animation (caught by `npx hyperframes validate` in Phase 4/5). Update **all** occurrences together — `templates/scene-*.html`, the skeletons in `workflows/phase-3-design.md` + `workflows/phase-4-production.md`, and every `example/**/*.html`:
  ```bash
  V=3.x.y   # new version
  H="sha384-$(curl -sL https://cdn.jsdelivr.net/npm/gsap@$V/dist/gsap.min.js | openssl dgst -sha384 -binary | base64)"
  # then replace src=…/gsap@$V/… and integrity="$H" in every file above (keep them in lock-step)
  ```

## Installation paths users invoke

```bash
# Recommended — the skills CLI auto-detects the agent and resolves its skills home:
npx skills add nebrass/hve-spielberg                                   # project install
npx skills add nebrass/hve-spielberg --global                         # global (Claude Code default)
npx skills add nebrass/hve-spielberg --agent github-copilot --global  # global for Copilot CLI

# Fallback — manual git clone into the agent's skills home:
git clone https://github.com/nebrass/hve-spielberg.git ~/.claude/skills/hve-spielberg
```

The repo ships a Claude Code plugin manifest at root (`.claude-plugin/plugin.json` + `marketplace.json`, source `./`) plus a root `AGENTS.md`. Other agents (GitHub Copilot CLI, OpenCode, Pi, Codex, Cursor) need no manifest — they discover the skill by directory convention from the homes `npx skills add` writes into (`.agents/skills/`, `.claude/skills/`, etc.). See `AGENTS.md` for the per-agent scan paths.

When testing skill changes locally, the global install path is `~/.claude/skills/hve-spielberg/` (Claude Code) or `~/.copilot/skills/hve-spielberg/` (GitHub Copilot CLI).

## Git / release conventions

Commits follow Conventional Commits (`feat`, `fix`, `docs`, `style`, `refactor`, `chore`). Recent history shows `feat(audio):`, `docs:`, `style(readme):`, `fix(readme):` — match the existing scope style. License is MIT.
