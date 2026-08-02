# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) — and GitHub Copilot CLI, which also reads `CLAUDE.md` — when working with code in this repository.

## What this repo is

This repo **is an agent skill** (`hve-video-director`) that runs on both **Claude Code** and **GitHub Copilot CLI**, not a typical application. The "source" is prompt content (markdown) plus Python helper scripts. There is no build system or lint config; pure-stdlib helper tests live under `test/`. The skill is consumed by future agent sessions that invoke `/hve-video-director <project-dir>` (a slash command on Claude Code; invoked by name/intent on Copilot CLI). The `SKILL.md` frontmatter uses the Claude Code skill schema; Copilot CLI loads the skill from `name`/`description` and harmlessly ignores the Claude-only fields.

The renderer is **HyperFrames** (HTML + GSAP, rendered via headless Chromium). React/Remotion are no longer used.

Two things to keep distinct:

- **This repo** — the skill definition (`SKILL.md`, `reasoning/`, `grammar/`, `workflows/`, `templates/`, `patterns/`, `sub-agents/`, `scripts/`, `design-systems/`, `compat/`). Edits here change behavior for *all* users.
- **Generated video projects** — created by the skill at runtime in `{project-dir}/`. They contain `project-plan.md`, `.hve/brief-state.json`, `context.md`, `storyboard.md` (the official HyperFrames storyboard shape since M4 — see below), `DESIGN.md`, `public/screenshots/`, `scenes/*.html`, `index.html` (root HyperFrames composition), `voiceover.mp3`, `out/final.mp4`, and — only while a Studio review round is open — `.hyperframes/frame-comments.json`. None of them lives in this repo.

**There is no committed reference build right now.** `example/` held the pre-rebase demo project and
was removed with it; the reference build is being regenerated against the HyperFrames-first
pipeline. Regenerating it is a **human-in-the-loop run**, not an automatable task: it needs real TTS
and music licensing, a headless-Chromium render, and — decisively — this skill's own per-phase
approvals, which no agent may self-grant (ADR-001). Do not fabricate one, and do not re-add a
directory that only looks like the output of a real run.

## Architecture

`SKILL.md` is the orchestrator prompt. It loads first, decides the entry mode (`new` / `continue` / `jump`), and dispatches to one of six phase workflows. Each phase has a user-approval checkpoint before advancing.

