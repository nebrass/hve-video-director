# Contributing a Design System

Adding a new brand to `design-systems/` looks like a 30-minute job. It isn't. The hard part is the **Motion section** of `DESIGN.md` — and that section is the entire reason this directory exists. Read this before adding a brand.

## Decision: should this brand be added?

Not every brand is worth vendoring. Use the criteria below:

| Criterion | Required |
|---|---|
| The brand has a recognisable, opinionated visual identity that a user might invoke by name ("make it look like X") | ✅ |
| The brand's motion DNA is *observable* — real product, real marketing video, real animation choices to study | ✅ |
| You can name at least 3 brand-specific anti-patterns (things to avoid that would betray the brand) | ✅ |
| Open-design has the upstream `DESIGN.md` in `design-systems/<slug>/` OR you can author equivalent web-spec content | ✅ |
| The brand is something hve-spielberg users would *plausibly* want as a preset for a product video | ✅ |

**If any of these fails: don't add it.** The 10 vendored brands are deliberately curated. A larger catalogue with weaker entries dilutes the choice.

Examples of brands we'd consider next: `figma`, `claude`, `raycast`, `openai`, `framer`, `loom`. Examples we'd reject: `random-portfolio-blog`, `internal-tool-with-no-marketing-presence`, `brand-that-has-a-deck-but-no-motion-DNA`.

## Single-file model

Every brand ships **one file**: `design-systems/<slug>/DESIGN.md`.

