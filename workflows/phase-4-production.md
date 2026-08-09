# Phase 4: Production (HyperFrames composition)

Assemble the storyboard, screenshots, and Phase 3 scene templates into a single HyperFrames composition. Output is a `index.html` at the project root that can be previewed in a browser and rendered to MP4.

Before assembly, require the accepted design artifacts to match the current story fingerprint:

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" require phase-3
```

A nonzero exit routes back to the earliest stale phase even when `DESIGN.md` and `scenes/` exist.

## Step 4.1: Initialize the Project

By the time you reach Phase 4, `{project-dir}/` already has `DESIGN.md` and `scenes/*.html` from
Phase 3, and `npx hyperframes init {project-dir}` would clobber both. **The supported flow skips
`init` entirely** — author `index.html` directly in the existing directory; to render you need only
that file, the Phase 3 `scenes/*.html`, and the Phase 5 audio (Step 4.3 has the full layout).
`INIT_SCAFFOLD` documents `init` and its starter examples for projects built *outside* this skill —
worth reading as reference compositions, but never run `init` against `{project-dir}/` itself.

`npx hyperframes` (no local install required) handles `lint`, `check`, `snapshot`, `preview`, and `render`. The bundled generation and verification scripts ship with the companion skills rather than the CLI: `hyperframes-animation` → `ANIMATION_MAP` (Step 4.7), `hyperframes-creative` → `CONTRAST_REPORT`, and `motion-doctrine` → `SEAM_STAMP` + `SEAM_VERIFIER` (Steps 4.5 and 4.6). Every path is registered in `compat/ecosystem.md`, and each script needs its owning skill's install directory resolved before it can run — there is no `hyperframes <subcommand>` equivalent for any of them.

## Step 4.2: Pull Catalog Blocks (Optional but Recommended)

`npx hyperframes add <name>` copies a ready-to-wire sub-composition into the project — the path
first-party templates take, and usually faster and more polished than authoring an effect from
scratch. `REGISTRY_CATALOG` lists the names `add` accepts, `REGISTRY_BLOCKS` the wiring contract,
and `REGISTRY_ADD_EXAMPLE` a worked install; a pulled block already carries its own wrapper and
registered timeline, so you supply only its window and track in the root composition.

The ones that earn their place here — as seams: `flash-through-white` (punchy section change),
`chromatic-radial-split` (cinematic moment), `cinematic-zoom` (hero reveal); as scene furniture:
`app-showcase` (device frame), `ui-3d-reveal` (screenshot reveal), `data-chart` (stat/proof beat),
`reddit-post` (social proof), `logo-outro` (closing card), `grain-overlay` (atmosphere on dark
scenes). `shimmer-sweep` is an element-scoped *component*, **not** a seam — in-scene accents only.

```bash
npx hyperframes add flash-through-white   # …and any other block named above
```

Use a block only when it implements the confirmed transition style and can be retokenized to the
confirmed theme without changing its identity. The user's `transition_style`, `transition_speed`,
and `theme` always win; a block's convenience never introduces a white flash into a dark
composition, or an unselected transition anywhere.

## Step 4.3: Accept the Scene Set, Reconcile Assets

Every `scenes/*.html` came from a builder holding **one frame's packet** — that frame's storyboard
block with its director keys, the design spec, the inlined bodies of the recipes it cites, its
canvas, and its bound capture paths. Assume what the packet guaranteed and do not re-derive it: a
`<template>`-wrapped sub-composition registering one paused timeline, whose layout, motion and copy
answer that frame's `goal:` / `tone:` / `energy:` / `density:`, and whose tokens and capture `src`
paths are the ones it was handed.

**Verify what no packet could reach.** A builder saw one frame and ran no CLI, so everything
cross-frame and every gate belongs to this phase: the loader wiring Step 4.4 lays out (values
`DATA_ATTRIBUTES`, track uniqueness `TRACKS_AND_CLIPS`, canvas parity and single-owner initial state
in that step's own comments); one design language and one theme across all scenes; no scene
animating its own exit; a real capture on screen somewhere in the film; and `lint` / `check` / seam
gate / hero-frame check, none of which means anything until the project is assembled.
Composition-level failures are repaired here — a failure *inside* one scene file goes back to its
builder (Step 4.6 § Re-dispatch a failing frame).

Confirm the directory layout. The Phase 4 composition expects:

```
{project-name}/
├── DESIGN.md                  # from Phase 3
├── index.html                 # root composition (this phase)
├── scenes/*.html              # from Phase 3
└── public/screenshots/        # from Phase 2
```

Screenshots stay at `public/screenshots/` — referenced from `index.html` via relative `<img src="public/screenshots/…">` tags.

## Step 4.4: Build the Root Composition

`index.html` is a single HyperFrames composition whose total duration equals the storyboard total.
It is the *modular orchestrator* shape `COMPOSITION_ARCHITECTURE` describes: no `<template>`
wrapper (only the sub-compositions it loads have one), a slot per scene, the audio mount, and a
near-empty root timeline.

**The master clock comes from each frame's `duration` bullet, accumulated in frame order** — one
loader per frame, its `src` naming the scene file. A frame's `window` bullet is a reading aid, not a
source: where the two disagree, `duration` wins and the disagreement is worth reporting, because it
usually means a hand-edit landed in one place only. Read the frames through
`validate_brief.py … storyboard --json` (Phase 3 § Reading the storyboard) rather than by eye;
`duration_seconds` there is the parsed number. Frame headings are 1-based while scene files and
composition ids stay 0-based, so **frame 1 is `scene-00-…`** — the loader comments below count
files, not frames.

Read `theme`, `transition_style`, and `transition_speed` from the confirmed Creative Brief before
writing the root. Resolve the root canvas and every transition overlay from the single
confirmed-theme token set in `DESIGN.md`; no root, loading, or overlap frame may expose an
opposite-theme default. Map speed exactly once: `quick = 0.4s`, `medium = 0.7s`, `slow = 1.2s`.
Call that value `D` — it is the whole seam's time budget at every boundary. Replace every uppercase
color and timing token below with computed literals before linting.

**Loader windows follow the boundary kind, and Step 4.5 decides which kind each boundary is.**
Write the ledger first, then size the loaders from it:

- **Cut boundary** (a ledger row) — instantaneous, so the two scenes never co-exist: the outgoing
  loader ends at the cut time and the incoming loader's `data-start` **is** that time, never earlier.
  Read `SEAM_LAW`'s clip-gating note first — a loader that opens before its entry tween is un-hidden
  sits at its initial state and fails the zero-overlap check, the commonest seam-gate failure.
- **Dissolve boundary** (no ledger row — `crossfade`, `metallic-swoosh`) — both scenes must be alive
  together: the outgoing loader stays alive `D` past its nominal end and the incoming starts at the
  nominal boundary, or the canvas flashes through.

A clip scene's inner `<video>` mirrors *its own loader's* full window either way. Paint `#root`
opaque in the confirmed theme — a render prerequisite, not a style choice; `SEAM_RENDER_MECHANICS`
(`seam-craft`) says which seam windows open a summed-opacity gap and why an unpainted root flashes
white through it.

```html
<!-- Document head, stylesheet mount and body wrapper per COMPOSITION_ARCHITECTURE. -->
<style>
  html, body { margin: 0; background: THEME_CANVAS; }
  /* Opaque stage ground — required, see SEAM_RENDER_MECHANICS. */
  #root { background: THEME_CANVAS; }
