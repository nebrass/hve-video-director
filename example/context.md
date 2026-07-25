# Product Context — blog.nebrass.fr promo

## What this video is

A ~50-second promo for **blog.nebrass.fr** — Nebrass Lamouchi's software-engineering blog —
**built by `hve-video-director`**. The flagship is now a *real product video for a real app with a
real UI*: the blog's actual screens are the spine of the video, captured live via Chrome
DevTools in Phase 2. The skill still demonstrates itself — this is a genuine video the
pipeline produced — and signs off with "made with `/hve-video-director`", but the **subject** is
the blog, not the tool.

> **Why this changed.** The previous flagship promoted *this skill* itself — a UI-less CLI
> skill — so it (legitimately) had no app to film and was built entirely from typography and a
> simulated terminal. That made the reference build model flat text-on-white, which read as
> "simple shapes and text." Re-subjecting the flagship to a real app puts the actual product on
> screen, which is what the skill is for. (This supersedes the old `context.md` line "No real
> app screenshots — the product is a skill, not a UI".)

## The product being filmed

`blog.nebrass.fr` — a Hugo / PaperMod blog: a personal hero/bio, long-form engineering posts
(Java, cloud, Kubernetes, security, AI/ML), syntax-highlighted code, a categories index, and
search. Public, no auth. Captured screens (`public/screenshots/`):

- `01-home-hero-light.png` — homepage hero ("Hi there, I'm Nebrass") + featured post card
- `01-home-full-light.png` — full-page homepage (tall) — for a scroll-within-frame beat
- `03-post-top-light.png` — a post reading view (the Puppeteer screencast-fix write-up)
- `04-post-code-light.png` — in-post syntax-highlighted code + diff blocks (the depth beat)
- `05-categories-light.png` — the categories index (breadth)

## Audience

- Developers who read engineering blogs and might subscribe / share
- Peers and recruiters discovering Nebrass's work
- (Meta) Claude Code users seeing what a real `hve-video-director` output looks like with the
  product on screen

## Goal

In ~50 seconds: show that this is a serious, deep, wide engineering blog worth reading — by
putting the real pages on screen — and close with where to find it. If a viewer thinks
*"I'd read that,"* the video did its job.

## Brand intent

- **Visual identity:** Vercel design system — sharp black-on-white, Geist typography,
  shadow-as-border, flash-through-white transitions. Frames the light blog screenshots cleanly.
  (See `DESIGN.md`, sourced from `design-systems/vercel/DESIGN.md`.)
- **Voice:** Matilda (ElevenLabs) — warm, authoritative.
- **Tone of script:** declarative, concrete, no marketing fluff. Real claims only.

## Real product, real claims (no invented metrics)

Every claim maps to something verifiable on the live blog:

- "Real bugs, real fixes — the Puppeteer screencast timing fix" → the post + merged PR #15112
- "Kubernetes, security, Azure, machine learning — dozens of topics" → the categories index
- "Years of write-ups" → posts dated 2023–2026 on the homepage
- No invented numbers, no `lorem ipsum`, no filler.

## Constraints

- ~50 seconds total, 16:9 1920×1080, light theme
- **Real product is the spine** (`product_surface: ui`): 4 of 5 scenes composite a real capture
  framed in browser chrome with motivated, seekable depth; 1 closing text CTA is connective tissue
- Must satisfy `patterns/anti-slop.md`: the real screenshot is the subject (not background
  texture), no decorative-gradient hero, no emoji feature icons, no invented metrics; vary scene
  durations and give each product scene a distinct camera move (avoid a product-card slideshow)
- All motion deterministic/seekable: wrapper-transform only, `fromTo`+`autoAlpha`, no
  `<img>`-dimension tweens, no clipPath transitions
