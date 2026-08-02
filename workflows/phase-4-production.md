# Phase 4: Production (HyperFrames composition)

Assemble the storyboard, screenshots, and Phase 3 scene templates into a single HyperFrames composition. Output is a `index.html` at the project root that can be previewed in a browser and rendered to MP4.

Before assembly, require the accepted design artifacts to match the current story fingerprint:

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" require phase-3
```

A nonzero exit routes back to the earliest stale phase even when `DESIGN.md` and `scenes/` exist.

## Step 4.1: Initialize the Project

By the time you reach Phase 4, `{project-dir}/` already has `DESIGN.md` and `scenes/*.html` from Phase 3. `npx hyperframes init {project-dir}` would clobber those files. **The supported flow is to skip `init` for hve-video-director projects** — author `index.html` directly in the existing directory.

You only need three things in the project directory to render:

```
{project-dir}/
├── index.html           ← write this in Step 4.4 below
├── scenes/*.html        ← from Phase 3
└── (audio files)        ← from Phase 5
```

`npx hyperframes` (no local install required) handles `lint`, `check`, `snapshot`, `preview`, and `render`. The bundled generation and verification scripts ship with the companion skills rather than the CLI: `hyperframes-animation` → `ANIMATION_MAP` (Step 4.7), `hyperframes-creative` → `CONTRAST_REPORT`, and `motion-doctrine` → `SEAM_STAMP` + `SEAM_VERIFIER` (Steps 4.5 and 4.6). Every path is registered in `compat/ecosystem.md`, and each script needs its owning skill's install directory resolved before it can run — there is no `hyperframes <subcommand>` equivalent for any of them.

### Starter templates (reference only; not used in the hve-video-director flow)

If you're building a HyperFrames project *outside* hve-video-director from scratch, `npx hyperframes init <dir>` supports `--example <name>` to seed with a richer starter than `blank`:

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

Most useful blocks for hve-video-director productions:

| Block | What it is | Use For |
|---|---|---|
| `flash-through-white` | Hard cut with brief white flash | Punchy section changes |
| `chromatic-radial-split` | RGB-shifted radial wipe | Cinematic moments |
| `cinematic-zoom` | Shader zoom transition | Hero reveals |
| `shimmer-sweep` | Element-scoped gradient shine (a *component*, **not** a seam) | In-scene card/text accents only |
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

Use a catalog block only when it implements the confirmed transition style and can be retokenized
to the confirmed theme without changing its identity. The user's `transition_style`,
`transition_speed`, and `theme` always win; never introduce a white flash into a dark composition
or an unselected transition because a block is convenient.

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
└── public/screenshots/        # from Phase 2
```

Screenshots stay at `public/screenshots/` — referenced from `index.html` via relative `<img src="public/screenshots/…">` tags.

## Step 4.4: Build the Root Composition

`index.html` is a single HyperFrames composition whose total duration equals the storyboard total. Standalone compositions (the root) do **not** use a `<template>` wrapper — the `data-composition-id` div sits directly in `<body>`. Sub-compositions loaded via `data-composition-src` are the only ones that need `<template>`.

Read `theme`, `transition_style`, and `transition_speed` from the confirmed Creative Brief before
writing the root. Resolve the root canvas and every transition overlay from the single
confirmed-theme token set in `DESIGN.md`; no root, loading, or overlap frame may expose an
opposite-theme default. Map speed exactly once: `quick = 0.4s`, `medium = 0.7s`, `slow = 1.2s`.
Call that value `D` — it is the whole seam's time budget at every boundary. Replace every uppercase
color and timing token below with computed literals before linting.

**Loader windows follow the boundary kind, and Step 4.5 decides which kind each boundary is.**
Write the ledger first, then size the loaders from it:

- **Cut boundary** (a row in the seam ledger) — the cut is instantaneous, so the two scenes never
  co-exist. The outgoing loader ends at the cut time; the incoming loader's `data-start` **is** the
  cut time and is never earlier. Read `SEAM_LAW`'s clip-gating note before setting either value —
  a loader that opens before its entry tween is un-hidden at its initial state and fails the
  zero-overlap check, which is the single most common seam-gate failure.
- **Dissolve boundary** (no ledger row — `crossfade`, `metallic-swoosh`) — both scenes must be
  alive together. The outgoing loader stays alive `D` past its nominal end, the incoming starts at
  the nominal boundary, and both render through the window; otherwise the canvas flashes through.

A clip scene's inner `<video>` always mirrors *its own loader's* full window, whichever model that
loader follows. Paint `#root` opaque in the confirmed theme — a render prerequisite, not a style
choice; `SEAM_RENDER_MECHANICS` (`seam-craft`) explains which seam windows open a summed-opacity
gap and why an unpainted root flashes white through it.

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="styles.css">
  <style>
    html, body { margin: 0; background: THEME_CANVAS; }
    /* Opaque stage ground — required, see SEAM_RENDER_MECHANICS. */
    #root { background: THEME_CANVAS; }
  </style>
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
           2. Loader windows come from the boundary kind (see above), so size them
              AFTER the seam ledger exists: a cut boundary ends the outgoing loader
              at the cut and opens the incoming loader ON the cut; a dissolve
              boundary overlaps the two by D or the canvas flashes through.
           3. Track indices must be UNIQUE for overlapping scenes — HyperFrames
              rejects same-track overlap. Use 1,2,3,4,5 (or any unique integers).
              data-track-index doesn't drive visual layering — DOM order does (with
              same z-index, later elements paint on top).
           4. Initial hidden state has ONE owner per scene. A scene named in the
              ledger gets its base state from SEAM_STAMP — leave its inline style
              off. A scene reached only by a dissolve keeps style="opacity:0".
              Declaring it twice is how a scene ships permanently invisible with
              every gate green.
    -->

    <!-- Scene 0 nominally spans 0 → 5. -->
    <div data-composition-id="scene-00-title-card"
         data-composition-src="scenes/00-title-card.html"
         data-start="0" data-duration="SCENE_00_LOADER_WINDOW"
         data-track-index="1"></div>

    <!-- Scene 1 nominally spans 5 → 9. Ledgered scene: no inline opacity. -->
    <div data-composition-id="scene-01-pain-point"
         data-composition-src="scenes/01-pain-point.html"
         data-start="SCENE_01_CUT_IN" data-duration="SCENE_01_LOADER_WINDOW"
         data-track-index="2"></div>

    <!-- Closing scene: nominal duration only; it never seams out.
         Reached by a dissolve here, so it owns its own initial state. -->
    <div data-composition-id="scene-02-feature"
         data-composition-src="scenes/02-feature.html"
         data-start="9" data-duration="SCENE_02_NOMINAL"
         data-track-index="3"
         style="opacity:0"></div>
    <!-- … etc … -->
  </div>

  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js" integrity="sha384-sG0Hv1tP1lZCk9KQmrIbY/XNwi+OY84GQqhMscbnsoBFqAz8KNCil1kvfL3Hbbk2" crossorigin="anonymous"></script>
  <script>
    // The root composition needs a registered timeline too, even if it only
    // hosts the seams and ambient effects.
    window.__timelines = window.__timelines || {};
    const tl = gsap.timeline({ paused: true });

    // <seams:auto>
    // SEAM_STAMP owns everything between these two markers: base states plus
    // every seam tween, generated from ledger.json in Step 4.5. Leave the
    // markers in place and never hand-edit between them — a re-stamp discards
    // whatever is here. If the markers are missing the stamper appends its
    // block after the registration below instead.
    // </seams:auto>

    // Everything hand-authored goes BELOW the markers so a re-stamp cannot
    // clobber it: dissolve boundaries (no ledger row), the carrier handoff of
    // a match-cut / morph row, and ambient root-level effects.
    // Keep the next four lines ONLY if the film has at least one dissolve
    // boundary, and substitute the token. Delete them outright when every
    // boundary is a stamped cut — an unsubstituted token throws at load and
    // fails `check` on a composition that never needed D.
    const D = Number("TRANSITION_DURATION_SECONDS");
    if (!Number.isFinite(D) || D <= 0) {
      throw new Error("Replace TRANSITION_DURATION_SECONDS from transition_speed");
    }

    window.__timelines["main"] = tl;
  </script>