</style>

<div id="root"
     data-composition-id="main"
     data-width="1920" data-height="1080"
     data-start="0" data-duration="42">
  <!-- data-width / data-height MUST match the canvas confirmed in Phase 1
       Step 1.1 and every scene template's own data-width / data-height. -->

  <!-- Audio (voiceover + music mixed in Phase 5). `id` is required: lint
       flags an <audio> without one, and the renderer silently drops it. -->
  <audio id="audio-main" data-start="0" data-duration="42" data-track-index="0"
         src="voiceover-with-music.mp3"></audio>

  <!-- Scene loaders. Three rules the ecosystem references do not cover:
         1. Windows come from the boundary kind — size them only AFTER the
            seam ledger exists (see above).
         2. Initial hidden state has ONE owner per scene. A scene named in the
            ledger gets its base state from SEAM_STAMP — leave its inline style
            off. A scene reached only by a dissolve keeps style="opacity:0".
            Declaring it twice is how a scene ships permanently invisible with
            every gate green.
         3. A non-default `runtime:` needs a ROOT bootstrap — see below. The
            scene cannot import it itself.
  -->

  <!-- Scene 1 nominally spans 5 → 9 (scene 0 elided). Ledgered cut: no inline opacity. -->
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
  // The root needs a registered timeline too, even if it only hosts seams.
  window.__timelines = window.__timelines || {};
  const tl = gsap.timeline({ paused: true });

  // <seams:auto>
  // SEAM_STAMP owns everything between these two markers: base states plus
  // every seam tween, generated from ledger.json in Step 4.5. Leave the
  // markers in place and never hand-edit between them — a re-stamp discards
  // whatever is here; without them the stamper appends after the
  // registration below instead.
  // </seams:auto>

  // Everything hand-authored goes BELOW the markers so a re-stamp cannot
  // clobber it: dissolve boundaries (no ledger row), the carrier handoff of
  // a match-cut / morph row, and ambient root-level effects.
  // Keep the next four lines ONLY if the film has at least one dissolve
  // boundary, and substitute the token; delete them outright when every
  // boundary is a stamped cut, or the unsubstituted token throws at load.
  const D = Number("TRANSITION_DURATION_SECONDS");
  if (!Number.isFinite(D) || D <= 0) {
    throw new Error("Replace TRANSITION_DURATION_SECONDS from transition_speed");
  }

  window.__timelines["main"] = tl;