```
SKILL.md (orchestrator)
  ├─ reasoning/ + grammar/              → the 16-stage reasoning pipeline (read by Phases 0, 1, 3, 4)
  ├─ workflows/phase-0-discovery.md     → produces context.md
  ├─ workflows/phase-1-storytelling.md  → produces storyboard.md
  ├─ workflows/phase-2-capture.md       → produces public/screenshots/ (via Chrome DevTools MCP)
  ├─ workflows/phase-3-design.md        → produces DESIGN.md + scenes/*.html (registry blocks
  │    └─ sub-agents/scene-builder-delta.md    first, then one ephemeral frame packet per scene,
  │                                            each packet carrying this builder-role delta)
  ├─ workflows/phase-4-production.md    → produces the seam ledger + root index.html composition
  │                                       (via hyperframes skill); seams are stamped from the ledger
  │                                       (SEAM_STAMP) and enforced numerically by SEAM_VERIFIER
  └─ workflows/phase-5-audio.md         → narration + music bed + SFX via the media-use audio engine,
                                          then the confirmed-track mix, reviewed captions,
                                          and out/final.mp4 (npx hyperframes render)
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

**The grammars decide WHEN and WHY; the HyperFrames ecosystem owns HOW.** This repo never becomes
the author of record for upstream mechanism text (ADR-002). Three forms are legal and only one is
not: a **pointer citation** (upstream motion by bare rule name or bare blueprint id, resolved
through `RULES_INDEX` / `BLUEPRINT_INDEX`; everything else by capability SYMBOL through
`compat/ecosystem.md`, ADR-007); **mechanical inlining at dispatch time** (copying a recipe body
into an ephemeral frame packet — see below); and an **additive local constraint** that narrows what
upstream permits. A *committed* restatement of upstream mechanism is the illegal one. Capability
derivation is mechanical, never a taste call (ADR-005), and a user's explicit creative instruction
still overrides any derived verdict (ADR-001, `user_directed: true`).

**Scene builders receive a frame packet, and nothing else (M5).** A packet is assembled at dispatch
time in Phase 3 Step 3.3, regenerated on every run, written to scratch and **never committed**. It
carries exactly five things: (1) that one frame's storyboard block verbatim, director keys included;
(2) the project's `DESIGN.md`; (3) the **bodies** of the recipes the frame cites, read from the
installed skill at that moment and pasted in — the legal inlining above, which is what frees the
builder from resolving a citation itself; (4) the builder role, `FRAME_WORKER_CORE` followed by
`sub-agents/scene-builder-delta.md`; (5) canvas size, the captions flag, and the exact paths of the
bound capture artifacts. Plus the starting point — a `templates/scene-*.html` skeleton or a block
already installed from the registry.

Two boundaries are easy to erode by being helpful:

- **A packet never carries a `reasoning/` or `grammar/` file** (ADR-004), nor another frame's block
  nor film-wide storyboard state. Those files *produced* the director keys; the keys **are** the
  conclusion, and shipping the derivation next to them is exactly what makes builder context
  unbounded. Adding "just a little" grammar context is the regression this rule exists to stop.
- **A builder returns one scene HTML file and runs no CLI.** `lint` / `check` / the seam gate all
  operate on the assembled project, so a builder running them reads other files and comes back
  falsely green. Phase 4 runs them and re-dispatches with a concrete finding.

Dispatch is a behavioral contract, not a preference: build **inline up to ~6 short frames**, and
beyond that give each worker **2–3 frames** (never one), start all workers in a single wave, and
allow **one retry per frame and only with a concrete finding**. The measurement behind the ~6
threshold is upstream's and is stated once, in `workflows/phase-3-design.md` Step 3.4 — cite it,
never re-derive or re-copy the numbers. **Registry-first** governs what a packet starts from: check
`REGISTRY_CATALOG` and install with `npx hyperframes add` before hand-authoring; a tested block
beats a hand-built scene, and hand-authoring covers only the gap.

**The storyboard is the official format. The brief deliberately is not.** M4 adopted
`STORYBOARD_FORMAT` for the generated `storyboard.md`: YAML frontmatter, one `## Frame N — Title`
section per frame, `- key: value` metadata bullets, free prose below them. Frames are 1-based while
scene *files* stay 0-based, so frame 1's `src` is `scenes/00-…`. Adopting the shape buys the
upstream parser, the Studio contact-sheet review, and the structured
`.hyperframes/frame-comments.json` feedback channel. Everything the official key set has no home
for — the director keys, the capture bindings, this skill's own frontmatter fields — rides along as
ordinary bullets and is preserved verbatim under the parser's `extra`. That preservation is the
load-bearing assumption of the whole format; the `STORYBOARD_EXTRA_KEYS` behavior probe in
`compat/ecosystem.md` guards it, and as of M4 it is automated in `bash test/run.sh`. Local shape
doc: `templates/storyboard.md`.

`BRIEF_FORMAT` (`BRIEF.md`) was **NOT** adopted, and that is a decision, not an omission. Its
companion `BRIEF_CONTRACT` derives a collaborative/autonomous run shape and explicitly *skips
questions the request already answers*. This skill's consent doctrine is the opposite — recommend,
never preselect; never infer an answer the user did not give (ADR-001) — so adopting the brief
would import a contract that contradicts the skill's central promise. `project-plan.md` therefore
remains this skill's Creative Brief and the single record of the levers the user owns. The
storyboard is different only because it is a *description of the film*, not a consent record. Two
consequences that are easy to undo by accident:

- **Never write `mode:` into storyboard frontmatter.** Upstream reserves that key for the
  interaction mode of the run-shape contract above. The content mode lives in `content_mode`.
- **Never re-point `scripts/validate_brief.py` at `BRIEF.md`.** A milestone that wants the official
  brief must replace the consent doctrine first, which is an ADR-001 change reviewed as such.

**No generated project is ever stranded or rewritten.** Nothing is gated on the storyboard's shape:
a project written before M4 still resumes. `validate_brief.py storyboard --json` reports which
shape a project is in, and `migrate-storyboard` converts one **only when the user asks**,
preserving the original alongside the converted file. Migration is additive; a legacy line with no
official home becomes an extra bullet rather than a guessed value.

