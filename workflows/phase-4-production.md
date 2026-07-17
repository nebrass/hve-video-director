# Phase 4: Production (HyperFrames composition)

Assemble the storyboard, screenshots, and Phase 3 scene templates into a single HyperFrames composition. Output is a `index.html` at the project root that can be previewed in a browser and rendered to MP4.

## Step 4.1: Initialize the Project

By the time you reach Phase 4, `{project-dir}/` already has `DESIGN.md` and `scenes/*.html` from Phase 3. `npx hyperframes init {project-dir}` would clobber those files. **The supported flow is to skip `init` for hve-spielberg projects** — author `index.html` directly in the existing directory.

You only need three things in the project directory to render:

```
{project-dir}/
├── index.html           ← write this in Step 4.4 below
├── scenes/*.html        ← from Phase 3
└── (audio files)        ← from Phase 5
```

`npx hyperframes` (no local install required) handles `lint`, `inspect`, `validate`, `preview`, and `render`. If you want to run the bundled verification scripts (`animation-map.mjs`, `contrast-report.mjs` — see Step 4.7), install the package locally first:

```bash
npm init -y                              # one-time, creates package.json
npm install hyperframes                  # installs into node_modules/
```

After that, both CLI subcommands and bundled scripts work. The local install is optional — skip it if you don't plan to run animation-map.

### Starter templates (reference only; not used in the hve-spielberg flow)

If you're building a HyperFrames project *outside* hve-spielberg from scratch, `npx hyperframes init <dir>` supports `--example <name>` to seed with a richer starter than `blank`:

| Template | Best for |
|---|---|
| `blank` | Default — minimal scaffold |
| `product-promo` | Marketing |
| `warm-grain` | Editorial / documentary tone |
| `swiss-grid` | Clean SaaS / data-heavy |
| `vignelli` | Modernist typography |
| `play-mode` | Playful / kinetic |
| `kinetic-type` | Type-driven hero |
| `decision-tree` | Explainers / flow diagrams |
| `nyt-graph` | Data-viz / chart-heavy |

These are useful as reference compositions to study. **Don't run `init` against `{project-dir}/` itself** — it will overwrite Phase 3 output.

## Step 4.2: Pull Catalog Blocks (Optional but Recommended)

HyperFrames ships a **catalog of pre-built, drop-in blocks** that handle the most common motion-design needs. Pulling a block via `npx hyperframes add <name>` copies a ready-to-wire sub-composition into your project. This is the conventional path used by first-party HyperFrames templates — composing catalog blocks is usually faster and more polished than authoring transitions and effects from scratch.

Most useful blocks for hve-spielberg productions:

| Block | What it is | Use For |
|---|---|---|
| `flash-through-white` | Hard cut with brief white flash | Punchy section changes |
| `chromatic-radial-split` | RGB-shifted radial wipe | Cinematic moments |
| `cinematic-zoom` | Shader zoom transition | Hero reveals |
| `shimmer-sweep` | Diagonal shine sweep (similar to our metallic-swoosh) | Premium beats |
| `grain-overlay` | Film-grain texture overlay | Atmosphere on dark scenes |
| `logo-outro` | Wordmark assembly + bloom glow | Closing card |
| `app-showcase` | Three-phone / desktop hybrid frame | Product feature scenes |
| `ui-3d-reveal` | UI panel flies in from z-depth | Screenshot reveals |
| `data-chart` | Animated bar/line chart | Stat/proof scenes |
| `reddit-post` | Stylised social-card overlay | Pull-quotes, social proof |

```bash
# Pull a few blocks at the start of Phase 4.
npx hyperframes add flash-through-white
npx hyperframes add chromatic-radial-split
npx hyperframes add logo-outro
```

Each `add` drops a sub-composition file (typically under `blocks/` or `catalog/`) which you then wire into the root `index.html` via `data-composition-src`, exactly like a Phase 3 scene template. The block's own `<template>` wrapper and registered timeline are already correct — you set its `data-start`, `data-duration`, `data-track-index` in the root composition.

When in doubt, prefer a catalog block over a hand-authored transition. The blocks have been tested for determinism, layout safety, and cross-aspect-ratio behaviour.

