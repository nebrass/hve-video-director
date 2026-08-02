# Visual Patterns — Animation Toolkit

Reference for animation choices in hve-video-director productions. The renderer is **HyperFrames** (HTML + GSAP). Times are in **seconds**, not frames. All motion is authored as GSAP tweens on a paused timeline; HyperFrames drives playback.

## Easing Vocabulary

GSAP eases map to product-video moods. Pick the ease first — it carries more emotional weight than duration.

| Ease | Feel | Use For |
|------|------|---------|
| `power3.out` | Confident landing, no overshoot | Titles, headlines, value props |
| `power2.out` | Gentle settle | Body text, subtitles, fades |
| `back.out(1.4)` | Slight overshoot, playful | Stats, badges, callouts |
| `expo.out` | Fast then very gentle | Hero reveals, screenshot drops |
| `power1.inOut` | Continuous, mechanical | Counters, progress, scroll |
| `none` (linear) | No easing | Numeric counters, marquee loops |

Avoid `elastic` and `bounce` in product videos — they read as toy-like.

## Entrance Tweens

Author every entrance with `tl.fromTo()` — give the explicit **from**-state (an offset, `opacity: 0`) and the rest state as the **to**-state. (Avoid bare `tl.from()` on opacity-bearing elements — see the stagger trap below.)

```html
<h1 id="hero" style="opacity:0">Your headline</h1>
<script>
  const tl = gsap.timeline({ paused: true });
  // Use fromTo with EXPLICIT end state — see "tl.from() stagger trap" below.
  tl.fromTo("#hero",
    { y: 40, opacity: 0 },
    { y: 0, opacity: 1, duration: 0.6, ease: "power3.out" },
    0.2);
  window.__timelines["scene-1"] = tl;
</script>
```

Key rules:

- The element's **resting style is its final state**. Don't animate to a position — animate **from** an offset to the rest position. HyperFrames inspects the rest layout to flag overlaps.
- Start `opacity: 0` inline on the element so the first paint is invisible.
- Times are seconds. The third positional arg to `tl.fromTo()` is the **absolute start time on the timeline**, not a delay.
- **Prefer `tl.fromTo()` over `tl.from()` whenever opacity is involved.** See trap below.

### The `tl.from()` stagger trap (read this before staggering opacity)

GSAP `tl.from()` records the END state at **registration time** by reading the element's *current computed style*. If the CSS rest state is `opacity: 0` (as it should be to prevent FOUC), the recorded end is also `opacity: 0` — so the animation goes `opacity 0 → 0`, never appearing.

The naive workaround — adding a `tl.to(..., { opacity: 1, duration: 0.01 })` snap right after the `tl.from(...)` — works for a single element but **breaks horribly with stagger**:

