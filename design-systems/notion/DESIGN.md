# Notion — Video Production Notes

Brand specification for HyperFrames compositions. See the Source line at the bottom for research provenance.

## 1. Atmosphere

A blank canvas that gets out of your way. Warm neutrals (not cold grays), near-black text instead of pure black, ultra-thin "whisper-weight" borders. The aesthetic is *quality paper rather than sterile glass* — a tactile, almost analog warmth. Single blue accent (Notion Blue) is the only chromatic colour in the chrome.

## 2. Palette (video-essential)

| Role | Hex |
|---|---|
| Canvas | `#ffffff` |
| Warm white surface | `#f6f5f4` (yellow undertone is key) |
| Primary text | `rgba(0,0,0,0.95)` / `#000000f2` (NOT pure black) |
| Warm dark surface | `#31302e` |
| Secondary text | `#615d59` (warm gray) |
| Muted / placeholder | `#a39e98` |
| Brand accent | `#0075de` (Notion Blue) |
| Active blue | `#005bab` |
| Decorative accent | `#ff64c8` (pink) / `#dd5b00` (orange) / `#391c57` (purple) — used very sparingly |

The yellow undertone in warm neutrals is non-negotiable. Don't substitute cool gray `#f5f5f5`.

## 3. Typography

- **Display + Body:** `NotionInter` (modified Inter), fallback `Inter`, `-apple-system`.
- **OpenType:** `"lnum"` (lining numerals) and `"locl"` (localized forms) on display/heading sizes.
- **Weights:** 400 body, 500 UI, 600 emphasis, 700 display.

Display sizes use aggressive negative tracking (-2.125px at 64px).

Video sizes:

| Role | Size | Weight |
|---|---|---|
| Hero | 120–160px | 700 |
| Section title | 80–110px | 700 |
| Card / feature title | 48–64px | 700 |
| Body / value prop | 32–44px | 400–500 |
| Caption | 24–28px | 500 |
| Stat number | 160–200px | 700 (lnum) |

## 4. Depth

Notion uses *whisper-weight* borders and barely-there shadows. Multi-layer shadow stacks with cumulative opacity never exceeding 0.05:

```css
box-shadow:
  0 1px 0 rgba(0,0,0,0.02),
  0 2px 6px rgba(0,0,0,0.04);
border: 1px solid rgba(0,0,0,0.1);
```

Border-radius: 4–8px for cards. **Pill badges at 9999px** with tinted blue backgrounds for status indicators.

## 5. Motion

Notion's brand is *editorial-software calm*. Soft eases, generous timing, hand-drawn feel. Marker highlights are *perfect* for this brand.

| Property | Choice |
|---|---|
| Default entrance ease | `power2.out` |
| Hand-drawn flourish | `patterns/marker-highlight.md` § scribble / circle modes |
| Entrance duration | 0.6–0.9s |
| Stagger | 0.10–0.15s |
| Scene-to-scene transition | Soft crossfade 0.6–0.8s, `power1.inOut`. Page-turn variants acceptable. |
| Section-boundary | Surface-swap from `#ffffff` to `#f6f5f4` (use the warm white) |
| Product-shot camera | Gentle 1.03→1.0 drift over ~1.5s, `power1.inOut` — no snap |
| Avoid | Flash transitions, glitch, hard cuts — wrong tone for editorial calm |

## 6. Video applications

- **Hero scene:** `#ffffff` canvas. Brand wordmark in NotionInter 700 at 140px, near-black text. Subtitle at 36px in warm gray `#615d59`. A *marker highlight* on one emphasized word in the headline lands well here.
- **Feature scene:** Screenshot in a card with whisper border + barely-there shadow. Tilt ≤3°. Caption at 36px weight 500.
- **Stat scene:** Number at 180px weight 700 with `lnum`, on `#f6f5f4` warm-white surface. Counter ease `power2.out` over ~2.2s. Label at 28px in warm gray.
- **CTA scene:** A pill badge with Notion Blue tinted background (`rgba(0,117,222,0.12)` fill, `#0075de` text) at 32px. Wordmark below. Hold.

## 7. Avoid

- **Cool gray neutrals (`#f5f5f5`).** The yellow undertone is the brand. Cool gray reads as anti-Notion.
- **Heavy borders or hard shadows.** Whisper-weight only.
- **Decorative accent overuse.** Pink, orange, purple are for occasional emphasis (1 use per scene max), never UI chrome.
- **Sans-serif system fonts in display.** NotionInter is the brand. Falling back to system Inter without the OpenType features loses the personality.

## Source

Informed by studying VoltAgent/awesome-design-md `design-md/notion/DESIGN.md` and the brand's actual product. Original prose authored by hve-video-director, MIT licensed.