## Step 4.3: Reconcile Assets

Confirm the directory layout. The Phase 4 composition expects:

```
{project-name}/
├── DESIGN.md                  # from Phase 3
├── index.html                 # root composition (this phase)
├── scenes/                    # from Phase 3
│   ├── 00-title-card.html
│   ├── 01-pain-point.html
│   └── ...
├── public/screenshots/        # from Phase 2
└── package.json               # optional — only if you ran `npm install hyperframes`
                               #            in Step 4.1 to enable animation-map (Step 4.7)
```

Screenshots stay at `public/screenshots/` — referenced from `index.html` via relative `<img src="public/screenshots/…">` tags.

## Step 4.4: Build the Root Composition

`index.html` is a single HyperFrames composition whose total duration equals the storyboard total. Standalone compositions (the root) do **not** use a `<template>` wrapper — the `data-composition-id` div sits directly in `<body>`. Sub-compositions loaded via `data-composition-src` are the only ones that need `<template>`.

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div id="root"
       data-composition-id="main"
       data-width="1920"
       data-height="1080"
       data-start="0"
       data-duration="42">
    <!-- data-width / data-height MUST match the Phase 1 aspect choice and
         every scene template's own data-width / data-height. Supported:
           16:9 → 1920×1080  (default, horizontal)
           9:16 → 1080×1920  (vertical / TikTok / Reels / Shorts)
           1:1  → 1080×1080  (square)
           4:5  → 1080×1350  (portrait IG feed) -->

    <!-- Audio (voiceover + music mixed in Phase 5).
         `id` is required — HyperFrames lint flags <audio> elements without
         an id, and the renderer silently drops audio that lacks one. -->
    <audio id="audio-main" data-start="0" data-duration="42" data-track-index="0"
           src="voiceover-with-music.mp3"></audio>

    <!-- Scene clips. CRITICAL invariants:
           1. data-composition-id on the loader must match the inner sub-comp's id.
           2. Adjacent scenes must OVERLAP during the crossfade window — each scene's
              data-duration extends 0.4s past its nominal end, and the next scene's
              data-start moves 0.4s earlier. Both render during the transition;
              otherwise the body color flashes through.
           3. Track indices must be UNIQUE for overlapping scenes — HyperFrames
              rejects same-track overlap. Use 1,2,3,4,5 (or any unique integers).
              data-track-index doesn't drive visual layering — DOM order does (with
              same z-index, later elements paint on top).
    -->

    <!-- Scene 0  (0 → 5.4) — extended 0.4s past nominal end -->
    <div data-composition-id="scene-00-title-card"
         data-composition-src="scenes/00-title-card.html"
         data-start="0"  data-duration="5.4" data-track-index="1"></div>

    <!-- Scene 1  (5 → 9.4) — starts 0.4s early, ends 0.4s late -->
    <div data-composition-id="scene-01-pain-point"
         data-composition-src="scenes/01-pain-point.html"
         data-start="5"  data-duration="4.4" data-track-index="2"
         style="opacity:0"></div>

    <!-- Scene 2  (9 → end) -->
    <div data-composition-id="scene-02-feature"
         data-composition-src="scenes/02-feature.html"
         data-start="9"  data-duration="6.4" data-track-index="3"
         style="opacity:0"></div>
    <!-- … etc … -->
  </div>

  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js" integrity="sha384-sG0Hv1tP1lZCk9KQmrIbY/XNwi+OY84GQqhMscbnsoBFqAz8KNCil1kvfL3Hbbk2" crossorigin="anonymous"></script>
  <script>
    // The root composition needs a registered timeline too, even if it only
    // hosts inter-scene transitions and ambient effects.
    window.__timelines = window.__timelines || {};
    const tl = gsap.timeline({ paused: true });

    // Crossfade pattern: ONLY animate the INCOMING scene's opacity 0→1.
    // The outgoing scene stays at opacity 1 below and is occluded as the
    // incoming one rises. Don't fade both simultaneously — that lets the
    // body color show through compositing math and creates a flash artifact.

    tl.to('[data-composition-id="scene-01-pain-point"]',
      { opacity: 1, duration: 0.4, ease: "power2.inOut" }, 5);
    tl.to('[data-composition-id="scene-02-feature"]',
      { opacity: 1, duration: 0.4, ease: "power2.inOut" }, 9);
    // … etc per scene boundary

    window.__timelines["main"] = tl;
  </script>
