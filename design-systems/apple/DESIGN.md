# Apple — Video Production Notes

Brand specification for HyperFrames compositions. See the Source line at the bottom for research provenance.

## 1. Atmosphere

Gallery-like calm punctuated by retail-density information blocks. Binary section rhythm: cinematic deep black alternates with pale neutral fields. The interface is engineered to *disappear* so hardware and materials become the narrative foreground. Typography stabilises everything — SF Pro Display carries hero hierarchy with compact line-heights and controlled tracking.

## 2. Palette (video-essential)

| Role | Hex |
|---|---|
| Cinematic canvas | `#000000` |
| Pale neutral field | `#f5f5f7` |
| Retail / dense canvas | `#ffffff` |
| Primary text on light | `#1d1d1f` |
| Secondary text | `#6e6e73` |
| Action accent | `#0071e3` (Apple blue) |
| Inline link | `#0066cc` |
| High-luminance link on dark | `#2997ff` |
| Dark elevated surfaces | `#272729` / `#28282b` |
| Soft border | `#d2d2d7` |

Alternate scenes between black canvas and pale-gray for rhythm; never go from `#000000` to `#ffffff` directly without an intermediate `#f5f5f7` beat unless the transition explicitly bridges.

## 3. Typography

- **Display:** `SF Pro Display`, fallback `Helvetica Neue`.
- **Body / UI:** `SF Pro Text`, fallback `Helvetica Neue`.

Hero is weight 600 with tight line-height (1.00–1.10). Body is 400 with relaxed line-height (1.47).

Video sizes:

| Role | Size | Weight |
|---|---|---|
| Hero (cinematic) | 120–160px | 600 |
| Section display | 72–96px | 500–600 |
| Product heading | 60–72px | 600 |
| Body / value prop | 32–44px | 400 |
| Caption | 24–28px | 400–600 |
| Stat number | 140–200px | 600 |

## 4. Depth

Apple uses depth *sparingly* — contrast and surface separation do the layering. When you need a card shadow:

```css
box-shadow: 0 20px 50px rgba(0,0,0,0.18);
```

Border-radius: pill (`980px` / `9999px`) for action buttons, capsule (`18–22px`) for cards.

## 5. Motion

Apple's brand is *spring physics tradition*. Generous timing. Restrained energy.

| Property | Choice |
|---|---|
| Default entrance ease | `power2.out` (curves) for opacity; spring for position/scale |
| Position / scale ease | spring approximation: `gsap.from(..., { duration: 0.6, ease: "back.out(1.1)" })` — subtle overshoot |
| Entrance duration | 0.6–0.8s |
| Stagger | 0.10–0.15s |
| Scene-to-scene transition | Crossfade 0.5–0.7s. Pale-to-black transitions: 0.7s `power1.inOut`. |
| Section-boundary | Surface-swap (one scene fades out as new surface colour fades in). NO flash. |
| Product-shot camera | Slow 1.0–1.2s push-in, `back.out(1.1)` spring settle |
| Avoid | Glitch, RGB-split, fast cuts, anything that breaks the gallery calm |

The hardware always gets the entrance flourish — never the chrome. In a product video, that means: a feature mockup arrives with spring-physics motion; the headline above it fades in plain.

## 6. Video applications

- **Hero (cinematic mode):** Deep `#000000` canvas. Brand mark or product silhouette enters with `back.out(1.1)` scale from 0.95 to 1.0 over 0.7s. Headline at 140px SF Pro Display fades in at 1.0s.
- **Pale-field feature scene:** Switch to `#f5f5f7` canvas (transition handles the chapter break). Product screenshot in a `#ffffff` card with soft shadow, hero-scale. Spec list beside it in SF Pro Text 32px.
- **Stat scene:** Centered number at 180px, `#1d1d1f` on `#f5f5f7`, counter ease `power1.inOut` over ~2.4s.
- **CTA scene:** Pill-shaped button with Apple blue background (`#0071e3`), white "Learn more" text at 32px. Held final frame.

## 7. Avoid

- **Three-stop trust gradients.** Apple's voice is monolithic surfaces, not gradients.
- **Cluttered scenes.** If a scene has more than 4 visual elements, it's off-brand. Reduce.
- **Marker highlights / scribble.** Editorial techniques are wrong tone for Apple.
- **Chrome heroics.** The hardware (or screenshot of the product) is the hero. Nav bars, buttons, and headlines arrive plainly.

## Source

Informed by studying VoltAgent/awesome-design-md `design-md/apple/DESIGN.md` and the brand's actual product. Original prose authored by hve-spielberg, MIT licensed.
