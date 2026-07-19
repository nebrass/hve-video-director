# Project Plan — {project-name}

## Creative Brief

| Field | Value |
|---|---|
| mode | {promo, showcase, or tutorial} |
| product_surface | {ui or none} |
| duration | {positive seconds, for example 60s} |
| theme | {light or dark} |
| aspect_ratio | {16:9 1920x1080, 9:16 1080x1920, 1:1 1080x1080, or 4:5 1080x1350} |
| identity_strategy | {design-system, hyperframes-style, screenshots, or custom} |
| identity_choice | {design-system slug, HyperFrames style name, captured-screenshots, or custom identity name} |
| voice | {elevenlabs:<name>:<voice-id> or kokoro:<voice-id>} |
| transition_style | {metallic-swoosh, zoom-through, crossfade, or slide-from-bottom} |
| transition_speed | {quick, medium, or slow} |
| music_strategy | {freesound, user-provided, or none} |
| final_music_track | {none or compact JSON with title, path, source, and license} |

Every field is a user-owned choice. The agent may mark a recommendation in an option's
label/description and explain why, but it never selects or infers an answer from Phase-0 research.

`final_music_track` remains a placeholder until Phase 5. Record either the exact value `none` or a
single-line JSON object, for example:

```json
{"license":"CC-BY-4.0","path":"background-music.mp3","source":"https://freesound.org/s/123/","title":"Example Track"}
```

Confirm the story fields before creating `storyboard.md`; confirm the exact final track (or `none`)
before mixing or rendering. The installed skill's `scripts/validate_brief.py` stores confirmations
and phase fingerprints atomically in `.hve/brief-state.json`. It never deletes generated artifacts;
changed fingerprints make the affected phase stamps stale.

**Created:** {date}

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
