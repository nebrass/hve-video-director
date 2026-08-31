# Patterns Index — the local map

Seven files, all of them things the HyperFrames ecosystem does not own. Everything else a phase needs
— rendering, motion recipes, seams, palettes, audio — is delegated, and the map for *that* is
`compat/ecosystem.md`, not this file.

## Local patterns (in this directory)

| File | What it owns |
|---|---|
| `visual-patterns.md` | Screenshot-as-subject craft, camera & depth on stills (push/drift, scroll-within-frame, motivated parallax, anchored callout, shine sweep, masked reveal), the legibility floor and its footage maths, the emphasis-spending judgment, the repo DON'Ts and the `tl.from()` stagger trap |
| `marker-highlight.md` | The mode → promo-arc mapping and the editorial caps on the drawn-marker device. Implementations are `MARKER_PATTERNS` |
| `transition-catalog.md` | Which transition serves which product-video moment, and the judgment for spending the energy budget. Seam *mechanics* are `SEAM_LAW`, `SEAM_RENDER_MECHANICS`, `CUT_CATALOG` |
| `anti-slop.md` | Cardinal sins, soft tells, polish tells — what separates "shipped by a marketer" from "AI default output", plus AI-tool-promo specifics and CTA discipline |
| `cli-terminal-capture.md` | Real terminal recording via `asciinema` + `agg`: install, shell pre-flight, cast editing, theme pairing, MP4 render, quality gate. The no-dependency fallback is `templates/scene-terminal.html` |
| `authenticated-browser-capture.md` | Attaching Chrome DevTools MCP to an already-authenticated Chrome session, capturing without navigating, and protecting auth data |
| `recorded-flow-capture.md` | Replaying a user-recorded DevTools Recorder flow as human-like capture (ADR-011): the accepted JSON contract, step→tool mapping, pacing law, ledger/cut discipline, whole-flow consent, and the secrets stance |

## Everything else is delegated

**`compat/ecosystem.md` is the wayfinding map for the ecosystem** — one row per capability, giving
the owning skill, what the capability is, and who uses it. It is also the only file in this repo
that holds an upstream *path* (ADR-007). Do not rebuild a second delegation tree here: this index
was that tree once, it rotted silently when upstream re-laid-out its skills, and the compat map
exists so that never happens again.

Each phase workflow cites the capabilities it needs at the point of use. Skill *names* are stable
and may be written anywhere; intra-skill paths may not.

## Reaching past the local patterns

The handful of capabilities no workflow currently names, listed so they resolve to a name instead
of being re-derived:

- Ready colour systems paired to a named identity → `hyperframes-creative` → `PALETTES`.
- Scene *arrangement* — picture-in-picture, text-behind-subject, title card, slide show →
  `hyperframes-creative` → `COMPOSITION_RECIPES`. Not the same document as
  `COMPOSITION_ARCHITECTURE` (the project shape and the root `index.html`); the two carry
  near-identical names and this index pointed at the wrong one once — see `compat/ecosystem.md`
  § Disambiguation.
- Animated charts, counters and bar races → `hyperframes-creative` → `DATA_IN_MOTION`.
- No strong opinion on motion, colour or type → `hyperframes-creative` → `HOUSE_STYLE`.
- Karaoke / beat-synced caption styling → `media-use` → `CAPTIONS_MOTION`. On-screen captions are
  **optional in promo and showcase** and mandatory in tutorial mode, which
  `workflows/phase-5-audio.md` states as a deliberate override of this default.
- No `ELEVENLABS_API_KEY` → `media-use` → `TTS_LOCAL` (native TTS; its local prerequisites are
  `AUDIO_REQUIREMENTS`).

Read by task, never by default — loading a whole skill at once eats the context a scene builder
needs.