</body>
</html>
```

Use the `hyperframes` skill for the composition authoring rules — the most important invariants:

- **Standalone root** has no `<template>` wrapper; sub-compositions do.
- Every clip has `data-start`, `data-duration`, `data-track-index`. Times are seconds; sub-second precision is fine (e.g. `data-duration="0.4"`).
- Visual clips share track index 1 or higher; audio uses track 0; transitions sit on a separate high track (e.g. 9) only to avoid same-track overlap — paint order is controlled by CSS `z-index` (and DOM order when `z-index` is equal), NOT by the track index (see the CRITICAL invariant above and `patterns/metallic-swoosh.md`).
- Layout the resting state first; add motion only after `npx hyperframes inspect` reports zero overlaps at any sampled timestamp.

### Clip scenes (footage timing)

- A clip scene's root-loader `data-duration` = the clip's on-screen length =
  `(out − in) / speed` (from the storyboard `Clip in/out` + `Speed`). Set the
  scene window from the footage — do **not** stretch a clip scene to fit VO; VO
  is written to fit the footage-derived window in Phase 5.
- **Each clip scene's inner `<video>` carries its own timing** — `id` + `data-start="0"`
  + `data-duration` + `data-media-start` + `data-track-index="0"`. The runtime
  only frame-syncs videos that have `data-start`; without it the clip isn't synced and, with
  2+ clip scenes, cross-routes (one scene plays another's footage, another plays black). The
  `scene-clip.html` / `scene-terminal-clip.html` archetypes pre-wire this — keep it.
  - The inner video's `data-duration` = the **loader's full window incl. the 0.4s crossfade
    extension** (Step 4.5), NOT the bare clip length — the runtime hides an expired track
    (`visibility:hidden`), so a video that ends at the nominal length blanks the frame during
    every crossfade out of the scene.
  - `data-media-start` = the storyboard's `Clip in` (trim offset, seconds; `0` if whole).
    Omitting it plays the source from `t=0`, discards the `Clip in/out` trim, and desyncs the
    footage from Phase 5's clip-audio window (`CIN`/`COUT`, Step 5.3a).
  - Set `defaultPlaybackRate` and `playbackRate` on the `<video>` to the storyboard `Speed`;
    reject values outside **0.1–5.0**, which HyperFrames clamps internally. Scene duration,
    footage, and clip-own audio must all use the same speed.
- A rigid real-time clip (e.g. a live command run) sets its own budget: keep it at
  `Speed: 1.0` and size the scene to the real length; speed-ramp **only** explicitly
  marked dead air.
- Overlays on a clip scene (captions, punch-in zoom, cursor emphasis) are keyed to
  **footage timecodes**; if `Speed` ≠ 1, remap those keys proportionally.
- **Promo framing check (orchestrator-enforced):** when `Mode: promo`, every clip
  scene MUST use the device-frame wrapper — bare-edge footage is not allowed in
  promo. Verify by eye in `npx hyperframes inspect` before advancing. (There is no
  programmatic gate; see spec §5.5/§14.)
- **Legibility check (orchestrator-enforced, spec §7.2a):** narrative-critical UI text in footage must read ≥24px effective in the rendered frame. If raw capture is below that, add a footage-time punch-in on the `.clip-frame` wrapper (see `patterns/visual-patterns.md` § Camera Moves on Stills — the "When footage text is too small" subsection). Verify by eye in `npx hyperframes inspect . --at <focal-t>`; there is no programmatic gate.
- **Segment cap (spec §7.2b, orchestrator-enforced):** no continuous instructional run exceeds ~90s without an authored recap beat. Insert a `scenes/NN-recap.html` (from `templates/scene-recap.html`) listing the steps just covered, then resume. Self-police; no programmatic gate.

## Step 4.5: Wire Transitions

Default to a quiet crossfade. Use `patterns/metallic-swoosh.md` only at major narrative beats (≤2 per video in a 30–60s spot). Transition timing rules:

- Crossfade: 0.3–0.5s, `power2.inOut`
- Metallic swoosh: 0.4s, see pattern doc
- No `clipPath` transitions (anti-aliased black slivers).
- No 3D rotations on transitions.
- The closing scene never transitions out — it ends on its final frame.

## Step 4.6: Preview

Open the composition in the HyperFrames Studio (headless Chrome + scrubbable timeline UI). The studio lists every composition in the project — `main` plus each scene sub-composition — so you can scrub them individually:

```bash
npx hyperframes preview .
```

Iterate. Then run the three gates before moving on:

```bash
npx hyperframes lint     .                # project DIR, not a file — finds index.html (flags missing audio id, track overlaps, etc.)
npx hyperframes inspect  . --samples 10   # visual layout audit (no overlaps) — use 15 for dense cuts
npx hyperframes validate .                # WCAG AA contrast + console errors in headless Chrome
```

All gates take the project **directory** (they resolve `index.html` inside it), not a file path — `lint index.html` errors with "Not a directory". `lint` reports issues like "audio element has no id" by default. To fail a build on warnings, use `inspect --strict` or `render --strict` / `--strict-all` (`lint` and `validate` have no `--strict`).

`--samples` controls how many timestamps `inspect` seeks to. Typical convention: `--samples 10` for 30s spots, `--samples 15` for denser transition-heavy cuts. Use `--at 1.5,4,7.25` instead if you want to audit specific hero frames.

All three must pass cleanly (or report only overflows you've consciously marked intentional).

### Hero-frame content check (mandatory — gates can't see "wrong content")

`lint`, `inspect`, and `validate` are mechanical: structure, layout overflow, contrast. **None of them judges whether each scene is showing the *right* content** — a clip wired to the wrong footage or a stale `<img src>` passes all three GREEN (this is exactly how the bare-`<video>` clip cross-route shipped unnoticed). Catch it here, cheaply, *before* the full render in Phase 5.

Re-run `inspect` at the **midpoint of each scene** (not a uniform sweep) so every scene contributes one readable hero frame:

```bash
# Midpoints from the storyboard scene windows, e.g. scene 0 spans 0–5 → 2.5, etc.
npx hyperframes inspect . --at 2.5,7,12,18,24,30
```

Then **Read each `.hyperframes/inspect/*.png`** and confirm, scene by scene, that the frame shows what the storyboard calls for — correct screenshot, correct clip footage, correct copy. This re-uses the headless-Chrome frames `inspect` already writes (no `ffmpeg`, no rendered MP4 needed — the render doesn't exist until Phase 5). Do not advance until every scene's hero frame matches its storyboard intent.

**Capture-coverage backstop:** if `product_surface: ui`, confirm at least one hero frame shows a real on-screen capture (the product framed) — this is the visual confirmation of the Phase-3 capture-coverage gate (`SKILL.md` § Entry Modes → `jump`). A promo/showcase whose hero frames are all text/CTA means the spine never made it on screen; return to Phase 3.

Ask:

```json
{
  "questions": [{
    "question": "How does the composition look? Ready for voiceover and music?",
    "header": "Preview",
    "options": [
      { "label": "Looks good, proceed", "description": "Move to Phase 5: audio + render" },
      { "label": "Needs changes", "description": "I'll give feedback per scene" }
    ],
    "multiSelect": false
  }]
}
```

Iterate on feedback before proceeding.

## Step 4.7: Animation Map Verification (Optional)

Before the aesthetic critique, run the bundled `animation-map.mjs` script to get a structural audit of every tween in the composition. It outputs an ASCII Gantt timeline, flags problematic tweens, and surfaces dead zones (long intervals with no motion).

This step requires a local `hyperframes` install (`npm install hyperframes` — see Step 4.1). The script ships inside the npm package; it's not exposed as a CLI subcommand.

```bash
# One-time, if you haven't already:
[ -f package.json ] || npm init -y
[ -d node_modules/hyperframes ] || npm install hyperframes

# Run the script (HYPERFRAMES_SKILL_BOOTSTRAP_DEPS=1 is required on first run):
HYPERFRAMES_SKILL_BOOTSTRAP_DEPS=1 \
  node node_modules/hyperframes/dist/skills/hyperframes/scripts/animation-map.mjs . \
  --out .hyperframes/anim-map
```

(If you ran `npx hyperframes init`, the script is also copied to `skills/hyperframes/scripts/animation-map.mjs` in your project.)

The script reports:

- **Per-tween summaries** — every animation with start time, duration, properties, target
- **ASCII Gantt timeline** — visual overview of when each element animates
- **Flag tally** — counts of `paced-fast` (<0.2s, may feel rushed), `paced-slow` (>2s, may feel sluggish), `offscreen` (animation target outside canvas), `collision` (multiple animations on same property at same time), `degenerate` (zero-duration or no-effect), `invisible` (animates a hidden element)
- **Dead zones** — windows >1s with no animation (acceptable for "hold" beats; suspicious for active scenes)
- **Stagger detection** — confirms intentional staggers vs accidental uniform timing

Fix or justify each flagged tween. Examples:

- `paced-fast` on a critical reveal → extend duration to 0.4s+
- `paced-slow` on a hover/microinteraction → tighten to under 0.3s
- `collision` on `opacity` → almost always the `tl.from() + tl.to()` race bug — switch to `tl.fromTo()` (see `patterns/visual-patterns.md` § stagger trap)
- `dead zone` spanning a whole scene → either add ambient motion (cursor pulse, grain shimmer) or accept as a deliberate hold

Skip this step for trivial edits. Run on every new composition or after significant animation changes.

## Step 4.8: Aesthetic Critique (Optional but Recommended)

`hyperframes lint`, `inspect`, and `validate` are mechanical gates — they catch syntax errors, layout overflow, and contrast failures, but they cannot judge whether the composition is *good*. This step adds an aesthetic gate before Phase 5 commits the design with voiceover.

### If the `critique` skill is installed

Invoke it on the rendered composition's HTML + sampled screenshots:

```
Invoke: Skill(critique)
Context: "Run a 5-dimension review on the HyperFrames composition at index.html.
Sample inspect screenshots are at .hyperframes/inspect/*.png. Audit for:
- Philosophy (one declared direction, held through every decision)
- Hierarchy (does the eye know where to land?)
- Detail (timing, spacing, micro-decisions)
- Functionality (does it serve the message?)
- Innovation (does it feel like every other AI-generated promo?)"
```

The critique output is three lists:

- **Keep** — what's working; do not touch
- **Fix** — visually expensive issues (P0/P1); address before Phase 5
- **Quick wins** — 5-15 minute tweaks with disproportionate impact

If there are P0/P1 Fix items, iterate Step 4.4 / 4.5 / 4.6 then re-critique. Don't move to Phase 5 until the Fix list is empty or each remaining item is consciously accepted.

### If `critique` skill is not installed

Prompt the user with a self-review checklist instead:

```json
{
  "questions": [{
    "question": "Self-review checklist before audio — any of these feel off?",
    "header": "Critique",
    "multiSelect": true,
    "options": [
      { "label": "Generic AI feel", "description": "Does it look like every other AI-generated promo? (Purple gradients, three-word headlines, rounded squares everywhere, ungrounded floating cards.)" },
      { "label": "Hierarchy unclear", "description": "Does the eye know where to land first in each scene?" },
      { "label": "Timing feels mechanical", "description": "Are all entrances the same duration? Same ease? Same stagger?" },
      { "label": "Philosophy drifts", "description": "Does each scene feel like a different design direction?" },
      { "label": "Composition looks empty", "description": "Are key elements smaller than they should be? Padding too tight or too loose?" }
    ]
  }]
}
```

For each checked item, propose 1-2 fixes and iterate. See `patterns/anti-slop.md` for cross-cutting craft rules that catch most of these failure modes.

## Output

- `index.html` — root HyperFrames composition referencing every Phase 3 scene template
- Passing `lint` + `inspect` + `validate` runs
- (If `critique` skill ran) Empty Fix list or consciously-accepted residual items

## Checkpoint

> "Composition built. [N] scenes, [duration]s, all screenshots integrated. `hyperframes inspect` and `validate` pass. Aesthetic critique complete.
>
> Ready to move to Phase 5: Audio & Render?"
