# Visual Patterns — craft, budgets, legibility

**What this file owns:** the craft of putting a *real captured product* on screen with depth and
motivated motion, the legibility floor that footage must clear, and the judgment for spending the
emphasis devices. That is product-video craft nobody upstream owns.

**What it does not own:** the motion mechanics. Eases, entrance recipes, counters, keyframe/pose
discipline, seek determinism and *which* camera move a frame earns all have owners now
(§ Where the mechanics live). Where this file and one of those disagree, **they win** — a mechanic
restated here would be a fork with no maintainer (ADR-002).

The renderer is **HyperFrames** (HTML + GSAP). Times are in **seconds**, not frames. All motion is
authored as `tl.fromTo()` / `tl.to()` on a paused timeline; HyperFrames drives playback. The
snippets below are timeline fragments — the GSAP `<script>` tag with its pinned SRI hash lives in
the scene skeleton, not in a fragment.

## Where the mechanics live

Nothing in this section is restated locally. Load the owner.

| You need | Owner | Cite |
|---|---|---|
| Ease families, their character/mood mapping, the house register, the stagger contract | `hyperframes-animation` | `EASING_AND_STAGGER` |
| Entrance recipes — spring/pop arrivals, staggered cascades, typewriter reveals | `hyperframes-animation` | `RULES_INDEX` (`spring-pop-entrance`, `waterfall-entry`, `gsap-effects`) |
| Animated counters and stat graphics | `hyperframes-creative` | `DATA_IN_MOTION` (mechanism: `counting-dynamic-scale`, `stat-bars-and-fills`) |
| Timeline registration, `fromTo` vs `from`, the transform/property contract | `hyperframes-animation` | `GSAP_ADAPTER` |
| Camera mechanism — the virtual-camera wrapper, off-centre zoom math, context reveals | `hyperframes-animation` | `RULES_INDEX` (`viewport-change`, `coordinate-target-zoom`, `zoom-out-workspace-reveal`) |
| Why every frame must be reproducible from its time value alone | `hyperframes-core` | `DETERMINISM_RULES` |
| The pose contract and its motion-proof diagnostics when a reveal renders wrong | `hyperframes-keyframes` | `KEYFRAME_DISCIPLINE` |
| Type scale for video, density, decorative opacity | `hyperframes-creative` | `VIDEO_COMPOSITION` |
| Palette and named visual identity | `hyperframes-creative` | `VISUAL_STYLES` + `PALETTES` |
| Ready-framed device/browser mockups, shine, grain | `hyperframes-registry` | `REGISTRY_CATALOG` (`app-showcase`, `ui-3d-reveal`, `shimmer-sweep`, `grain-overlay`) |

**Which camera move a frame earns is not decided here.** `grammar/camera.md` owns move selection —
the viewer question each move answers, the Tier-A/Tier-B split, and the `camera:` key a storyboard
writes. This file starts *after* that verdict: given a still and a chosen move, how it is executed
without breaking seek or legibility.

Every path behind those symbols is resolved by `compat/ecosystem.md`, and lives nowhere else
(ADR-007).

## The `tl.from()` stagger trap

`GSAP_ADAPTER` already says to prefer `fromTo()` over `from()`, for a re-seek reason: `from()`
snapshots the start state at registration, and a seek back through the mount desyncs it. **This is
a second, different failure with the same fix**, found here, and it is the one that actually bites
in this repo — so it is stated rather than assumed.

`tl.from()` records the END state at **registration time** by reading the element's current
computed style. Scene elements rest at `opacity: 0` in CSS so the first paint is invisible — so the
recorded end is *also* `opacity: 0`, and the tween runs `0 → 0`, never appearing.

The naive workaround — a `tl.to(..., { opacity: 1, duration: 0.01 })` snap right after the
`tl.from(...)` — works for a single element and **breaks under stagger**:

1. At that timeline position, every element snaps to `opacity: 1` at once (the `tl.to` does not
   stagger).
