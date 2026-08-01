# Marker Highlight Patterns

Five drawing-mode patterns for emphasizing words in product videos — kicker lines, value props, stats, callouts. Pure CSS + GSAP, no library dependency, fully deterministic under HyperFrames render.

Adapted from `MARKER_PATTERNS` in the `hyperframes-animation` skill — read it for caption-specific variations, multi-line cases, and the full pattern depth; path in `compat/ecosystem.md`. This file is product-video focused: each mode below is paired with the moment in a promo arc where it lands best.

## When to use which mode

| Mode | Best for | Energy | Promo arc moment |
|------|----------|--------|------------------|
| Highlight | Kicker lines, value props, single emphasis words | Calm, confident | Hook, solution, results |
| Circle | One-word emphasis on a critical claim | Casual, hand-drawn | Pain reveal, before/after |
| Burst | High-energy stat numbers, surprise reveals | Loud, kinetic | Stat moments, CTA |
| Scribble | Underline a phrase, draw attention to a quote | Editorial, playful | Pull-quotes, social proof |
| Sketchout | "Before" prices, struck-out competitors | Comparative | Before/after, competitor frames |

One mode per scene. Cycling modes across a 30s spot reads as chaotic — pick one tone and commit.

## 1. Highlight — yellow marker sweep

Most common. Behind-text yellow bar that sweeps from left → right under a key phrase.

```html
<span class="mh-highlight-wrap">
  <span class="mh-highlight-bar" id="hl-1"></span>
  <span class="mh-highlight-text">ship faster</span>
</span>
```

```css
.mh-highlight-wrap {
  position: relative;
  display: inline;
}
.mh-highlight-bar {
  position: absolute;
  top: 0; left: -6px; right: -6px; bottom: 0;
  background: #fdd835;          /* match brand accent for non-yellow palettes */
  opacity: 0.35;
  transform: scaleX(0);
  transform-origin: left center;
  border-radius: 3px;
  z-index: 0;
}
.mh-highlight-text { position: relative; z-index: 1; }
```

```js
// In the scene's GSAP timeline. Fire after the kicker line has settled.
tl.to("#hl-1", { scaleX: 1, duration: 0.5, ease: "power2.out" }, 0.8);
```

**Tuning:** `opacity: 0.20` on light backgrounds, `0.45` on dark. Drop `border-radius` to `0` for editorial; keep `3px` for friendly.

**Skew for hand-drawn feel:** `gsap.set("#hl-1", { skewX: -2 });` before the tween.

## 2. Circle — hand-drawn ellipse

Wraps a critical word with a slightly rotated red ring. Use sparingly — overused, it reads as comic-book.

```html
<span class="mh-circle-wrap">
  <span class="mh-circle-text">CRITICAL</span>
  <span class="mh-circle-ring" id="circle-1"></span>
</span>
```

```css
.mh-circle-wrap { position: relative; display: inline; }
.mh-circle-text { position: relative; z-index: 1; }
.mh-circle-ring {
  position: absolute;
  top: 50%; left: 50%;
  width: 130%; height: 160%;
  transform: translate(-50%, -50%) rotate(-3deg) scale(0);
  border: 3px solid #e53935;     /* brand emphasis colour */
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
}
```

```js
tl.to("#circle-1", {
  scale: 1,
  rotation: -3,
  duration: 0.6,
  ease: "back.out(1.7)",
  transformOrigin: "center center",
}, 0.9);
```

**Variations:** `width: 150% / height: 180%` for short words (1–2 letters), `border-radius: 30%` for a rounded-rectangle outline, `width: 150% / height: 130%` for a wide ellipse over a short phrase.

## 3. Burst — radiating lines

Lines erupt outward from a word's centre. High-energy. Perfect for **stat reveals** ("$12M raised", "10× faster") and CTA punchlines.

```html
<span class="mh-burst-wrap">
  <span class="mh-burst-text">10×</span>
  <span class="mh-burst-container" id="burst-1">
    <!-- 12 lines at 30° spacing, varied length -->
    <span class="mh-burst-line" style="--angle:   0deg; --len: 70px;"></span>
    <span class="mh-burst-line" style="--angle:  30deg; --len: 55px;"></span>
    <span class="mh-burst-line" style="--angle:  60deg; --len: 80px;"></span>
    <span class="mh-burst-line" style="--angle:  90deg; --len: 45px;"></span>
    <span class="mh-burst-line" style="--angle: 120deg; --len: 65px;"></span>
    <span class="mh-burst-line" style="--angle: 150deg; --len: 75px;"></span>
    <span class="mh-burst-line" style="--angle: 180deg; --len: 50px;"></span>
    <span class="mh-burst-line" style="--angle: 210deg; --len: 60px;"></span>
    <span class="mh-burst-line" style="--angle: 240deg; --len: 80px;"></span>
    <span class="mh-burst-line" style="--angle: 270deg; --len: 40px;"></span>
    <span class="mh-burst-line" style="--angle: 300deg; --len: 70px;"></span>
    <span class="mh-burst-line" style="--angle: 330deg; --len: 55px;"></span>
  </span>
</span>
```