</script>
```

The composition contract itself is upstream's, and this workflow does not restate it:
`COMPOSITION_ARCHITECTURE` for the modular root and its `<template>`-free shape,
`DATA_ATTRIBUTES` for every `data-*` value and its units, `TRACKS_AND_CLIPS` for track assignment
and overlap, `SEAM_RENDER_MECHANICS` for seam compositing. One local ordering rule on top: lay out
the resting state first, and add motion only once `npx hyperframes check` reports zero overlaps at
every sampled timestamp.

### Clip scenes (footage timing)

- A clip scene's root-loader `data-duration` = the clip's on-screen length =
  `(out − in) / speed` (from the frame's `clip_in` / `clip_out` + `speed` bullets). Set the
  scene window from the footage — do **not** stretch a clip scene to fit VO; VO
  is written to fit the footage-derived window in Phase 5.
- **Verify the inner `<video>`'s attribute contract; never re-derive it here.** It is
  `workflows/phase-3-design.md` § Clip scene, over `DATA_ATTRIBUTES` — confirm the builder wired it
  from the frame's bullets, because the runtime frame-syncs only a video declaring `data-start` and
  a bare one cross-routes across 2+ clip scenes (one plays another's footage, another plays black)
  while every gate stays green.
  One value only Phase 4 can supply: the inner video's `data-duration` is **its own loader's full
  window**, read off the loader you sized above — not the bare clip length. The runtime hides an
  expired track, so a video ending before its loader blanks the frame for the rest of the window,
  seam out included.
- A rigid real-time clip (e.g. a live command run) sets its own budget: keep it at
  `speed: 1.0` and size the scene to the real length; speed-ramp **only** explicitly
  marked dead air.
- Overlays on a clip scene (captions, punch-in zoom, cursor emphasis) are keyed to
  **footage timecodes**; if `speed` ≠ 1, remap those keys proportionally.
- **Promo framing check (orchestrator-enforced):** when the confirmed `mode` is `promo`, every clip
  scene MUST use the device-frame wrapper — bare-edge footage is not allowed in
  promo. Verify by eye in `npx hyperframes snapshot` before advancing. (There is no
  programmatic gate; see spec §5.5/§14.)
- **Legibility check (orchestrator-enforced, spec §7.2a):** narrative-critical UI text in footage must read ≥24px effective in the rendered frame. If raw capture is below that, add a footage-time punch-in on the `.clip-frame` wrapper (see `patterns/visual-patterns.md` § Camera Moves on Stills — the "When footage text is too small" subsection). Verify by eye in `npx hyperframes snapshot . --at <focal-t>`; there is no programmatic gate.
- **Segment cap (spec §7.2b, orchestrator-enforced):** no continuous instructional run exceeds ~90s without an authored recap beat. Insert a `scenes/NN-recap.html` (from `templates/scene-recap.html`) listing the steps just covered, then resume. Self-police; no programmatic gate.

## Step 4.5: Author and Stamp the Seams

Seams belong to `motion-doctrine`. Load `SEAM_LAW` — the vector law (axis, direction, speed,
phase), the film's current, carriers, causal motion, the build gate — before writing a single
transition tween; it routes on to `cut-the-curve` (`CUT_CATALOG`) for technique parameters and
`seam-craft` (`SEAM_RENDER_MECHANICS`) for render-side compositing. **`SEAM_LAW` supersedes the
selection guidance in `patterns/transition-catalog.md` wherever the two disagree**, but never
supersedes a confirmed Creative Brief field — see the dissolve case below. Follow its authoring
order exactly: **vector ledger → stamp the master seams → name a sustained-motion route per scene →
carriers and causes → build the comps → verify** (that last rung is Step 4.6's, after `check`).

### What this workflow still decides

Upstream owns *how* a seam is built and *whether* it is correct. Three decisions stay here:

1. **Which boundary gets which technique** — a narrative call, read off the `transition_in` bullet
   of the frame the boundary leads *into* and the adjacent frames' `energy:` keys. The tone →
   transition table in `reasoning/scene-analysis.md` is the prior.
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
cuts inside a section use `crossfade`. **A boundary is recorded on the frame it leads into**, as
that frame's `transition_in` (plus `transition_speed`) bullet — so the boundary between frames N and
N+1 is read off frame **N+1**. Frame 1 carries no `transition_in`, and the closing frame is followed
by no boundary at all. Never quietly downgrade a confirmed `zoom-through`, `slide-from-bottom`,
`medium`, or `slow`.

`D` is the seam's whole time budget (`quick / medium / slow` mapped once in Step 4.4). Split it into
the row's exit and entry durations using the ratio the chosen technique states in `CUT_CATALOG`, and
honor the confirmed pacing — never clamp a confirmed `slow` down to a technique's nominal total.

| Incoming frame's `transition_in` | Seam kind | Ledger row? |
|---|---|---|
| `zoom-through` | velocity-matched Z cut | yes — a `cut` row on the Z axis |
| `slide-from-bottom` | velocity-matched Y cut; both sides travel the incoming scene's direction | yes — a `cut` row on the Y axis |
| `crossfade` | dissolve | **no** |
| `metallic-swoosh` (crossfade + shine) | dissolve | **no** |
| `cut` | a hard cut with no seam motion | no — nothing to verify |
| *(absent — frame 1, and after the closing frame)* | not a boundary; open cold, then hold the final frame | no |

A cut boundary where one concrete element genuinely persists across it — the same card, cursor, or
mark — is stronger as a `match-cut` or `morph` row carrying that carrier pair. That is an upgrade
within the confirmed style, not a substitute for it: the vector still runs in the confirmed
direction.

A dissolve cannot be a ledger row, and that is structural rather than an omission: a `cut` row has
to show zero overlap and a match-cut/morph row has to name a carrier, and a dissolve has neither by
definition. `SEAM_LAW` classes a carrier-less dissolve as an anti-pattern for that same reason.

**State the consequence out loud, because the gate will not.** Under a confirmed `crossfade` or
`metallic-swoosh` *every* boundary is a dissolve, `ledger.json` is empty, and the verifier reports
zero seams and exits 0 — a green gate that verified nothing; even under `zoom-through` or
`slide-from-bottom` the connective cuts inside a section stay unverified. Count the unverified
boundaries and report the number at the Step 4.6 checkpoint every time. Recommend the
velocity-matched alternative — the only route to a numerically verified film — then comply with
whatever the user decides (ADR-001). Changing `transition_style` is a **Phase-1 brief revision** (it
re-stales the story fingerprint and needs re-confirmation and a re-stamp), so never rewrite the
field from inside Phase 4.

### Resolve the seam tooling

`SEAM_STAMP` and `SEAM_VERIFIER` ship inside the `motion-doctrine` skill; neither is a
`hyperframes` subcommand. Resolve that skill's install directory the same way Step 4.7 resolves
`hyperframes-animation`:

```bash
# $SKILL_HOMES is the canonical home list defined in SKILL.md § Runtime Compatibility.
# Keep this line identical to that definition; edit it there, not here.
SKILL_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SKILL_HOMES="$HOME/.claude/skills|$HOME/.copilot/skills|$HOME/.agents/skills|$HOME/.pi/agent/skills|$HOME/.config/opencode/skills|$HOME/.cursor/skills|$HOME/.codex/skills|/etc/codex/skills|.claude/skills|.github/skills|.agents/skills|.pi/skills|.opencode/skills|.cursor/skills|.codex/skills|$SKILL_ROOT/.claude/skills|$SKILL_ROOT/.github/skills|$SKILL_ROOT/.agents/skills|$SKILL_ROOT/.pi/skills|$SKILL_ROOT/.opencode/skills|$SKILL_ROOT/.cursor/skills|$SKILL_ROOT/.codex/skills"
# zsh does not word-split unquoted $SKILL_HOMES and makes an unmatched glob fatal;
# both make this loop silently resolve to nothing. No-ops in bash/dash/sh.
if [ -n "${ZSH_VERSION:-}" ]; then setopt shwordsplit nullglob; fi
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
resolver in the same call.**

