# Transition Catalog

One-page index of every transition family available in HyperFrames, mapped to the moments where each fits in a product video. The deep implementations live in the `hyperframes` skill at `references/transitions/`. This file tells you *which* transition to reach for; the linked file shows you *how* to wire it.

## Picking by mood

| Moment in the video | Reach for | Why |
|---|---|---|
| Default scene-to-scene cut | **Crossfade** or **Blur Crossfade** | Quiet, professional. Default in `references/transitions/css-dissolve.md`. |
| Section boundary (Hook → Pain, Solution → Features) | **Metallic Swoosh** (`patterns/metallic-swoosh.md`) or **Flash through White** | Signals "new chapter" without overpowering. |
| Hero / product reveal | **Cinematic Zoom** or **Zoom Through** | Earns the visual flourish — `css-scale.md`. |
| Stat or proof moment | **Chromatic Radial Split** or **Diamond Iris** | Energetic, pulls eye to the centre — `css-radial.md`. |
| Before / after, competitor comparison | **Diagonal Split** or **Push Slide** | Spatial metaphor for "this vs that" — `css-radial.md` + `css-push.md`. |
| Editorial pull-quote | **Focus Pull** or **Color Dip** | Cinema-y, soft. `css-dissolve.md`. |
| Drama / tension reveal | **Glitch** or **Page Burn** | Use ONCE per video at most — `css-distortion.md`, `css-destruction.md`. |
| Mechanical / countdown | **Shutter** or **Clock Wipe** | Editorial gravitas — `css-mechanical.md`. |
| Closing fade-to-end-card | Plain **Crossfade** to a held final frame | Never use a "flashy" transition on the final exit. |

## Catalog blocks (use these first)

Before authoring a transition from scratch, pull one of these via `npx hyperframes add <name>` — they're tested, deterministic, and aspect-ratio-aware:

| Block | What it does | Energy |
|---|---|---|
| `flash-through-white` | Hard cut with brief white flash | Punchy |
| `chromatic-radial-split` | RGB-shifted radial wipe | Cinematic |
| `cinematic-zoom` | Shader zoom transition | Premium |
| `shimmer-sweep` | Diagonal shine (close cousin of our metallic-swoosh) | Premium |
| `grain-overlay` | Persistent film-grain texture | Atmosphere |

See `workflows/phase-4-production.md` Step 4.2 for how to wire them into the root composition.

## Full CSS transition reference

| HF reference file | Transitions inside |
|---|---|
| `references/transitions/catalog.md` | Hard rules, scene template, shader rules |
| `references/transitions/css-dissolve.md` | Crossfade, Blur Crossfade, Focus Pull, Color Dip |
| `references/transitions/css-scale.md` | Zoom Through, Zoom Out |
| `references/transitions/css-radial.md` | Circle Iris, Diamond Iris, Diagonal Split |
| `references/transitions/css-push.md` | Push Slide, Vertical Push, Elastic Push, Squeeze |
| `references/transitions/css-cover.md` | Staggered Colour Blocks, Horizontal/Vertical Blinds |
| `references/transitions/css-blur.md` | Blur Through, Directional Blur |
| `references/transitions/css-distortion.md` | Glitch, Chromatic Aberration, Ripple, VHS Tape |
| `references/transitions/css-light.md` | Light Leak, Overexposure Burn, Film Burn |
| `references/transitions/css-3d.md` | 3D Card Flip |
| `references/transitions/css-mechanical.md` | Shutter, Clock Wipe |
| `references/transitions/css-destruction.md` | Page Burn |
| `references/transitions/css-grid.md` | Grid Dissolve |
| `references/transitions/css-other.md` | Gravity Drop, Morph Circle |

All paths are relative to the installed HyperFrames skill location — `~/.claude/skills/hyperframes/` (Claude Code) or `~/.copilot/skills/hyperframes/` (GitHub Copilot CLI).

## Hard rules (don't skip these)

These come from `references/transitions/catalog.md` and bite if violated:

- **Scenes must OVERLAP during the confirmed transition window.** Map `transition_speed` once (`quick = 0.4s`, `medium = 0.7s`, `slow = 1.2s`) and extend every non-closing scene's `data-duration` by that value past its nominal end. Start the incoming scene at the nominal boundary. If adjacent scenes do not overlap, neither renders during the transition and the body color flashes through — producing a visible artifact that is one of the most obvious "AI-rendered" tells. See `workflows/phase-4-production.md` § Step 4.4 for the corrected composition pattern.
- **Track indices must be UNIQUE for overlapping scenes.** HyperFrames rejects same-track overlap. Use 1, 2, 3, 4, 5. Track index doesn't drive visual layering — DOM order does (later in DOM = on top with equal z-index).
- **Only fade the INCOMING scene's opacity 0→1.** Don't simultaneously fade the outgoing scene 1→0 — that lets the body color contribute to the composite during the crossfade (visible as darkening). The outgoing scene stays at opacity 1 below and is occluded naturally as the incoming one covers it.
- **Body background should be white** (or whatever neutral matches your scene backgrounds). If anything ever exposes the body — a single-frame timing gap, a clipping artifact — white reads as intentional pacing. Black reads as a render bug.
- **Scene 1 visible by default** — no `opacity: 0`. Scenes 2+ start at `opacity: 0` on the *container*; GSAP reveals them.
- **No `class="clip"` on standalone scene divs.** Only the root composition gets `data-composition-id`/`data-start`/`data-duration` — with one exception: the `<video>` inside a clip scene carries its own `data-start`/`data-duration`/`data-media-start`/`data-track-index` per the explicit clip contract (`workflows/phase-3-design.md` § Clip scene). Never strip those.
- **Z-index on exit-revealing transitions** (gravity drop, zoom out, diagonal split): outgoing scene goes ON TOP (`z-index: 10`) so it exits while revealing the new scene behind (`z-index: 1`).
- **Light-leak overlays must be larger than the frame (2400px+)** so the edge never crosses the canvas during sweep. A visible-shape leak looks fake.
- **Glitch RGB overlays at 35% opacity with NORMAL blend mode** — `mix-blend-mode: multiply` is invisible on dark backgrounds, which is exactly when you'd reach for glitch.
- **Blinds count scales with energy**: 4h/6v calm, 6–8h/8v medium, 12–16h/16v high.
- **Page burn**: hide scene 1 via `tl.set` at burn end, NEVER `onComplete` (not reversible under seek).
- **Banned**: star iris (polygon interpolation broken), tilt-shift (no selective CSS blur), lens flare (visible shape, not optical), hinge/door (distorts too fast).

## How to choose

1. **Default to crossfade.** Most scene cuts in a product video should be invisible. Save the heavy artillery for ≤ 2 moments per spot.
2. **Match transition energy to the moment.** A 0.4s glitch into a pricing table is wrong; a 0.4s glitch into "your data is everywhere" is right.
3. **Match transition duration to total runtime.** 30s spot → max 0.5s transitions. 60s spot → up to 0.8s. Anything over 1s reads as sluggish.
4. **Don't transition out of the closing scene.** The video ends on a held frame, not a flourish.
5. **Pull a catalog block before hand-authoring.** `flash-through-white`, `chromatic-radial-split`, `cinematic-zoom` cover 80% of real needs.
