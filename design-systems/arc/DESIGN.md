# Arc — Video Production Notes

Brand specification for HyperFrames compositions. See the Source line at the bottom for research provenance.

## 1. Atmosphere

Arc dissolves the boundary between the chrome and the page. The visual signature is **frosted glass plus a single saturated gradient** — most often peach-to-coral or violet-to-fuchsia — that sets the emotional temperature of the entire window. Squircle-soft 12–16px radii everywhere. Translucent surfaces; borders are rare.

## 2. Palette (video-essential)

Arc is *gradient-led*, not flat-colour-led. Pick one gradient pair as the canvas:

| Gradient pair | Hex (start → end) | Mood |
|---|---|---|
| Sunset (default) | `#ff7e5f` → `#feb47b` | Warm, hospitable |
| Twilight | `#7f5af0` → `#e84393` | Premium, evening |
| Aurora | `#16f2b3` → `#0db4f7` | Fresh, technical |

Frosted-glass layers over the gradient:

| Role | RGBA |
|---|---|
| Standard frosted pane | `rgba(255,255,255,0.7)` |
| Active pane / command bar | `rgba(255,255,255,0.85)` |
| Dark-mode frosted | `rgba(20,20,25,0.6)` |
| Frosted edge border | `rgba(255,255,255,0.4)` |

Ink on frosted surface:

| Role | Hex |
|---|---|
| Primary | `#1a1a1f` |
| Secondary | `#54545a` |
| Muted | `#8c8c93` |
| Inverse (on dark frost) | `#fafafa` |

## 3. Typography

- **Marketing display:** `Argent CF` (serif) — Arc's rare editorial voice. Fallback `Source Serif Pro`, `Georgia`.
- **Product / UI:** `Inter`. Fallback `system-ui`, `-apple-system`.
- **Mono:** `Berkeley Mono`.

Display tightens tracking with size: -0.03em at 72px, returning to normal by 15px.

Video sizes:

| Role | Size | Weight |
|---|---|---|
| Marketing hero (Argent CF) | 130–160px | 400 |
| Section heading (Argent CF) | 72–96px | 400 |
| Product UI (Inter) | 32–48px | 400–600 |
| Caption | 24–28px | 500 |
| Stat (Argent CF) | 180–220px | 400 |

Argent CF is the brand's *editorial moment*. Use sparingly — typically the hero and one feature label. Inter handles everything else.

## 4. Depth

Subtle shadow over the gradient backdrop:

```css
backdrop-filter: blur(40px);
background: rgba(255,255,255,0.7);
box-shadow: 2px 8px 32px rgba(0,0,0,0.08);
border: 1px solid rgba(255,255,255,0.4);
border-radius: 16px;
```

Note: HyperFrames doesn't natively use `backdrop-filter` for video render in some Chromium configs — fall back to a static colour-tint that approximates frost when needed (a `rgba(255,255,255,0.7)` over the gradient renders identically in most cases).

**Shadow offsets follow the film's key light, not this page.** The x-offsets above assume the
house key at 32% 14% (upper-left). Blur, alpha and colour are this brand's and never move; only
the offset answers to the light, and it flips sign if a film declares its key on the other side.
A stack with every casting layer at x=0 reads as no light at all — it is a web-card shadow, and
on video it disappears.

## 5. Motion (from upstream)

Arc's documented motion vocabulary:

| Property | Choice |
|---|---|
| Hover | 200ms |
| Tab create / close | 320ms |
| "Little Arc" window expand | 480ms |
| Easing | `cubic-bezier(0.32, 0.72, 0, 1)` (Apple's spring-style) |
| Tab swap | 1px translate + opacity blend, **no scale change** |

For video:

| Property | Choice |
|---|---|
| Default entrance ease | `cubic-bezier(0.32, 0.72, 0, 1)` (configure in GSAP: `CustomEase.create("arc", "M0,0 C0.32,0.72 0,1 1,1")`) or `power3.out` as close approximation |
| Entrance duration | 0.5–0.7s (matches Arc's 320–480ms with video-scale uplift) |
| Stagger | 0.08–0.12s |
| Scene-to-scene transition | Crossfade with subtle gradient drift 0.5–0.7s — let the gradient continue moving slightly during transition |
| Section-boundary | Cross-gradient morph (sunset → twilight) over 0.7s |
| Product-shot camera | None — a scale push-in is off-brand (Arc's tab-swap explicitly forbids scale change). If motion is needed, a slow ≤2% positional/parallax drift of the frosted pane, `power1.inOut` |
| Avoid | Scale-driven transitions (Arc's tab-swap explicitly forbids scale change), hard cuts, flash |

Arc's voice: smooth, generous, frosted-glass elegant. Motion never snaps.

## 6. Video applications

- **Hero scene:** Sunset gradient canvas. Argent CF marketing hero at 140px in `#fafafa` (the gradient is bright enough that you want light text). Subtitle in Inter 400 at 36px below. Frosted-glass pane behind text if contrast needs help.
- **Feature scene:** Product screenshot inside a frosted-glass pane (white-translucent over the gradient), 16px corner radius, with the soft Arc shadow stack. Caption in Inter 500 beside.
- **Stat scene:** Number at 200px Argent CF on the gradient (light text if Sunset / Aurora; dark text if Twilight at lower-light end). Counter ease `cubic-bezier(0.32,0.72,0,1)` over 2.0s.
- **CTA scene:** Pill button with `rgba(255,255,255,0.85)` frosted background, dark ink text in Inter 600. Brand wordmark above in Argent CF. Hold.

## 7. Avoid

- **Flat backgrounds.** Arc's brand IS the gradient. A solid-colour canvas reads as anti-Arc.
- **Bold sans for marketing.** Argent CF (serif) is the brand's marketing voice. Switching to Inter Bold for the hero is anti-Arc.
- **Hard cuts between scenes.** Arc's motion vocabulary is smooth; cuts feel wrong.
- **Visible borders.** Arc prefers frosted backgrounds over CSS borders. A solid 1px border on a card looks anti-tone.

## Source

Informed by studying Arc's actual product. Original prose authored by hve-video-director, MIT licensed.
