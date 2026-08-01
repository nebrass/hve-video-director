# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) — and GitHub Copilot CLI, which also reads `CLAUDE.md` — when working with code in this repository.

## What this repo is

This repo **is an agent skill** (`hve-video-director`) that runs on both **Claude Code** and **GitHub Copilot CLI**, not a typical application. The "source" is prompt content (markdown) plus Python helper scripts. There is no build system or lint config; pure-stdlib helper tests live under `test/`. The skill is consumed by future agent sessions that invoke `/hve-video-director <project-dir>` (a slash command on Claude Code; invoked by name/intent on Copilot CLI). The `SKILL.md` frontmatter uses the Claude Code skill schema; Copilot CLI loads the skill from `name`/`description` and harmlessly ignores the Claude-only fields.

The renderer is **HyperFrames** (HTML + GSAP, rendered via headless Chromium). React/Remotion are no longer used.

Two things to keep distinct:

- **This repo** — the skill definition (`SKILL.md`, `reasoning/`, `grammar/`, `workflows/`, `templates/`, `patterns/`, `scripts/`, `design-systems/`, `compat/`) plus the canonical demo (`example/`). Edits here change behavior for *all* users.
- **Generated video projects** — created by the skill at runtime in `{project-dir}/`. They contain `project-plan.md`, `.hve/brief-state.json`, `context.md`, `storyboard.md`, `DESIGN.md`, `public/screenshots/`, `scenes/*.html`, `index.html` (root HyperFrames composition), `voiceover.mp3`, `out/final.mp4`. These do not live in this repo (except `example/`, which is *this skill's own* generated project, committed as the reference build).

## Architecture

`SKILL.md` is the orchestrator prompt. It loads first, decides the entry mode (`new` / `continue` / `jump`), and dispatches to one of six phase workflows. Each phase has a user-approval checkpoint before advancing.

```
SKILL.md (orchestrator)
  ├─ reasoning/ + grammar/              → the 16-stage reasoning pipeline (read by Phases 0, 1, 3, 4)
  ├─ workflows/phase-0-discovery.md     → produces context.md
  ├─ workflows/phase-1-storytelling.md  → produces storyboard.md
  ├─ workflows/phase-2-capture.md       → produces public/screenshots/ (via Chrome DevTools MCP)
  ├─ workflows/phase-3-design.md        → produces DESIGN.md + scenes/*.html (via hyperframes skill)
  ├─ workflows/phase-4-production.md    → produces root index.html composition (via hyperframes skill)
  └─ workflows/phase-5-audio.md         → produces voiceover.mp3 + background-music.mp3 + out/final.mp4 (npx hyperframes render)
```

**`reasoning/` and `grammar/` are first-class skill directories, not documentation.** They hold the
reasoning layer the phases run on, and a phase workflow points at them instead of restating them.
`reasoning/scene-analysis.md` is the per-frame instrument (the question set, the director keys it
emits onto each storyboard frame, and — single-sourced, ADR-008 — the cognitive-load budgets; no
other file may restate one of those numbers). `reasoning/capability-catalog.md` owns and versions
the capability-tag vocabulary and turns a frame's derived tags into a runtime. The four grammars
supply the vocabulary those stages choose from: `grammar/camera.md` (camera moves, two tiers),
`grammar/motion.md` (motion principles), `grammar/metaphors.md` (concept → picture), and
`grammar/three-taxonomy.md` (when a frame earns Three.js, and how to record rejecting it).

**The grammars decide WHEN and WHY; the HyperFrames ecosystem owns HOW.** No mechanism text is ever
copied into this repo (ADR-002): upstream motion is cited by bare rule name or bare blueprint id and
resolved through `RULES_INDEX` / `BLUEPRINT_INDEX`; everything else upstream is cited by capability
SYMBOL through `compat/ecosystem.md` (ADR-007). Capability derivation is mechanical, never a taste
call (ADR-005), and a user's explicit creative instruction still overrides any derived verdict
(ADR-001, `user_directed: true`).

**Phase prerequisites are enforced in `jump` mode** — see `SKILL.md`. When editing workflows, preserve the file-presence contract:
- Phase 1 needs `context.md`
- Phase 2 needs `context.md` + `storyboard.md`
- Phase 3 needs capture artifacts (`public/screenshots/` and/or `public/clips/`)
- Phase 4 needs context + storyboard + `DESIGN.md` + `scenes/*.html`
- Phase 5 needs `index.html` (root composition) and passing `npx hyperframes lint` + `npx hyperframes check`
- Tutorial content mode prefers `public/clips/` but degrades to stills with a warning when clips are absent (warn-don't-block, spec §7.3); only missing captions is a hard check in tutorial mode

**External dependencies the skill calls out to:**
- `mcp__chrome-devtools__*` for app capture (Phase 2)
- The `hyperframes` skill for HTML/GSAP authoring rules (Phases 3 + 4)
- There is **no** `gsap` companion skill — it is not installed in any skills home and is not an ecosystem skill. GSAP choreography guidance (timeline registration, the property contract, ease families, stagger) is `GSAP_ADAPTER` + `EASING_AND_STAGGER` in `hyperframes-animation`. `scripts/check_requirements.sh` still probes for a `gsap` skill and reports it as a `recommended` check that degrades gracefully when absent, which is harmless; do not re-add it to prose.
- `npx hyperframes` CLI for `init`, `add` (pull catalog blocks, Phase 4), `lint`, `preview`, `check` (required final gate; `inspect`/`validate`/`layout` are deprecated aliases), `render`, `doctor` (render-environment diagnostics, Phase 5), `transcribe` (preferred voiceover-timing verifier in Phase 5; falls back to standalone Whisper if unavailable), and `tts` (used in Phase 5 when the user explicitly confirms a local Kokoro voice)
- `mcp__chrome-devtools__screencast_*` + `resize_page` for Phase-2 web-clip capture (experimental, feature-detected — needs `--experimentalScreencast=true`; falls back to screenshots), and optional `asciinema`+`agg` for CLI clip recording (otherwise the authored-terminal path)
- `mcp__chrome-devtools__list_pages` + `select_page` for the explicit authenticated-session path. The user must first connect the MCP to running Chrome with Chrome 144+ `--autoConnect` (preferred) or the dedicated-profile `--browser-url` fallback; attached capture never navigates and follows `patterns/authenticated-browser-capture.md`.
- `scripts/generate_voiceover.py` → ElevenLabs API + optional Whisper transcription (Phase 5)
- `scripts/caption_gen.py` → preserves legacy ASR `voiceover.srt`/`.vtt` drafts and implements the Phase-5 `draft` → human review → `approve` → `finalize` → `validate` contract. Approval fingerprints the exact speech/speaker/meaningful-sound cues; final sidecars and deterministic state publish as one rollback-protected set. Pure stdlib with required `ffprobe`.
- `scripts/capture_screen.py` → fixed-duration, silent native desktop/region capture orchestrator (pure stdlib). Uses macOS `screencapture`, Windows `gdigrab`, X11 `x11grab`, or feature-detected Wayland `wf-recorder`; WSL and unavailable Wayland return explicit recording handoffs. It trims through sibling `stitch_clip.py`, validates duration/frame count within one frame, and uses `<clip>.capture.pending` + fingerprinted `<clip>.capture.json` state so failed retakes preserve prior valid media but cannot count as complete.
- `scripts/stitch_clip.py` → canonical normalizer/stitcher for raw captures (CFR30, H.264 High/yuv420p, even dimensions, no audio, `+faststart`) via the ffmpeg concat filter (pure stdlib)
- `scripts/validate_brief.py` → parses the exact `project-plan.md` Creative Brief table, consent-migrates legacy plans with empty placeholders, confirms revision-bound story/audio fingerprints, atomically writes `.hve/brief-state.json`, stamps phases, and rejects stale prerequisites (pure stdlib)
- `scripts/search_music.py` → Freesound API for CC music (Phase 5)
- `scripts/check_requirements.sh` → verifies the toolchain (node/python/ffmpeg/chrome-headless-shell/hyperframes CLI + companion skills + env vars). Default, `--json`, and `--plan` are side-effect-free; report modes never use online `npx` probes. `--fix=<id,id>` runs only selected safe user-scoped actions (`chrome-shell`, `hyperframes-skill`, `whisper`), while bare `--fix` retains all-safe behavior. System/sudo/environment actions are printed, never run. Its `SKILL_HOMES` line must stay in lock-step with the canonical list in `SKILL.md` (same parity rule as the Phase 3/5 resolvers).

`templates/` files are copied into generated projects. `patterns/` files are referenced for visual techniques — `metallic-swoosh.md` documents *why* clipPath transitions are banned (black-sliver artifacts), and `cli-terminal-capture.md` documents the `asciinema` + `agg` workflow for the optional real-terminal-clip path (the dependency-free authored-terminal path uses `templates/scene-terminal.html`; the asciinema clip path uses `templates/scene-terminal-clip.html`).

## Working with the skill scripts

The media scripts run inside generated video projects; `validate_brief.py` runs from the installed
skill against a generated project via `--project-dir`. `generate_voiceover.py` and
`search_music.py` self-install `requests` via pip on first run; `caption_gen.py`,
`capture_screen.py`, `stitch_clip.py`, and `validate_brief.py` are pure standard library (the
capture/clip helpers invoke platform tools and `ffmpeg`/`ffprobe` with argv, while
`caption_gen.py` invokes `ffprobe` for the final-audio duration; none invokes a shell).

```bash
# Voiceover generation (from inside a generated project)
ELEVENLABS_API_KEY=... python3 scripts/generate_voiceover.py

# Reviewed caption delivery (after the final soundtrack exists)
python3 scripts/caption_gen.py draft           # ASR drafts + captions-review.json
python3 scripts/caption_gen.py approve         # binds explicit approval to exact cues
python3 scripts/caption_gen.py finalize        # writes out/final.srt + out/final.vtt
python3 scripts/caption_gen.py validate        # verifies final-audio/output fingerprints

# Fixed-duration silent native desktop/region capture
python3 scripts/capture_screen.py --duration 6 --region 100,80,1280,720 \
  -o public/clips/scene-02-dashboard.mp4

# Normalize / stitch a capture into the Phase-2 clip contract
python3 scripts/stitch_clip.py raw.mp4 -o public/clips/scene-02-dashboard.mp4

# Validate/confirm the stable Creative Brief and phase fingerprints
python3 /path/to/hve-video-director/scripts/validate_brief.py \
  --project-dir /path/to/generated-project status --json
# Legacy plans only, after explicit user consent
python3 /path/to/hve-video-director/scripts/validate_brief.py \
  --project-dir /path/to/generated-project migrate

# Music search (from inside a generated project) — query is a required argument
FREESOUND_API_KEY=... python3 scripts/search_music.py "cinematic corporate uplifting"
```

Run the stdlib tests with `bash test/run.sh`; the suite covers brief validation/fingerprints,
question-contract integration, mocked platform capture, and a synthetic ffmpeg normalization
integration test when ffmpeg/ffprobe are installed.

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
- **Change the Creative Brief schema** → update `templates/project-plan.md`,
  `scripts/validate_brief.py`, `example/project-plan.md`, workflow field names, and validator tests
  together. Story fields stale Phase 1–5; only `final_music_track` is audio-only and stales Phase 5.
- **Adjust prerequisite checks** → update `scripts/check_requirements.sh` and its stdlib tests. `SKILL.md` Phase -1 consumes `--json` only for direct/default `new` mode with no `project-plan.md`; explicit `continue`/`jump` skip it.
- **Add a user-interaction prompt in a workflow** → write it as a neutral `{"questions":[...]}` block (the runtime-agnostic schema), introduced by plain prose ("ask the user…", "present selectable options…"). **Never name a picker tool** (`AskUserQuestion`, `ask_user`) or write a literal tool call inside a workflow — the per-runtime binding for the question schema, `Skill(<name>)`, and `multiSelect` lives in **one place**: `SKILL.md` § Runtime Compatibility. This is the "name actions, not tools" rule that keeps the phase content portable; a tool name hard-coded in a phase body is a portability regression. (Qualified MCP names like `mcp__chrome-devtools__*` are *not* a violation — they're identical across runtimes; the rule targets names that *differ* per runtime.)
- **Change where the skill can be installed** (`$SKILL_HOMES`) → `SKILL.md` § Runtime Compatibility holds the canonical search list. The same `SKILL_ROOT=…` bootstrap and pipe-delimited `SKILL_HOMES="…"` line are repeated in the `SKILL.md` prereq probe, the `SKILL_DIR` resolver of `workflows/phase-3-design.md` + `workflows/phase-5-audio.md`, the `ANIM_SKILL_DIR` resolver of `workflows/phase-4-production.md` (Step 4.7), and `scripts/check_requirements.sh` (shell state can't cross the agent's separate bash calls, so the list is re-stated at each bootstrap point rather than sourced). The `|` delimiter plus `IFS='|'` preserves skill paths containing spaces. Keep all `SKILL_HOMES` lines byte-identical; verify with:
  ```bash
  grep -rho 'SKILL_HOMES="[^"]*"' SKILL.md workflows/*.md scripts/check_requirements.sh | sort -u | wc -l   # must print 1
  ```
- **Add a camera move / motion principle / visual metaphor** → edit the relevant `grammar/` file
  (`camera.md`, `motion.md`, `metaphors.md`, or `three-taxonomy.md`) and **declare the entry's
  capability tags in its own row** — that declaration is what stage 13 unions, so an entry with no
  tags is invisible to runtime selection. The tag vocabulary is owned and versioned by
  `reasoning/capability-catalog.md`: use its spellings, never invent one, and a genuinely new tag
  needs a catalog row plus a runtime that serves it *before* a grammar entry may declare it. Cite
  upstream vocabulary by **bare rule name** (`coordinate-target-zoom`), **bare blueprint id**
  (`camera-journey`), or capability **SYMBOL** — never an upstream file path, and never a restated
  mechanism (`compat/ecosystem.md` § Citing upstream vocabulary; the bare, extension-less form is
  what keeps the citation legal under `test/unit/test_compat_pointers.py`). Budget numbers stay in
  `reasoning/scene-analysis.md` — cite the table, never copy a number.
- **Change an ecosystem dependency** (an upstream HyperFrames skill, a file inside one, or the
  `npx hyperframes` CLI surface) → edit `compat/ecosystem.md` and nothing else. Intra-skill **file
  paths** for ecosystem skills live there and nowhere else in the repo; every other file names the
  skill plus the capability SYMBOL and lets that map resolve the path. Skill **names** are stable
  public API — name them freely anywhere. Enforced by `test/unit/test_compat_pointers.py`. To take
  an upstream update: `npx hyperframes skills update` → `bash test/run.sh` → commit
  `skills-lock.json` only when green (full procedure, incl. the pointer sweep and behavior probes,
  in `compat/ecosystem.md` § Pin and update policy). Cadence: milestone boundaries or monthly,
  whichever comes first.
- **Bump skill metadata** → frontmatter at top of `SKILL.md` (especially `allowed-tools` if a new MCP tool is needed).
- **Bump the GSAP version** → the CDN `<script>` tags carry a Subresource Integrity hash (`integrity="sha384-…" crossorigin="anonymous"`), pinned to `gsap@3.14.2`. Changing the version *requires* recomputing the hash, or the script is blocked and every scene renders without animation (caught by `npx hyperframes check` in Phase 4/5). Update **all** occurrences together — `templates/scene-*.html`, the skeletons in `workflows/phase-3-design.md` + `workflows/phase-4-production.md`, and every `example/**/*.html`:
  ```bash
  V=3.x.y   # new version
  H="sha384-$(curl -sL https://cdn.jsdelivr.net/npm/gsap@$V/dist/gsap.min.js | openssl dgst -sha384 -binary | base64)"
  # then replace src=…/gsap@$V/… and integrity="$H" in every file above (keep them in lock-step)
  ```

## Installation paths users invoke

```bash
# Recommended — the skills CLI auto-detects the agent and resolves its skills home:
npx skills add nebrass/hve-video-director                                   # project install
npx skills add nebrass/hve-video-director --global                         # global (Claude Code default)
npx skills add nebrass/hve-video-director --agent github-copilot --global  # global for Copilot CLI

# Fallback — manual git clone into the agent's skills home:
git clone https://github.com/nebrass/hve-video-director.git ~/.claude/skills/hve-video-director
```

The repo ships a Claude Code plugin manifest at root (`.claude-plugin/plugin.json` + `marketplace.json`, source `./`) plus a root `AGENTS.md`. Other agents (GitHub Copilot CLI, OpenCode, Pi, Codex, Cursor) need no manifest — they discover the skill by directory convention from the homes `npx skills add` writes into (`.agents/skills/`, `.claude/skills/`, etc.). See `AGENTS.md` for the per-agent scan paths.

When testing skill changes locally, the global install path is `~/.claude/skills/hve-video-director/` (Claude Code) or `~/.copilot/skills/hve-video-director/` (GitHub Copilot CLI).

## Git / release conventions

Commits follow Conventional Commits (`feat`, `fix`, `docs`, `style`, `refactor`, `chore`). Recent history shows `feat(audio):`, `docs:`, `style(readme):`, `fix(readme):` — match the existing scope style. License is MIT.