```css
.mh-burst-wrap { position: relative; display: inline; }
.mh-burst-text { position: relative; z-index: 2; }
.mh-burst-container {
  position: absolute;
  top: 50%; left: 50%;
  width: 0; height: 0;
  z-index: 1;
}
.mh-burst-line {
  position: absolute;
  display: block;
  width: 3px;
  height: var(--len);
  background: #1e88e5;          /* brand accent */
  left: -1.5px;
  top: calc(-1 * var(--len));
  transform: rotate(var(--angle));
  transform-origin: bottom center;
  opacity: 0;
}
```

```js
tl.fromTo(
  "#burst-1 .mh-burst-line",
  { scaleY: 0, opacity: 0 },
  { scaleY: 1, opacity: 1, duration: 0.4, ease: "power2.out", stagger: 0.03 },
  0.9
);
```

**Critical:** vary line lengths in the 40–80px range. Equal lengths look mechanical and cheap.

## 4. Scribble — wavy SVG underline

A drawn-on-the-fly underline (or strikethrough). Friendly and editorial. Great for pull-quotes and social-proof framing ("'It just works.' — @user").

```html
<span class="mh-scribble-wrap">
  <span class="mh-scribble-text">it just works</span>
  <svg class="mh-scribble-svg" viewBox="0 0 500 24" preserveAspectRatio="none">
    <path
      id="scribble-1"
      d="M0,12 Q31,0 62,12 Q93,24 125,12 Q156,0 187,12 Q218,24 250,12 Q281,0 312,12 Q343,24 375,12 Q406,0 437,12 Q468,24 500,12"
      fill="none"
      stroke="#FDD835"
      stroke-width="3"
      stroke-linecap="round"
    />
  </svg>
</span>
```

```css
.mh-scribble-wrap { position: relative; display: inline; }
.mh-scribble-text { position: relative; z-index: 1; }
.mh-scribble-svg {
  position: absolute;
  left: 0; bottom: -6px;
  width: 100%; height: 24px;
  z-index: 0;
}
```

```js
// One-time path-length measurement — keep this in the scene's <script>,
// not the timeline, so it runs at parse time.
var path = document.querySelector("#scribble-1");
var len  = path.getTotalLength();
gsap.set(path, { strokeDasharray: len, strokeDashoffset: len });

tl.to("#scribble-1",
  { strokeDashoffset: 0, duration: 0.8, ease: "power1.inOut" },
  0.9);
```

**Strikethrough variant:** move the SVG to `top: 50%; transform: translateY(-50%);` instead of `bottom: -6px`.

**Wavy path tuning:**
- Tight waves (more wiggle): half-wave every 25px.
- Loose waves (calmer): half-wave every 50px.
- Amplitude: y range `0..24` (standard) or `0..16` (subtle).

## 5. Sketchout — cross-hatch strikethrough

Two angled lines cross over de-emphasized text. The **definitive** "old vs new" pattern — strike out a competitor or an outdated price.

```html
<span class="mh-sketchout-wrap">
  <span class="mh-sketchout-text">$99 / month</span>
  <span class="mh-sketchout-lines" id="sketchout-1">
    <span class="mh-sketchout-line mh-sketchout-fwd"></span>
    <span class="mh-sketchout-line mh-sketchout-bwd"></span>
  </span>
</span>
```

```css
.mh-sketchout-wrap { position: relative; display: inline; }
.mh-sketchout-text { position: relative; z-index: 0; }
.mh-sketchout-lines {
  position: absolute;
  top: 0; left: -4px; right: -4px; bottom: 0;
  overflow: hidden;
  z-index: 1;
}
.mh-sketchout-line {
  position: absolute;
  display: block;
  top: 50%; left: 0;
  width: 100%; height: 2px;
  background: #e53935;
  transform-origin: left center;
  transform: scaleX(0);
}
.mh-sketchout-fwd { transform: scaleX(0) rotate(-12deg); }
.mh-sketchout-bwd { transform: scaleX(0) rotate( 12deg); }
```

```js
tl.to("#sketchout-1 .mh-sketchout-fwd",
  { scaleX: 1, duration: 0.3, ease: "power2.out" },
  1.0);

tl.to("#sketchout-1 .mh-sketchout-bwd",
  { scaleX: 1, duration: 0.3, ease: "power2.out" },
  1.15);
```

**Pair with a fresh "new" callout** below — circle or highlight mode — for a strong before/after beat.

## Don'ts

- **Don't mix modes within a single scene.** Reads as undisciplined. One mode per scene; rotate only across major narrative beats.
- **Don't animate marker colour.** Set it once, fade or scale it in. Animated hue shifts on emphasis cues look like Web 2.0.
- **Don't strike out your own brand name.** Sketchout is for *what you replace*, not who you are. If you want to ironize, use circle.
- **Don't time the highlight earlier than the word's settle.** Always sweep *after* the text has landed at its rest position (Phase 3 `gsap.from(...)` entrance must complete first). Otherwise it looks like the highlight is leading the text.

## Source

Full versions of these patterns (including multi-line variants, mode-cycling for captions, and the path-length math) live in `MARKER_PATTERNS`, owned by the `hyperframes-animation` skill; path in `compat/ecosystem.md`. This file is a product-video focused subset.