</body>
</html>
```

Use the `hyperframes` skill for the composition authoring rules — the most important invariants:

- **Standalone root** has no `<template>` wrapper; sub-compositions do.
- Every clip has `data-start`, `data-duration`, `data-track-index`. Times are seconds; sub-second precision is fine (e.g. `data-duration="0.4"`).
- Visual clips share track index 1 or higher; audio uses track 0; transitions sit on a separate high track (e.g. 9) only to avoid same-track overlap — paint order is controlled by CSS `z-index` (and DOM order when `z-index` is equal), NOT by the track index (see the CRITICAL invariant above; track/clip timing is `TRACKS_AND_CLIPS`, seam compositing is `SEAM_RENDER_MECHANICS`).
- Layout the resting state first; add motion only after `npx hyperframes check` reports zero overlaps at any sampled timestamp.

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
  - The inner video's `data-duration` = **its own loader's full window** — read it off the loader
    you sized in Step 4.4, not off the bare clip length, and not off a nominal scene length. The
    runtime hides an expired track (`visibility:hidden`), so a video that ends before its loader
    blanks the frame for the rest of the scene's window, including its seam out.
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
  promo. Verify by eye in `npx hyperframes snapshot` before advancing. (There is no
  programmatic gate; see spec §5.5/§14.)
- **Legibility check (orchestrator-enforced, spec §7.2a):** narrative-critical UI text in footage must read ≥24px effective in the rendered frame. If raw capture is below that, add a footage-time punch-in on the `.clip-frame` wrapper (see `patterns/visual-patterns.md` § Camera Moves on Stills — the "When footage text is too small" subsection). Verify by eye in `npx hyperframes snapshot . --at <focal-t>`; there is no programmatic gate.
- **Segment cap (spec §7.2b, orchestrator-enforced):** no continuous instructional run exceeds ~90s without an authored recap beat. Insert a `scenes/NN-recap.html` (from `templates/scene-recap.html`) listing the steps just covered, then resume. Self-police; no programmatic gate.

## Step 4.5: Author and Stamp the Seams

Seams belong to `motion-doctrine`. Load it before writing a single transition tween: `SEAM_LAW` is
the vector law (axis, direction, speed, phase), the film's current, carriers, causal motion, and
the build gate. It routes to `cut-the-curve` for technique parameters (`CUT_CATALOG`) and to
`seam-craft` for render-side compositing (`SEAM_RENDER_MECHANICS`). **`SEAM_LAW` supersedes the
selection guidance in `patterns/transition-catalog.md` wherever the two disagree.** It does *not*
supersede a confirmed Creative Brief field — see the dissolve case below.

Follow upstream's authoring order exactly, and do not reorder it: **vector ledger → stamp the
master seams → name a sustained-motion route per scene → carriers and causes → build the comps →
verify.** Verification is the last rung of the Step 4.6 gate ladder, after `check`.

### What this workflow still decides

Upstream owns *how* a seam is built and *whether* it is correct. Three decisions stay here:

1. **Which boundary gets which technique** — a narrative call, read off the storyboard's
   `Transition to next` and the adjacent frames' `energy:` keys. The tone → transition table in
   `reasoning/scene-analysis.md` is the prior.
2. **The energy budget** — transition types per film, cited from the budget table in
   `reasoning/scene-analysis.md`. That table is the only place those numbers live; never copy one
   into this file or into a scene.
3. **The film's current** — one dominant direction, chosen once for the whole film. `SEAM_LAW`
   owns what each vector *means* and when a reserved one may be spent; deciding which beat is worth
   spending it on is a story judgment, and it is ours.

Everything else — travel distances, ease pairs, blur values, exit/entry ratios, the Z scale-sign
rule — is `CUT_CATALOG`'s, read there per seam and never restated in this repo (ADR-002).

### Classify every boundary before writing anything

The storyboard is authoritative at each boundary and already carries the confirmed
`transition_style` / `transition_speed`: main section boundaries use the chosen style, connective
cuts inside a section use `crossfade`, and the closing scene uses `none`. Never quietly downgrade a
confirmed `zoom-through`, `slide-from-bottom`, `medium`, or `slow`.

`D` is the seam's whole time budget (`quick / medium / slow` mapped once in Step 4.4). Split it
into the row's exit and entry durations using the ratio the chosen technique states in
`CUT_CATALOG`. Honor the confirmed pacing — do not clamp a confirmed `slow` down to a technique's
nominal total.

| Storyboard boundary | Seam kind | Ledger row? |
|---|---|---|
| `zoom-through` | velocity-matched Z cut | yes — a `cut` row on the Z axis |
| `slide-from-bottom` | velocity-matched Y cut; both sides travel the incoming scene's direction | yes — a `cut` row on the Y axis |
| `crossfade` | dissolve | **no** |
| `metallic-swoosh` (crossfade + shine) | dissolve | **no** |
| `none` — the closing scene | not a seam; hold the final frame | no |

A cut boundary where one concrete element genuinely persists across it — the same card, cursor, or
mark — is stronger as a `match-cut` or `morph` row carrying that carrier pair. That is an upgrade
within the confirmed style, not a substitute for it: the vector still runs in the confirmed
direction.

A dissolve cannot be a ledger row, and that is structural rather than an omission: a `cut` row has
to show zero overlap and a match-cut/morph row has to name a carrier, and a dissolve has neither by
definition. `SEAM_LAW` classes a carrier-less dissolve as an anti-pattern for that same reason.

**State the consequence out loud, because the gate will not.** When the confirmed
`transition_style` is `crossfade` or `metallic-swoosh`, *every* boundary in the film is a dissolve,
`ledger.json` is empty, and the verifier reports zero seams and exits 0 — a green gate that
verified nothing. Even under `zoom-through` or `slide-from-bottom`, the connective cuts inside a
section remain dissolves and remain unverified. Count the unverified boundaries and report the
number at the Step 4.6 checkpoint every time.

Recommend the velocity-matched alternative — it is the only route to a numerically verified film —
then comply with whatever the user decides (ADR-001). Changing `transition_style` is a **Phase-1
brief revision**: it re-stales the story fingerprint and needs re-confirmation and a re-stamp, so
never rewrite the field from inside Phase 4.

### Resolve the seam tooling

`SEAM_STAMP` and `SEAM_VERIFIER` ship inside the `motion-doctrine` skill; neither is a
`hyperframes` subcommand. Resolve that skill's install directory the same way Step 4.7 resolves
`hyperframes-animation`:

```bash
# $SKILL_HOMES is the canonical home list defined in SKILL.md § Runtime Compatibility.
# Keep this line identical to that definition; edit it there, not here.
SKILL_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SKILL_HOMES="$HOME/.claude/skills|$HOME/.copilot/skills|$HOME/.agents/skills|$HOME/.pi/agent/skills|$HOME/.config/opencode/skills|$HOME/.cursor/skills|$HOME/.codex/skills|/etc/codex/skills|.claude/skills|.github/skills|.agents/skills|.pi/skills|.opencode/skills|.cursor/skills|.codex/skills|$SKILL_ROOT/.claude/skills|$SKILL_ROOT/.github/skills|$SKILL_ROOT/.agents/skills|$SKILL_ROOT/.pi/skills|$SKILL_ROOT/.opencode/skills|$SKILL_ROOT/.cursor/skills|$SKILL_ROOT/.codex/skills"
DOCTRINE_SKILL_DIR=$(
  OLD_IFS=$IFS
  IFS='|'
  for h in $SKILL_HOMES; do
    [ -d "$h/motion-doctrine" ] && { echo "$h/motion-doctrine"; break; }
  done
  IFS=$OLD_IFS
)
[ -n "$DOCTRINE_SKILL_DIR" ] || { echo "WARN: motion-doctrine install dir not found — set DOCTRINE_SKILL_DIR manually, or take the degraded path below" >&2; }
node --version   # the verifier needs the minimum SEAM_GATE_REFERENCE states
```

Shell state does not survive between bash calls, so **every command block below re-runs that
resolver in the same call.** Each `<SYMBOL>` placeholder stands for that symbol's skill-relative
path — read it from `compat/ecosystem.md` and substitute it before running.

### Author `ledger.json`

Write it at the project root, one row per seam. `SEAM_GATE_REFERENCE` (`motion-doctrine`) owns the
field shape; read the schema there rather than inferring it. What *this* workflow supplies per row
is the storyboard boundary it stands for, its cut time on the master clock, the technique chosen
above, and the vector — the same axis and the same signed direction on both sides. Exit and entry
must agree in the **plan**; a mismatched row is fixed by fixing the plan, never by re-easing a tween.

**The first pass is not circular.** Draft the loaders in Step 4.4 at the storyboard's nominal
boundaries, write the ledger against the root-loader selectors you just gave them, then resize
those loaders from the ledger's cut times and stamp. A boundary may instead be carried by a hero
element *inside* the sub-composition; probing is how you correct such a row once the gate reports
the motion is not on the wrapper:

```bash
# Re-run the resolver above in this same call.
# Substitute <SEAM_VERIFIER> with its skill-relative path from compat/ecosystem.md.
node "$DOCTRINE_SKILL_DIR/<SEAM_VERIFIER>" probe --t CUT_TIME_SECONDS --project .
```

### Stamp the master seams

```bash
# Re-run the resolver above in this same call.
# Substitute <SEAM_STAMP> with its skill-relative path from compat/ecosystem.md.
node "$DOCTRINE_SKILL_DIR/<SEAM_STAMP>" --ledger ledger.json --write index.html
```

This rewrites the `<seams:auto>` block in the root composition (Step 4.4) with the base states and
every seam tween. **`cut` rows are generated in full and pass the gate by construction — do not
hand-tune them**; re-stamp after any ledger edit instead.

Exactly one thing is hand-authored: the **carrier handoff of a `match-cut` or `morph` row**. The
stamper emits only visibility sets for those rows, so the handoff itself is yours, written below
the markers, and the gate still checks its carrier continuity and overlap. `SEAM_LAW` § transition
vocabulary states that hand-written shared-element morphs do not count against a transition
budget — apply that when counting against the budget table in `reasoning/scene-analysis.md`.

Dissolve boundaries are hand-authored below the markers too. When the confirmed style is
`metallic-swoosh`, the shine is a **full-frame light overlay** riding that dissolve — the light
family; take the implementation from `TRANSITION_FAMILIES`, size its window from `D`, and centre
the brightest moment on the dissolve window. **Not `shimmer-sweep`:** `REGISTRY_CATALOG` lists that
as an element-scoped *component* (`text, shimmer, highlight, effect`), not a seam — wired across a
boundary it decorates one element while every gate passes (see `patterns/transition-catalog.md`).

Three local rules survive the handover and bind everything you hand-author:

- Scene-internal timelines never own an exit. The seam is the exit; only the closing scene animates
  out (`TRANSITION_OVERVIEW` states the ban and its final-scene exception).
- No `clipPath` in any seam — it produces anti-aliased black slivers in this renderer
  (`patterns/visual-patterns.md` § DON'Ts records the finding and its cause).
- No 3D rotation and no perspective in a seam.

### When the seam tooling is unavailable

Feature-detect; never assume. The two scripts have different needs, so degrade in two tiers rather
than all-or-nothing:

| Detected | `SEAM_STAMP` | `SEAM_VERIFIER` | Do this |
|---|---|---|---|
| `motion-doctrine` under no `$SKILL_HOMES` entry | unavailable | unavailable | hand-author every seam from `CUT_CATALOG`; **all** boundaries unverified |
| `node --version` below the minimum in `SEAM_GATE_REFERENCE` | unavailable | unavailable | as above |
| no local Chrome — `npx hyperframes doctor --json` reports no usable browser | works | unavailable | stamp anyway; stamped seams still pass by construction, but **all** boundaries go unverified |

Environment diagnosis stays with `DOCTOR` (ADR-003) — do not add a parallel browser probe here.

A missing optional gate never blocks the pipeline. It does change what you are allowed to claim:
report at the Step 4.6 checkpoint which boundaries were stamped, which were verified, and which
went unverified and why. "All gates pass" is a false statement when the seam gate never ran.

## Step 4.6: Preview

Open the composition in the HyperFrames Studio (headless Chrome + scrubbable timeline UI). The studio lists every composition in the project — `main` plus each scene sub-composition — so you can scrub them individually:

```bash
npx hyperframes preview .
```

Iterate, re-running the fast static check after each structural change:

```bash
npx hyperframes lint . # project DIR, not a file — finds index.html (flags missing audio id, track overlaps, etc.)
```

Then run the required gate before moving on:

```bash
npx hyperframes check . --samples 10   # reruns lint, then audits layout (no overlaps), WCAG AA contrast,
                                       # console errors, and motion in one headless-Chrome pass — use 15 for dense cuts