2. As each later staggered `tl.from` activates, it re-applies its recorded from-state
   (`opacity: 0`), **re-hiding an element a sibling already revealed.**

Visible symptom: staggered elements flash briefly, then vanish one by one as their own tween
activates. The failure is silent — no console error, no lint warning, and `check` does not flag it.

```js
// ✅ correct — works with stagger
tl.fromTo(".chip",
  { y: 30, autoAlpha: 0 },
  { y: 0, autoAlpha: 1, duration: 0.4, ease: "power3.out", stagger: 0.18 },
  1.0);

// ❌ wrong — flashes-then-disappears under stagger
tl.from(".chip", { y: 30, opacity: 0, duration: 0.4, stagger: 0.18 }, 1.0);
tl.to(".chip", { opacity: 1, duration: 0.01 }, 1.0);
```

Use `autoAlpha`, not bare `opacity`, wherever the CSS rest state is
`visibility: hidden; opacity: 0` — a plain `opacity` tween leaves `visibility: hidden` in place and
the element never appears (§ DON'Ts).

## Screenshot Presentation

The Phase-2 capture is the **subject** of the frame, not background texture. A screenshot pasted
flat on a colour field is the single most common way a product video reads as a template
(`anti-slop.md` § The screenshot test). Frame it, give it depth, and let one motivated move do the
work.

- **Reach for a catalog block first.** `app-showcase` (device/browser/hybrid framing) and
  `ui-3d-reveal` (a UI panel arriving from z-depth) are tested, deterministic and
  aspect-ratio-aware; `REGISTRY_CATALOG` is the authoritative list of names `npx hyperframes add`
  accepts. Hand-author a wrapper only when no block fits.
- **Keep the perspective static.** A mockup may rest at a fixed
  `perspective(1000px) rotateY(-5deg) rotateX(3deg)` — inside the tilt limits in § DON'Ts — but
  animating `perspective` itself is jittery. Animate the wrapper's `transform`, never the
  perspective value.
- **Motion goes on a non-timed wrapper, never the `<img>`.** Tween the wrapper's `scale` /
  `translate`; animating `width`/`height` on the image forces layout recompute and breaks
  deterministic seek (§ DON'Ts).
- **One frame treatment per film.** Browser chrome on one scene and a laptop bezel on the next
  reads as two different videos. Pick the framing in `DESIGN.md` and hold it.

## Camera & Depth

This is the vocabulary that gives a still the life it otherwise lacks. The default beat of a
product video is a captured screenshot (`templates/scene-screenshot.html`) carrying **one** of the
moves below; flat text scenes are connective tissue between them, not the substance.

These earn their keep only when **motivated** — pushing toward the thing the eye should land on,
scrolling to reveal what is below the fold, parallaxing real product layers. Pile on particles, 3D,
grain and ambient loops and you have traded a flat template for a busy one (`anti-slop.md`
§ P1/P2). Pick **one** move per scene, key it to the work it does, and respect every ban in
§ DON'Ts — these entries add structured *permission with guardrails*, never a loophole. The move
itself is chosen upstream of here, in `grammar/camera.md`.

### Camera Moves on Stills

A held screenshot takes a slow **push** (scale up toward a focal region), **pull** (scale down to
reveal context), **lateral drift** or **diagonal drift** — always on the **non-timed wrapper**
(`.shot-browser` / `.clip-frame`), **never** the `<img>`/`<video>` dimensions (§ DON'Ts). Set
`transformOrigin` at the region the eye should land on (x% y% of the frame).

```js
// Slow push toward a focal UI region. transformOrigin points at the thing
// the eye should land on. Wrapper only — the <img> is along for the ride.
tl.fromTo(root + ' .shot-browser',
  { scale: 1.0 },
  { scale: 1.06, transformOrigin: "32% 28%", duration: 2.2, ease: "power1.inOut" },
  1.1);
```

**Guardrails:**

- **Release before the confirmed inter-scene transition window.** End the move (and any settle)
  before the duration mapped from `transition_speed` (`quick = 0.4s`, `medium = 0.7s`,
  `slow = 1.2s`) so it never pulls back mid-transition. No scene-internal exit tween on non-final
  scenes — the seam owns the exit (§ DON'Ts).
- **Only the closing scene may end mid-hold.** It exits passively, with no seam after it, so a push
  there can settle and hold instead of releasing. On that scene the move must **push or hold only —
  never pull back**; a pull-out on the final frame reads as the video walking away from the
  product. The conservative default is no camera move on the closing scene at all
  (`templates/scene-screenshot.html` bakes this in); a held push is the deliberate exception.

**When footage text is too small (the legibility case).** When narrative-critical UI text in
recorded footage renders below the floor in § Legibility floor, this push *is* the remedy: scale
the non-timed `.clip-frame` wrapper toward the text. Key it to **footage time** (seconds into the
clip); if the clip's `Speed` ≠ 1, remap the times proportionally. Release before the crossfade as
above.

```
effective_px = source_px × scale × (rendered_frame_width / source_capture_width)
```

Pick `scale` so the smallest narrative-critical glyph clears the floor. Verify by eye with
`npx hyperframes snapshot . --at <focal-t>` — there is no programmatic gate for this.

### Scroll-Within-Frame

Reveal a tall full-page capture by panning it upward inside a fixed `overflow:hidden` viewport —
the framed browser stays put while the page scrolls inside it. Drive it with a **timeline
`translateY` on the INNER non-timed wrapper** (`.shot-pan`) only.

```js
// Travel = (viewHeight − renderedImageHeight), negative. Measure from the real
// PNG so the end lands on the footer, not past it.
tl.to(root + ' .shot-pan',
  { y: -640, duration: 3.0, ease: "power1.inOut" },
  1.1);
```

**Guardrail:** **NEVER** drive this with `scrollTop`, a `scroll` event listener, or an
`IntersectionObserver`. None of those is a pure function of timeline `t`, so a seeked frame would
read whatever scroll state the DOM happened to be in — the failure `DETERMINISM_RULES` exists to
prevent. The translate is the only deterministic path. Release before the crossfade; no exit on
non-final scenes.

### Motivated Parallax

Depth from the **real product**: split a captured UI (or a foreground UI panel over a background
app surface) into 2–3 DOM layers and translate them at **different rates**, so nearer layers travel
further. This stays **2D translate** — no `perspective`, no 3D camera, no `rotateX/Y` on the
layers. Pull `ui-3d-reveal` from the catalog when a panel flying in from z-depth covers the beat;
hand-author the layered translate for a sustained drift.

Reveal the layers with a staggered entrance from `RULES_INDEX`, then hold the differential drift —
the rate difference *is* the depth:

```js
// Same product, three layers. Back travels least, front most. Pure 2D translate.
tl.to(root + ' .layer-back',  { y: -12, duration: 2.4, ease: "power1.inOut" }, 1.0);
tl.to(root + ' .layer-front', { y: -48, duration: 2.4, ease: "power1.inOut" }, 1.0);
```

**Guardrail:** this is parallax on **real product layers**, the exact opposite of the banned
decorative blob / wave parallax (`anti-slop.md` § P1 — "meaningless geometry"). If the layers are
not the actual UI, you are decorating, not building depth. For atmosphere over them the only
sanctioned texture is a `grain-overlay` catalog block — never an ambient particle field.

### Anchored Callout / Spotlight

Direct attention to one region of an on-screen UI — either a **marker** drawn over the spot
(`marker-highlight.md`) **or** a **spotlight**: a dimming overlay with a brighter hole over the
region. This is the **highest slop risk** on the page; stacked highlights, glows and dimmers turn a
clean frame into a ransom note.

**Emphasis budget (enforce).** The per-frame emphasis limit and the film-wide marker limit are
rows of the budget table in `reasoning/scene-analysis.md` — the only place those numbers live
(ADR-008). The judgment for spending them:

- **Pick EITHER a marker highlight OR a spotlight, never both on one region.** Two attention cues
  aimed at the same place cancel out; the eye reads "busy", not "look here".
- **A marker highlight is a reserved editorial beat, not a tool.** Spend it on the single moment
  that most deserves it (`marker-highlight.md` § When to use which mode). A spotlight is the
  lighter-weight alternative once the marker is spent.
- **Reveal via `autoAlpha` — never `display`/`visibility`, never `clipPath`** (§ DON'Ts). The dim
  overlay's hole is a *static* `radial-gradient` mask or inset `box-shadow`: you fade the overlay
  in, you never animate the cutout's shape.

### In-Scene Shine Sweep

A one-shot specular pass over a UI card as it settles — an absolutely-positioned gradient overlay
whose `background-position` animates across the element once. This is **intra-scene**: it lives
inside one scene and decorates one element. Pull `shimmer-sweep` from the catalog before
hand-authoring — it is the tested version, and `REGISTRY_CATALOG` lists it as an element-scoped
*component*, which is exactly why it belongs here and **cannot serve a seam**
(`patterns/transition-catalog.md`).

**Guardrails:**

- **One-shot, not an ambient loop.** A shine that keeps sweeping for the whole scene is the
  looping-motion tell (`anti-slop.md` § P2). Fire it once, when the card lands.
- **Self-police `mix-blend-mode: screen` luminance.** `check` is not a luminance audit and will not
  detect overflow. `screen` blending can push a near-white band past 100% luminance and produce a
  flash; preview against your **brightest** scene background by eye, and if it blows out, drop the
  band's `rgba` alpha to ~0.65 or remove the blend mode and rely on `opacity` alone. This holds for
  **any** `screen`-blended band in this repo, in a scene or across a seam.

### Masked Reveal

Wipe a single element into view by animating **`mask-position`** over a **static** `mask-image` —
the mask shape stays fixed, only its offset slides, so the element is progressively unveiled. Same
safe class as `background-position`: a continuous numeric property, fully seekable. Prefix the
property for headless Chromium and tween both forms.

**Guardrail:** this is **distinct from the banned `clipPath` seam** (§ DON'Ts carries the why).
`mask-position` interpolates **no polygon vertices** — the geometry is constant, so there is no
edge to mis-render. Keep the mask shape static, do not interpolate its stops, and do not press it
into service as an inter-scene transition: a seam belongs to `SEAM_LAW`, not to a scene. A static
`clip-path` reveal window is the same safe class — that shape is `TECHNIQUES` #12 *Clip-Path Reveal
Masks*.

## Legibility floor

**Nothing narrative-critical renders below 24px in the final frame** — authored type or captured
UI. Below that it stops being readable at typical playback resolution and on a phone.

- **Authored type scale is `VIDEO_COMPOSITION`'s** — headline / body / label ranges, decorative
  opacity, border weights. Read it there; this file carries no size table. Its rule and this floor
  agree: a font-size under 24px in a video composition has to be justified.
- **Captured footage** is measured, not styled:
  `effective_px = source_px × scale × (rendered_frame_width / source_capture_width)`. When it comes
  out under the floor, the remedy is a footage-time push-in — § Camera Moves on Stills.
- **No gate catches this.** `check` (`CHECK_GATE`) enforces WCAG AA *contrast* (4.5:1 normal, 3:1
  for large text ≥24px, or ≥19px bold); it does not audit size. Self-police with
  `npx hyperframes snapshot`.

## Step Label / Chapter Overlay

Tutorial-mode instructional scenes carry an on-screen `Step N of M` pill plus a chapter title,
layered over the clip or recap scene.

- **Copy is authored, never derived.** Take it verbatim from the frame's `step_label` and
  `chapter` bullets on the storyboard — never recount from the frame number, which includes the
  cold open.
- **Reveal with `autoAlpha`, and give it no exit tween.** The inter-scene seam owns the exit
  (§ DON'Ts).
- **Both elements clear the § Legibility floor**, and the pill sits in a consistent corner for the
  whole film — a step counter that moves between scenes reads as a mistake.

## Transitions are not a scene's business

Nothing in this file authors a scene-to-scene seam; a seam is a **composition-level** concern.
*Which* transition serves a moment and how much energy the film may spend →
`patterns/transition-catalog.md`. The law of the handoff → `SEAM_LAW`, verified by `SEAM_VERIFIER`.
How the two scenes composite → `SEAM_RENDER_MECHANICS`. The named velocity-matched seams and their
parameters → `CUT_CATALOG`.

The two consequences that bind *scene* authoring are already in § DON'Ts: no exit animation on a
non-final scene, and no `clipPath` seam. Transition duration comes from the confirmed
`transition_speed` in the brief and is never quietly shortened after the user chose it (ADR-001).

## DON'Ts (Critical)

- **No jitter or shake** — reads as cheap. `check` will not catch it; self-police.
- **No full 360° rotations** — disorienting. Subtle `rotateY` ≤ 8° or `rotateZ` ≤ 4° only, and on
  mockups only.
- **No `elastic` or `bounce` eases** — they read as toy-like in a product video. This narrows
  `EASING_AND_STAGGER`, which permits overshoot as a rare explicitly-playful register: in this
  repo the overshoot families stop at a `back.out`-class settle on a badge or stat, and a brand's
  own Avoid list may forbid even that.
- **No exit animations on non-final scenes** — the seam owns the exit (`SEAM_LAW`). Animating an
  element out *and* transitioning the scene out is double-motion.
- **No `clipPath` for transitions** — *the why, learned the hard way in this repo:* a polygon
  `clipPath` that sweeps between two scenes leaves a **1px anti-aliased black sliver** along the
  moving edge, because the exiting and entering half-planes never share an exact subpixel
  boundary — each anti-aliases its own edge against nothing, and the page behind shows through the
  gap. It survives every gate (`check` reads layout and contrast, not a hairline seam) and appears
  only in the rendered frames. Use a crossfade with a full-frame light overlay instead — the light
  family in `TRANSITION_FAMILIES` — and let `SEAM_RENDER_MECHANICS` own the compositing. **This
  bans `clipPath` as a *seam*, not as a static shape**: a fixed `clip-path` on an element, or an
  animated `mask-position` over a static mask (§ Masked Reveal), interpolates no vertices and has
  no seam to mis-render.
- **Never animate `display`, `visibility`, or call `.play()` inside a timeline** — both are binary,
  and `.play()` from inside a timeline breaks the deterministic seek `DETERMINISM_RULES` requires.
  Use `autoAlpha` (which tweens opacity *and* toggles visibility) or `opacity` +
  `pointer-events: none`.
- **Never animate `<img>` dimensions directly** — wrap each animated `<img>` in a non-timed `<div>`
  and tween the wrapper's `transform`. Animating `width`/`height` forces layout recompute that
  breaks deterministic seek.
- **Never use `gsap.set()` at script-load time on elements that enter the timeline later** — a
  sub-comp clip with `data-start > 0` is not in the DOM at page load, so its elements do not exist
  yet and the call is a silent no-op. Use `tl.set(selector, vars, timePosition)` *inside* the
  timeline, at or after the clip's `data-start`:
  ```js
  // ✅ correct — runs inside the timeline at t=5s, after #late-card exists
  tl.set("#late-card", { opacity: 0, x: -100 }, 5);
  tl.to("#late-card", { opacity: 1, x: 0, duration: 0.5 }, 5);

  // ❌ wrong — fires before #late-card is rendered, has no effect
  gsap.set("#late-card", { opacity: 0, x: -100 });
  tl.to("#late-card", { opacity: 1, x: 0, duration: 0.5 }, 5);
  ```
- **No tiny text** — see § Legibility floor. `check` reads contrast, not size.
