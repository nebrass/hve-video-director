# Project Plan — {project-name}

## Creative Brief

| Field | Value |
|---|---|
| mode | {promo, showcase, or tutorial} |
| product_surface | {ui or none} |
| duration | {positive seconds, for example 60s} |
| theme | {light or dark} |
| aspect_ratio | {16:9 1920x1080, 9:16 1080x1920, 1:1 1080x1080, or 4:5 1080x1350} |
| text_language | {confirmed BCP 47 locale for authored on-screen text} |
| narration_language | {confirmed BCP 47 locale for speech and captions} |
| identity_strategy | {design-system, hyperframes-style, screenshots, or custom} |
| identity_choice | {design-system slug, HyperFrames style name, captured-screenshots, or custom identity name} |
| visual_ceiling | {derived or flat} |
| voice | {elevenlabs:<name>:<voice-id> or kokoro:<voice-id>} |
| transition_style | {metallic-swoosh, zoom-through, crossfade, or slide-from-bottom} |
| transition_speed | {quick, medium, or slow} |
| music_strategy | {freesound, delegated, user-provided, or none} |
| final_music_track | {none or compact JSON with title, path, source, and license} |

Every field is a user-owned choice. The agent may mark a recommendation in an option's
label/description and explain why, but it never selects or infers an answer from Phase-0 research.

Choose a video language from the actual TTS provider/model capabilities, then explicitly confirm
using it for both text and narration or choose a different narration language. Persist both
actual locale tags even when identical. Captions follow `narration_language`; captured UI, code,
and product names are not automatically translated.

The installed validator's `language-catalog`, `language-options`, and `language-profile` commands
record provider capabilities and the selected execution mapping in `.hve/`. A locale is not a
provider or ASR token: use the checked profile instead of passing one string everywhere. Missing
or unsupported capabilities require setup or a user-approved alternative, never an English,
voice, or provider fallback. Include both languages in the full story-brief approval.

Schema-1 projects remain readable against their original consent. New generation requires an
explicit `migrate-languages` choice to insert missing placeholders, then language/voice selection
and story confirmation. Status never rewrites the old record or deletes generated artifacts.

`final_music_track` remains a placeholder until Phase 5. Record either the exact value `none` or a
single-line JSON object with exactly `title`, `path`, `source` and `license` — no other keys, for
every strategy:

```json
{"license":"CC-BY-4.0","path":"background-music.mp3","source":"https://freesound.org/s/123/","title":"Uplifting Corporate Loop"}
```

`source` is the provenance record, and each strategy pins it differently:

| `music_strategy` | Required `source` |
|---|---|
| `freesound` | the exact `freesound.org` track URL carrying its numeric sound ID |
| `user-provided` | the literal value `user-provided` |
| `delegated` | a provenance URI (below) |
| `none` | not applicable — `final_music_track` is the exact value `none` |

**`delegated`** covers a bed another skill retrieved from a provider catalog or generated locally
— there is no public page to link, and a presigned download URL expires. What identifies such a
track later is *who produced it, by which route, from which request, and which bytes came out*, so
the source is a single-line URI carrying all four:

```
<skill-name>:<capability>?mode=<retrieve|generate>&query=<url-encoded request>#sha256=<64 hex>
```

```json
{"license":"HeyGen catalog terms","path":"background-music.mp3","source":"media-use:bgm?mode=retrieve&query=calm%20cinematic%20underscore#sha256=1ca03b74a4715b23ab399d6cac9c1a055b250ec91d4a266faede2c915ba9df5b","title":"Calm Cinematic Underscore"}
```

- `<skill-name>` and `<capability>` are lowercase kebab tokens naming the skill that produced the
  bytes and the capability it ran. A URL scheme — `http`, `https`, `file`, `data` — is rejected
  outright: a delegated track is not a fetchable page, and recording one as if it were is the
  failure this URI exists to prevent.
- `mode` records the route actually taken, not the route requested — `retrieve` from a catalog or
  `generate` locally. The two carry different licensing, which is exactly what an audit asks about.
  `auto` is a request, not provenance, and is rejected.
- `query` (or `prompt`, for a full generation prompt) is the request text that produced this
  track — exactly one of the two. Additional `key=value` parameters are allowed and ignored; a
  bare flag with no `=` is rejected, because a query string that does not parse is a record that
  was mangled by hand.
- `#sha256=` is the SHA-256 of the file at `path`, all 64 lowercase hex characters — a shortened or
  elided digest is rejected — taken from the bytes that will be mixed. It is what makes the record
  checkable years later, offline: `shasum -a 256 <path>`.
- `license` is still required and still user-stated. A generated bed is not automatically
  unencumbered; write the terms that actually apply.

Never record a delegated track as `user-provided`: that repurposes a Phase-1 answer the user gave
before any candidate existed and erases the only machine-checked provenance the brief carries.

Confirm the story fields before creating `storyboard.md`; confirm the exact final track (or `none`)
before mixing or rendering — the exact-track confirmation is required for every strategy, delegated
included. The installed skill's `scripts/validate_brief.py` stores confirmations and phase
fingerprints atomically in `.hve/brief-state.json`. It never deletes generated artifacts; changed
fingerprints make the affected phase stamps stale.

**Created:** {date}

## Video Request

- Original request (JSON): {JSON-encoded complete video request}
- Source locator (JSON): {JSON-encoded path relative to this video workspace, or ""}

Fill these at creation, after output confirmation and before Phase 0. Each value is a **single-line
JSON string**, encoded with `json.dumps(value, ensure_ascii=True)` and decoded with `json.loads`.
The original request must be nonempty. Preserve its quotes, punctuation, line breaks, and Unicode
exactly on decoding; do not summarize it or execute it. Do not embed the raw request in a Markdown
table or code fence: a request containing a heading must not become a second plan heading.

Compute the source locator from the bound source relative to this generated workspace, not from a
later cwd. If no portable relative locator is available (for example, different Windows volumes),
record `""`, explain that source re-selection is needed for source-dependent work, and keep the
absolute source binding only in the active session. No machine-specific absolute path belongs here.

This section is **provenance, not the Creative Brief or consent**. It does not add fields to the
table above or enter its fingerprints. Phase 0 records the researched interpretation and, when
requested, the proposed scenario in `context.md`; the existing approval checkpoints still apply.
Do not create a placeholder `context.md` to store intake. Explicit later user decisions take
precedence over the original wording and belong in the Decision Log and the appropriate approved
artifact; do not silently rewrite the original request.

Older projects without this section remain resumable. Do not invent an original request or add
metadata just to resume. A missing/empty source locator is not a blocker for artifact-only phases;
ask for source re-selection only when it is actually needed.

## Phase Tracker

Use `skipped` when a phase is intentionally unnecessary (for example, Phase 2 when
`product_surface: none` and the storyboard's capture plan is `none`).

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