```

Both take the project **directory** (they resolve `index.html` inside it), not a file path — `lint index.html` errors with "Not a directory". `lint` reports issues like "audio element has no id" by default; `check` reruns it, so don't chain a standalone `lint` immediately before `check`. To fail a build on warnings, use `check --strict` or `render --strict` / `--strict-all` (`lint` has no `--strict`).

`--samples` controls how many timestamps `check` seeks to. Typical convention: `--samples 10` for 30s spots, `--samples 15` for denser transition-heavy cuts. Use `--at 1.5,4,7.25` instead if you want to audit specific hero frames.

`check` must pass cleanly (or report only overflows you've consciously marked intentional).

### Seam gate (numeric — runs after `check`, before the hero-frame check)

The gate ladder is **`lint` → `check` → seam gate → hero-frame check → user approval**, and the
order is load-bearing: `check` proves the composition is structurally sound in a browser, the seam
gate then samples real motion at every cut, and only a composition that survives both is worth a
human's eyes.

```bash
# Re-run the Step 4.5 $DOCTRINE_SKILL_DIR resolver in this same call — shell state
# does not cross bash calls. Substitute <SEAM_VERIFIER> with its skill-relative
# path from compat/ecosystem.md.
node "$DOCTRINE_SKILL_DIR/<SEAM_VERIFIER>" verify --ledger ledger.json --project .
```

`--project` spawns a fresh preview server and kills it afterwards — prefer it, because it cannot
serve a stale bundle. Pass `--url <preview-url>` instead only to reuse the server `preview` is
already running, and restart that server after every composition edit or you will verify the
previous build. `--json` gives machine output.

Read the report per seam rather than only the exit code:

- **FAIL** — a real seam defect: a settled exit, an entry starting from rest, a measured direction
  that contradicts the ledger, both sides visible in one frame, a Z sign fight, or a carrier that
  jumps. Fix the **ledger row**, re-stamp (Step 4.5), and re-run; do not hand-patch a stamped tween.
- **WARN** — most often a speed mismatch. Judge it against the beat, but never silence it by
  editing the ledger to match the measurement.
- **`0 seams`** — not a pass. It means nothing was ledgerable; say so explicitly at the checkpoint.

Two rules the script cannot check, and which reopen a seam that already passed: **any edit to a
scene's opening or closing motion invalidates that boundary's audit**, and **audio is the clock** —
re-timing scenes to a new voiceover in Phase 5 reopens every seam it touches. `SEAM_LAW` states
both; re-run this gate after either.

If the seam tooling is unavailable, skip this gate per the degrade table in Step 4.5, and carry the
unverified-boundary count into the checkpoint below. A skipped optional gate does not block Phase 5.

### Hero-frame content check (mandatory — gates can't see "wrong content")

`lint` and `check` are mechanical: structure, layout overflow, contrast. **Neither judges whether each scene is showing the *right* content** — a clip wired to the wrong footage or a stale `<img src>` passes both GREEN (this is exactly how the bare-`<video>` clip cross-route shipped unnoticed). Catch it here, cheaply, *before* the full render in Phase 5.

Capture a `snapshot` at the **midpoint of each scene** (not a uniform sweep) so every scene contributes one readable hero frame:

```bash
# Midpoints from the storyboard scene windows, e.g. scene 0 spans 0–5 → 2.5, etc.
npx hyperframes snapshot . --at 2.5,7,12,18,24,30
```

Then **Read each PNG `snapshot` writes to the project's snapshots directory** and confirm, scene by scene, that the frame shows what the storyboard calls for — correct screenshot, correct clip footage, correct copy. These are headless-Chrome stills (no `ffmpeg`, no rendered MP4 needed — the render doesn't exist until Phase 5). Do not advance until every scene's hero frame matches its storyboard intent.

**Capture-coverage backstop:** if `product_surface: ui`, confirm at least one hero frame shows a real on-screen capture (the product framed) — this is the visual confirmation of the Phase-3 capture-coverage gate (`SKILL.md` § Entry Modes → `jump`). A promo/showcase whose hero frames are all text/CTA means the spine never made it on screen; return to Phase 3.

**Theme backstop:** confirm every hero frame, browser/terminal mockup, clip matte, root canvas, and
seam frame visibly matches the Creative Brief theme. Any opposite-theme default routes
back to Phase 3; do not approve it as an intentional contrast unless the Creative Brief itself is
changed and reconfirmed.

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

Before the aesthetic critique, run the `ANIMATION_MAP` verifier to get a structural audit of every tween in the composition. It outputs an ASCII Gantt timeline, flags problematic tweens, and surfaces dead zones (long intervals with no motion).

The script ships inside the `hyperframes-animation` skill (`ANIMATION_MAP` in `compat/ecosystem.md`); it's not exposed as a CLI subcommand. Resolve that skill's install directory the same way Phase 3 resolves this one:

```bash
# $SKILL_HOMES is the canonical home list defined in SKILL.md § Runtime Compatibility.
# Keep this line identical to that definition; edit it there, not here.
SKILL_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SKILL_HOMES="$HOME/.claude/skills|$HOME/.copilot/skills|$HOME/.agents/skills|$HOME/.pi/agent/skills|$HOME/.config/opencode/skills|$HOME/.cursor/skills|$HOME/.codex/skills|/etc/codex/skills|.claude/skills|.github/skills|.agents/skills|.pi/skills|.opencode/skills|.cursor/skills|.codex/skills|$SKILL_ROOT/.claude/skills|$SKILL_ROOT/.github/skills|$SKILL_ROOT/.agents/skills|$SKILL_ROOT/.pi/skills|$SKILL_ROOT/.opencode/skills|$SKILL_ROOT/.cursor/skills|$SKILL_ROOT/.codex/skills"
ANIM_SKILL_DIR=$(
  OLD_IFS=$IFS
  IFS='|'
  for h in $SKILL_HOMES; do
    [ -d "$h/hyperframes-animation" ] && { echo "$h/hyperframes-animation"; break; }
  done
  IFS=$OLD_IFS
)
[ -n "$ANIM_SKILL_DIR" ] || { echo "ERROR: hyperframes-animation install dir not found — set ANIM_SKILL_DIR to the skill's path manually" >&2; }

