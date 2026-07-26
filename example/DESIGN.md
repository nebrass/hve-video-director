# Vercel — Video Production Notes

Brand specification for HyperFrames compositions. See the Source line at the bottom for research provenance.

## 1. Atmosphere

Developer infrastructure made invisible. Minimalism as engineering principle. Overwhelmingly white canvas with near-black text — every element earns its pixel. The Geist design system treats the interface like a compiler treats code: every unnecessary token stripped away until only structure remains.

## 2. Palette (video-essential)

| Role | Hex |
|---|---|
| Canvas | `#ffffff` |
| Primary text | `#171717` (not pure black) |
| Secondary text | `#4d4d4d` |
| Tertiary text | `#666666` |
| Workflow accent — ship | `#ff5b4f` (coral red) |
| Workflow accent — preview | `#de1d8d` (magenta) |
| Workflow accent — develop | `#0a72ef` (blue) |
| Link | `#0072f5` |
| Console blue (in terminal mockups) | `#0070f3` |
| Console green (in terminal mockups) | `#00ff87` |

Each "workflow accent" maps to a deployment stage. Pick one per video — using all three in a 30s spot is incoherent.

## 3. Typography

- **Display + Body:** `Geist`. OpenType `"liga"` globally.
- **Mono:** `Geist Mono`, fallback `SF Mono`, `Menlo`.

Aggressive negative tracking: -2.4px to -2.88px at display sizes.

Video sizes:

| Role | Size | Weight |
|---|---|---|
| Hero | 140–180px | 600 |
| Section title | 80–110px | 600 |
| Body / value prop | 36–48px | 400 |
| Caption | 24–28px | 500 |
| Stat number | 180–220px | 700 |
| Terminal / mono content | 28–32px (mono) | 400 |

## 4. Depth

The signature **shadow-as-border** technique:

```css
box-shadow:
  0 0 0 1px rgba(0,0,0,0.08),   /* the "border" layer */
  0 2px 4px rgba(0,0,0,0.06),
  0 12px 32px rgba(0,0,0,0.08);
```

Border-radius: 8–12px. Pill badges at 9999px for status.

## 5. Motion

Vercel's brand is *razor-sharp minimalism*. Very fast entrances, hard contrast, **flash-through-white transitions are signature**.

| Property | Choice |
|---|---|
| Default entrance ease | `expo.out` or `power3.out` |
| Entrance duration | 0.4–0.6s (fast — the brand is "instant") |
| Stagger | 0.06–0.10s |
| Scene-to-scene transition | **`flash-through-white` catalog block** (0.3–0.4s) — the iconic Vercel motion |
| Section-boundary | Hard cut OR flash-through-white |
| Stat-counter ease | `power2.out`, ~1.6s (faster than other brands) |
| Avoid | Soft crossfades over 0.5s, swoosh transitions, anything ornamental |

Vercel's voice is "deploys finish in milliseconds, ship is instant." Motion duration carries that message. Slower than 0.6s reads as off-brand — except deliberate camera moves (a slow push-in or scroll-within-frame over a framed screenshot), which run several seconds by design and release before the crossfade.

## 6. Video applications

This promo's spine is the **real blog, framed** — `templates/scene-screenshot.html` composites each
`public/screenshots/*.png` in light browser chrome (traffic lights + `blog.nebrass.fr` URL bar) on a
near-white radial surface with a layered elevation shadow. Per-scene:

- **Establishing (`00-establishing`):** homepage hero in a browser frame; slow motivated push-in (1.0→1.05) toward the hero text, released before the crossfade.
- **Depth (`01-depth`):** a post's syntax-highlighted code + diff; gentle push-in (1.0→1.06) toward the code block.
- **Breadth (`02-breadth`):** the categories index; **no** camera move — a deliberate beat of stillness for rhythm.
- **Volume (`03-scroll`):** the full-page homepage panned inside a fixed frame (scroll-within-frame — timeline-driven `translateY` on the inner wrapper, never `scrollTop`).
- **CTA (`04-cta`):** closing text scene — `blog.nebrass.fr` in Geist 600 + a `/hve-video-director` sign-off pill on `#ffffff`, held to the end.

## 7. Avoid

- **Purple gradients.** The "Vercel triangle" mark uses gradients, but body chrome doesn't. A purple→pink hero is generic-AI-promo cosplay.
- **Soft / decorative motion.** Off-brand. Vercel motion is fast, clean, and stops the moment it lands.
- **Multiple workflow accents in one scene.** Pick one — ship-red OR preview-magenta OR develop-blue.
- **Bouncy eases.** `back.out` / `elastic` are wrong tone.

## Source

Informed by studying VoltAgent/awesome-design-md `design-md/vercel/DESIGN.md` and the brand's actual product. Original prose authored by hve-video-director, MIT licensed.
