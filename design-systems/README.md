# Curated Design Systems

10 brand identities you can pick as a Phase 1 visual identity preset. Each ships a single **`DESIGN.md`** file — an MIT-licensed brand specification authored by this skill, focused on what a HyperFrames composition actually needs:

- **Atmosphere** — one paragraph capturing the brand's mood
- **Palette** — 6–10 hex codes with roles
- **Typography** — display + body + mono families and a video-scale size hierarchy
- **Depth** — signature shadow/border/radius treatment as a single CSS block
- **Motion** — entrance ease, duration, stagger, transition energy, and brand-specific motion DNA
- **Video applications** — per-scene-type recipes (hero / feature / stat / CTA)
- **Avoid** — brand-specific anti-patterns

**Phase 3 (Path A) copies `design-systems/<slug>/DESIGN.md` to the project's root as `DESIGN.md`.**

Web-only sections (Components, Responsive Behavior, Touch Targets) that appear in generic brand specs are intentionally absent — they don't apply to a HyperFrames composition and would dilute the file. If you also need a web-focused brand spec for a separate project, `npx getdesign add <slug>` from the [awesome-design-md catalog](https://github.com/VoltAgent/awesome-design-md) is the canonical source (73 brands, MIT).

## Catalog

| Name | Slug | Vibe | Motion energy | Best for |
|---|---|---|---|---|
| Stripe | `stripe` | Premium fintech — sohne-var weight 300, blue-tinted shadows | Dignified-slow (0.7–1.0s, expo.out, no bounce) | Payments / fintech / dev-tools |
| Linear | `linear-app` | Engineered minimalism — Inter 510, dark-mode-native | Engineered precision (0.4–0.6s, power3.out, no flourish) | Issue trackers, SaaS, prod tools |
| Apple | `apple` | Quiet authority — SF Pro, binary section rhythm | Spring physics (0.6–0.8s, back.out(1.1)) | Hardware, consumer launches |
| Notion | `notion` | Editorial-software — warm neutrals, NotionInter | Soft editorial (0.6–0.9s, power2.out, marker-friendly) | Productivity, docs, content tools |
| Vercel | `vercel` | Sharp black-on-white — Geist, tight tracking | Razor-sharp (0.4–0.6s, expo.out, flash-through-white signature) | Dev infra, deploy platforms |
| Airbnb | `airbnb` | Warm rounded — Cereal, generous radii | Hospitable bounce (0.6–0.9s, back.out(1.2) on rounded) | Travel, hospitality, consumer marketplaces |
| GitHub | `github` | Engineered density — system-ui, hairline borders | Anti-decoration (0.3–0.5s, ease-out, "things appear") | Code platforms, dev tools |
| Cal.com | `cal` | Monochromatic restraint — Cal Sans + Inter | Confident-not-flourishy (0.5–0.7s, power3.out + slight back.out) | Scheduling, OSS tools |
| Arc | `arc` | Frosted gradients — Argent CF + Inter | Smooth glass (0.5–0.7s, cubic-bezier(0.32,0.72,0,1)) | Browsers, consumer SaaS |
| Bento | `bento` | Playful link-in-bio — cream surfaces, peach accent | Playful but stable (0.4–0.6s, power2.out, grid-stagger signature) | Social, creator tools |

## Usage

Pick one in **Phase 1 Step 1.2** (visual identity question). Phase 3 copies `design-systems/<slug>/DESIGN.md` to your project's root as `DESIGN.md` and skips both screenshot extraction AND the HyperFrames named-style seed.

Hierarchy of brand-extraction strategies:

1. **Vendored design system** (this directory) — fastest, most opinionated, motion-aware
2. **HyperFrames named style** (`VISUAL_STYLES` in the `hyperframes-creative` skill — 8 options; path in `compat/ecosystem.md`) — moderate
3. **Screenshot extraction** (Phase 3 default) — slowest, most adaptive

## Adding more brands

The canonical source of brand-spec research material is [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) — 73 brands, MIT-licensed, with a `npx getdesign add <slug>` CLI. **Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before adding** — it codifies the quality bar for `DESIGN.md` (especially the Motion section, which is easy to fake) plus the 5-criterion brand-selection gate, required structure, and a 14-point self-check.

## Provenance

Each `DESIGN.md` cites its research material at the bottom. For brands present in awesome-design-md, the citation points at the upstream file there. For brands not yet in awesome-design-md, the citation names the brand's actual product as the sole source.

All `DESIGN.md` files in this directory are **original prose authored by this skill** (MIT-licensed). They were informed by studying the upstream research material but contain no verbatim content from it. To study the awesome-design-md upstream when authoring a new file:

```bash
npx getdesign add <slug>                 # fetches into your cwd
# or read directly:
curl https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/<slug>/DESIGN.md
```
