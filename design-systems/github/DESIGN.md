# GitHub — Video Production Notes

Brand specification for HyperFrames compositions. See the Source line at the bottom for research provenance.

## 1. Atmosphere

Engineered, not decorated. A tool for people who care about diffs, builds, and pull requests. Information density is the brand — dense panes separated by hairline borders rather than negative space. The signature is *muted accents on dense grayscale*: Primer blue for links, GitHub green for success.

## 2. Palette (video-essential)

| Role | Hex |
|---|---|
| Canvas (light) | `#ffffff` |
| Canvas (dark mode) | `#0d1117` |
| Subtle surface | `#f6f8fa` |
| Code-block surface | `#eaeef2` |
| Primary text | `#1f2328` |
| Secondary text | `#656d76` |
| Primer Blue (links / primary) | `#0969da` |
| Primer Blue hover | `#0550ae` |
| Merge / success green | `#1a7f37` |
| Danger / closed red | `#cf222e` |
| Warning yellow | `#9a6700` |
| Hairline border | `#d0d7de` |

Two accents only (Primer blue + merge green). Reds and yellows are status, not chrome.

## 3. Typography

- **Body + UI:** `system-ui` stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial`). **No custom typeface** — text must render instantly on slow connections.
- **Mono:** `SFMono`, `Menlo`, `Consolas`.

**14px body, not 16px.** GitHub's prose density is its identity. **Weight binary:** 400 default, 600 emphasis. No 500, no 700.

Video sizes (scale up for legibility — keep the binary-weight discipline):

| Role | Size | Weight |
|---|---|---|
| Display | 100–140px | 600 |
| H1 / section title | 64–80px | 600 |
| H2 / sub-section | 48–56px | 600 |
| Body / prose | 32–40px | 400 |
| Code / mono | 28–36px (mono) | 400 |
| Caption | 24–28px | 400 |
| Stat number | 160–200px | 600 |

## 4. Depth

Hairline borders, almost no shadow:

```css
border: 1px solid #d0d7de;
border-radius: 6px;
/* shadow: optional, very light */
box-shadow: 0 1px 3px rgba(0,0,0,0.04);
```

Pill-shaped status badges with strong colour semantics (Primer blue / merge green / danger red).

## 5. Motion

Upstream explicit rule: *"Things appear; they do not perform."* Reduced motion. Avoided: page-load animation, parallax, persistent micro-interactions.

| Property | Choice (from upstream) |
|---|---|
| Hover duration | 80ms |
| Menu / popover open | 200ms |
| Open ease | `ease-out` |
| Close ease | `ease-in` |
| Default entrance ease (video) | `power2.out` |
| Entrance duration (video) | 0.3–0.5s (very short — GitHub motion is fast and disappears) |
| Stagger | 0.05–0.08s |
| Scene-to-scene transition | Plain crossfade 0.3s, `power2.inOut`. Hard cuts also on-brand. |
| Section-boundary | Hard cut or 0.3s crossfade. **No flourish.** |
| Product-shot camera | None — GitHub's anti-decoration stance rules out camera moves; use static product shots with a hard cut or 0.3s crossfade only |
| Avoid | Spring, bounce, marker highlights, shader transitions, anything decorative |

Of all 10 brands, GitHub has the strongest anti-decoration stance. If you're tempted to add a flourish, you've drifted off-brand.

## 6. Video applications

- **Hero scene:** Light canvas `#ffffff`. Headline in system-ui 600 at 120px on `#1f2328`. Subtitle at 36px weight 400. Both arrive in 0.4s, no flourish.
- **Feature scene (dark variant):** Code-editor mockup — `#0d1117` canvas, SFMono code lines streaming in. Caption in system-ui 600 beside it. This is the strongest scene for GitHub.
- **Stat scene:** Number at 180px system-ui 600, on `#ffffff` or `#f6f8fa`. Counter ease `power2.out` over 1.4s — fastest of all brands.
- **CTA scene:** Octicon at 80px, "Star on GitHub" or "Try it free" in system-ui 600 at 48px, Primer blue (`#0969da`) link colour. Hold.

## 7. Avoid

- **Custom display fonts.** GitHub's voice is "the OS you're already on." Loading Inter or any webfont is anti-brand.
- **Decorative motion.** Anything that performs rather than works is off-tone.
- **Soft / pastel palette.** GitHub's neutrals are functional and slightly cool. Warm beige reads as anti-GitHub.
- **Weight 500.** The binary weight (400/600) is the brand. Weight 500 dilutes it.

## Source

Informed by studying GitHub's actual product. Original prose authored by hve-spielberg, MIT licensed.
