# Transition Catalog

One-page index of every transition family available in HyperFrames, mapped to the moments where each fits in a product video. The deep implementations live in the `hyperframes-animation` skill — `TRANSITION_CATALOG`, `TRANSITION_OVERVIEW`, and the per-family `TRANSITION_FAMILIES` pages, whose paths are registered in `compat/ecosystem.md`. This file tells you *which* transition to reach for; those pages show you *how* to wire it.

## Picking by mood

| Moment in the video | Reach for | Why |
|---|---|---|
| Default scene-to-scene cut | **Crossfade** or **Blur Crossfade** | Quiet, professional. Default of the dissolve family. |
| Section boundary (Hook → Pain, Solution → Features) | **Metallic Swoosh** (`patterns/metallic-swoosh.md`) or **Flash through White** | Signals "new chapter" without overpowering. |
| Hero / product reveal | **Cinematic Zoom** or **Zoom Through** | Earns the visual flourish — scale family. |
| Stat or proof moment | **Chromatic Radial Split** or **Diamond Iris** | Energetic, pulls eye to the centre — radial family. |
| Before / after, competitor comparison | **Diagonal Split** or **Push Slide** | Spatial metaphor for "this vs that" — radial + push families. |
| Editorial pull-quote | **Focus Pull** or **Color Dip** | Cinema-y, soft. Dissolve family. |
| Drama / tension reveal | **Glitch** or **Page Burn** | Use ONCE per video at most — distortion + destruction families. |
| Mechanical / countdown | **Shutter** or **Clock Wipe** | Editorial gravitas — mechanical family. |
| Closing fade-to-end-card | Plain **Crossfade** to a held final frame | Never use a "flashy" transition on the final exit. |

Family names above resolve through `TRANSITION_FAMILIES`; for upstream's own energy/mood selection guidance read `TRANSITION_OVERVIEW`. Both live in the `hyperframes-animation` skill — paths in `compat/ecosystem.md`.

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

Everything below is owned by the `hyperframes-animation` skill and registered in `compat/ecosystem.md` — that map is the only place the file paths live:

- `TRANSITION_CATALOG` — the normative page: hard rules, scene template, shader rules.
- `TRANSITION_OVERVIEW` — selection guidance: energy/mood, narrative position, presets, CSS vs shader.
- `TRANSITION_FAMILIES` — the per-family implementation pages (dissolve, scale, radial, push and the rest); the map holds the complete, current list.
- `TRANSITION_REGISTRY` — machine-readable registry, a curated Tier-B subset and **not** the full catalog.

Which named transition lives in which family is upstream's to state, and it changes with upstream: start at `TRANSITION_OVERVIEW`, then open the family page. This file deliberately keeps no copy of that inventory.

## Hard rules (don't skip these)

Seam law is owned by the `motion-doctrine` skill (`SEAM_LAW`; numeric verifier `SEAM_VERIFIER`); render-compositing mechanics by `seam-craft` (`SEAM_RENDER_MECHANICS`).

These come from `TRANSITION_CATALOG` (`hyperframes-animation`) and bite if violated:

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