# Live path — registered as ANIMATION_MAP in compat/ecosystem.md; if upstream moves it, edit both.
node "$ANIM_SKILL_DIR/scripts/animation-map.mjs" . --out .hyperframes/anim-map
```

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

`hyperframes lint` and `check` are mechanical gates — they catch syntax errors, layout overflow, and contrast failures, but they cannot judge whether the composition is *good*. This step adds an aesthetic gate before Phase 5 commits the design with voiceover.

### If the `critique` skill is installed

Invoke it on the rendered composition's HTML + sampled screenshots:

```
Invoke: Skill(critique)
Context: "Run a 5-dimension review on the HyperFrames composition at index.html.
Sample hero-frame stills are in the project's snapshots directory. Audit for:
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
  "questions": [
    {
      "question": "Which composition issues still feel off?",
      "header": "Composition",
      "multiSelect": true,
      "options": [
        { "label": "Generic AI feel", "description": "Purple gradients, three-word headlines, rounded squares, or ungrounded floating cards." },
        { "label": "Hierarchy unclear", "description": "The eye does not know where to land first in a scene." },
        { "label": "Composition looks empty", "description": "Key elements are undersized or spacing feels unbalanced." }
      ]
    },
    {
      "question": "Which motion or consistency issues still feel off?",
      "header": "Motion",
      "multiSelect": true,
      "options": [
        { "label": "Timing feels mechanical", "description": "Entrances repeat the same duration, ease, or stagger." },
        { "label": "Philosophy drifts", "description": "Scenes feel like different design directions." }
      ]
    }
  ]
}
```

For each checked item, propose 1-2 fixes and iterate. See `patterns/anti-slop.md` for cross-cutting craft rules that catch most of these failure modes.

## Output

- `index.html` — root HyperFrames composition referencing every Phase 3 scene template, with its
  `<seams:auto>` block generated from the ledger
- `ledger.json` — the vector ledger at the project root, one row per ledgerable seam
- Passing `lint` + `check` runs, and a passing seam gate over every ledgered seam
- (If `critique` skill ran) Empty Fix list or consciously-accepted residual items

## Checkpoint

After the user accepts the preview and the HyperFrames gates pass, stamp Phase 4:

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" stamp phase-4
```

Do not advance on a nonzero exit.

Report the seam result honestly — the counts, not an adjective. If the gate did not run, name the
reason instead of the numbers.

> "Composition built. [N] scenes, [duration]s, all screenshots integrated. `hyperframes check` passes.
> Seams: [S] stamped and verified, [U] dissolve boundaries carrying no verified vector[, seam gate skipped — reason]. Aesthetic critique complete.
>
> Ready to move to Phase 5: Audio & Render?"