1. At the timeline position, all elements snap to `opacity: 1` simultaneously (the `tl.to` doesn't stagger).
2. As each subsequent staggered `tl.from` activates, it re-applies its recorded from-state (`opacity: 0`), **re-hiding the element after a sibling has already revealed it**.

Visible symptom: every staggered element flashes briefly visible, then disappears suddenly as its own tween activates.

**Always use `tl.fromTo()` for opacity tweens** — both states are explicit, no current-state recording, no race with snap-hacks:

```js
// ✅ correct — works with stagger
tl.fromTo(".chip",
  { y: 30, opacity: 0 },
  { y: 0, opacity: 1, duration: 0.4, ease: "power3.out", stagger: 0.18 },
  1.0);

// ❌ wrong — flashes-then-disappears under stagger
tl.from(".chip", { y: 30, opacity: 0, duration: 0.4, stagger: 0.18 }, 1.0);
tl.to(".chip", { opacity: 1, duration: 0.01 }, 1.0);
```

The failure mode is silent — there's no console error or lint warning. Elements flash visible briefly, then disappear suddenly as their staggered tween activates. If you see this pattern in a render, the cause is almost always a `tl.from()` + stagger combo on opacity-bearing elements that have `opacity: 0` in CSS.

## Scene Entry Catalog

> These snippets use `autoAlpha`, not bare `opacity`. Scene elements rest at `visibility: hidden; opacity: 0` in CSS (see the DON'Ts below); `autoAlpha` tweens opacity *and* clears `visibility`, so the element actually appears. A plain `opacity` tween would leave `visibility: hidden` in place and the element would never show.

### Fade Up
Clean, professional. Default for headlines and body copy.

```js
tl.fromTo(".fade-up",
  { y: 40, autoAlpha: 0 },
  { y: 0, autoAlpha: 1, duration: 0.6, ease: "power3.out", stagger: 0.08 },
  0.2);
```

### Scale In
Energetic, modern. Good for badges, stat cards, CTAs.

```js
tl.fromTo(".scale-in",
  { scale: 0.85, autoAlpha: 0 },
  { scale: 1, autoAlpha: 1, duration: 0.55, ease: "back.out(1.4)" },
  0.3);
```

### Stagger
Multiple elements arriving in sequence — list items, feature pills, social proof logos.

```js
tl.fromTo(".feature-pill",
  { y: 24, autoAlpha: 0 },
  { y: 0, autoAlpha: 1, duration: 0.45, ease: "power2.out", stagger: 0.12 },
  0.4);
```

### Typewriter
Reveal headline word-by-word for emphasis. Wrap each word in a `<span class="word">` server-side or in setup.

```js
tl.fromTo(".word",
  { y: 12, autoAlpha: 0 },
  { y: 0, autoAlpha: 1, duration: 0.35, ease: "power2.out", stagger: 0.06 },
  0.2);
```

### Counter
Animate a number from 0 to a target. Use a proxy object — never tween `textContent` directly.

```js
const stat = { v: 0 };
tl.to(stat, {
  v: 12_500,
  duration: 2.2,
  ease: "power1.out",
  onUpdate: () => { document.getElementById("stat").textContent = Math.round(stat.v).toLocaleString(); }
}, 0.8);
```

### Step Label / Chapter Overlay

Tutorial scenes carry an on-screen `Step N of M` pill + chapter title, layered over a clip
or recap scene (authored copy from the storyboard `Step label:`/`Chapter:` fields). `autoAlpha`
reveal; **no exit tween** — the inter-scene transition owns the exit. Text ≥24px.

```html
<div class="chapter-ov">
  <span class="step-pill">Step 2 of 5</span>
  <span class="chapter-title">Configure the pipeline</span>
</div>
<style>
  [data-composition-id="scene-NN-clip"] .chapter-ov{position:absolute;left:64px;top:56px;z-index:5;
    display:flex;align-items:center;gap:20px;visibility:hidden;opacity:0}
  [data-composition-id="scene-NN-clip"] .step-pill{font-family:"Geist Mono",monospace;font-size:24px;
    font-weight:600;color:#fff;background:#0a72ef;padding:8px 18px;border-radius:999px}
  [data-composition-id="scene-NN-clip"] .chapter-title{font-size:34px;font-weight:600;color:#fff;
    text-shadow:0 2px 12px rgba(0,0,0,.6)}
</style>
```

```js
tl.fromTo(root + ' .chapter-ov', { y: -16, autoAlpha: 0 },
  { y: 0, autoAlpha: 1, duration: 0.4, ease: "power2.out" }, 0.2);
```

## Screenshot Presentation

### Browser Mockup with 3D Tilt

Pure CSS — no GSAP needed for the tilt itself.

```html
<div class="mockup">
  <img src="public/screenshots/scene-01.png" alt="">
</div>

<style>
  .mockup {
    transform: perspective(1000px) rotateY(-5deg) rotateX(3deg);
    box-shadow: 0 30px 60px rgba(0,0,0,0.4);
    border-radius: 12px;
    overflow: hidden;
    max-width: 75%;
  }
  .mockup img { width: 100%; display: block; }
</style>
```

Animate the mockup's entrance with `tl.fromTo()` — `y`, `opacity`, `scale`. Keep the perspective static; animating perspective values is jittery.

### Floating Card
Screenshot with rounded corners + large soft shadow. Float in from below (`y: 60, opacity: 0, ease: "expo.out", duration: 0.9`).

### Device Frame
Wrap the `<img>` in a device frame `<div>` (laptop or phone). Frame is static — the screenshot **inside** can pan or scroll via a child wrapper translated by GSAP.

## Camera & Depth

This is the vocabulary that gives a still the cinematic life it otherwise lacks — the difference between a screenshot pasted on a flat surface and *the real product, framed with depth and motivated motion*. The default beat of a product video is a captured screenshot (see `templates/scene-screenshot.html`) with one of these moves on it; flat text scenes are connective tissue between them, not the substance.

These earn their keep only when **motivated** — pushing toward the thing the eye should land on, scrolling to reveal what's below the fold, parallaxing real product layers. Pile on particles, 3D, grain, and ambient loops and you've traded a flat template for a busy one (see `anti-slop.md` § P1/P2). Pick **one** move per scene, key it to the work it does, and respect every ban in § DON'Ts — these entries add structured *permission with guardrails*, never a loophole.

All snippets below are JS timeline fragments — `tl.fromTo()` / `tl.to()` on the scene's paused timeline. The GSAP `<script>` tag (with its pinned SRI hash) lives in the scene skeleton, not in these fragments.

### Camera Moves on Stills

The aesthetic default for a held screenshot: a slow **push** (scale up toward a focal region), **pull** (scale down to reveal context), **lateral drift**, or **diagonal drift** — always on the **non-timed wrapper** (`.shot-browser` / `.clip-frame`), **never** the `<img>`/`<video>` dimensions (see § DON'Ts). Set `transformOrigin` at the region the eye should land on (x% y% of the frame). Pull `app-showcase` from the HyperFrames catalog (`npx hyperframes add app-showcase`) when you want a ready-framed device/hybrid mockup to move; hand-author the wrapper below only when the catalog frame doesn't fit.

```js
// Slow push toward a focal UI region. transformOrigin points at the thing
// the eye should land on. Wrapper only — the <img> is along for the ride.
tl.fromTo(root + ' .shot-browser',
  { scale: 1.0 },
  { scale: 1.06, transformOrigin: "32% 28%", duration: 2.2, ease: "power1.inOut" },
  1.1);
```

**Guardrails:**

- **Release before the confirmed inter-scene transition window.** End the move (and any settle) before the duration mapped from `transition_speed` (`quick = 0.4s`, `medium = 0.7s`, `slow = 1.2s`) so it never pulls back mid-transition. No scene-internal exit tween on non-final scenes — the root transition owns the exit (§ DON'Ts).
- **Only the closing scene may end mid-hold.** Because the closing scene exits passively (no transition), a push there can settle/hold instead of releasing. But on the closing scene the move must **push or hold only — never pull back** (a pull-out on the final frame reads as the video walking away from the product). The conservative default is no camera move on the closing scene at all (`templates/scene-screenshot.html` bakes this in); a held push is the deliberate exception.

**When footage text is too small (the legibility case).** When narrative-critical UI text in recorded footage renders below ~24px in the final frame, this push *is* the remedy: scale the non-timed `.clip-frame` wrapper toward the text. Key it to **footage time** (seconds into the clip); if the clip's `Speed` ≠ 1, remap the times proportionally. Release before the crossfade as above.

Effective size: `effective_px = source_px × scale × (rendered_frame_width / source_capture_width)`. Pick `scale` so the smallest narrative-critical glyph clears 24px. Verify by eye with `npx hyperframes snapshot . --at <focal-t>`.

### Scroll-Within-Frame

Reveal a tall full-page capture by panning it upward inside a fixed `overflow:hidden` viewport — the framed browser stays put while the page scrolls inside it. Drive it with a **timeline `translateY` on the INNER non-timed wrapper** (`.shot-pan`) only.

```js
// Travel = (viewHeight − renderedImageHeight), negative. Measure from the real
// PNG so the end lands on the footer, not past it.
tl.to(root + ' .shot-pan',
  { y: -640, duration: 3.0, ease: "power1.inOut" },
  1.1);
```

**Guardrail:** **NEVER** drive this with `scrollTop`, a `scroll` event listener, or an `IntersectionObserver`. None of those are pure functions of timeline `t`, so they break HyperFrames' deterministic paused-timeline seek (a seeked frame would read whatever scroll state the DOM happened to be in). The translate is the only deterministic path. Release before the crossfade; no exit on non-final scenes.

### Motivated Parallax

Depth from the **real product**: split a captured UI (or a foreground UI panel + a background app surface) into 2–3 DOM layers and translate them at **different rates** so nearer layers travel further. This stays **2D translate** — no `perspective`, no 3D camera, no `rotateX/Y` on the layers. Pull `ui-3d-reveal` from the catalog (`npx hyperframes add ui-3d-reveal`) when a UI panel flying in from z-depth covers the beat; hand-author the layered translate below for a sustained drift.

Reveal each layer with `tl.fromTo()` + `autoAlpha` (never `tl.from()` — see the stagger trap above, which re-hides earlier-revealed siblings under stagger):

```js
// 3 layers of the SAME product, parallaxed. Back travels least, front most.
tl.fromTo(root + ' .layer-back',
  { y: 24, autoAlpha: 0 }, { y: 0,  autoAlpha: 1, duration: 0.6, ease: "power2.out" }, 0.2);
tl.fromTo(root + ' .layer-mid',
  { y: 40, autoAlpha: 0 }, { y: 0,  autoAlpha: 1, duration: 0.6, ease: "power2.out" }, 0.3);
tl.fromTo(root + ' .layer-front',
  { y: 64, autoAlpha: 0 }, { y: 0,  autoAlpha: 1, duration: 0.6, ease: "power2.out" }, 0.4);
// Sustained drift afterward — different rates = depth, still pure 2D translate.
tl.to(root + ' .layer-back',  { y: -12, duration: 2.4, ease: "power1.inOut" }, 1.0);
tl.to(root + ' .layer-front', { y: -48, duration: 2.4, ease: "power1.inOut" }, 1.0);
```

**Guardrail:** this is parallax on **real product layers**, the exact opposite of the **banned decorative blob / wave parallax** (`anti-slop.md` § P1 — "meaningless geometry"). If the layers aren't the actual UI, you're decorating, not building depth. Keep it 2D translate; animating `perspective` is jittery (§ Browser Mockup) and a 3D camera is out of scope. For atmosphere over the layers, the only sanctioned texture is a `grain-overlay` catalog block (`anti-slop.md` § P1) — never an ambient particle field.

### Anchored Callout / Spotlight

Direct attention to one region of an on-screen UI — either a **marker** drawn over the spot (sweep, ring, burst from `marker-highlight.md`) **or** a **spotlight** (a dimming overlay with a brighter hole over the region). This is the **highest slop risk** on the page: stacked highlights, glows, and dimmers turn a clean frame into a ransom note.

```js
// Spotlight = a full-frame dim that reveals over the region. Reveal via autoAlpha.
tl.fromTo(root + ' .spotlight-dim',
  { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.5, ease: "power2.out" }, 1.0);
```

**Emphasis budget (enforce).** The emphasis and marker-highlight limits are counted from the
budget table in `reasoning/scene-analysis.md` — the only place those numbers live (ADR-008). The
judgment for spending them:

- **Pick EITHER a marker highlight OR a spotlight, never both on one region.** Two attention cues
  aimed at the same place cancel each other out; the eye reads "busy", not "look here".
- **A marker highlight is a reserved editorial beat, not a tool.** Spend it on the single moment
  that most deserves it (`marker-highlight.md` § When to use which mode). A spotlight is the
  lighter-weight alternative once the marker is spent.
- **Reveal via `autoAlpha` — never `display`/`visibility`, never `clipPath`** (§ DON'Ts). The dim overlay's hole is a static `radial-gradient` mask or `box-shadow` inset; you fade the overlay in, you don't animate the cutout's shape.

### In-Scene Shine Sweep

A one-shot specular pass over a UI card — an absolutely-positioned gradient overlay whose `background-position` animates across the element once, as the card settles. This is **intra-scene**: it lives inside one scene and decorates one card. Nothing here applies to a scene-to-scene seam — that is `SEAM_LAW` / `SEAM_RENDER_MECHANICS` territory (`patterns/transition-catalog.md`). Pull `shimmer-sweep` from the catalog (`npx hyperframes add shimmer-sweep`) before hand-authoring — it's the tested version of this effect. Note what it is: `REGISTRY_CATALOG` lists it as an element-scoped *component*, which is precisely why it belongs here and cannot serve a seam.

```html
<div class="card-shine" aria-hidden="true"></div>
<style>
  .card-shine{
    position:absolute; inset:0; pointer-events:none; border-radius:inherit;
    background:linear-gradient(115deg, transparent 35%,
      rgba(255,255,255,.35) 47%, rgba(255,255,255,.85) 50%,
      rgba(255,255,255,.35) 53%, transparent 65%);
    background-size:250% 100%; background-position:-75% 0;
    opacity:0;
  }
</style>
```

```js
// One-shot: pop in, sweep across, fade out. NOT an ambient loop.
tl.to(root + ' .card-shine', { opacity: 1, duration: 0.08, ease: "power1.out" }, 1.0);
tl.to(root + ' .card-shine', { backgroundPosition: "175% 0", duration: 0.5, ease: "power2.inOut" }, 1.0);
tl.to(root + ' .card-shine', { opacity: 0, duration: 0.08, ease: "power1.in" }, 1.42);
```

**Guardrails:**

- **One-shot, not an ambient loop.** A shine that keeps sweeping the whole scene is the looping-motion tell (`anti-slop.md` § P2). Fire it once when the card lands.
- **Self-police `mix-blend-mode: screen` luminance.** If you add `mix-blend-mode: screen` for a hotter pop, `check` does not detect luminance overflow — it is not a luminance audit. Preview against your **brightest** scene background by eye; `screen` blending can push near-white past 100% luminance and produce a flash. If that happens, drop the band's `rgba` alpha to ~0.65, or remove the blend mode and rely on `opacity` alone. This caveat holds for **any** `screen`-blended band in this repo, in a scene or across a seam.

### Masked Reveal (mask-position)

Wipe a single element into view by animating **`mask-position`** over a **static** `mask-image` (e.g. a soft-edged gradient mask) — the mask stays fixed in shape, only its position slides, so the element is progressively unveiled. This is the **same safe class** as `background-position`: a continuous numeric property, fully seekable.

```html
<div class="masked-reveal"><img class="shot-img" src="public/screenshots/SHOT.png" alt=""></div>
<style>
  .masked-reveal{
    /* Static gradient mask; only its POSITION animates. Prefix for headless Chromium. */
    -webkit-mask-image:linear-gradient(100deg, transparent 0 40%, #000 60% 100%);
            mask-image:linear-gradient(100deg, transparent 0 40%, #000 60% 100%);
    -webkit-mask-size:250% 100%;  mask-size:250% 100%;
    -webkit-mask-position:100% 0;  mask-position:100% 0;   /* start: element hidden */
  }
</style>
```

```js
// Slide the mask so the element is unveiled left→right. Tween the prefixed
// property too — verify the unprefixed form animates in your target Chromium
// before relying on it alone.
tl.to(root + ' .masked-reveal',
  { webkitMaskPosition: "0% 0", maskPosition: "0% 0", duration: 0.7, ease: "power2.inOut" },
  0.8);
```

**Guardrail:** this is **distinct from the banned `clipPath` transitions** (§ DON'Ts, which carries the why). `mask-position` does **no polygon vertex interpolation** — the mask geometry is constant, only its offset moves, so there is no seam to mis-render. Keep the mask shape static; do not interpolate the mask's stops, and do not press this into service as an inter-scene transition — a seam is `SEAM_LAW`'s, not a scene's.

## Transitions are not a scene's business

Nothing in this file authors a scene-to-scene seam. A seam is a **composition-level** concern and
belongs to the doctrine:

- *Which* transition serves this moment, and how much transition energy the film can spend →
  `patterns/transition-catalog.md`.
- The law of the handoff — how this scene's exit determines the next scene's entry → `SEAM_LAW`
  (`motion-doctrine`), verified numerically by `SEAM_VERIFIER`.
- How the two scenes actually composite across the seam → `SEAM_RENDER_MECHANICS` (`seam-craft`).
- The named velocity-matched seams and their parameters → `CUT_CATALOG` (`cut-the-curve`).

The two consequences that bind scene authoring are already in § DON'Ts: **no exit animation on a
non-final scene** (the seam owns the exit) and **no `clipPath` transitions**. Transition duration
comes from the confirmed `transition_speed` in the brief and is never quietly shortened after the
user chose it (ADR-001); `workflows/phase-4-production.md` Step 4.5 is the wiring call site.

## Color Psychology

| Color | Feeling | Use For |
|-------|---------|---------|
| Blue (#3b82f6) | Trust, reliability | SaaS, enterprise |
| Purple (#8b5cf6) | Innovation, premium | AI, creative tools |
| Green (#22c55e) | Growth, success | Fintech, health |
| Orange (#f97316) | Energy, urgency | CTAs, highlights |
| Red (#ef4444) | Urgency, passion | Sales, alerts |

## Text Sizing Guide

| Element | Size Range | Weight |
|---------|-----------|--------|
| Hero headline | 80–120px | Bold/Black |
| Section title | 60–80px | Bold |
| Subtitle | 40–56px | Medium |
| Body text | 32–44px | Regular |
| Caption | 24–32px | Regular |
| Stat number | 90–140px | Bold |

HyperFrames' `check` enforces WCAG AA contrast (4.5:1 normal text, 3:1 large text ≥24px or ≥19px bold). Tiny text is *not* auto-flagged — self-police anything below 24px because it loses legibility at typical playback resolutions.

## DON'Ts (Critical)

- **No jitter or shake** — looks cheap; HyperFrames `check` will not catch this, you must self-police.
- **No full 360° rotations** — disorienting. Subtle `rotateY` ≤ 8° or `rotateZ` ≤ 4° only.
- **No exit animations on non-final scenes** — let the transition handle the exit. Animating the same element out and then transitioning the scene out is double-motion.
- **No `clipPath` for transitions** — *the why, learned the hard way in this repo:* a polygon `clipPath` that sweeps between two scenes leaves a **1px anti-aliased black sliver** along the moving edge, because the exiting and entering half-planes never share an exact subpixel boundary — each anti-aliases its own edge against nothing, and the page behind shows through the gap. It survives every gate (`check` reads layout and contrast, not a hairline seam) and only appears in the rendered frames. Reach for a crossfade with a full-frame light overlay over it instead — the light family in `TRANSITION_FAMILIES` — and let `SEAM_RENDER_MECHANICS` own the compositing. **This bans `clipPath` as a *seam*, not as a static shape** — a fixed `clip-path` on an element, or an animated `mask-position` over a static mask (§ Masked Reveal), interpolates no vertices and has no seam to mis-render.
- **Never animate `display`, `visibility`, or call `.play()` inside a timeline** — GSAP can't tween `display`/`visibility` (they're binary), and `.play()` from inside a timeline breaks HyperFrames' deterministic seek. Use `autoAlpha` (which tweens opacity AND toggles visibility) or `opacity` + `pointer-events: none`:
  ```js
  // ✅ correct — autoAlpha tweens opacity AND toggles visibility
  tl.fromTo("#el", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.5 }, 0.3);

  // ❌ wrong — visibility:hidden is binary, GSAP can't interpolate it
  tl.from("#el", { visibility: "hidden", duration: 0.5 }, 0.3);
  ```
- **Never animate `<img>` dimensions directly** — wrap each animated `<img>` in a non-timed `<div>` and tween the wrapper's `transform` (`scale`, `translate`). Animating `width`/`height` on the `<img>` causes layout recompute that breaks deterministic seek.
- **Never use `gsap.set()` at script-load time on elements that enter the timeline later** — sub-comp clips with `data-start > 0` aren't in the DOM at page load. Their elements don't exist yet, so `gsap.set("#late-element", ...)` is a no-op. Instead, use `tl.set(selector, vars, timePosition)` *inside the timeline* at or after the clip's `data-start`:
  ```js
  // ✅ correct — runs inside the timeline at t=5s, after #late-card exists
  tl.set("#late-card", { opacity: 0, x: -100 }, 5);
  tl.to("#late-card", { opacity: 1, x: 0, duration: 0.5 }, 5);

  // ❌ wrong — fires before #late-card is rendered, has no effect
  gsap.set("#late-card", { opacity: 0, x: -100 });
  tl.to("#late-card", { opacity: 1, x: 0, duration: 0.5 }, 5);
  ```
- **No tiny text** — below 24px is unreadable in rendered video. `check` won't flag it (contrast, not size), so self-police.