### Author `ledger.json`

Write it at the project root, one row per seam. `SEAM_GATE_REFERENCE` (`motion-doctrine`) owns the
field shape; read the schema there rather than inferring it. What *this* workflow supplies per row is
the storyboard boundary it stands for, its cut time on the master clock, the technique chosen above,
and the vector — same axis, same signed direction on both sides. Exit and entry must agree in the
**plan**; a mismatched row is fixed by fixing the plan, never by re-easing a tween.

**The first pass is not circular.** Draft the loaders in Step 4.4 at the storyboard's nominal
boundaries, write the ledger against the root-loader selectors you just gave them, then resize
those loaders from the ledger's cut times and stamp. A boundary may instead be carried by a hero
element *inside* the sub-composition; probing is how you correct such a row once the gate reports
the motion is not on the wrapper:

```bash
# Re-run the resolver above in this same call.
# Live path — registered as SEAM_VERIFIER in compat/ecosystem.md; if upstream moves it, edit both.
node "$DOCTRINE_SKILL_DIR/scripts/seam-gate.mjs" probe --t CUT_TIME_SECONDS --project .
```

### Stamp the master seams

```bash
# Re-run the resolver above in this same call.
# Live path — registered as SEAM_STAMP in compat/ecosystem.md; if upstream moves it, edit both.
node "$DOCTRINE_SKILL_DIR/scripts/seam-stamp.mjs" --ledger ledger.json --write index.html
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

Feature-detect; never assume. The two scripts have different needs, so degrade in tiers:

| Detected | `SEAM_STAMP` | `SEAM_VERIFIER` | Do this |
|---|---|---|---|
| `motion-doctrine` under no `$SKILL_HOMES` entry | unavailable | unavailable | hand-author every seam from `CUT_CATALOG`; **all** boundaries unverified |
| `node --version` below the minimum in `SEAM_GATE_REFERENCE` | unavailable | unavailable | as above |
| no local Chrome — `npx hyperframes doctor --json` reports no usable browser | works | unavailable | stamp anyway; stamped seams still pass by construction, but **all** boundaries go unverified |

Environment diagnosis stays with `DOCTOR` (ADR-003) — do not add a parallel browser probe here. A
missing optional gate never blocks the pipeline, but it does change what you may claim: report at
the Step 4.6 checkpoint which boundaries were stamped, which were verified, and which went
unverified and why. "All gates pass" is a false statement when the seam gate never ran.

### Bootstrapping a non-default runtime (cross-frame — the root's job)

A frame whose `runtime:` is `three`, `html-in-canvas` or any other non-default runtime **cannot
load it itself**. Its `<script>` is cloned out of its `<template>` and re-executed in this
document, where module semantics do not survive: a bare `import` throws `Cannot use import
statement outside a module`, the runtime audit of `CHECK_GATE` fails on the page error, and
nothing shows it while the scene is previewed alone — it appears only here, at assembly.

So the root imports the module **once** and publishes it on a global with a ready-queue, and the
scene consumes that global from a classic script (`sub-agents/scene-builder-delta.md` binds the
scene half). Late subscribers must run immediately, so a scene works whether it is cloned before
or after the module resolves:

```html
<script type="module">
  import * as THREE from "<the exact version THREE_ADAPTER pins>";
  window.THREE = THREE;
  const pending = window.__threeReady || [];
  window.__threeReady = { push: (fn) => fn(THREE) };
  pending.forEach((fn) => fn(THREE));
