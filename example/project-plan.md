# Project Plan — blog.nebrass.fr promo

**Mode:** promo
**Product surface:** ui
**Aspect:** 16:9 1920×1080
**Visual identity strategy:** design-system
**Design system:** vercel
**HyperFrames style:** none
**Duration:** 53s
**Created:** 2026-06-24

This is a real promo for **blog.nebrass.fr** (Nebrass Lamouchi's software-engineering blog),
**built by hve-spielberg**. It is the skill's reference build: a genuine video the pipeline
produced for a real app with a real UI, so the **real product is on screen** as the spine. It
still dogfoods the skill (closing "made with /hve-spielberg" sign-off).

> **Re-subjected (v0.0.4).** The previous flagship promoted hve-spielberg itself — a UI-less
> CLI/prompt skill — so it had no app to film and was built from typography + a simulated
> terminal, which modeled flat text-on-white. Re-subjecting to a real app puts the actual
> product on screen, which is what the skill is for. (Reverses the old `context.md` "No real
> app screenshots" decision.)

## Phase Tracker

| Phase | Status | Notes |
|-------|--------|-------|
| 0. Discovery | ✅ done | Subject: blog.nebrass.fr (Hugo/PaperMod). `product_surface: ui`. |
| 1. Storytelling | ✅ done | 5-scene 53s promo; real product is the spine, text is connective tissue |
| 2. Capture | ✅ done | 5 real screenshots via Chrome DevTools (hero, post code, categories, full-page, post top) |
| 3. Design | ✅ done | DESIGN.md from `design-systems/vercel/DESIGN.md`; scenes from `templates/scene-screenshot.html` |
| 4. Production | ✅ done | 5 scene templates + root index.html, incoming-only crossfades |
| 5. Audio & Render | ✅ done | ElevenLabs (Matilda) + `npx hyperframes transcribe` verify + Freesound music + ffmpeg mix + render |

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-24 | Re-subject flagship to blog.nebrass.fr | hve-spielberg has no UI to film; a real app puts the product on screen (fixes the flat "shapes and text" reference build) |
| 2026-06-24 | `product_surface: ui` | The blog has a real UI; captures are the spine and the Phase-3 coverage gate applies |
| 2026-06-24 | Promo mode, 53s | Long enough for 4 product beats + CTA; short enough as a launch asset |
| 2026-06-24 | Vercel design system, light | Sharp black-on-white + Geist frames the light blog screenshots cleanly |
| 2026-06-24 | Real product as spine (4 of 5 scenes) | Each product scene gets a distinct motivated camera move (push-in, push-in-to-code, static, scroll-within-frame) to avoid a product-card slideshow |
| 2026-06-24 | Keep "made with /hve-spielberg" sign-off | The flagship still dogfoods the skill while filming a real app |
