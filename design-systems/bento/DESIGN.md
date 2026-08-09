# Bento — Video Production Notes

Brand specification for HyperFrames compositions. See the Source line at the bottom for research provenance.

## 1. Atmosphere

Modular grid layout with card-like blocks. Clear hierarchy, soft spacing, subtle visual contrast. Playful link-in-bio energy: bold colour blocks, casual warmth, scannable density. The brand reads as *accessible, friendly, slightly retro*.

## 2. Palette (video-essential)

| Role | Hex |
|---|---|
| Primary (CTA) | `#FAD4C0` (peach) |
| Secondary | `#80A1C1` (steel blue) |
| Success | `#16A34A` |
| Warning | `#D97706` |
| Danger | `#DC2626` |
| Surface (background) | `#FFF5E6` (warm cream) |
| Text | `#111827` |

The cream surface (`#FFF5E6`) is the brand's atmospheric signature — most other systems use white. Don't substitute pure `#ffffff`.

Cap visible Primary uses at 2 per scene; the peach is meant to draw the eye to ONE thing.

## 3. Typography

- **Display + Body:** `Inter`.
- **Mono:** `JetBrains Mono`.
- **Scale:** 12 / 14 / 16 / 20 / 24 / 32 (web baseline — scale up substantially for video).

Bento's instruction: *"Headings should carry the style personality; body text should optimize scanability and contrast."*

Video sizes:

| Role | Size | Weight |
|---|---|---|
| Hero | 110–140px | 700 |
| Section title | 64–80px | 700 |
| Card title (the "bento" block heading) | 40–56px | 600 |
| Body | 28–40px | 400 |
| Caption | 24px | 500 |
| Stat | 140–180px | 700 |

## 4. Depth

Modular grid blocks ("bento boxes") with rounded corners and a subtle drop:

```css
border-radius: 20px;
background: #ffffff;     /* card on cream canvas */
box-shadow:
  1px 2px 4px rgba(0,0,0,0.04),
  2px 8px 24px rgba(0,0,0,0.06);
```

The grid-of-cards aesthetic is the brand's structural signature. Use it for feature reveals — multiple small cards entering with stagger.

**Shadow offsets follow the film's key light, not this page.** The x-offsets above assume the
house key at 32% 14% (upper-left). Blur, alpha and colour are this brand's and never move; only
the offset answers to the light, and it flips sign if a film declares its key on the other side.
A stack with every casting layer at x=0 reads as no light at all — it is a web-card shadow, and
on video it disappears.

## 5. Motion (from upstream § 7)

Upstream rule: *"Default to short, purposeful transitions (150–250ms) with stable easing. Use subtle transitions that emphasize Primary (#FAD4C0) as the interaction signal."*

| Property | Choice |
|---|---|
| Default entrance ease | `power2.out` (stable, not bouncy) |
| Card-grid entrance | Stagger across the bento blocks — each card 0.4s with 0.08s offset |
| Entrance duration | 0.4–0.6s (matches upstream 150–250ms with video uplift) |
| Stagger | 0.06–0.10s (snappy for bento-grid reveals) |
| Scene-to-scene transition | Crossfade 0.4s, `power2.inOut`. Cards-shuffle effect (each card stagger-fades out then new scene's cards stagger-fade in) is on-brand. |
| Section-boundary | Surface tint shift OR card-shuffle |
| Counter ease | `power2.out`, ~1.6s |
| Product-shot camera | Gentle 1.03→1.00 push-in over ~1.2s, `power2.out` — friendly, never flashy (inferred from the brand's soft card motion) |
| Avoid | Glitch, flash, hard cuts — wrong tone for friendly link-in-bio |

The signature animated moment is **bento-grid reveal**: a 2×3 grid of cards each entering with stagger from `y: 30, opacity: 0`. Plan one such scene per video.

## 6. Video applications

- **Hero scene:** `#FFF5E6` cream canvas. Inter 700 wordmark at 130px in `#111827`. Tagline at 36px below. One Primary (`#FAD4C0`) emphasized word in the tagline.
- **Bento-grid feature scene (the signature):** 2×3 grid of `#ffffff` cards on cream canvas, each containing one feature title + small icon. Cards enter staggered with `tl.fromTo(".card", { y: 30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.4, stagger: 0.08, ease: "power2.out" }, 0.3)` — `fromTo` is required because `tl.from()` + stagger + CSS `opacity: 0` hits the flash-then-disappear trap (see `patterns/visual-patterns.md` § "The `tl.from()` stagger trap"). Hold for ~3s, then transition.
- **Stat scene:** Number at 160px Inter 700 on cream surface. Counter ease `power2.out` over 1.6s. Label at 28px below.
- **CTA scene:** Pill button with Primary peach background (`#FAD4C0`), `#111827` text in Inter 600 at 28px. Wordmark in Inter 700 above. Hold.

## 7. Avoid

- **Pure white canvas.** The cream `#FFF5E6` is the brand's atmospheric tone. Substituting white reads as generic.
- **Slow, dignified motion.** Bento is playful — 0.8s+ entrances feel off-brand. Stay 0.4–0.6s.
- **Monolithic full-bleed scenes.** Bento's voice is grid-of-cards. A single-element-on-canvas hero scene is fine, but feature/showcase scenes should lean into the grid aesthetic.
- **Cool palette.** The warm cream + peach is the system. Cool grays read as anti-Bento.

## Source

Informed by studying Bento's actual product. Original prose authored by hve-video-director, MIT licensed.