**Phase prerequisites are enforced in `jump` mode** — see `SKILL.md`. When editing workflows, preserve the file-presence contract:
- Phase 1 needs `context.md`
- Phase 2 needs `context.md` + `storyboard.md`
- Phase 3 needs capture artifacts (`public/screenshots/` and/or `public/clips/`)
- Phase 4 needs context + storyboard + `DESIGN.md` + `scenes/*.html`
- Phase 5 needs `index.html` (root composition), a passing seam gate (`SEAM_VERIFIER` — re-run it when scenes are re-timed to the voiceover), and passing `npx hyperframes lint` + `npx hyperframes check`
- Tutorial content mode prefers `public/clips/` but degrades to stills with a warning when clips are absent (warn-don't-block, spec §7.3); only missing captions is a hard check in tutorial mode

**External dependencies the skill calls out to:**
- `mcp__chrome-devtools__*` for app capture (Phase 2)
- The `hyperframes` skill for HTML/GSAP authoring rules (Phases 3 + 4)
- The `media-use` skill for **all** Phase-5 audio generation — `AUDIO_ENGINE` runs TTS, the music bed (BGM) and SFX from one request, and `TRANSCRIBE` / `CAPTIONS_AUTHORING` / `TRANSCRIPT_HANDLING` supply caption data. Word timestamps come back only from its HeyGen voice route; the ElevenLabs and local Kokoro routes still need a transcription pass. Delegation stops at generation: the exact-track confirmation, the caption review state machine, the verified mix recipes, and render approval stay here (ADR-001)
- There is **no** `gsap` companion skill — it is not installed in any skills home and is not an ecosystem skill. GSAP choreography guidance (timeline registration, the property contract, ease families, stagger) is `GSAP_ADAPTER` + `EASING_AND_STAGGER` in `hyperframes-animation`. `scripts/check_requirements.sh` still probes for a `gsap` skill and reports it as a `recommended` check that degrades gracefully when absent, which is harmless; do not re-add it to prose.
- `npx hyperframes` CLI for `init`, `add` (pull catalog blocks — registry-first scene planning in Phase 3, seams and furniture in Phase 4), `lint`, `preview`, `check` (required final gate; `inspect`/`validate`/`layout` are deprecated aliases), `render`, `doctor` (render-environment diagnostics, Phase 5), `transcribe` (preferred voiceover-timing verifier in Phase 5; falls back to standalone Whisper if unavailable), and `tts` (used in Phase 5 when the user explicitly confirms a local Kokoro voice)
- `mcp__chrome-devtools__screencast_*` + `resize_page` for Phase-2 web-clip capture (experimental, feature-detected — needs `--experimentalScreencast=true`; falls back to screenshots), and optional `asciinema`+`agg` for CLI clip recording (otherwise the authored-terminal path)
- `mcp__chrome-devtools__list_pages` + `select_page` for the explicit authenticated-session path. The user must first connect the MCP to running Chrome with Chrome 144+ `--autoConnect` (preferred) or the dedicated-profile `--browser-url` fallback; attached capture never navigates and follows `patterns/authenticated-browser-capture.md`.
- `scripts/generate_voiceover.py` → **the voiceover-section assembler, and only that, since M6.** `--assemble-only` places already-synthesized `vo_section_NN.mp3` files at their exact start times, separates them with silence, pads to `VIDEO_DURATION` and warns on overrun; **both** audio paths use it, whoever synthesized the sections. The flag is now optional (assembly is the only mode) and kept accepted so every invocation already written into a workflow keeps working. M6 removed the ElevenLabs acquisition path and its Whisper verification pass; the file is pure stdlib, needs no API key and no network, and timing verification is a separate Phase-5 step against the assembled `voiceover.mp3`. **Do not delete this file** — retiring ElevenLabs did not retire assembly
- `scripts/caption_gen.py` → preserves legacy ASR `voiceover.srt`/`.vtt` drafts and implements the Phase-5 `draft` → human review → `approve` → `finalize` → `validate` contract. Approval fingerprints the exact speech/speaker/meaningful-sound cues; final sidecars and deterministic state publish as one rollback-protected set. Pure stdlib with required `ffprobe`.
- `scripts/capture_screen.py` → fixed-duration, silent native desktop/region capture orchestrator (pure stdlib). Uses macOS `screencapture`, Windows `gdigrab`, X11 `x11grab`, or feature-detected Wayland `wf-recorder`; WSL and unavailable Wayland return explicit recording handoffs. It trims through sibling `stitch_clip.py`, validates duration/frame count within one frame, and uses `<clip>.capture.pending` + fingerprinted `<clip>.capture.json` state so failed retakes preserve prior valid media but cannot count as complete.
- `scripts/mix_clip_audio.py` → mixes one clip's own audio into the canonical soundtrack (trim → speed → loudnorm → volume → placement, then a sidechain duck under the clip). Pure stdlib, argv-only ffmpeg. Validates its inputs, refuses a placement whose audio would be truncated at the film's end, and replaces the soundtrack atomically only on success — a failed run leaves it byte-identical
- `scripts/stitch_clip.py` → canonical normalizer/stitcher for raw captures (CFR30, H.264 High/yuv420p, even dimensions, no audio, `+faststart`) via the ffmpeg concat filter (pure stdlib)
- `scripts/validate_brief.py` → parses the exact `project-plan.md` Creative Brief table, consent-migrates legacy plans with empty placeholders, confirms revision-bound story/audio fingerprints, atomically writes `.hve/brief-state.json`, stamps phases, and rejects stale prerequisites (pure stdlib). It also **reads** `storyboard.md` — read-only, and deliberately outside every fingerprint, because the storyboard describes the film while the brief records consent: `storyboard --json` reports the shape and frames, `migrate-storyboard` converts a pre-adoption file only on request and preserves the original alongside it
- `scripts/check_requirements.sh` → verifies the toolchain (node/python/ffmpeg/chrome-headless-shell/hyperframes CLI + companion skills + env vars). Default, `--json`, and `--plan` are side-effect-free; report modes never use online `npx` probes. `--fix=<id,id>` runs only selected safe user-scoped actions (`chrome-shell`, `hyperframes-skill`, `whisper`), while bare `--fix` retains all-safe behavior. System/sudo/environment actions are printed, never run. Its `SKILL_HOMES` line must stay in lock-step with the canonical list in `SKILL.md` (same parity rule as the Phase 3/5 resolvers).

`templates/` files are copied into generated projects; the `scene-*.html` skeletons double as the starting point a frame packet ships when no registry block covers the archetype. `sub-agents/` holds role deltas for dispatched builders — today just the scene builder. `patterns/` files are referenced for visual techniques — `transition-catalog.md` maps moments to transition families under `SEAM_LAW` (the seam rationale that used to live in a local pattern file is now upstream: the vector law in `motion-doctrine`, render-side compositing and edge artifacts in `seam-craft` via `SEAM_RENDER_MECHANICS`; the repo keeps only the narrowing clipPath/3D bans in `SKILL.md` § DON'Ts), and `cli-terminal-capture.md` documents the `asciinema` + `agg` workflow for the optional real-terminal-clip path (the dependency-free authored-terminal path uses `templates/scene-terminal.html`; the asciinema clip path uses `templates/scene-terminal-clip.html`).

## Working with the skill scripts

The media scripts run inside generated video projects; `validate_brief.py` runs from the installed
skill against a generated project via `--project-dir`.

**M6 retired the local *narration* fallback only.** `search_music.py` was retired with it and has since been **restored** — Freesound search is the default music path, because a real recording has an author, a stable URL and an auditable licence that a generated bed does not. Meanwhile
`generate_voiceover.py`'s ElevenLabs half with it. Phase 5's audio path is the `media-use` engine
(`AUDIO_ENGINE`); with no engine, narration is `npx hyperframes tts` on an explicitly confirmed
local voice and the music bed is user-provided. **`generate_voiceover.py` itself survives and must
not be deleted**: `--assemble-only` is the section assembler both paths use, and removing the file
would break the delegated path too.

Every Python helper here is now pure standard library — no pip install, no `requests`, no network.
They invoke platform tools and `ffmpeg`/`ffprobe` with argv (`caption_gen.py` uses `ffprobe` for the
final-audio duration); none invokes a shell. (`check_requirements.sh` is the exception by design:
its consented `--fix` actions run `npx --yes skills add`.)

```bash
# Voiceover-section assembly — used by both audio paths, whoever synthesized the
# sections. Reads vo_section_NN.mp3, writes voiceover.mp3. No API key needed.
python3 scripts/generate_voiceover.py --assemble-only

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
```

Run the stdlib tests with `bash test/run.sh`; the suite covers brief validation/fingerprints,
question-contract integration, mocked platform capture, and a synthetic ffmpeg normalization
integration test when ffmpeg/ffprobe are installed.

`scripts/check_requirements.sh` accepts both `ELEVENLABS_API_KEY` and `ELEVEN_LABS_API_KEY`
(back-compat). Since M6 no script in this repo reads either one — the key serves the delegated
engine's ElevenLabs route, which is the only path that still consumes it.

## Editing rules — DON'Ts that are easy to violate

These are enforced verbally in the `## DON'Ts` section of `SKILL.md` — except the seam rules, which `SEAM_VERIFIER` enforces numerically. If you modify workflows or patterns, do not reintroduce them:

- **No jitter** (shaking, vibrating motion).
- **No 360° scene spins.** Subtle `rotateY` ≤ 8° / `rotateZ` ≤ 4° on mockups only.
- **Seams belong to `SEAM_LAW`, not to this repo.** The vector law (axis/direction/speed/phase), the ban on a scene authoring its own exit — only the closing scene may animate out — and the fact that a crossfade carries nothing across the cut (a dissolve, not a seam) are `motion-doctrine`'s, stamped by `SEAM_STAMP` and checked by `SEAM_VERIFIER`. **The numeric gate is authoritative where local prose disagrees**; fix the seam ledger, not the assertion. It still never overrides the user's confirmed transition style — it governs execution, not choice (ADR-001).
- **Additive seam bans this repo keeps** (narrowing only, never overriding the law): no `clipPath`-driven inter-scene wipe (anti-aliased black sliver at the boundary; render-side rules are `SEAM_RENDER_MECHANICS`) and no 3D/perspective transforms as a seam effect — a Z seam is a signed *scale* change.
- **Never animate `display`, `visibility`, or call `.play()` inside a timeline.** Breaks HyperFrames' deterministic seek; use `opacity` + `pointer-events`.
- **Never animate `<img>` dimensions directly.** Wrap the `<img>` in a non-timed `<div>` and animate the wrapper's `transform`. Direct dimension tweens trigger layout recompute that breaks deterministic seek.
- **Never use `tl.from()` for opacity tweens.** GSAP records the end-state at registration; if the CSS rest is `opacity:0` the recorded end is `opacity:0` (the tween goes nowhere), and under stagger later instances re-hide elements earlier ones revealed. Always use `tl.fromTo(target, {opacity:0,...}, {opacity:1,...}, pos)`.
- **Never ship a bare `<video>` in a clip scene.** The runtime only frame-syncs videos carrying `data-start`; with 2+ clip scenes bare videos cross-route (wrong footage / black) while every gate passes green. The explicit contract is `id` + `data-start="0"` + `data-duration` (loader's crossfade-extended window, not the bare clip length) + `data-media-start` (storyboard `Clip in`) + `data-track-index="0"` — see `workflows/phase-3-design.md` § Clip scene.

## Common edits

- **Add a voice** → update both the `## ElevenLabs Voice IDs` table in `SKILL.md` and the `## Voices` table in `README.md` (the two tables must stay in sync). Those IDs are the user-facing voice contract that the brief's `voice` field spells out and the `media-use` engine's ElevenLabs route synthesizes; no script in this repo resolves them any more.
- **Change the scene-builder contract** → `sub-agents/scene-builder-delta.md` is the role text every
  frame packet ships, and it is a **delta**: it only re-points conventions of `FRAME_WORKER_CORE`
  and adds local law, so anything already stated upstream does not belong in it. Change the packet's
  *shape* (what the five items are, what is forbidden in one) in `workflows/phase-3-design.md`
  Step 3.3, the dispatch rules in Step 3.4, and re-dispatch in `workflows/phase-4-production.md`
  Step 4.6 — those three plus the delta must stay consistent, and `SKILL.md` § Pipeline summarizes
  them. Two invariants a change may not quietly drop: a packet carries no `reasoning/` or `grammar/`
  file (ADR-004), and recipe bodies are inlined at dispatch and never written into a committed file
  (ADR-002). If a runtime has no dispatch capability, the builds run inline — see
  `SKILL.md` § Runtime Compatibility.
- **Change the audio path** → Phase 5's primary *generator* is the `media-use` audio engine, wired in
  `workflows/phase-5-audio.md`. Its capabilities (`AUDIO_ENGINE`, `BGM`, `SFX`, `TRANSCRIBE`,
  `TTS_LOCAL`, `CAPTIONS_AUTHORING`, `TRANSCRIPT_HANDLING`) are cited by symbol and resolved through
  `compat/ecosystem.md`, so an upstream relayout is a one-row edit there, never a workflow edit.
  The delegation seam is fixed: generation may move, but the exact-track music confirmation,
  `scripts/caption_gen.py`'s review contract, the verified mix recipes, and render approval are
  this skill's governance (ADR-001) and are never handed to the engine. M6 removed the local
  acquisition fallbacks, so there is nothing left to fall back *to* for synthesis or music search:
  with no engine, narration is `npx hyperframes tts` on a confirmed local voice and the bed is
  user-provided. `generate_voiceover.py --assemble-only` stays on **both** paths — never fold it
  into the engine, and never delete the file while doing audio work.
- **Change a transition** → edit that seam's row in the **seam ledger**, then re-stamp and re-verify
  (`SEAM_STAMP` → `SEAM_VERIFIER`). Never hand-tune easing at the boundary until the gate goes
  green: the mechanics are `motion-doctrine`'s (`SEAM_LAW`, row schema `SEAM_GATE_REFERENCE`), the
  named seam techniques and their parameters are `cut-the-curve`'s (`CUT_CATALOG`), and the numeric
  gate outranks any prose in this repo. The ledger's location and its place in the Phase-4 order are
  in `workflows/phase-4-production.md`; `patterns/transition-catalog.md` only maps moments to
  families. This repo adds nothing but the narrowing bans in `SKILL.md` § DON'Ts.
- **Change phase logic** → edit the relevant `workflows/phase-N-*.md`; update the prerequisite list in `SKILL.md` if a new required file is introduced.
- **Change the Creative Brief schema** → update `templates/project-plan.md`,
  `scripts/validate_brief.py`, workflow field names, and validator tests together. Story fields
  stale Phase 1–5; only `final_music_track` is audio-only and stales Phase 5.
  `music_strategy`'s vocabulary is `freesound` | `delegated` | `user-provided` | `none`, and each
  pins `final_music_track.source` differently — the exact Freesound URL, a provenance URI, the
  literal `user-provided`, or nothing at all. A **delegated** bed (retrieved from a provider catalog
  or generated locally by another skill) has no public page to link and an expiring download URL, so
  its source is a single-line
  `<skill-name>:<capability>?mode=<retrieve|generate>&query=<url-encoded request>#sha256=<64 hex>`:
  who produced it, by which route actually taken, from which request, and which bytes came out
  (`shasum -a 256 <path>` re-checks it offline, years later). `prompt=` substitutes for `query=` on
  a generation; exactly one of the two is required. Never record a delegated track as
  `user-provided` — that repurposes a Phase-1 answer given before any candidate existed and erases
  the only machine-checked provenance the brief carries. The exact-track confirmation gates the mix
  on **every** strategy, delegated included.
- **Change the storyboard format** → `templates/storyboard.md` is the shape doc copied into
  generated projects; `reasoning/scene-analysis.md` owns the director keys; `STORYBOARD_FORMAT`
  (through `compat/ecosystem.md`) owns the official keys, which this repo does not restate. A new
  local key must not collide with an official one — `test/unit/test_storyboard_extra_keys.py` fails
  if it does, because a colliding bullet is reinterpreted as upstream's field instead of preserved
  under `extra`. Adding a *director* key is an architecture change (the key set is closed); adding a
  capture binding also means updating `workflows/phase-1-storytelling.md`, the Phase-2/3 readers,
  and the legacy mapping table in `templates/storyboard.md` so `migrate-storyboard` keeps round-tripping.
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
- **Bump the GSAP version** → the CDN `<script>` tags carry a Subresource Integrity hash (`integrity="sha384-…" crossorigin="anonymous"`), pinned to `gsap@3.14.2`. Changing the version *requires* recomputing the hash, or the script is blocked and every scene renders without animation (caught by `npx hyperframes check` in Phase 4/5). Update **all** occurrences together — `templates/scene-*.html` and the skeletons in `workflows/phase-3-design.md` + `workflows/phase-4-production.md` (grep the tree; a stale hash anywhere ships silent, animation-free scenes):
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
