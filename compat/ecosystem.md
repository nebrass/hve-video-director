# Ecosystem Compatibility Map

The thin waist between hve-video-director and the HyperFrames ecosystem (ADR-007). Upstream
publishes no stability guarantees: it split the monolithic `hyperframes` skill into a router plus
the `hyperframes-*` domain family (7 dirs) alongside `media-use`, `motion-doctrine`, `seam-craft`,
`cut-the-curve`, `oversized-cursor`, `motion-graphics`, and `figma`; and it deprecated the
`validate`/`inspect`/`layout` gates. Both changes rotted this repo silently. This file is the
single blast radius for that churn.

**The one rule.**

- **Skill *names* are stable** — they are the ecosystem's public API. `hyperframes-core`,
  `media-use`, `motion-doctrine` and friends may be named anywhere in the repo, freely.
- **Intra-skill *file paths* churn** — `references/visual-styles.md`, `transitions/catalog.md`,
  `scripts/animation-map.mjs`. They live **here and nowhere else**. Everywhere else, prose names
  the skill and the capability (by SYMBOL) and points at this map for the exact path.
- Corollary for CLI: command names, the flags we pass, and format-version notes also live here.
- Corollary for upstream **rules** and **blueprints**: they are cited by *bare name*, not by
  symbol and not by path — see § Citing upstream vocabulary below.

**Why symbols and not just paths.** A phase reading "load the `hyperframes-creative` skill and
read VISUAL_STYLES" needs no indirection to know *what* it is getting; only the resolver — this
file — needs to know *where*. This generalizes the repo's existing "name actions, not tools"
rule (`CLAUDE.md`) from per-runtime tool names to per-release file paths.

**When upstream moves something.** Edit the one row here. Do not chase the path across
`workflows/`, `patterns/`, or `design-systems/` — if a path appears there, that is the bug.
Never copy upstream mechanism text into this repo to "stabilize" it (ADR-002): cite, don't fork.

**Resolving a skill home.** Paths below are *skill-relative*. Resolve the skill's install
directory for your runtime per `SKILL.md` § Runtime Compatibility (`$SKILL_HOMES`). Verified
against the local install under `.agents/skills/` on 2026-08-01.

---

## Capability registry

Every path below was confirmed to exist on disk at authoring time, and is re-asserted by the
pointer-validity suite on every `bash test/run.sh` where the ecosystem is installed
(§ `SKILL_SPLIT_TOPOLOGY`).

### `hyperframes-core` — the runtime contract

| Symbol | Owning skill | Skill-relative path | What it is | Used by |
|---|---|---|---|---|
| `DATA_ATTRIBUTES` | `hyperframes-core` | `references/data-attributes.md` | Full `data-*` table declaring timing/structure to the framework — the authoring contract every scene obeys | Phase 3 scene authoring; the clip-`<video>` contract (`data-start`/`data-duration`/`data-media-start`/`data-track-index`) |
| `DETERMINISM_RULES` | `hyperframes-core` | `references/determinism-rules.md` | Why every frame must be reproducible from its time value alone — the source of the "never animate `display`/`visibility`, never `.play()`" bans | Phase 3 + 4; `CLAUDE.md` § DON'Ts; `patterns/visual-patterns.md` |
| `TRACKS_AND_CLIPS` | `hyperframes-core` | `references/tracks-and-clips.md` | Track/clip timing rules — unique `data-track-index` for overlapping scenes, clip windows | Phase 4 Step 4.4 (scene overlap during a transition) |
| `SUB_COMPOSITIONS` | `hyperframes-core` | `references/sub-compositions.md` | Mechanics of a `<template>`-wrapped sub-composition file loaded via `data-composition-src` | Phase 3 (every `scenes/*.html` is a sub-comp) |
| `COMPOSITION_ARCHITECTURE` | `hyperframes-core` | `references/composition-patterns.md` | **Architecture**: monolithic vs modular, and the thin *Modular Orchestrator* `index.html` that declares slots, mounts audio, and registers a near-empty root timeline | Phase 4 root `index.html` wiring — this repo is always modular |
| `STORYBOARD_FORMAT` | `hyperframes-core` | `references/storyboard-format.md` | `STORYBOARD.md` shape + the `StoryboardManifest` it parses into; unknown `- key: value` bullets are preserved under `extra` | **Adopted at M4** — this repo's `storyboard.md` *is* this shape (frontmatter, `## Frame N — Title`, `- key: value` bullets), so the upstream parser, the Studio board review and the `.hyperframes/frame-comments.json` sidecar all apply to it. Everything the official key set has no home for — the M1 director keys, the capture bindings, this skill's own frontmatter fields — rides in `extra`, which is what the `STORYBOARD_EXTRA_KEYS` probe guards. Phase 1 writes it; `templates/storyboard.md` is the local shape doc |
| `FRAME_WORKER_CORE` | `hyperframes-core` | `references/frame-worker-core.md` | The workflow-agnostic frame-builder role: reveal paced across the frame's **full** duration (front-loading is the "PowerPoint slide" failure), the exit ban, and what `scene`/`voiceover`/`duration` mean to a builder | M1 `grammar/motion.md` (Reveal, Progressive disclosure, Exit discipline); Phase 3 scene direction |
| `FULL_SCREEN_MOTION` | `hyperframes-core` | `references/full-screen-motion.md` | One shared continuous background layer + transparent timed content layers, instead of stacked opaque per-scene backgrounds | **Not wired today, and unclaimed** — no M1 module cites it. Registered purely so a continuous-background need resolves to this name instead of a new one. Drop the row if M2 still has no caller |
| `BRIEF_FORMAT` | `hyperframes-core` | `references/brief-format.md` | `BRIEF.md` — the ecosystem's confirmed-intent document | **Deliberately NOT adopted — decided at M4, on ADR-001.** `project-plan.md` stays this skill's Creative Brief and the single record of the levers the user owns; `validate_brief.py` is not re-pointed at `BRIEF.md`. Registered so the name resolves here rather than being re-derived, and so the decision is found before someone "finishes the job". The reason is `BRIEF_CONTRACT` |
| `BRIEF_CONTRACT` | `hyperframes-core` | `references/brief-contract.md` | Collaborative/autonomous run-shape derivation; skips questions the request already answers | **The reason `BRIEF_FORMAT` is not adopted.** Deriving a run shape and skipping questions the request already answers is the opposite of this skill's consent doctrine — recommend, never preselect; never infer an answer the user did not give (ADR-001). Adopting the brief would import a contract that contradicts the skill's central promise, which is why M4 adopted the *storyboard* (a description of the film) and not the brief (a consent record). **Not wired** — and its interaction `mode` is the one official storyboard frontmatter key this repo never writes |

