# Copilot Instructions — hve-spielberg

## What this repo is

This repo **is an agent skill** (`hve-spielberg`) that runs on both **GitHub Copilot CLI** and **Claude Code**, not a typical application. The "source" is prompt content (markdown) plus Python helper scripts. There is no build system or lint config; pure-stdlib helper tests live under `test/`. The skill is consumed by future agent sessions that invoke `/hve-spielberg <project-dir>` (a slash command on Claude Code; invoked by name/intent on Copilot CLI). The `SKILL.md` frontmatter follows the Claude Code skill schema; Copilot CLI loads the skill from its `name`/`description` and harmlessly ignores the Claude-only fields (`allowed-tools`, `user-invocable`, `argument-hint`). See the **Runtime Compatibility** section in `SKILL.md` for how interaction blocks (`{"questions": […]}`), companion-skill loading (`Skill(<name>)`), and skill-home paths map across runtimes — preserve that mapping when editing.

The renderer is **HyperFrames** (HTML + GSAP, rendered via headless Chromium). React/Remotion are **not** used.

Keep two scopes distinct when editing:

- **This repo** — the skill definition (`SKILL.md`, `workflows/`, `templates/`, `patterns/`, `scripts/`, `design-systems/`). Edits here change behavior for *all* users.
- **Generated video projects** — created by the skill at runtime in `{project-dir}/`. They contain `project-plan.md`, `.hve/brief-state.json`, `context.md`, `storyboard.md`, `DESIGN.md`, `public/screenshots/`, `scenes/*.html`, `index.html` (root HyperFrames composition), `voiceover.mp3`, `out/final.mp4`. These do **not** live in this repo (except the canonical reference build under `example/`).

## Architecture

`SKILL.md` is the orchestrator prompt. It loads first, decides the entry mode (`new` / `continue` / `jump`), and dispatches to one of six phase workflows. Each phase has a user-approval checkpoint before advancing.