</script>
```

Pin the same version the frame packet gave its builder; two versions in one document is the
silent-breakage case `THREE_ADAPTER` warns about. Add this only when a frame actually needs it —
an unused bootstrap is a network fetch on every render.

## Step 4.6: Preview

Scrub the composition in the studio, then iterate against the gates. `PREVIEW_RENDER` owns the studio
and `CHECK_GATE` the `lint` / `check` / `snapshot` semantics — what each audits, that all take the
project **directory** rather than a file, that `check` reruns `lint`, and how to fail on warnings.

```bash
npx hyperframes preview .              # studio: every composition — `main` plus each scene sub-comp
npx hyperframes lint .                 # fast static pass after each structural change
npx hyperframes check . --samples 10   # the required gate
```

Local sampling convention: `--samples 10` for a 30s spot, `--samples 15` for denser
transition-heavy cuts; `--at 1.5,4,7.25` instead for specific hero frames. `check` must pass
cleanly, or report only overflows you have consciously marked intentional.

### Seam gate (numeric — runs after `check`, before the hero-frame check)

The gate ladder is **`lint` → `check` → seam gate → hero-frame check → user approval**, and the
order is load-bearing: `check` proves the composition is structurally sound in a browser, the seam
gate then samples real motion at every cut, and only a composition surviving both is worth a human's
eyes.

```bash
# Re-run the Step 4.5 $DOCTRINE_SKILL_DIR resolver in this same call — shell state
# does not cross bash calls.
# Live path — registered as SEAM_VERIFIER in compat/ecosystem.md; if upstream moves it, edit both.
node "$DOCTRINE_SKILL_DIR/scripts/seam-gate.mjs" verify --ledger ledger.json --project .
```

Prefer `--project`: it spawns a fresh preview server and kills it afterwards, so it cannot serve a
stale bundle. Reuse a running `preview` server with `--url <preview-url>` only if you restart it
after every composition edit — otherwise you verify the previous build. `--json` for machine output.

Read the report per seam rather than only the exit code:

- **FAIL** — a real seam defect; `SEAM_GATE_REFERENCE` enumerates exactly what the gate measures
  and why each measurement fails. Fix the **ledger row**, re-stamp (Step 4.5), and re-run; never
  hand-patch a stamped tween.
- **WARN** — most often a speed mismatch. Judge it against the beat, but never silence it by
  editing the ledger to match the measurement.
- **`0 seams`** — not a pass. It means nothing was ledgerable; say so explicitly at the checkpoint.

Two rules the script cannot check, and which reopen a seam that already passed: **any edit to a
scene's opening or closing motion invalidates that boundary's audit**, and **audio is the clock** —
re-timing scenes to a new voiceover in Phase 5 reopens every seam it touches. `SEAM_LAW` states
both; re-run this gate after either. If the tooling is unavailable, skip the gate per the degrade
table in Step 4.5 and carry the unverified-boundary count into the checkpoint below; a skipped
optional gate does not block Phase 5.

### Hero-frame content check (mandatory — gates can't see "wrong content")

`lint` and `check` are mechanical: structure, layout overflow, contrast. **Neither judges whether each scene is showing the *right* content** — a clip wired to the wrong footage or a stale `<img src>` passes both GREEN (this is exactly how the bare-`<video>` clip cross-route shipped unnoticed). Catch it here, cheaply, *before* the full render in Phase 5.

Capture a `snapshot` at the **midpoint of each scene** (not a uniform sweep) so every scene contributes one readable hero frame:

```bash
# Midpoints from the frame durations accumulated in order, e.g. frame 1 spans 0–5 → 2.5, etc.
npx hyperframes snapshot . --at 2.5,7,12,18,24,30
```

Then **Read each PNG `snapshot` writes to the project's snapshots directory** and confirm, scene by scene, that the frame shows what the storyboard calls for — correct screenshot, correct clip footage, correct copy. These are headless-Chrome stills (no `ffmpeg`, no rendered MP4 needed — the render doesn't exist until Phase 5). Do not advance until every scene's hero frame matches its storyboard intent.

**Capture-coverage backstop:** if `product_surface: ui`, confirm at least one hero frame shows a real on-screen capture (the product framed) — this is the visual confirmation of the Phase-3 capture-coverage gate (`SKILL.md` § Entry Modes → `jump`). A promo/showcase whose hero frames are all text/CTA means the spine never made it on screen; return to Phase 3.

**Theme backstop:** confirm every hero frame, browser/terminal mockup, clip matte, root canvas, and
seam frame visibly matches the Creative Brief theme. Any opposite-theme default routes
back to Phase 3; do not approve it as an intentional contrast unless the Creative Brief itself is
changed and reconfirmed.

### Re-dispatch a failing frame

Re-dispatch is a **return arc into `check`**, not a sixth rung of the ladder. A finding is
re-dispatchable when it lives **inside one scene file and is fixable from that frame's own packet**:
a `check` overflow or contrast failure in one scene, an `ANIMATION_MAP` flag on one scene's tween
(Step 4.7), a hero frame whose copy contradicts the storyboard. Everything else is yours and is
repaired here — loader windows, track indices, the ledger and its stamped tweens (fix the row and
re-stamp), the audio mount, the root canvas. Two look re-dispatchable and are not: a **wrong capture
binding**, because a builder re-handed the same packet re-emits the same path — fix the binding
upstream in Phase 2/3; and a **caption sub-comp** defect, because those are built from Phase 5's
transcript and wired here, not by a frame builder. A caption-*zone* finding against a scene's own
small critical text *is* the builder's — the delta gives it that courtesy rule — so it re-dispatches
normally.

To re-dispatch, regenerate that frame's packet exactly as Phase 3 assembles it — recipe bodies
re-read from the installed skill, never cached — and append the one concrete finding: the gate that
reported it, the scene file, the element or selector, the timestamp, and measured vs expected. "Make
it better" is not a finding and is not dispatchable. The builder returns the same single file,
overwritten; it still runs no CLI, edits no storyboard, and touches no other frame.

**One retry per frame.** If the second pass still fails, stop dispatching: repair it here, install a
shipped registry block that already does the job (Step 4.2), or take it to the user at the
checkpoint below. Inline repair is usually cheaper anyway — the measured fan-out economics Phase 3
dispatches under only pay beyond ~6 frames, so fan out re-dispatches only when more than ~6 frames
carry findings, and then batch 2–3 frames per worker in a single wave.

**Two things Phase 4 re-asserts afterwards.** A returned clip scene cannot know its loader's full
window — that is computed here, after the ledger — so re-assert the inner `<video>`'s
`data-duration` and `data-media-start` against the loader you sized in Step 4.4 before re-running
anything. And a scene edit reopens that boundary's audit (§ Seam gate above), so re-run `check`
**and** the seam gate, not only the rung that failed.

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

Before the aesthetic critique, run the `ANIMATION_MAP` verifier for a structural audit of every
tween — its report shape, flag names and dead-zone rule are its own. The script ships inside the
`hyperframes-animation` skill; it is not a CLI subcommand. Resolve that skill's install directory
the same way Phase 3 resolves this one:

```bash
# $SKILL_HOMES is the canonical home list defined in SKILL.md § Runtime Compatibility.
# Keep this line identical to that definition; edit it there, not here.
SKILL_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SKILL_HOMES="$HOME/.claude/skills|$HOME/.copilot/skills|$HOME/.agents/skills|$HOME/.pi/agent/skills|$HOME/.config/opencode/skills|$HOME/.cursor/skills|$HOME/.codex/skills|/etc/codex/skills|.claude/skills|.github/skills|.agents/skills|.pi/skills|.opencode/skills|.cursor/skills|.codex/skills|$SKILL_ROOT/.claude/skills|$SKILL_ROOT/.github/skills|$SKILL_ROOT/.agents/skills|$SKILL_ROOT/.pi/skills|$SKILL_ROOT/.opencode/skills|$SKILL_ROOT/.cursor/skills|$SKILL_ROOT/.codex/skills"
# zsh does not word-split unquoted $SKILL_HOMES and makes an unmatched glob fatal;
# both make this loop silently resolve to nothing. No-ops in bash/dash/sh.
if [ -n "${ZSH_VERSION:-}" ]; then setopt shwordsplit nullglob; fi
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

