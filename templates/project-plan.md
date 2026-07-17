# Project Plan — {project-name}

**Mode:** {promo | showcase | tutorial}
**Product surface:** {ui | none}   <!-- ui = the product has a UI and real captures are the video's spine (default); none = intentional abstract/no-product brand film (CLI lib, API, pure backend) — waives the Phase-3 capture-coverage gate -->
**Aspect:** {16:9 1920×1080 | 9:16 1080×1920 | 1:1 1080×1080 | 4:5 1080×1350}
**Visual identity strategy:** {design-system | hyperframes-style | screenshots}
**Design system:** {none | stripe | linear-app | apple | notion | vercel | airbnb | github | cal | arc | bento}
**HyperFrames style:** {none | Swiss Pulse | Velvet Standard | Deconstructed | Maximalist Type | Data Drift | Soft Signal | Folk Frequency | Shadow Cut}
**Duration:** {30s | 60s | 90s}
**Theme:** {light | dark}
**Voice:** {Matilda | Rachel | Daniel | Josh | custom} — {ElevenLabs voice ID}
**Section transition:** {crossfade | branded swoosh | hard cut | flash-through-white} · speed {slow | medium | fast}
**Music:** {none | Freesound: <name/id> | user-provided: <path>}
**Created:** {date}

## Creative Brief — user-owned selections

Every lever below is the **user's** choice, surfaced as a native prompt in Phase 1 and **never**
self-answered from the Phase-0 codebase analysis (see `SKILL.md` § "creative instinct governs
craft, not the user's choices"). The agent *recommends* (with a smart default pre-highlighted); the
user *decides*. Tick each box only after the user has explicitly confirmed that lever — do not
advance to the storyboard with the identity or voice still unconfirmed.

| Lever | Recorded in | Confirmed by user |
|---|---|---|
| Video mode | `Mode` above | ⬜ |
| Product surface (film the real product?) | `Product surface` above | ⬜ |
| Duration | `Duration` above | ⬜ |
| Theme (light/dark) | `Theme` above | ⬜ |
| Aspect ratio | `Aspect` above | ⬜ |
| Visual identity / design system | `Visual identity strategy` + `Design system`/`HyperFrames style` above | ⬜ |
| Voiceover voice | `Voice` above | ⬜ |
| Section transition · speed | `Section transition` above | ⬜ |
| Music | `Music` above | ⬜ |

**Locked once confirmed — changing a lever invalidates downstream artifacts.** If a confirmed lever
changes later, treat everything derived from it as stale and re-run from the earliest affected phase,
then re-confirm the changed lever:

- **Identity / theme / aspect** → invalidate `DESIGN.md`, `scenes/`, `index.html`, and the render.
- **Duration** → invalidate `storyboard.md` onward (scene timings, composition, voiceover length).
- **Voice / music** → invalidate `voiceover.mp3`, `background-music.mp3`, `out/final.mp4`.

## Phase Tracker

Use `skipped` when a phase is intentionally unnecessary (for example, Phase 2 when
`Product surface: none` and the storyboard's capture plan is `none`).

| Phase | Status | Started | Completed |
|-------|--------|---------|-----------|
| 0. Discovery | ⬜ pending | — | — |
| 1. Storytelling | ⬜ pending | — | — |
| 2. Capture | ⬜ pending | — | — |
| 3. Design | ⬜ pending | — | — |
| 4. Production | ⬜ pending | — | — |
| 5. Audio & Render | ⬜ pending | — | — |

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| | | |