```
SKILL.md (orchestrator)
  ├─ workflows/phase-0-discovery.md     → produces context.md
  ├─ workflows/phase-1-storytelling.md  → produces storyboard.md
  ├─ workflows/phase-2-capture.md       → produces public/screenshots/ (via Chrome DevTools MCP)
  ├─ workflows/phase-3-design.md        → produces DESIGN.md + scenes/*.html (via hyperframes skill)
  ├─ workflows/phase-4-production.md    → produces root index.html composition (via hyperframes skill)
  └─ workflows/phase-5-audio.md         → produces voiceover.mp3 + background-music.mp3 + out/final.mp4
                                          (npx hyperframes render)
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
- The `hyperframes` companion agent skill for HTML/GSAP authoring rules (Phases 3 + 4) — distinct from the `hyperframes` npm CLI
- The `gsap` skill (optional companion) for choreography reference
- `npx hyperframes` CLI for `init`, `add` (pull catalog blocks, Phase 4), `lint`, `preview`, `inspect`, `validate`, `render`, `doctor` (render-environment diagnostics, Phase 5), `transcribe` (preferred voiceover-timing verifier in Phase 5; falls back to standalone Whisper if unavailable), and `tts` (used in Phase 5 when the user explicitly confirms a local Kokoro voice)
- `mcp__chrome-devtools__screencast_*` + `resize_page` for Phase-2 web-clip capture (experimental, feature-detected — needs `--experimentalScreencast=true`; falls back to screenshots), and optional `asciinema`+`agg` for CLI clip recording (otherwise the authored-terminal path)
- `scripts/generate_voiceover.py` → ElevenLabs API + optional Whisper transcription (Phase 5)
- `scripts/caption_gen.py` → transcript JSON to SRT/VTT caption sidecars (pure stdlib)
- `scripts/capture_screen.py` → fixed-duration, silent native desktop/region capture orchestrator (pure stdlib): macOS `screencapture`, Windows `gdigrab`, X11 `x11grab`, or feature-detected Wayland `wf-recorder`; WSL/unavailable Wayland return explicit handoffs. It trims via sibling `stitch_clip.py`, validates duration/frame count within one frame, and uses `<clip>.capture.pending` + fingerprinted `<clip>.capture.json` state so failed retakes preserve prior valid media but cannot count as complete.
- `scripts/stitch_clip.py` → canonical raw-capture normalizer/stitcher for CFR30 H.264 High/yuv420p, even dimensions, no audio, and `+faststart` (pure stdlib wrapper for ffmpeg/ffprobe)
- `scripts/validate_brief.py` → exact Creative Brief parser, consent-gated legacy placeholder migration, revision-bound story/audio fingerprints, atomic `.hve/brief-state.json`, phase stamps, and stale-prerequisite checks (pure stdlib)
- `scripts/search_music.py` → Freesound API for CC music (Phase 5)
- `scripts/check_requirements.sh` → structured toolchain preflight. Default, `--json`, and
  `--plan` are side-effect-free and never use online `npx` probes. Scoped
  `--fix=<id,id>` runs only selected safe user-scoped fixes; bare `--fix` means all safe fixes.
  It never runs system/sudo commands or sets environment variables. Phase -1 consumes its JSON
  only for a direct/default first `new` run; explicit `continue` and `jump` skip onboarding.

`templates/` files are copied into generated projects. `patterns/` files are referenced for visual techniques. `patterns/INDEX.md` is the wayfinding map between local patterns and the deeper `hyperframes` skill references — read it before adding new pattern files. `patterns/metallic-swoosh.md` documents *why* clipPath transitions are banned (black-sliver artifacts).

`design-systems/<slug>/DESIGN.md` is the brand spec consumed by Phase 3 Path A — MIT-licensed, video-focused, authored by this skill. The canonical research source for new contributions is [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) (MIT, 73 brands, has a `npx getdesign add <slug>` CLI). The skill is **video-only** — it does not produce, render, or analyse web/UI artifacts.

## Working with the skill scripts

The media scripts run inside generated video projects; `validate_brief.py` runs from the installed
skill against a generated project via `--project-dir`. Only `generate_voiceover.py` and
`search_music.py` self-install `requests`; capture, stitch, caption, and Creative Brief validation
helpers are pure standard library.

```bash
# Voiceover generation (from inside a generated project)
ELEVENLABS_API_KEY=... python3 scripts/generate_voiceover.py

# Fixed-duration silent native screen/region capture
python3 scripts/capture_screen.py --duration 6 --region 100,80,1280,720 \
  -o public/clips/scene-02-dashboard.mp4

# Normalize or stitch existing recordings
python3 scripts/stitch_clip.py raw.mov -o public/clips/scene-02-dashboard.mp4

# Validate the Creative Brief in a generated project
python3 /path/to/hve-spielberg/scripts/validate_brief.py \
  --project-dir /path/to/generated-project status --json
# Legacy plans only, after explicit user consent
python3 /path/to/hve-spielberg/scripts/validate_brief.py \
  --project-dir /path/to/generated-project migrate

# Music search (from inside a generated project)
FREESOUND_API_KEY=... python3 scripts/search_music.py
```

Both `ELEVENLABS_API_KEY` and `ELEVEN_LABS_API_KEY` are accepted (back-compat).

There is no build or lint command for this repo. Run `bash test/run.sh` for the stdlib helper tests;
validation of workflow changes still happens by running `/hve-spielberg <project-dir>` end-to-end
in Claude Code. The canonical reference build is `example/` (run `example/voiceover.py` then
`npx hyperframes render` to reproduce its `out/final.mp4`).

## Editing rules — DON'Ts that are easy to violate

These are enforced verbally in the `## DON'Ts` section of `SKILL.md`. If you modify workflows or patterns, do not reintroduce them:

- **No jitter** (shaking, vibrating motion).
- **No 360° scene spins.** Subtle `rotateY` ≤ 8° / `rotateZ` ≤ 4° on mockups only.
- **No 3D transforms in transitions.** 2D only (opacity, position, scale, gradient masks).
- **No clipPath transitions.** They cause anti-aliased black slivers; use crossfade + shine overlay (see `patterns/metallic-swoosh.md`).
- **No exit animations except on the closing scene.** The inter-scene transition owns the exit.
- **Never animate `display`, `visibility`, or call `.play()` inside a timeline.** Breaks HyperFrames' deterministic seek; use `opacity` + `pointer-events`.
- **Never animate `<img>` dimensions directly.** Wrap the `<img>` in a non-timed `<div>` and animate the wrapper's `transform`. Direct dimension tweens trigger layout recompute that breaks deterministic seek.
- **Never use `tl.from()` for opacity tweens with stagger.** GSAP records the END state at registration; if CSS rest is `opacity:0` the recorded end stays `opacity:0`. Always use `tl.fromTo(target, {opacity:0,...}, {opacity:1,...}, pos)`. See `patterns/visual-patterns.md` § "tl.from() stagger trap".

Anti-slop content rules (see `patterns/anti-slop.md`) also matter: no default Tailwind indigo/purple gradients (`#6366f1`, `#4f46e5`, etc.), no emoji as feature icons, no invented metrics, no lorem-ipsum filler.

## Common edits

- **Add a voice** → update both the `## ElevenLabs Voice IDs` table in `SKILL.md` and the `## Voices` table in `README.md` (the two tables must stay in sync).
- **Change phase logic** → edit the relevant `workflows/phase-N-*.md`; update the prerequisite list in `SKILL.md` if a new required file is introduced.
- **Change the Creative Brief schema** → update the template, validator, example plan, workflow
  field names, and tests together. Story changes stale Phase 1–5; final-track-only changes stale
  Phase 5.
- **Adjust prerequisite checks** → update `scripts/check_requirements.sh` and its stdlib tests;
  keep the first-run Phase -1 interpretation in `SKILL.md` aligned with the JSON schema.
- **Bump skill metadata** → frontmatter at top of `SKILL.md` (especially `allowed-tools` if a new MCP tool is needed).
- **Add a pattern file** → also register it in `patterns/INDEX.md` so phase workflows can find it.

## Installation paths users invoke

```bash
# Recommended — the skills CLI auto-detects the agent and resolves its scanned skills home:
npx skills add nebrass/hve-spielberg                                   # project install (Copilot scans .github/skills, .agents/skills)
npx skills add nebrass/hve-spielberg --agent github-copilot --global  # global for Copilot CLI (~/.copilot/skills/)
npx skills add nebrass/hve-spielberg --global                         # global for Claude Code (default agent)

# Fallback — manual git clone into the agent's skills home:
git clone https://github.com/nebrass/hve-spielberg.git ~/.copilot/skills/hve-spielberg
```

The repo ships a Claude Code plugin manifest at root (`.claude-plugin/plugin.json` + `marketplace.json`, source `./`) plus a root `AGENTS.md`. Other agents (GitHub Copilot CLI, OpenCode, Pi, Codex, Cursor) need no manifest — they discover the skill by directory convention from the homes `npx skills add` writes into (`.agents/skills/`, `.claude/skills/`, etc.). See `AGENTS.md` for the per-agent scan paths.

When testing skill changes locally, the global install path is `~/.claude/skills/hve-spielberg/` (Claude Code) or `~/.copilot/skills/hve-spielberg/` (GitHub Copilot CLI).

## Git / release conventions

Commits follow Conventional Commits (`feat`, `fix`, `docs`, `style`, `refactor`, `chore`). Recent history shows scoped forms like `feat(audio):`, `docs:`, `style(readme):`, `fix(readme):` — match the existing scope style. License is MIT.
