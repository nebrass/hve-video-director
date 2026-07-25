# Cal.com — Video Production Notes

Brand specification for HyperFrames compositions. See the Source line at the bottom for research provenance.

## 1. Atmosphere

A masterclass in monochromatic restraint — a grayscale world where boldness comes from confidence rather than colour. Cal Sans (custom geometric display) creates dense, architectural headlines that feel carved into the page. The elevation system is unusually sophisticated for a minimal site: multi-layered shadows combining ring borders, soft diffused shadows, and inset highlights. Built on Framer.

## 2. Palette (video-essential)

| Role | Hex |
|---|---|
| Canvas | `#ffffff` |
| Primary text (Charcoal) | `#242424` (warmer than black) |
| Deepest text | `#111111` |
| Secondary text (Mid gray) | `#898989` |
| Subtle surface tint | `#f5f5f5` |
| Link (rare) | `#0099ff` |
| Focus ring | `#3b82f6` at 50% opacity |
| Border (shadow-based) | `rgba(34,42,53,0.08–0.10)` |

The brand is *purely grayscale*. The single blue link colour is the only chromatic moment. **Do not** introduce a brand accent that wasn't in the upstream system.

## 3. Typography

- **Display:** `Cal Sans` (custom geometric, open-source on Google Fonts). Extremely tight letter-spacing at large sizes — defining feature.
- **Body:** `Inter` (Cal Sans is for display only; Inter handles prose).
- **UI light:** `Cal Sans UI Variable Light` (300 weight) with -0.2px tracking — softer voice.
- **Mono:** `Roboto Mono`.

Video sizes:

| Role | Size | Weight |
|---|---|---|
| Hero (Cal Sans) | 130–170px | 600 |
| Section title (Cal Sans) | 80–100px | 600 |
| Feature heading (Cal Sans) | 56–72px | 600 |
| Body (Inter) | 32–44px | 400 |
| Body light (Cal Sans UI Light) | 32–40px | 300 |
| Caption | 24–28px | 500 |
| Stat number (Cal Sans) | 160–200px | 600 |

## 4. Depth

Sophisticated multi-layer shadows — ring border + soft diffused + inset highlight:

```css
box-shadow:
  inset 0 1px 0 rgba(255,255,255,0.6),     /* inset highlight */
  0 0 0 1px rgba(34,42,53,0.10),           /* ring border */
  0 4px 12px rgba(0,0,0,0.06),             /* soft elevation */
  0 12px 32px rgba(0,0,0,0.08);            /* ambient depth */
```

Border-radius scale: 2px to 9999px (pill). Cards typically 8–12px; buttons pill.

## 5. Motion

Cal.com is built on **Framer** — Framer Motion's spring physics is in the brand DNA. Moderate energy, approachable but not flourishy.

| Property | Choice |
|---|---|
| Default entrance ease | `power3.out` (curves) for opacity; spring for position |
| Position / scale | spring-approx: `gsap.from(..., { duration: 0.6, ease: "back.out(1.05)" })` — very subtle overshoot |
| Entrance duration | 0.5–0.7s |
| Stagger | 0.08–0.12s |
| Scene-to-scene transition | Crossfade 0.4–0.5s, `power2.inOut` |
| Section-boundary | Surface tint shift (`#ffffff` → `#f5f5f5`) |
| Counter ease | `power2.out`, ~2.0s |
| Product-shot camera | Restrained 1.02→1.00 settle over ~0.8s, `power2.out` — confident without showing off (inferred from Framer-Motion defaults) |
| Avoid | Hard flash, glitch, shader transitions — wrong tone for OSS friendliness |

The brand is "approachable competence." Motion is confident without showing off.

## 6. Video applications

- **Hero scene:** Cal Sans 600 wordmark at 150px on `#ffffff`. Tagline in Inter 400 at 36px in mid-gray. Both arrive with `power3.out` over 0.6s.
- **Feature scene:** Scheduling UI screenshot in a card with the multi-layer shadow stack (the ring-border-plus-soft-shadow technique is signature). Caption in Cal Sans UI Light at 36px in `#898989`.
- **Stat scene:** Number at 180px Cal Sans 600 in `#242424`. Counter ease `power2.out` over ~2.0s. Label in Inter 400 at 32px below.
- **CTA scene:** Pill button with `#242424` background, `#ffffff` text in Inter 600 at 32px ("Get started — it's free"). Brand wordmark above. Hold.

## 7. Avoid

- **Brand colour.** Cal.com deliberately has none. Adding one (even a muted blue) reads as off-brand.
- **Sans body in display.** Inter is for body. Cal Sans does display; the tight letter-spacing IS the brand voice at large sizes.
- **Pure black headings.** `#242424` is warmer than `#000000` and the system specifies the difference.
- **Decorative shadows.** The depth system is precise. Adding a casual `box-shadow: 0 4px 8px black` undermines the sophistication.

## Source

Informed by studying VoltAgent/awesome-design-md `design-md/cal/DESIGN.md` and the brand's actual product. Original prose authored by hve-video-director, MIT licensed.