This is original work authored by this skill, MIT-licensed. The canonical research source is [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) — MIT-licensed, 73 brands. You may *study* its upstream brand specs (and the brand's actual product, marketing site, etc.) as research material; do not copy verbatim text into your DESIGN.md.

The DESIGN.md you write should cite its research source at the bottom (typically the awesome-design-md file you read, plus the brand directly) for attribution.

## Step-by-step

```bash
# 1. (Research only — don't vendor) Study the upstream brand spec:
npx getdesign@latest add <slug>                  # fetches into your cwd as DESIGN.md
# or read raw:
curl https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/<slug>/DESIGN.md

# 2. Visit the brand's actual product. Time their motion. Note their
#    palette, typography, depth treatment. This is the most important step.

# 3. Author DESIGN.md (use an existing one as template):
mkdir -p design-systems/<slug>
$EDITOR design-systems/<slug>/DESIGN.md

# 4. Add a row to the catalog table in design-systems/README.md

# 5. Add an option to Phase 1 Step 1.2 in workflows/phase-1-storytelling.md
#    (the second question block, "Which design system?")

# 6. Verify the slug appears in all three:
#    - templates/project-plan.md `Design system:` enum
#    - workflows/phase-3-design.md Path A slug list
#    - README.md if it lists supported systems
```

## DESIGN.md required structure

Target length: **70–110 lines**. Below 70, you're under-specifying the brand. Above 110, you're either being verbose or you're copying web-spec content that doesn't belong here.

Every file must have these sections, in this order, with these headings:

```markdown
# <Brand> — Video Production Notes

Brand specification for HyperFrames compositions. See the Source line at the bottom for research provenance.

## 1. Atmosphere
## 2. Palette (video-essential)
## 3. Typography
## 4. Depth
## 5. Motion
## 6. Video applications
## 7. Avoid
## Source
```

### § 1. Atmosphere

**Required:** one paragraph (3–5 sentences) that captures the brand's *feeling*, not its components. If you find yourself listing button styles, you're in the wrong section.

**Quality check:** delete the brand name from the paragraph. Could it still apply uniquely? If not, redo it — you wrote generic copy.

### § 2. Palette

**Required:** a single table mapping role → hex code. Only the colours a video actually needs (canvas, primary text, secondary text, accent, surface tints, optional decorative).

**Anti-pattern:** copying the upstream palette wholesale (often 30+ colours). Distil to 6–10. Variations on the same hue belong in the upstream `DESIGN.md`, not here.

### § 3. Typography

**Required:** font families (display + body + mono), key OpenType features, weight ladder, and a video-sized hierarchy table (sizes ≥24px because that's the legibility floor for video).

**Anti-pattern:** listing 14 type roles. Pick the 5–6 that map to product-video scenes: hero, section title, body, caption, stat number, mono.

### § 4. Depth

**Required:** one fenced CSS block showing the brand's signature shadow / border / radius treatment, suitable to drop into a HyperFrames scene.

**Anti-pattern:** generic `box-shadow: 0 2px 8px rgba(0,0,0,0.1)`. If your block could apply to any brand, you've missed the signature.

### § 5. Motion — the section that justifies this whole directory

This is the section that distinguishes a real preset from a borrowed web spec. **It is the hardest to write well and the easiest to fake.**

**Required table** with at least these rows:

| Property | Choice |
|---|---|
| Default entrance ease | … |
| Entrance duration | … |
| Stagger | … |
| Scene-to-scene transition | … |
| Section-boundary | … |
| Counter / stat ease | … |
| Product-shot camera | <push-in / parallax rate, or "none"> |
| Avoid | … |

The `Product-shot camera` row is **required** — because real product captures are the spine of a generated video, every preset must declare its camera behaviour on a product shot; when a brand should hold still, state `none` explicitly rather than omitting the row. It describes per-brand camera *motion* on a product shot (the framing itself lives in § 6). It must be **deterministic**: a WRAPPER-transform tween only — never an `<img>`/`<video>` dimension animation, never `.play()` / video-as-clock; release before the crossfade window.

Plus 1–2 paragraphs explaining the brand's motion *voice*.

**Sources to base your choices on**, in order of authority:

1. **Documented motion vocabulary in the upstream `DESIGN.md`** (e.g. Arc, GitHub, Bento have explicit § 6 Motion sections — port them).
2. **The brand's own marketing videos or product UI.** Open the brand's website. Hover something. Open a modal. Submit a form. Watch the motion. Time it (rough estimate is fine — "fast" is ~150–300ms, "moderate" is ~400–600ms, "generous" is ~600–900ms).
3. **The brand's design framework defaults** (Linear → no published motion, but their product is engineered → infer `power3.out`, 0.4–0.6s; Cal → built on Framer → infer Framer Motion spring defaults).
4. **Last resort: inference from atmosphere.** A "premium" brand gets longer durations and softer eases. A "developer-infrastructure" brand gets short, sharp motion. Document the inference so a reviewer can challenge it.

**The fail-state to guard against:** a Motion section that could be copy-pasted into any other brand's file unchanged. If your motion section says only *"power2.out, 0.5s, stagger 0.08s, crossfade transitions"* with no brand-specific rationale, **you have not done the work.** Redo it.

**Examples of brand-specific motion language:**

- Stripe: *"The 'anti-shout' voice extends to motion: a Stripe video that snaps and pops is off-brand."*
- Vercel: *"`flash-through-white` catalog block — the iconic Vercel motion. Vercel's voice is 'deploys finish in milliseconds, ship is instant.' Motion duration carries that message."*
- GitHub: *"Of all 10 brands, GitHub has the strongest anti-decoration stance. If you're tempted to add a flourish, you've drifted off-brand."*
- Arc: *"Tab swap = 1px translate + opacity blend, no scale change."* (verbatim from upstream)

If your motion section lacks language like this, it isn't done.

### § 6. Video applications

**Required:** concrete prescriptions for at least 4 scene types — Hero, Feature, Stat, CTA. Each is 2–4 lines describing what the scene looks like *in this brand's terms*.

**Anti-pattern:** "Hero scene: a big headline and subtitle." Specific to nothing. Compare:

- ❌ "Hero scene: brand wordmark with subtitle, fades in."
- ✅ "Hero scene: `#08090a` canvas. Inter 510 headline at 140px. No mockup, no decoration. Subtitle at 32px in `#d0d6e0` arrives 0.4s later. Both elements settle, then transition."

### § 7. Avoid

**Required:** 3–5 brand-specific anti-patterns. These must be specific to this brand, not the universal anti-slop rules (those live in `patterns/anti-slop.md`).

**Examples:**

- Stripe: *"Default purple gradient hero. Stripe's purple is anchored, not gradient-led."*
- Linear: *"Light-mode hero. The brand IS the dark canvas."*
- GitHub: *"Custom display fonts. GitHub's voice is 'the OS you're already on.' Loading Inter or any webfont is anti-brand."*
- Bento: *"Pure white canvas. The cream `#FFF5E6` is the brand's atmospheric tone."*

Each anti-pattern should be a *trap a careful designer could fall into* — not a universal "don't use Comic Sans" warning.

### § Source

**Required:** one line citing whichever sources you studied while authoring the file (typically an upstream brand-spec file at a specific commit, and/or the brand's actual product). Confirm the prose is original work, MIT-licensed.

Example:

```markdown
## Source

Informed by studying VoltAgent/awesome-design-md `design-md/<slug>/DESIGN.md` and the brand's actual product. Original prose authored by hve-spielberg, MIT licensed.
```

If your file ports an explicit Motion section from a source, name that source on the same line.

## Self-check before opening a PR

Run through this list. If any answer is "no" or "not sure", revise before submitting.

1. **Atmosphere paragraph passes the brand-name-removal test** — could it apply uniquely to this brand without naming it?
2. **Palette table has 6–10 rows, not 30** — you distilled, you didn't paste.
3. **Typography section has video-scale sizes** (hero ≥110px, body ≥32px) — not the upstream's 14–48px web scale.
4. **Depth section's CSS is signature-specific** — not generic `box-shadow`.
5. **Motion section sources are documented** — you cited the upstream Motion section, or you watched the real product, or you inferred from atmosphere with a justification.
6. **Motion table has a brand-specific paragraph alongside it** — not just numbers.
7. **The "Motion section fail-state test" passes** — your section could *not* be copy-pasted into another brand's file unchanged.
8. **Video applications are concrete** — each scene-type description names specific colours, font sizes, durations.
9. **Avoid section is brand-specific** — universal anti-slop rules belong in `patterns/anti-slop.md`, not here.
10. **The file is 70–110 lines** — under-specified vs verbose-or-web-spec.
11. **The catalog table in `README.md` has a new row** with a Motion-energy descriptor (e.g. *"Razor-sharp (0.4–0.6s, expo.out, flash-through-white signature)"*).
12. **Phase 1 Step 1.2 (`workflows/phase-1-storytelling.md`) has a new option** for this brand.
13. **`templates/project-plan.md`** enum list includes the new slug.
14. **`workflows/phase-3-design.md`** Path A slug list mentions the new slug.

## Anti-patterns by section (one-line summary)

| Section | The fail mode |
|---|---|
| Atmosphere | Generic adjectives — "clean, modern, minimal" without specifics |
| Palette | Copying the full upstream palette instead of distilling |
| Typography | Pasting upstream's web-scale hierarchy (14–48px) without scaling for video |
| Depth | Generic shadow recipe with no signature character |
| Motion | Universal defaults dressed up — would copy-paste cleanly into any other brand |
| Applications | Vague "fades in", "looks good" — no specific hex / size / duration |
| Avoid | Universal rules ("no Comic Sans") instead of brand-specific traps |

## License

Your DESIGN.md contribution is licensed MIT (this repo's license). By contributing, you confirm the content is original work — not copied verbatim from an Apache-2.0 / GPL / other-licensed source. You may *reference* and *be informed by* such sources, but the prose, structure, and motion choices in your file must be your own.

Cite the source material at the bottom of the file (e.g. "Informed by studying VoltAgent/awesome-design-md `design-md/<slug>/DESIGN.md` and the brand's actual product motion at <date>").