### `hyperframes-animation` — motion recipes and transitions

| Symbol | Owning skill | Skill-relative path | What it is | Used by |
|---|---|---|---|---|
| `TRANSITION_CATALOG` | `hyperframes-animation` | `transitions/catalog.md` | Hard rules + scene template + shader rules for transitions — the normative page | `patterns/transition-catalog.md` § Where the mechanics live; Phase 4 Step 4.5 |
| `TRANSITION_OVERVIEW` | `hyperframes-animation` | `transitions/overview.md` | Selection guidance — energy/mood, narrative position, presets, CSS vs shader | `patterns/transition-catalog.md` § Picking by mood |
| `TRANSITION_FAMILIES` | `hyperframes-animation` | `transitions/css-<family>.md`, 13 files: `css-3d`, `css-blur`, `css-cover`, `css-destruction`, `css-dissolve`, `css-distortion`, `css-grid`, `css-light`, `css-mechanical`, `css-other`, `css-push`, `css-radial`, `css-scale` | Per-family implementations (the *how*) behind the family names our catalog maps to moments | `patterns/transition-catalog.md` § Picking by mood + § Where the mechanics live; `patterns/visual-patterns.md` § DON'Ts (the light-family replacement for a clipPath seam) |
| `TRANSITION_REGISTRY` | `hyperframes-animation` | `transitions/TRANSITION-REGISTRY.md` | Machine-readable registry — a curated Tier-B subset, **not** the full catalog | `patterns/transition-catalog.md`; seam tooling |
| `MARKER_PATTERNS` | `hyperframes-animation` | `rules/css-marker-patterns.md` | Full depth of word-emphasis drawing patterns (highlight, circle, burst, scribble, sketchout) incl. multi-line + mode cycling | `patterns/marker-highlight.md` — which owns the mode → promo-arc mapping and the editorial caps, and **none** of the drawing; Phase 3 caption emphasis |
| `RULES_INDEX` | `hyperframes-animation` | `rules-index.md` | Index of the atomic motion recipes at `rules/<name>.md`, composed a few at a time into one scene — the count this repo writes is the `motion:` row of the director-keys contract in `reasoning/scene-analysis.md`, not a number this map carries | Phase 3 scene choreography (entry point — do not enumerate `rules/*` outside this file) |
| `BLUEPRINT_INDEX` | `hyperframes-animation` | `blueprints-index.md` | Index of the 22 proven whole-frame shapes at `blueprints/<id>.md`, plus the Reproduce/Adapt/Compose method | Phase 3 scene-shape selection; M1 `blueprint:` storyboard key (entry point — do not enumerate `blueprints/*` outside this file) |
| `TECHNIQUES` | `hyperframes-animation` | `techniques.md` | The 13 numbered visual techniques (#1 SVG path draw … #13 WebGL fragment shader), plus upstream's own per-composition minimum — read that expectation there; this map does not restate it. Cite by **number + title**, never by path | M1 `grammar/camera.md` (#12 clip-path reveal window), `grammar/motion.md` (#4 per-word kinetic type), `grammar/metaphors.md` (#9 MotionPath), `grammar/three-taxonomy.md` (#13 shader plates) |
| `RUNTIME_PICKER` | `hyperframes-animation` | `SKILL.md` (§ Picking a runtime, § coexistence) | Upstream's own one-line-per-runtime selection guidance, plus the rule that runtimes coexist — each registers on its global so HyperFrames seeks all in one pass | M1 `reasoning/capability-catalog.md`: this is the **base truth** the catalog extends with capability tags. The catalog may add mapping and tie-breaks; it may never contradict this |
| `GSAP_ADAPTER` | `hyperframes-animation` | `adapters/gsap.md` | GSAP-in-HyperFrames adapter rules — timeline registration and the property/transform contract (transforms/perf in sibling `adapters/gsap-*.md`; easing/stagger has its own symbol below) | M1 `reasoning/capability-catalog.md` (GSAP is the default runtime and the master clock every other runtime hangs off); Phase 3/4 authoring. Also the standing answer for the optional standalone `gsap` companion skill that `SKILL.md`/`CLAUDE.md`/`README.md` name but which is **not installed** — this is where that guidance actually lives now |
| `EASING_AND_STAGGER` | `hyperframes-animation` | `adapters/gsap-easing-and-stagger.md` | The ease-family palette with its character/mood mapping, the house easing register, and the stagger contract — *selection* guidance a director needs, not only mechanism | M1 `grammar/motion.md` (Easing discipline, Follow-through, Hierarchy); `reasoning/scene-analysis.md` easing register per tone |
| `THREE_ADAPTER` | `hyperframes-animation` | `adapters/three.md` | The whole Three.js integration contract: render from `hf-seek`, importmap version pinning, asset preload, mandatory `data-duration`, `AnimationMixer.setTime`, camera pose as a pure function of time | M1 `grammar/three-taxonomy.md` (built entirely on it) + `reasoning/capability-catalog.md` `three` row + `grammar/camera.md` Tier B. Grammars name scene categories and ingredients; they never restate this contract |
| `HTML_IN_CANVAS` | `hyperframes-animation` | `adapters/html-in-canvas-patterns.md` | Live HTML captured as a GPU texture (`drawElementImage`) with bloom/shatter/portal/liquid post-fx, incl. its environment caveats and fallback rule | M1 `reasoning/capability-catalog.md` (`cinematic-hero` on real UI) + `grammar/three-taxonomy.md` § HTML-as-texture. Also the upstream origin of the **hero-beat doctrine** both grammars budget against — the limit itself is a row of the budget table in `reasoning/scene-analysis.md` and lives nowhere else (ADR-008), including here |
| `TYPEGPU_ADAPTER` | `hyperframes-animation` | `adapters/typegpu.md` | WebGPU/WGSL canvases — particle sims, liquid glass, custom shaders — and their sync-registration rules | M1 `reasoning/capability-catalog.md` (`gpu-compute`). Environment-gated: confirm with `DOCTOR` before selecting, else fall back to Three.js or DOM |
| `LOTTIE_ADAPTER` | `hyperframes-animation` | `adapters/lottie.md` | Pre-baked After Effects timelines seeked by absolute time (no runtime loop/speed); local assets only | M1 `reasoning/capability-catalog.md` (`prebaked-asset`) — asset-reality gated: no exported asset, never Lottie |
| `ANIMEJS_ADAPTER` | `hyperframes-animation` | `adapters/animejs.md` | Lightweight tweening when GSAP is overkill, plus the instance-registry discipline that keeps it seekable | M1 `reasoning/capability-catalog.md` — explicitly secondary to GSAP |
| `CSS_ANIMATIONS_ADAPTER` | `hyperframes-animation` | `adapters/css-animations.md` | Zero-JS repeated motifs (shimmer/glow/pulse/grain) with finite iterations | M1 `reasoning/capability-catalog.md` (`decorative-loop`) — banned as idle motion inside a GSAP-choreographed scene (wall-clock desync) |
| `WAAPI_ADAPTER` | `hyperframes-animation` | `adapters/waapi.md` | Native browser keyframes without a GSAP dependency; document-time seek, clip offsets expressed as `delay` | M1 `reasoning/capability-catalog.md` — weakest diagnostics of any runtime; last resort |
| `ANIMATE_TEXT` | `hyperframes-animation` | `adapters/animate-text.md` | A **pointer**, not a catalog: it defers to Pixel Point's external `animate-text` skill for 24 named text-effect IDs and gives a GSAP fallback recipe. The catalog is deliberately not vendored, and that skill is **not installed here** — a storyboard naming an effect ID resolves to nothing until `npx skills add pixel-point/animate-text` runs | M1 `grammar/motion.md` + `reasoning/capability-catalog.md` (`text-choreography` by name). Treat named IDs as *unavailable* unless the upstream skill is installed; otherwise direct the effect in plain motion vocabulary |
| `ANIMATION_MAP` | `hyperframes-animation` | `scripts/animation-map.mjs` | Node verifier that maps what actually animates across the timeline — ships with the skill, **not** exposed as a CLI subcommand | Phase 4 Step 4.7 (resolves the skill dir into `ANIM_SKILL_DIR`) |

### `hyperframes-keyframes` — motion proof

| Symbol | Owning skill | Skill-relative path | What it is | Used by |
|---|---|---|---|---|
| `KEYFRAME_DISCIPLINE` | `hyperframes-keyframes` | `SKILL.md` (gateway) | The pose contract — visible states, continuous subject identity, seek-safe runtime, verified pixels — plus its `--shot`/`--ghost` diagnostics | M1 `grammar/motion.md` (Transformation/morph) + `reasoning/capability-catalog.md` (`identity-morph`). Not a runtime: a verification layer *over* the runtimes |
| `KEYFRAME_PATTERNS` | `hyperframes-keyframes` | `references/keyframe-patterns.md` | The mechanism shelf — runtime skeletons, FLIP, SVG morph/draw, paths/masks, 3D depth, and the GSAP-proxy pattern for driving a non-DOM camera from the timeline | M1 `grammar/three-taxonomy.md` (camera driven via a GSAP proxy); Phase 3 when a single subject's motion must be *proven* |

### `hyperframes-creative` — design direction

| Symbol | Owning skill | Skill-relative path | What it is | Used by |
|---|---|---|---|---|
| `VISUAL_STYLES` | `hyperframes-creative` | `references/visual-styles.md` | The 8 named mood-based visual identities | Phase 1 `identity_strategy: hyperframes-style`; Phase 3 (Path B); `design-systems/README.md` |
| `PALETTES` | `hyperframes-creative` | `palettes/<name>.md`, 9 files: `bold-energetic`, `clean-corporate`, `dark-premium`, `jewel-rich`, `monochrome`, `nature-earth`, `neon-electric`, `pastel-soft`, `warm-editorial` | Ready colour systems, paired with a visual style | Phase 3 `DESIGN.md` |
| `HOUSE_STYLE` | `hyperframes-creative` | `references/house-style.md` | Sensible defaults for motion, colour, type when there is no strong opinion | Phase 3 fallback |
| `MOTION_PRINCIPLES` | `hyperframes-creative` | `references/motion-principles.md` | Motion philosophy — easing is emotion, speed is weight, build/breathe/resolve | Phase 3 + 4, read once per project; M1 `grammar/motion.md` doctrine |
| `BEAT_DIRECTION` | `hyperframes-creative` | `references/beat-direction.md` | Per-beat direction: concept, mood, choreography, transition, depth layers, SFX cues, rhythm planning — and the "every element gets a motion verb" law | M1 `grammar/motion.md` (Staging; the verb law) and `reasoning/scene-analysis.md` per-frame questions |
| `VIDEO_COMPOSITION` | `hyperframes-creative` | `references/video-composition.md` | Video frames are not web pages — density, type scale, decorative opacity; what is strict from the design spec vs adaptable for video | M1 `reasoning/scene-analysis.md` `density:` values; `grammar/motion.md` (Staging) |
| `STORY_SPINE` | `hyperframes-creative` | `references/story-spine.md` | Value-first narrative doctrine — the hook speaks outcome language, reverse iceberg (value claim by beat 2), implementation is the footnote | Reserved name for Phase 1 beat ordering. **Not wired today** |
| `NARRATION` | `hyperframes-creative` | `references/narration.md` | Script-writing rules and upstream's words-per-second pacing budget | Reserved name for Phase 1 voiceover word budgets. **Not wired today** |
| `TYPOGRAPHY` | `hyperframes-creative` | `references/typography.md` | Font pairing + OpenType features (tabular-nums for stat scenes) | Phase 3 `DESIGN.md` |
| `DATA_IN_MOTION` | `hyperframes-creative` | `references/data-in-motion.md` | Animated charts, counters, bar races | Phase 3 stat scenes |
| `COMPOSITION_RECIPES` | `hyperframes-creative` | `references/composition-patterns.md` | **Visual composition recipes**: picture-in-picture, text-behind-subject, title card with fade, slide show, and a flat top-level clip example | Phase 3 scene shapes; Phase 4 when a scene needs PiP/title-card layout |
| `AUDIO_REACTIVE` | `hyperframes-creative` | `references/audio-reactive.md` | Beat-matched motion from pre-extracted frequency bands (never Web Audio at render time) | Phase 5 optional flourishes |
| `CONTRAST_REPORT` | `hyperframes-creative` | `scripts/contrast-report.mjs` | Node contrast reporter shipped with the skill, complementing `check`'s WCAG pass | Phase 4 verification |

> **Disambiguation.** `MOTION_PRINCIPLES` and `BEAT_DIRECTION` are both creative-owned motion
> philosophy and overlap. Split by scope: `MOTION_PRINCIPLES` is **film-wide** (easing is emotion,
> speed is weight, build/breathe/resolve) — read once per project, cite it in a grammar's Doctrine
> section. `BEAT_DIRECTION` is **per-beat** (the motion-verb law, mood, choreography, depth layers,
> rhythm) — cite it from a grammar row or a per-frame question. A file needing both says which is
> doing what; neither is a synonym for the other.

> **Disambiguation.** `composition-patterns.md` exists in *both* core and creative and they are
> different documents. `COMPOSITION_ARCHITECTURE` (core) answers *how is the project structured
> and what does the root `index.html` look like*. `COMPOSITION_RECIPES` (creative) answers *what
> visual arrangement does this scene use*. Phase 4's root-composition wiring resolves to
> **`COMPOSITION_ARCHITECTURE`**.

### `media-use` — audio, captions, transcripts

| Symbol | Owning skill | Skill-relative path | What it is | Used by |
|---|---|---|---|---|
| `CAPTIONS_AUTHORING` | `media-use` | `audio/references/captions/authoring.md` | The on-screen caption mechanism (GROUPS) + its `[caption-lint]` self-check | Phase 3 caption-track scene; Phase 5 caption verification |
| `TRANSCRIPT_HANDLING` | `media-use` | `audio/references/captions/transcript-handling.md` | Turning a word-level transcript into caption cues | Phase 5, alongside `CAPTIONS_AUTHORING` |
| `CAPTIONS_MOTION` | `media-use` | `audio/references/captions/motion.md` | Audio-reactive caption styling — karaoke, beat-sync emphasis | High-energy spots only |
| `TRANSCRIBE` | `media-use` | `audio/references/transcribe.md` | Word-level timestamps; **always pass `--model` explicitly** (the CLI default `small.en` silently translates non-English audio) | Phase 5 voiceover-timing verification |
| `TTS_LOCAL` | `media-use` | `audio/references/tts.md` | Local Kokoro-82M TTS — 54 voices, 8 languages | Phase 5 fallback when no `ELEVENLABS_API_KEY`, on explicit user confirmation |
| `AUDIO_REQUIREMENTS` | `media-use` | `audio/references/requirements.md` | Local prerequisites for the audio paths | `patterns/INDEX.md` § Reaching past the local patterns only, as a parenthetical beside `TTS_LOCAL`. No workflow cites it directly |
| `AUDIO_ENGINE` | `media-use` | `audio/scripts/audio.mjs` | The shared TTS + BGM + SFX engine — one implementation for every official video workflow | Phase 5 narration + music bed + SFX (M2). the only local audio script left is `scripts/generate_voiceover.py --assemble-only` (section assembly, used by both paths); M6 retired the acquisition fallbacks |
| `BGM` | `media-use` | `audio/references/bgm.md` | One music bed per composition, produced by `AUDIO_ENGINE` | Phase 5 (M2) — see `AUDIO_ENGINE` |
| `SFX` | `media-use` | `audio/references/sfx.md` | Named sound effects, provider-gated by `AUDIO_ENGINE`'s single switch | Phase 5 (M2) — see `AUDIO_ENGINE` |

### `motion-doctrine` / `seam-craft` / `cut-the-curve` — seam law, mechanics, technique

| Symbol | Owning skill | Skill-relative path | What it is | Used by |
|---|---|---|---|---|
| `SEAM_LAW` | `motion-doctrine` | `SKILL.md` (gateway) | The vector law — how Scene A exits determines how Scene B enters (axis, direction, speed, phase). **Supersedes** local transition guidance where they disagree | `patterns/INDEX.md`; `patterns/transition-catalog.md`; Phase 4 Step 4.5 |
| `SEAM_GATE_REFERENCE` | `motion-doctrine` | `references/seam-gate.md` | How the build-gate enforcement of the seam law works | Phase 4 seam verification |
| `SEAM_VERIFIER` | `motion-doctrine` | `scripts/seam-gate.mjs` | Numeric seam verifier — run after assembling the master timeline | Phase 4 verification |
| `SEAM_STAMP` | `motion-doctrine` | `scripts/seam-stamp.mjs` | Stamps master seams from a vector ledger so they pass the gate by construction | Phase 4 (authoring order: ledger → stamp → build → verify) |
| `SEAM_RENDER_MECHANICS` | `seam-craft` | `SKILL.md` | Render-side prerequisites — the opaque stage-ground white-flash guard, wrapper overlap/compositing | `patterns/transition-catalog.md`; `patterns/visual-patterns.md`; Phase 4 |
| `CUT_CATALOG` | `cut-the-curve` | `SKILL.md` (gateway) | The seam *technique* catalog — five velocity-matched seams (zoom-through, inverse zoom-through, cut-the-curve, waterfall cut, rack-focus blur-cut) plus waterfall entry and the nudge curve, with their parameters | M1 `grammar/motion.md` (Continuity — every seam needs a *named carrier*); `patterns/transition-catalog.md`. `SEAM_LAW` still governs; this supplies the parameters and mechanics |

> **These three resolve to the skill root.** `SEAM_LAW`, `SEAM_RENDER_MECHANICS` and `CUT_CATALOG`
> point at each skill's `SKILL.md` entry point, which cannot move without the skill being renamed —
> so they are the *least* volatile rows here. Naming `motion-doctrine`, `seam-craft` or
> `cut-the-curve` in prose elsewhere is legal and expected (skill names are stable); only a path
> *inside* them would be a violation.

### `oversized-cursor` / `motion-graphics` — technique skills

| Symbol | Owning skill | Skill-relative path | What it is | Used by |
|---|---|---|---|---|
| `CURSOR_TECHNIQUE` | `oversized-cursor` | `SKILL.md` (gateway) | The oversized-pointer technique — off-screen entry law, tip-targeting and the click tap, click-ignites-the-next-beat, exit / cross-scene handoff | M1 `grammar/motion.md` (Causal motion) and `grammar/camera.md` (Follow / Lock-On); Phase 3 UI-demo scenes |
| `MG_CATALOG_MAP` | `motion-graphics` | `catalog-map.md` | Category → registry-block map (charts, kinetic type, logo reveal, lower thirds, maps, news, stat, tweet, webpage, asset fusion) with what to customize per block | M1 `grammar/metaphors.md` rows whose best expression is a shipped block (geography/maps, stat plates) — names what to pull with `hyperframes add` |
| `MG_ASSET_FUSION` | `motion-graphics` | `categories/asset-fusion/module.md` | The asset-fusion category module — binding motion to a fixed overlay/affordance; source of the "no camera push under a fixed overlay" constraint | M1 `grammar/camera.md` § Hard rules |
| `MG_MOTION_VOCABULARY` | `motion-graphics` | `references/motion-vocabulary.md` | `motion-graphics`' **own** primitive→GSAP vocabulary, used by its Director/Builder pair | Guardrail only. This is **not** the director's motion vocabulary — our motion names come from `RULES_INDEX` / `BLUEPRINT_INDEX` / `TECHNIQUES`. Registered so the two namespaces are never mixed. Deliberately excluded, *not* awaiting adoption — never wire this |

### `hyperframes-registry` — catalog blocks

| Symbol | Owning skill | Skill-relative path | What it is | Used by |
|---|---|---|---|---|
| `REGISTRY_BLOCKS` | `hyperframes-registry` | `references/wiring-blocks.md` | How an installed block (own `data-composition-id`, dimensions, duration, timeline) is wired into a host composition via `data-composition-src` | Phase 4 Step 4.2, after `hyperframes add` |
| `REGISTRY_ADD_EXAMPLE` | `hyperframes-registry` | `examples/add-block.md` | Worked example of installing a block | Phase 3/4 when pulling `flash-through-white`, `cinematic-zoom`, `chromatic-radial-split`, … |
| `REGISTRY_CATALOG` | `hyperframes-registry` | `references/discovery.md` | The browsable block/component catalog — the exact names `hyperframes add` accepts, including the six VFX blocks (`vfx-portal`, `vfx-shatter`, `vfx-liquid-background`, `vfx-magnetic`, `vfx-iphone-device`, `vfx-text-cursor`) | M1 `grammar/metaphors.md` + `grammar/three-taxonomy.md` — reuse a shipped block before hand-authoring a hero beat |
| `REGISTRY_VFX_TEMPLATE` | `hyperframes-registry` | `references/templates.md` | Starter templates, incl. the Three.js VFX block pattern: seeded PRNG for anything "random", and render via `onUpdate` — never `requestAnimationFrame` | M1 `grammar/three-taxonomy.md` § Fields (seeded, deterministic instancing) |

### `hyperframes-cli` — gate semantics

| Symbol | Owning skill | Skill-relative path | What it is | Used by |
|---|---|---|---|---|
| `CHECK_GATE` | `hyperframes-cli` | `references/lint-validate-inspect.md` | Semantics of `lint` (fast iteration) vs `check` (required final gate: lint + runtime + layout + motion + contrast in one browser session), `snapshot`, and the deprecated trio | `SKILL.md` prerequisites; Phase 4 + Phase 5 gates |
| `PREVIEW_RENDER` | `hyperframes-cli` | `references/preview-render.md` | `preview` studio + `render` semantics | Phase 3/4 preview; Phase 5 final render |
| `DOCTOR` | `hyperframes-cli` | `references/doctor-browser.md` | Render-environment diagnosis and browser management | Phase 5 pre-render troubleshooting (ADR-003: defer to `doctor`, never build a parallel diagnostic) |
| `INIT_SCAFFOLD` | `hyperframes-cli` | `references/init-and-scaffold.md` | `init` project scaffolding (and `capture`) | Phase 4 Step 4.1 |
| `CLI_MISC` | `hyperframes-cli` | `references/upgrade-info-misc.md` | `transcribe`, `tts`, `info`, `upgrade` | Phase 5 |

**Not registered.** The `hyperframes` skill is an intent **router**: it ships only `SKILL.md` and
holds no reference files of its own. Name it when you want routing; never cite a path "inside" it.

---

## Citing upstream vocabulary

Three citation forms exist, and only three. `grammar/` and `reasoning/` modules use these instead
of paths; so does every workflow and pattern file.

| Kind | Cite as | Resolved through | Example |
|---|---|---|---|
| Upstream **rule** — 48 under `rules/` | bare name, backticked, no directory, no `.md` | `RULES_INDEX` | `` `coordinate-target-zoom` `` |
| Upstream **blueprint** — 22 under `blueprints/` | bare id, backticked, no directory, no `.md` | `BLUEPRINT_INDEX` | `` `camera-journey` `` |
| Everything else upstream | the capability SYMBOL registered above | this file | `THREE_ADAPTER`, `SEAM_LAW` |

**Resolution order for a bare name.** `BLUEPRINT_INDEX` first, then `RULES_INDEX`. The two
namespaces overlap in *shape* but not in content, and the proposals that seeded M1 mix them
freely, so the order has to be stated rather than inferred. A name in neither index is invalid:
drop the citation or map it to the nearest real entry and say so. Never invent a name, and never
back-derive one from a recipe's prose.

**Why rules and blueprints are not symbols.** Registering 48 + 22 more rows would roughly triple
this map and buy nothing. The two index files already *are* the upstream registry for those
items, and they are the entry points upstream maintains. A rule NAME is a stable identifier — a
rename is a breaking change upstream ships deliberately — while its PATH is exactly the kind of
thing that churns silently (ADR-007). Copying the index rows' one-line summaries here would also
be an immediate fork of upstream authorship (ADR-002).

**`css-marker-patterns` has two identities — use the symbol.** It is simultaneously a rule listed
in `RULES_INDEX` and the registered symbol `MARKER_PATTERNS`. Cite `MARKER_PATTERNS`; do not cite
it as a bare rule name. It is the only such overlap in the registry today.

**Enforcement.** `test/unit/test_compat_pointers.py` asserts that every registered path resolves
under an installed skill home, that every SYMBOL cited in repo prose is defined here, and — since
M1 — that every bare rule/blueprint citation in the reasoning layer resolves against
`RULES_INDEX` and `BLUEPRINT_INDEX`, so a citation naming a nonexistent rule or blueprint is a red
test rather than a silent dead pointer. Both indexes are machine-parseable, which is what makes
that resolution cheap: rules are listed as `<name path="rules/name.md">…</name>` elements,
blueprints as `<blueprint id="…" roles="…" duration="…">…</blueprint>` elements. The two counts
published in the table above are parsed out of *this* file and compared against the installed
indexes, so a hand-typed count that drifts (an early draft said 47 rules) fails too — which is
why those counts are stated once, there, and not repeated in this paragraph. Two consequences for
authors:

- **Keep citations backticked** — that is what the scanner sees.
- **Keep them extension-less and directory-less** — a `.md` suffix or a leading `rules/` reads as
  a path and violates the one rule at the top of this file.

**Which files the suite reads.** Three surfaces, deliberately different in width:

- **Path rules** (no `skill` → `path` citation, no registered path string, no distinctive upstream
  basename) run over the markdown in `workflows/`, `patterns/`, `grammar/` and `reasoning/`, the
  whole `design-systems/` tree, and the three root prompt files — `SKILL.md`, `CLAUDE.md`,
  `README.md`. This file is exempt because it *is* the map.
- **Symbol definition** runs wider, and recursively: every markdown file this repo authors as
  prompt content, which additionally covers `templates/`, `compat/`, `.github/` and the remaining
  root docs.
- **Bare rule/blueprint resolution** is scoped to the markdown directly in `grammar/` and
  `reasoning/` — the only prose that cites upstream recipes by name.

Everything outside those lists is unchecked by design: `CHANGELOG.md` is history, `docs/` is the
spec bundle, `example/` is a generated project. All three are off-limits to edits, and a test may
not demand a fix it forbids.

---

## Registered literal paths — where an upstream path is written out on purpose

**A runnable command cannot indirect through a symbol.** `node "$DIR/$SEAM_VERIFIER"` resolves to
nothing: a shell expands variables, not this map. So a workflow step that *runs* a skill-resident
script has to spell the path out, and the prose rule above ("if a path appears there, that is the
bug") would otherwise make every such step a violation. The sanction is explicit rather than
implied, and this is where a maintainer learns which paths live in two places.

Three call sites exist today, **all** in `workflows/phase-4-production.md`:

| Literal written out | Registered as | Where it runs |
|---|---|---|
| `scripts/seam-stamp.mjs` | `SEAM_STAMP` (`motion-doctrine`) | Step 4.5 — stamp the master seams from the ledger |
| `scripts/seam-gate.mjs` | `SEAM_VERIFIER` (`motion-doctrine`) | Step 4.5 (`probe` one boundary) and Step 4.6 (`verify` after `check`) |
| `scripts/animation-map.mjs` | `ANIMATION_MAP` (`hyperframes-animation`) | Step 4.7 — animation-map verification |

All three are skill-resident scripts with **no** `hyperframes <subcommand>` equivalent — the shape
`ANIMATION_MAP_LOCATION` describes. That absence is the whole justification: a command upstream
exposes through the CLI needs no literal, because the CLI's command names are stable and already
live in § CLI surface.

**The sanction is per-line, per-file, and fenced-code only.** The pointer-validity suite carries a
`(repo-relative file, registered path)` allowlist; a literal is exempt only *inside* a fenced code
block of exactly that file. Prose in the same file is checked like everywhere else — writing "run
the seam gate at `scripts/seam-gate.mjs`" outside a fence is still a violation, and so is the same
command in any other workflow. The exemption covers the registered path and its bare basename
through one list, not two, so it cannot drift against itself.

```bash
# The registered pairs, and the only place they live:
grep -n -A6 'RUNNABLE_PATH_ALLOWLIST' test/unit/test_compat_pointers.py
```

**Both halves are edited together.** Each call site carries the comment *"Live path — registered as
`<SYMBOL>` in compat/ecosystem.md; if upstream moves it, edit both."* The registry row stays the
authority; the literal is a copy of it. Only the row is checked for resolution, so an upstream move
shows up here as a failing registry path, and the copy has to be repaired by hand from this list.

**Adding a fourth is a cost, not a convenience.** It puts another copy of a churning path in the
repo, and the suite can only prove the *registry* row resolves. Add one only when the command is
genuinely runnable and upstream ships no CLI equivalent — never to quiet a sentence. `CONTRAST_REPORT`
is the fourth script of this shape and is deliberately **not** on the list, because no workflow runs
it in a fenced command today.

---

## CLI surface

Package: [`hyperframes`](https://www.npmjs.com/package/hyperframes) — invoked as `npx hyperframes
<command>`, no local install required. **Version tested against: `0.7.87`** (verify with
`npx --no-install hyperframes --version`). Treat the version as a *record*, not a branch
condition — see Behavior probes.

| Command | Purpose | Flags we rely on | Notes |
|---|---|---|---|
| `init` | Scaffold a composition project | `<dir>` positional | Phase 4 Step 4.1. Also offers `-t/--template`, `--resolution`, `--tailwind`, `--non-interactive`, `--skip-skills` |
| `add` | Install a registry block/component | `<name>` positional | Phase 3/4. Pull a block before hand-authoring a transition. Wiring: `REGISTRY_BLOCKS` |
| `catalog` | Browse registry blocks/components | `--type`, `--tag`, `--json` | **Not wired into any phase.** Discovery aid only — phases name blocks explicitly and call `add` |
| `capture` | Capture a website for video production | — | **Not wired.** Phase 2 uses `mcp__chrome-devtools__*` plus `scripts/capture_screen.py`; that capture contract is this repo's, deliberately |
| `preview` | Live studio for iterating on a composition | `.` (project dir) | Phase 3 scene review, Phase 4 composition review |
| `lint` | Fast static validation | `.`, `--json` | Iteration only. Never chain a standalone `lint` immediately before `check` — `check` reruns it |
| `check` | **The required final gate** — lint + runtime + layout + motion + WCAG contrast in one browser session | `.`, `--samples`, `--json`; available: `--strict`, `--at-transitions`, `--snapshots`, `--frame-check`, `--caption-zone` | Phase 4 exit gate and Phase 5 prerequisite. Its `--json` `_meta` carries **no** `deprecated` key — that absence is the feature probe |
| `snapshot` | Capture still PNGs (hero frames, zoomed crops) | `.`, `--at <t,t,…>` | Not deprecated; the standalone still-capture utility. `check --snapshots` covers the gate's own needs |
| `render` | Render to MP4/WebM/MOV/GIF/PNG-seq | `.`, `--output`, `--docker`, `--no-low-memory-mode` | Phase 5. Also available: `-c/--composition`, `-f/--fps`, `-q/--quality`, `-w/--workers`, `--format`, `--gpu`, `--browser-gpu`/`--no-browser-gpu` |
| `doctor` | Render-environment diagnostics | `--json` | Phase 5. ADR-003: troubleshooting defers here |
| `transcribe` | Word-level timestamps from audio/video | `<file>`, `--model` | Phase 5 voiceover-timing verification, preferred over standalone Whisper. **Always pass `--model`** (default `small.en` silently translates non-English audio) |
| `tts` | Local Kokoro-82M speech | `--list`, `-v/--voice`, `--text-file`, `--output` | Phase 5 fallback, only on explicit user confirmation |
| `skills` | Install / check / update HyperFrames skills | `check`, `update` | Pin maintenance — see below |
| ~~`validate`~~ ~~`inspect`~~ ~~`layout`~~ | **DEPRECATED aliases of `check`** | `--json` | All three still run, print a deprecation notice on **stderr**, and set `_meta.deprecated: true` in `--json`. Do not add them to any workflow; keep them only as a documented fallback if `check` is ever unavailable |

---

## Behavior probes

Load-bearing upstream **behaviors** — the things that would break this skill without any path
changing and without any gate turning red. Each names its probe and whether that probe is
automated.

### `STORYBOARD_EXTRA_KEYS` — unknown bullets survive parsing

- **What.** `STORYBOARD_FORMAT` states that per-frame `- key: value` bullets outside the known
  set are "kept verbatim under the frame's `extra`", and unknown frontmatter keys under
  `globals.extra`. The parser is documented as **lenient**: it never throws and records anything
  surprising as a `warning`.
- **Why it matters.** Since M4 adopted the official shape, *everything this skill knows about a
  frame that upstream has no key for* rides on this: the director keys, the capture bindings, this
  skill's own frontmatter fields. Two ways it breaks, both silent. Upstream **drops** unknown keys
  and every frame loses its direction; or upstream **promotes** one of our key names into its own
  official set, and the value is reinterpreted as upstream's field instead of preserved. `lint`,
  `check` and the seam gate stay green through either — the exact failure class this compat layer
  exists to catch. A future *strict* parser fails differently (throws / errors) and would at least
  be loud; a key-dropping or key-capturing parser is the silent one.
- **Probe — two halves, both automated.** `test/unit/test_storyboard_extra_keys.py`, inside
  `bash test/run.sh`.
  - **Round trip through an upstream parser.** Four installed ecosystem workflow skills —
    `faceless-explainer`, `music-to-video`, `pr-to-video`, `product-launch-video` — each vendor a
    dependency-free plain-JS port of the canonical parser at `scripts/lib/storyboard.mjs`, which
    their own scripts run under plain `node`. The test discovers them **by export name**
    (`parseStoryboard`) rather than by path, so a relayout inside those skills does not blind it;
    it writes one frame carrying every director key, runs it through **every** copy found, and
    asserts each key *and its value* comes back under `frames[].extra`, plus this skill's
    frontmatter fields under `globals.extra`. Values are asserted, not just names — a parser that
    kept keys and truncated values would pass a presence-only check — with the backticked
    comma-separated `motion:` list and an embedded-colon `runtime_rejected:` as the hard cases.
  - **Documented contract.** Reads `STORYBOARD_FORMAT` — resolved *through this map*, so the test
    itself holds no upstream path — and asserts the per-frame key table still carries its catch-all
    "unknown key → `extra`" row, the frontmatter section still names `globals.extra`, the published
    `StoryboardManifest` still declares `extra`, and, the precise half, that **no director key has
    appeared in the official per-frame key set**. Structural where phrasing would be brittle, exact
    where the question is precise: a reworded guarantee must not fail, a collision must not pass.
    Needs no `node` and no npm anything.
- **Status: IMPLEMENTED — with one honest gap.** The round trip runs against an upstream-authored
  **port**, not `@hyperframes/core` itself. Re-verified 2026-08-02: the canonical package is still
  unreachable here. The repo has no `package.json` and no `node_modules`; `@hyperframes/core` is
  not a dependency of the published `hyperframes` CLI package and appears in no npx cache. The CLI
  *does* bundle the parser, but exposes it through **no subcommand** — it is absent from `--help`,
  from `info --json` and from the dist command set, and the CLI entry module exports nothing. The
  only execution route to the canonical parser is the Studio HTTP read API behind `preview`, which
  needs a live server and therefore belongs in the same browser-gated tier as
  `CHECK_DEPRECATION_SIGNAL`, not the stdlib suite. The port declares itself a faithful copy kept
  in lockstep with core; a port/core divergence is the residual risk this probe does not cover, so
  re-read `STORYBOARD_FORMAT` at every lock bump anyway.
- **Residual limits.** Both halves skip when the ecosystem is not installed. The round trip also
  skips with no `node` on PATH, and with it goes *alias* detection: an official alias (a synonym of
  `scene:` or `voiceover:`) captures a bullet into a named field, which only the execution half
  sees. The probed key set is the fourteen director keys, read from their single source
  `reasoning/scene-analysis.md`; the capture bindings and frontmatter fields owned by
  `templates/storyboard.md` are exercised only as a representative sample, so a collision against
  one of those is caught by the execution half and not by the documented-contract half.

### `SUBCOMP_ROOT_ATTRIBUTE_SELECTOR` — the scene templates' root styling survives scoping

- **What.** A sub-composition may style its own root with a leftmost
  `[data-composition-id="<id>"] { … }` rule, and reach its descendants with
  `[data-composition-id="<id>"] .child`, without carrying `id="root"`. Both match after the render
  pipeline scopes the sub-composition's CSS.
- **Why it matters.** All seven `templates/scene-*.html` and both Phase-3 skeletons use exactly
  that pattern. `SUB_COMPOSITIONS` § "Pitfall 3" says to style the root by `#root`, "never a
  class", and lints a violation as `subcomposition_root_styled_by_class`. Whether an *attribute*
  selector falls under that rule was unresolved and load-bearing: if it did, every scene in every
  generated project would render unstyled while the storyboard, the timeline and the gates all
  looked correct — the "all gates green, output wrong" failure this repo keeps meeting.
- **Probe.** Build a two-scene composition: scene A styles its root by the bare attribute selector
  with no `id="root"`, scene B by `#root`. Give each a distinct saturated background and a
  descendant-selector child. Snapshot both times and sample the centre pixel; a scene whose CSS
  failed to apply shows the page background instead of its own.
- **Status: verified empirically on CLI 0.7.87, macOS, hardware GPU.** Scene A rendered
  `#ff0000` with its descendant-styled label painted and its flex centring applied — its root rule
  and its descendant rules both matched. Scene B rendered green as expected. `lint` returned
  **0 errors**, and `subcomposition_root_styled_by_class` did not fire on either scene: the rule
  targets a class on the root, not an attribute selector. **The templates are correct as shipped.**
  Not automated — it needs headless Chrome and a render, so it belongs in the same
  browser-gated tier as `CHECK_DEPRECATION_SIGNAL`. Re-run it if upstream changes how
  sub-composition CSS is scoped; the reproduction above is the whole test.

### `CHECK_DEPRECATION_SIGNAL` — deprecation is machine-detectable

- **What.** Deprecated gates keep working and announce themselves; `check` does not.
- **Why it matters.** This is *the* justification for feature-detection over version-sniffing. It
  lets the skill notice a command has been deprecated without knowing which release did it.
- **Probe (two-sided — both halves are required).**
  - `npx hyperframes validate --json` → `_meta.deprecated === true`
  - `npx hyperframes check --json` → `_meta` has **no** `deprecated` key
  The absence on `check` is what makes the presence on an alias meaningful; probing only the
  alias would pass even if every command were flagged.
- **Status: automated-able, verified manually on 0.7.87.** All three aliases were run against
  `test/clip-sample`: `validate`, `inspect`, and `layout` each returned
  `_meta: {version, latestVersion, updateAvailable, deprecated: true}`; `check` returned the same
  `_meta` **without** `deprecated`. The stderr notice reads
  `'hyperframes validate' is deprecated and will be removed in a future release. Use 'hyperframes check' instead.`
  Not yet in `test/run.sh` (it needs headless Chrome, so it belongs in a network/browser-gated
  tier, not the pure-stdlib suite).

### `ANIMATION_MAP_LOCATION` — the verifier ships with the skill, not the CLI

- **What.** `ANIMATION_MAP` lives inside the `hyperframes-animation` **skill** directory, not in
  the CLI package, and has no `hyperframes <subcommand>` equivalent.
- **Why it matters.** Phase 4 Step 4.7 must resolve a *skill install home* to run it. That is a
  different resolution path from every other tool the phase invokes, and it broke once already
  when the monolith split moved the script. If upstream ever promotes it to a CLI subcommand, the
  resolver block becomes dead weight.
- **Probe.** `test -f "$ANIM_SKILL_DIR/scripts/animation-map.mjs"` after resolving
  `$SKILL_HOMES`; and `npx hyperframes --help` must **not** list an `animation-map` command.
- **Status: manual.** Verified on disk at authoring time. The same shape applies to
  `CONTRAST_REPORT` (`hyperframes-creative`) and `SEAM_VERIFIER` / `SEAM_STAMP`
  (`motion-doctrine`) — all three are skill-resident scripts with no CLI surface.

### `TRANSCRIBE_MODEL_DEFAULT` — the default model translates

- **What.** `transcribe`'s default model is `small.en`, which silently *translates* non-English
  audio into English rather than transcribing it.
- **Why it matters.** A non-English voiceover produces plausible-looking English captions and
  every gate passes. Silent, and wrong in a user-visible artifact.
- **Probe.** Manual: `--model` must be explicit at every `transcribe` call site in `workflows/`.
- **Status: manual.** Documented upstream in `TRANSCRIBE`.

### `SKILL_SPLIT_TOPOLOGY` — the registry itself

- **What.** Every path in the registry above still exists under a resolved `$SKILL_HOMES` entry.
- **Why it matters.** This is the failure that motivated ADR-007: a relayout invalidates pointers
  with zero local signal.
- **Probe.** The **pointer-validity suite** — assert every skill-relative path in this file
  resolves, every SYMBOL cited elsewhere in the repo is defined here, and every bare
  rule/blueprint citation in the reasoning layer resolves against the two upstream indexes.
- **Status: IMPLEMENTED.** `test/unit/test_compat_pointers.py` runs inside `test/run.sh` and
  asserts both directions (registered path resolves; cited SYMBOL is defined), the
  no-paths-outside-the-map rules, the row-shape and enumerated-file-count rules, and — since M1 —
  recipe-citation resolution plus the published rule/blueprint counts. `grammar/` and `reasoning/`
  are inside both the path surface and the symbol surface; see § Citing upstream vocabulary for
  the three scan lists.
- **Residual limits** — real, and none of them a coverage gap this file can close by itself:
  - Path and citation *resolution* **skip** when no HyperFrames install is found under any
    `$SKILL_HOMES` entry. The ecosystem is optional at test time, so a green suite on a bare
    machine proves the shape rules, not the pointers.
  - The four single-word symbols (`PALETTES`, `TRANSCRIBE`, `BGM`, `SFX`) are deliberately never
    collected from prose — an underscore-free grammar produces more false positives than it
    catches. Their rows are still covered by the path and row-shape rules.
  - `templates/` sits in the symbol surface but in **neither** the path surface nor the
    recipe-citation surface, so a leaked upstream path or an invented recipe name in a template
    that gets copied into every generated project is invisible today.
  - A resolving path proves the file still exists, never that the capability still lives in it. A
    silent *content* move stays a manual read at lock-bump time.

---

## Pin and update policy

**The pin.** `skills-lock.json` at the repo root records, per installed skill, its source
(`heygen-com/hyperframes`), the `skillPath` it was installed from, and a `computedHash`.

> **Known limitation — read before trusting the lock.** The lock hashes **one file per skill**
> (that skill's `SKILL.md`). It is structurally blind to a relayout of `references/*`,
> `transitions/*`, `rules/*`, or `scripts/*` — which is *precisely* the churn that broke
> `patterns/INDEX.md`. The lock detects skill-level identity drift; only the **pointer-validity
> suite** protects this registry. Do not treat a matching hash as evidence that the paths above
> still resolve.

**Update procedure.**

1. `npx hyperframes skills update` — updates the core set plus every already-installed HyperFrames
   skill, and removes any no longer published. **Gotcha:** with no skill names passed it *never
   expands a partial install*, so a newly-required skill will not appear until you name it
   explicitly (`npx hyperframes skills update <name>`).
2. Re-verify every path in this file — the pointer-validity suite does this; it is part of step 3.
3. `bash test/run.sh` — the stdlib suite, including the question-contract tests.
4. Re-run the `CHECK_DEPRECATION_SIGNAL` probe (needs headless Chrome; not in `test/run.sh`).
5. Commit the new `skills-lock.json` **only when all of the above are green.** Hash drift without
   a green suite is a failure, not a rubber stamp.

**Cadence and ownership.** Lock bumps happen at milestone boundaries **or monthly, whichever
comes first**. Owner: the maintainer.

**Feature-detect, never version-sniff.** Probe the capability, not the release number:

| Question | Probe | Fallback |
|---|---|---|
| Is this command deprecated? | `--json` → `_meta.deprecated === true` | Treat absent key as "current" |
| Is the environment render-ready? | `hyperframes doctor --json` | Report, do not work around |
| Is `check` available? | `hyperframes check --help` exits 0 | `lint` + the deprecated trio, with a loud warning |

Branching on `_meta.version` is banned. It encodes today's release into prompt text that nobody
re-reads, which is the failure mode this whole file exists to prevent.