Fix or justify each flagged tween — the tool flags, you judge (a dead zone is fine on a deliberate
hold beat, suspicious on an active scene). Examples:

- `paced-fast` on a critical reveal → extend duration to 0.4s+
- `paced-slow` on a hover/microinteraction → tighten to under 0.3s
- `collision` on `opacity` → almost always the `tl.from() + tl.to()` race bug — switch to `tl.fromTo()` (see `patterns/visual-patterns.md` § stagger trap)
- `dead zone` spanning a whole scene → either add ambient motion (cursor pulse, grain shimmer) or accept as a deliberate hold

A per-scene flag is re-dispatchable (Step 4.6). Skip this step for trivial edits; run it on every new composition or after significant animation changes.

**Then read the register, which `ANIMATION_MAP` does not measure.** Pacing and character are
different questions: a scene can be perfectly paced and still express one emotion nine times.

```bash
python3 "$SKILL_DIR/scripts/motion_register.py"
```

It reports when most of a scene's tweens share one ease across near-identical durations — the
`same ease + same duration = same emotion` tell in `patterns/anti-slop.md`, which every mechanical
gate passes green because none of them is looking for it. This is **not** a second `ANIMATION_MAP`
and reports no pacing verdict (ADR-003 forbids a parallel validator); it answers a question that
needs the frame's intent, which is why it lives here.

Report-never-gate, and it takes judgment: a scene built from one repeated element — a list
revealing in stagger — looks monotonous by this measure and is right. Where it is a real finding,
the fix is register, not decoration: an arrival, an emphasis and a settle are different events and
should not share one constant. The *family* stays the brand's (`DESIGN.md` outranks any recipe's
ease); only the variation within it is at issue. A genuine finding is re-dispatchable per Step 4.6.

## Step 4.8: Aesthetic Critique (Optional but Recommended)

The mechanical gates cannot judge whether the composition is *good*. This step adds an aesthetic one before Phase 5 commits the design with voiceover.

### If the `critique` skill is installed — invoke it on the HTML + sampled stills

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

The critique returns three lists — **Keep** (working; do not touch), **Fix** (visually expensive
P0/P1 issues), **Quick wins** (5–15 minute tweaks with disproportionate impact). If there are
P0/P1 Fix items, iterate Step 4.4 / 4.5 / 4.6 then re-critique. Do not move to Phase 5 until the
Fix list is empty or each remaining item is consciously accepted.

### If `critique` is not installed — prompt a self-review checklist instead

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
