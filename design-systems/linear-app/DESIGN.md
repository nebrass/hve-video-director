# Linear — Video Production Notes

Brand specification for HyperFrames compositions. See the Source line at the bottom for research provenance.

## 1. Atmosphere

Darkness as the *native medium* — not a dark theme applied to a light design. Information emerges from near-black like starlight. Achromatic palette with a single indigo-violet accent used sparingly. Every element exists in a carefully calibrated luminance hierarchy. The feeling is *engineered, not designed*.

## 2. Palette (video-essential)

| Role | Hex |
|---|---|
| Marketing background (canvas) | `#08090a` |
| Panel / second-level surface | `#0f1011` |
| Elevated surface (cards) | `#191a1b` |
| Primary text | `#f7f8f8` |
| Secondary text | `#d0d6e0` |
| Tertiary / muted | `#8a8f98` |
| Brand accent | `#5e6ad2` (CTAs) / `#7170ff` (interactive) |
| Status green (rare) | `#27a644` |
| Border | `rgba(255,255,255,0.05)` |

Single accent. Cap visible uses at 2 per scene.

## 3. Typography

- **Display + Body:** `Inter Variable` with OpenType `"cv01", "ss03"` globally (geometric alternates, single-story `a`).
- **Mono:** `Berkeley Mono`, fallback `SF Mono`.
- **Signature weight:** **510** for UI text — between regular and medium. 590 for emphasis. 400 for body prose.

Aggressive negative tracking at display: -1.58px at 72px, -1.06px at 48px.

Video sizes:

| Role | Size | Weight |
|---|---|---|
| Hero | 120–160px | 510 |
| Section title | 72–96px | 510 |
| Body / feature copy | 32–40px | 400–510 |
| Stat number | 160–220px | 510 (tnum-tight) |
| Caption | 24–28px | 510 |

## 4. Depth

Multi-layered shadows with inset variants for depth on dark surfaces:

```css
box-shadow:
  inset 0 1px 0 rgba(255,255,255,0.04),
  0 1px 0 rgba(0,0,0,0.6),
  0 10px 30px rgba(0,0,0,0.4);
```

Borders are barely-there: `1px solid rgba(255,255,255,0.05)`.

## 5. Motion

Linear's brand is *engineered precision*. Motion is fast, deterministic, no overshoot.

| Property | Choice |
|---|---|
| Default entrance ease | `power3.out` |
| Stat-counter ease | `power2.out` |
| Entrance duration | 0.4–0.6s |
| Stagger | 0.06–0.10s (snappy) |
| Scene-to-scene transition | Quick crossfade 0.3–0.4s, `power2.inOut` |
| Section-boundary | Hard cut OR 0.3s crossfade. **No flourish.** |
| Product-shot camera | Crisp 1.02→1.0 settle over ~0.5s, `power3.out` — no overshoot |
| Avoid | `back.out`, `elastic`, shader transitions, marker-highlights, anything ornamental |

The brand voice is "things work because they're well-built, not because they look impressive." Motion follows.

## 6. Video applications

- **Hero scene:** Single Inter 510 headline at 140px on `#08090a`. No mockup, no decoration. Subtitle at 32px in `#d0d6e0` arrives 0.4s later. Both elements settle, then transition.
- **Feature scene:** Product screenshot in a card with elevated surface `#191a1b` and the inset-highlight shadow stack. Tilt ≤3°. Caption in 32px Inter 510 beside it.
- **Stat scene:** Number at 200px on dark canvas, tabular-figures, counter ease `power2.out` over ~1.8s. Label at 32px below.
- **CTA scene:** `npm i linear` or equivalent in Berkeley Mono on an elevated surface. Brand mark below at 80px. Hold.

## 7. Avoid

- **Decorative motion.** Linear's voice rejects anything that performs rather than works.
- **Light-mode hero.** The brand IS the dark canvas. Switching to white reads as anti-brand.
- **More than one accent colour.** Indigo-violet is the only chromatic colour; everything else is achromatic.
- **Bouncy / elastic eases.** Off-brand. Use `power*.out` family exclusively.

## Source

Informed by studying VoltAgent/awesome-design-md `design-md/linear.app/DESIGN.md` and the brand's actual product. Original prose authored by hve-video-director, MIT licensed.
