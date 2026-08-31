# Copilot Instructions — hve-video-director

## What this repo is

This repo **is an agent skill** (`hve-video-director`) that runs on both **GitHub Copilot CLI** and **Claude Code**, not a typical application. The "source" is prompt content (markdown) plus Python helper scripts. There is no build system or lint config; pure-stdlib helper tests live under `test/`. The skill is consumed by future agent sessions that invoke `/hve-video-director <project-dir>` (a slash command on Claude Code; invoked by name/intent on Copilot CLI). The `SKILL.md` frontmatter follows the Claude Code skill schema; Copilot CLI loads the skill from its `name`/`description` and harmlessly ignores the Claude-only fields (`allowed-tools`, `user-invocable`, `argument-hint`). See the **Runtime Compatibility** section in `SKILL.md` for how interaction blocks (`{"questions": […]}`), companion-skill loading (`Skill(<name>)`), and skill-home paths map across runtimes — preserve that mapping when editing.

The renderer is **HyperFrames** (HTML + GSAP, rendered via headless Chromium). React/Remotion are **not** used.

Keep two scopes distinct when editing:

- **This repo** — the skill definition (`SKILL.md`, `workflows/`, `templates/`, `patterns/`, `scripts/`, `design-systems/`). Edits here change behavior for *all* users.
- **Generated video projects** — created by the skill at runtime in `{project-dir}/`. They contain `project-plan.md`, `.hve/brief-state.json`, `context.md`, `storyboard.md`, `DESIGN.md`, `public/screenshots/`, `scenes/*.html`, `index.html` (root HyperFrames composition), `voiceover.mp3`, `out/final.mp4`. These do **not** live in this repo, and no reference build is committed while its replacement is being regenerated (see above).

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
- Phase 5 needs `index.html` (root composition) and passing `npx hyperframes lint` + `npx hyperframes check`
- Tutorial content mode prefers `public/clips/` but degrades to stills with a warning when clips are absent (warn-don't-block, spec §7.3); only missing captions is a hard check in tutorial mode

**External dependencies the skill calls out to:**

- `mcp__chrome-devtools__*` for app capture (Phase 2)
- The `hyperframes` companion agent skill for HTML/GSAP authoring rules (Phases 3 + 4) — distinct from the `hyperframes` npm CLI
- GSAP choreography reference lives in the `hyperframes-animation` skill (there is no standalone `gsap` companion skill)
- `npx hyperframes` CLI for `init`, `add` (pull catalog blocks — registry-first scene planning in Phase 3, seams and furniture in Phase 4), `lint`, `preview`, `check` (required final gate; `inspect`/`validate`/`layout` are deprecated aliases), `snapshot`, `render`, `doctor` (render-environment diagnostics, Phase 5), `transcribe` (preferred voiceover-timing verifier in Phase 5; falls back to standalone Whisper if unavailable), and `tts` (used in Phase 5 when the user explicitly confirms a local Kokoro voice)
- `mcp__chrome-devtools__screencast_*` + `resize_page` for Phase-2 web-clip capture (experimental, feature-detected — needs `--experimentalScreencast=true`; falls back to screenshots), and optional `asciinema`+`agg` for CLI clip recording (otherwise the authored-terminal path)
- `mcp__chrome-devtools__list_pages` + `select_page` for the explicit authenticated-session path. The user must first connect the MCP to running Chrome with Chrome 144+ `--autoConnect` (preferred) or the dedicated-profile `--browser-url` fallback; attached capture never navigates and follows `patterns/authenticated-browser-capture.md` — with one carve-out: a user-recorded flow replayed after the Phase-2 whole-flow consent may perform exactly its own recorded steps (ADR-011; § Recorded-flow exception in that pattern).
- `scripts/generate_voiceover.py` → `--assemble-only` section assembler used by both audio paths (exact start times, padding, overrun warning). M6 retired its ElevenLabs acquisition path; narration now comes from the `media-use` audio engine
- `scripts/caption_gen.py` → backward-compatible ASR drafts plus the Phase-5 reviewed-caption workflow: `draft` creates an audio-bound manifest, `approve` binds explicit user approval to the exact cues, `finalize` transactionally publishes `out/final.srt` + `out/final.vtt` + deterministic state, and `validate` rejects stale audio/manifest/state/outputs (pure stdlib + required `ffprobe`)
- `scripts/capture_screen.py` → fixed-duration, silent native desktop/region capture orchestrator (pure stdlib): macOS `screencapture`, Windows `gdigrab`, X11 `x11grab`, or feature-detected Wayland `wf-recorder`; WSL/unavailable Wayland return explicit handoffs. It trims via sibling `stitch_clip.py`, validates duration/frame count within one frame, and uses `<clip>.capture.pending` + fingerprinted `<clip>.capture.json` state so failed retakes preserve prior valid media but cannot count as complete.
- `scripts/stitch_clip.py` → canonical raw-capture normalizer/stitcher for CFR30 H.264 High/yuv420p, even dimensions, no audio, and `+faststart` (pure stdlib wrapper for ffmpeg/ffprobe)
- `scripts/validate_brief.py` → exact Creative Brief parser, consent-gated legacy placeholder migration, revision-bound story/audio fingerprints, atomic `.hve/brief-state.json`, phase stamps, and stale-prerequisite checks (pure stdlib)
- `scripts/check_requirements.sh` → structured toolchain preflight. Default, `--json`, and
  `--plan` are side-effect-free and never use online `npx` probes. Scoped
  `--fix=<id,id>` runs only selected safe user-scoped fixes; bare `--fix` means all safe fixes.
  It never runs system/sudo commands or sets environment variables. Phase -1 consumes its JSON
  only for a direct/default first `new` run; explicit `continue` and `jump` skip onboarding.

`templates/` files are copied into generated projects. `patterns/` files are referenced for visual techniques. `patterns/INDEX.md` is the map of the seven *local* pattern files — read it before adding another one; ecosystem wayfinding belongs in `compat/ecosystem.md`, not there. The seam rationale that used to live in a local pattern file is now upstream — the vector law in `motion-doctrine`, render-side compositing and edge artifacts in `seam-craft` via `SEAM_RENDER_MECHANICS`; `patterns/transition-catalog.md` keeps only the moment-to-transition mapping and the energy budget, and `patterns/visual-patterns.md` § DON'Ts keeps the clipPath ban with its rationale.

`design-systems/<slug>/DESIGN.md` is the brand spec consumed by Phase 3 Path A — MIT-licensed, video-focused, authored by this skill. The canonical research source for new contributions is [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) (MIT, 73 brands, has a `npx getdesign add <slug>` CLI). The skill is **video-only** — it does not produce, render, or analyse web/UI artifacts.

## Working with the skill scripts

The media scripts run inside generated video projects; `validate_brief.py` runs from the installed
skill against a generated project via `--project-dir`. Every remaining helper — voiceover
assembly, clip-audio mixing, capture, stitch, caption, and Creative Brief validation — is pure
standard library. Caption finalization invokes the required `ffprobe` binary for
duration validation.

```bash
# Voiceover-section assembly (from inside a generated project) — both audio
# paths use it, whoever synthesized the sections. No API key, no network.
python3 scripts/generate_voiceover.py --assemble-only

# Fixed-duration silent native screen/region capture
python3 scripts/capture_screen.py --duration 6 --region 100,80,1280,720 \
  -o public/clips/scene-02-dashboard.mp4

# Normalize or stitch existing recordings
python3 scripts/stitch_clip.py raw.mov -o public/clips/scene-02-dashboard.mp4

# Validate a recorded browse flow + emit its consent brief; verify a cut clip
python3 scripts/replay_flow.py plan --recording recordings/drill.json --storyboard storyboard.md
python3 scripts/replay_flow.py check --recording recordings/drill.json \
  --steps 3-6 -o public/clips/scene-01-drill.mp4

# Validate the Creative Brief in a generated project
python3 /path/to/hve-video-director/scripts/validate_brief.py \
  --project-dir /path/to/generated-project status --json
# Legacy plans only, after explicit user consent
python3 /path/to/hve-video-director/scripts/validate_brief.py \
  --project-dir /path/to/generated-project migrate

```

`scripts/check_requirements.sh` accepts both `ELEVENLABS_API_KEY` and `ELEVEN_LABS_API_KEY`
(back-compat). Since M6 no script in this repo reads either one — the key serves the delegated
engine's ElevenLabs route.

There is no build or lint command for this repo. Run `bash test/run.sh` for the stdlib helper tests;
validation of workflow changes still happens by running `/hve-video-director <project-dir>` end-to-end
in Claude Code. The canonical reference build is `example/` — the source artifacts of one real end-to-end run
(media gitignored; see `example/README.md` for how to reproduce the render). It is a record of a
human-in-the-loop run, so never hand-edit it and never regenerate it from a partial run; a
replacement needs real TTS, music licensing and per-phase approvals no agent may self-grant.

## Editing rules — DON'Ts that are easy to violate

These are enforced verbally in the `## DON'Ts` section of `SKILL.md`. If you modify workflows or patterns, do not reintroduce them:

- **No jitter** (shaking, vibrating motion).
- **No 360° scene spins.** Subtle `rotateY` ≤ 8° / `rotateX` ≤ 4° / `rotateZ` ≤ 4° on mockups only. Always name the axis a limit governs.
- **No 3D transforms in transitions.** 2D only (opacity, position, scale, gradient masks).
- **No clipPath transitions.** A polygon `clipPath` sweeping between two scenes leaves an anti-aliased black sliver at the boundary, and no gate catches it. Use a crossfade with a full-frame light overlay over it (the light family, `TRANSITION_FAMILIES`); render-side rules are `SEAM_RENDER_MECHANICS`. See `patterns/visual-patterns.md` § DON'Ts.
- **No exit animations except on the closing scene.** The inter-scene transition owns the exit.
- **Never animate `display`, `visibility`, or call `.play()` inside a timeline.** Breaks HyperFrames' deterministic seek; use `opacity` + `pointer-events`.
- **Never animate `<img>` dimensions directly.** Wrap the `<img>` in a non-timed `<div>` and animate the wrapper's `transform`. Direct dimension tweens trigger layout recompute that breaks deterministic seek.
- **Never use `tl.from()` for opacity tweens with stagger.** GSAP records the END state at registration; if CSS rest is `opacity:0` the recorded end stays `opacity:0`. Always use `tl.fromTo(target, {opacity:0,...}, {opacity:1,...}, pos)`. See `patterns/visual-patterns.md` § "tl.from() stagger trap".

Anti-slop content rules (see `patterns/anti-slop.md`) also matter: no default Tailwind indigo/purple gradients (`#6366f1`, `#4f46e5`, etc.), no emoji as feature icons, no invented metrics, no lorem-ipsum filler.

## Common edits

- **Write down how upstream *behaves*** → name the upstream file that says it. If you can, cite it and delete your sentence (ADR-002 forbids a committed restatement). If you cannot, the behavior is undocumented: keep only the narrowing imperative a builder must obey, and register it as a `### SYMBOL` row in `compat/ecosystem.md` § Behavior probes with a `- **Local text.**` field naming the file you edited. `test/unit/test_probe_local_text.py` checks the row's shape; nothing checks that you wrote one.
- **Add a voice** → three sites must agree: the `## ElevenLabs Voice IDs` table in `SKILL.md`, the `## Voices` table in `README.md`, and the picker (plus its worked `elevenlabs:<name>:<id>` example) in `workflows/phase-1-storytelling.md`. A voice in the tables but not the picker can never be chosen. Enforced by `test/unit/test_voice_parity.py`.
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
npx skills add nebrass/hve-video-director                                   # project install (Copilot scans .github/skills, .agents/skills)
npx skills add nebrass/hve-video-director --agent github-copilot --global  # global for Copilot CLI (~/.copilot/skills/)
npx skills add nebrass/hve-video-director --global                         # global for Claude Code (default agent)

# Fallback — manual git clone into the agent's skills home:
git clone https://github.com/nebrass/hve-video-director.git ~/.copilot/skills/hve-video-director
```

The repo ships a Claude Code plugin manifest at root (`.claude-plugin/plugin.json` + `marketplace.json`, source `./`) plus a root `AGENTS.md`. Other agents (GitHub Copilot CLI, OpenCode, Pi, Codex, Cursor) need no manifest — they discover the skill by directory convention from the homes `npx skills add` writes into (`.agents/skills/`, `.claude/skills/`, etc.). See `AGENTS.md` for the per-agent scan paths.

When testing skill changes locally, the global install path is `~/.claude/skills/hve-video-director/` (Claude Code) or `~/.copilot/skills/hve-video-director/` (GitHub Copilot CLI).

## Git / release conventions

Commits follow Conventional Commits (`feat`, `fix`, `docs`, `style`, `refactor`, `chore`). Recent history shows scoped forms like `feat(audio):`, `docs:`, `style(readme):`, `fix(readme):` — match the existing scope style. License is MIT.
