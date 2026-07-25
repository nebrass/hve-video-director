# Stripe — Video Production Notes

Brand specification for HyperFrames compositions. See the Source line at the bottom for research provenance.

## 1. Atmosphere

A financial institution redesigned by a world-class type foundry. Clean white canvas, deep-navy headings, signature saturated purple as the single brand anchor. The voice is *whispered authority* — confident enough not to shout. The signature texture is blue-tinted multi-layer shadows that read as atmospheric depth, like elements floating in a twilight sky.

## 2. Palette (video-essential)

| Role | Hex |
|---|---|
| Background canvas | `#ffffff` |
| Primary text / headings | `#061b31` (deep navy — not black) |
| Brand anchor (accent) | `#533afd` (Stripe purple) |
| Dark scene background | `#1c1e54` |
| Body secondary | `#273951` |
| Decorative gradient stops | `#ea2261` (ruby) → `#f96bee` (magenta) |
| Shadow tint | `rgba(50,50,93,0.25)` + `rgba(0,0,0,0.10)` |

Use the purple sparingly: max 1–2 visible uses per scene. Ruby/magenta only for decorative gradient moments, never as text.

## 3. Typography

- **Display:** `sohne-var` with OpenType `"ss01"`. **Weight 300** at display sizes (the anti-shout move). Aggressive negative tracking (-1.4px at 56px).
- **Body:** `sohne-var` weight 300–400, `"ss01"` everywhere.
- **Mono / data:** `SourceCodePro` with `"tnum"` for tabular numbers (financial data, stats).

Fallbacks: `SF Pro Display`, `SFMono-Regular`.

Video sizes (scale up from web — the floor is 24px):

| Role | Size | Weight |
|---|---|---|
| Hero | 110–140px | 300 |
| Section title | 72–96px | 300 |
| Body / value prop | 36–48px | 300–400 |
| Caption / kicker | 24–28px | 400 |
| Stat number | 140–200px | 300 (tnum) |

## 4. Depth

Multi-layer blue-tinted shadows for cards / browser mockups:

```css
box-shadow:
  0 7px 14px rgba(50,50,93,0.10),
  0 3px 6px  rgba(0,0,0,0.08),
  0 12px 36px rgba(50,50,93,0.15);
```

Border-radius: **4–8px**. Nothing pill-shaped, nothing aggressively rounded.

## 5. Motion (video-critical)

Stripe's brand is *premium-restraint*. Motion is dignified and slow.

| Property | Choice |
|---|---|
| Default entrance ease | `expo.out` |
| Stat-counter ease | `power1.inOut` |
| Scale-in ease | `power3.out` (NOT `back.out` — no bounce, no overshoot) |
| Entrance duration | 0.7–1.0s |
| Stagger | 0.12–0.18s (deliberate, not machine-gun) |
| Scene-to-scene transition | Plain crossfade 0.5–0.7s, `power2.inOut`. No flash. |
| Section-boundary transition | Slow gradient wipe (ruby→magenta band), 0.7s |
| Product-shot camera | Imperceptible 1.04→1.0 drift over ~2s, `power1.inOut` |
| Avoid | `back.out`, `elastic`, flash transitions, glitch, hard cuts |

The "anti-shout" voice extends to motion: a Stripe video that snaps and pops is off-brand.

## 6. Video applications

- **Hero scene:** A single declarative line at 110px, weight 300, deep navy on white. Subtitle at 36px arrives 0.5s later. No mockup yet. Let the type breathe.
- **Feature scene:** A product screenshot inside a card with the signature blue-tinted shadow stack, tilted ≤4° on Y. Caption beside it in weight-300 type.
- **Stat scene:** Centered number at 180px, `tnum`-enabled, weight 300, deep navy. Counter tweens from 0 over ~2.5s `power1.inOut`. Label below in 36px secondary.
- **CTA scene:** Brand mark + a single line of microcopy. No big button — let the brand carry the close.

## 7. Avoid

- **Default purple gradient hero.** Stripe's purple is anchored, not gradient-led. A purple→cyan two-stop reads as generic-AI-promo, not Stripe.
- **Bold headlines.** The weight-300 anti-shout is the brand. Switching to bold defeats the system.
- **Hard flash transitions.** Off-tone for premium fintech.
- **Emoji.** Use monoline icons or no icons at all.

## Source

Informed by studying VoltAgent/awesome-design-md `design-md/stripe/DESIGN.md` and the brand's actual product. Original prose authored by hve-spielberg, MIT licensed.
