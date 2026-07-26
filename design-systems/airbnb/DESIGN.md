# Airbnb — Video Production Notes

Brand specification for HyperFrames compositions. See the Source line at the bottom for research provenance.

## 1. Atmosphere

A travel magazine that happens to be an app. Pristine white canvases give way to full-bleed photography. The signature Rausch coral-pink is used sparingly but unmistakably. Photography carries the narrative weight; the interface disappears so the content breathes. Generous corner-rounding (14–20px) gives every container a soft, hospitable shape.

## 2. Palette (video-essential)

| Role | Hex |
|---|---|
| Canvas | `#ffffff` |
| Subsurface tint | `#f7f7f7` |
| Primary text (ink) | `#222222` |
| Secondary copy | `#3f3f3f` |
| Muted / metadata | `#6a6a6a` |
| Brand accent (Rausch) | `#ff385c` |
| Deep Rausch (pressed) | `#e00b41` |
| Tier accent — Plus | `#92174d` (magenta) |
| Tier accent — Luxe | `#460479` (deep purple) |
| Hairline border | `#dddddd` |

Rausch is the single highest-visibility colour on every scene. Cap visible uses at 2 per scene — one CTA-emphasis, one supporting accent.

## 3. Typography

- **Display + Body + UI:** `Airbnb Cereal VF` (one family for everything), fallback `Circular`, `-apple-system`.
- **Weights observed:** 500, 600, 700. **No 400-regular** — Cereal's "body" weight is 500 (gives every block subtle extra density).
- **OpenType:** `"salt"` (stylistic alternates) on compact 11–14px labels.

Video sizes:

| Role | Size | Weight |
|---|---|---|
| Hero | 110–140px | 700 |
| Section title | 64–80px | 700 |
| Listing / feature title | 48–60px | 600 |
| Body / value prop | 32–40px | 500 |
| Subtitle bold | 36–42px | 600 |
| Caption | 24–28px | 500 |
| Stat number (e.g. rating) | 200–260px | 700 |

## 4. Depth

Soft, rounded, generous. Cards float on subtle shadow:

```css
box-shadow:
  0 6px 16px rgba(0,0,0,0.12),
  0 2px 4px rgba(0,0,0,0.06);
border-radius: 16px;
```

Photographic content uses **14–20px corner rounding edge-to-edge**. Pill shapes (`9999px`) on category tabs and CTAs.

## 5. Motion

Airbnb's brand is *warm, rounded, hospitable*. Motion has slight bounce on rounded elements; otherwise generous and welcoming.

| Property | Choice |
|---|---|
| Default entrance ease | `power3.out` |
| Rounded-element entrance | `back.out(1.2)` — subtle overshoot fits the rounded geometry |
| Entrance duration | 0.6–0.9s (generous) |
| Stagger | 0.10–0.15s |
| Scene-to-scene transition | Soft crossfade 0.5–0.7s, `power2.inOut` |
| Photo / hero reveal | Image scales 1.04 → 1.00 over 0.8s (slow Ken Burns) |
| Counter / rating ease | `power1.out` (so the 4.81 settles confidently) |
| Product-shot camera | Slow Ken Burns 1.04→1.00 over ~1.5s, `power1.out` — warm and unhurried (matches the documented hero-photo reveal) |
| Avoid | Hard flash transitions, glitch, sharp `expo.out` — wrong tone for hospitality |

The signature animated moment is the **Guest Favorite lockup**: a large centered rating number between two laurel wreaths. In a video, a rating scene should *settle* like this — slow counter, generous hold, no rush.

## 6. Video applications

- **Hero scene:** Full-bleed lifestyle photo or `#ffffff` canvas with brand wordmark in Cereal 700 at 120px. Rausch coral accent on a single emphasized word.
- **Feature scene:** Listing-card style — 4:3 photo at 16px rounded corners, title in Cereal 600 at 56px below, subtitle at 32px weight 500. The card itself enters with `back.out(1.2)` from y:24 over 0.7s.
- **Stat / rating scene:** "4.81" at 240px Cereal 700, centred between two laurel wreath SVGs. Counter tweens from 0 over 1.8s `power1.out`. Label "Guest Favorite" at 32px in Cereal 600 below.
- **CTA scene:** Pill button in Rausch (`#ff385c`) at 56px height, white "Reserve" text at 28px weight 500. Brand wordmark at 56px below. Hold.

## 7. Avoid

- **Cool gray neutrals.** Airbnb's grayscale runs warm — `#222222` not `#000000`, `#f7f7f7` not `#f0f0f0`.
- **Sharp corners.** Anywhere a container could be rounded, it should be (14–20px standard, pill for CTAs).
- **Multiple Rausch uses.** The colour is precious — overuse defangs it.
- **Hero with no photography.** Airbnb's voice IS photography. A typography-only hero feels off-brand unless it's an explicit "intro to typography" moment.

## Source

Informed by studying VoltAgent/awesome-design-md `design-md/airbnb/DESIGN.md` and the brand's actual product. Original prose authored by hve-video-director, MIT licensed.
